from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .candidates.base import CandidateBase


Coefficients = tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class Episode:
    channels: np.ndarray
    targets: np.ndarray


@dataclass(frozen=True)
class OracleEpisode:
    episode: Episode
    active_index: int
    context_index: int
    coefficients: Coefficients


@dataclass(frozen=True)
class ForecastQuery:
    channels: np.ndarray


def _fit_models(episode: Episode, active: int, context: int):
    x, c, y = episode.channels[:, active], np.rint(episode.channels[:, context]).astype(int), episode.targets
    models: dict[int, tuple[float, float]] = {}
    squared_error = 0.0
    for regime in (-1, 0, 1):
        mask = c == regime
        if mask.sum() < 2:
            continue
        design = np.column_stack((x[mask], np.ones(mask.sum())))
        theta = np.linalg.lstsq(design, y[mask], rcond=None)[0]
        models[regime] = (float(theta[0]), float(theta[1]))
        squared_error += float(np.square(design @ theta - y[mask]).sum())
    return models, squared_error / len(y), len(y) * 12


def _screen(episode: Episode):
    matrix = episode.channels
    rows, width = matrix.shape
    context = min(
        range(width),
        key=lambda j: float(np.abs(matrix[:, j] - np.rint(matrix[:, j])).mean())
        + (3 - len(set(np.rint(matrix[:, j]).astype(int)) & {-1, 0, 1})),
    )
    choices = []
    for active in range(width):
        if active != context:
            models, error, regression_ops = _fit_models(episode, active, context)
            choices.append((error if len(models) == 3 else float("inf"), active, models, regression_ops))
    error, active, models, regression_ops = min(choices)
    return active, context, models, rows * width * 5 + regression_ops, error


def _exhaustive(episode: Episode):
    matrix = episode.channels
    rows, width = matrix.shape
    choices = []
    for context in range(width):
        rounded = np.rint(matrix[:, context])
        if float(np.abs(matrix[:, context] - rounded).mean()) > 1e-8:
            continue
        for active in range(width):
            if active != context:
                models, error, _ = _fit_models(episode, active, context)
                if len(models) == 3:
                    choices.append((error, active, context, models))
    error, active, context, models = min(choices)
    return active, context, models, rows * width * width * 12, error


def _linear_scores(episode: Episode) -> np.ndarray:
    matrix = episode.channels - episode.channels.mean(axis=0)
    target = episode.targets - episode.targets.mean()
    return np.abs(matrix.T @ target) / (np.sqrt(np.square(matrix).sum(axis=0) * np.square(target).sum()) + 1e-12)


class ContinuousCandidate(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_input_ops = self.last_search_ops = self.last_execution_ops = 0
        self.last_memory_reads = self.last_bytes_loaded = 0
        self.last_cache_hit = False

    def _record(self, query: ForecastQuery, search: int, execution: int, hit: bool, input_ops: int) -> None:
        self.last_input_ops = input_ops
        self.last_search_ops = search
        self.last_execution_ops = execution
        self.last_memory_reads = input_ops + search
        self.last_bytes_loaded = input_ops * 8 + self.state_bytes()
        self.last_ops = input_ops + search + execution
        self.last_cache_hit = hit


class SwitchingAR(ContinuousCandidate):
    discovery = "screen"
    query_overhead = 0
    update_overhead = 0

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.active = self.context = 0
        self.models: dict[int, tuple[float, float]] = {}

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        found = _exhaustive(episode) if self.discovery == "exhaustive" else _screen(episode)
        self.active, self.context, self.models, self.fit_ops, _ = found

    def query(self, query: ForecastQuery, steps: int) -> tuple[float, ...]:
        x, output, changes, previous = float(query.channels[0, self.active]), [], 0, None
        for row in query.channels[:steps]:
            regime = int(round(float(row[self.context])))
            changes += int(previous is not None and regime != previous)
            a, b = self.models.get(regime, (0.0, 0.0))
            x = a * x + b
            output.append(x)
            previous = regime
        self._record(query, self.query_overhead + changes, 5 * len(output), len(output) == steps, len(output) + 1)
        return tuple(output)

    def update(self, episode: Episode, target: object = None) -> None:
        models, _, ops = _fit_models(episode, self.active, self.context)
        self.models.update(models)
        self.update_ops = ops + self.update_overhead

    def state_bytes(self) -> int:
        return 96 + len(self.models) * 40


class ExhaustiveSwitchingAR(SwitchingAR):
    discovery = "exhaustive"


class ScreenedSwitchingAR(SwitchingAR):
    pass


class EventPredictiveState(SwitchingAR):
    query_overhead = 5
    update_overhead = 24

    def state_bytes(self) -> int:
        return super().state_bytes() + 64


class VarianceTriggeredKalman(SwitchingAR):
    query_overhead = 2

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.covariances = {regime: np.eye(2) * 1e9 for regime in (-1, 0, 1)}

    def _learn(self, episode: Episode, reset_on_event: bool) -> int:
        triggered: set[int] = set()
        for x, row, y in zip(episode.channels[:, self.active], episode.channels, episode.targets):
            regime = int(round(float(row[self.context])))
            phi = np.array((x, 1.0))
            theta = np.array(self.models.get(regime, (0.0, 0.0)))
            if reset_on_event and regime not in triggered and abs(float(y - phi @ theta)) > 1e-5:
                theta, self.covariances[regime] = np.zeros(2), np.eye(2) * 1e9
                triggered.add(regime)
            covariance = self.covariances[regime]
            gain = covariance @ phi / (1.0 + phi @ covariance @ phi)
            theta += gain * float(y - phi @ theta)
            self.covariances[regime] = covariance - np.outer(gain, phi) @ covariance
            self.models[regime] = (float(theta[0]), float(theta[1]))
        return len(episode.targets) * 24

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.active, self.context, _, screen_ops, _ = _screen(episode)
        self.models = {}
        self.fit_ops = screen_ops + self._learn(episode, False)

    def update(self, episode: Episode, target: object = None) -> None:
        self.update_ops = self._learn(episode, True)

    def state_bytes(self) -> int:
        return super().state_bytes() + sum(value.nbytes for value in self.covariances.values())


class LastValueForecaster(ContinuousCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.active = 0

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.active = int(np.argmax(_linear_scores(episode)))
        self.fit_ops = episode.channels.size * 4

    def query(self, query: ForecastQuery, steps: int) -> tuple[float, ...]:
        value = float(query.channels[0, self.active])
        answer = (value,) * steps
        self._record(query, 0, steps, False, 1)
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        self.update_ops = len(episode.targets)

    def state_bytes(self) -> int:
        return 72


class RandomContinuousGuess(ContinuousCandidate):
    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, query: ForecastQuery, steps: int) -> tuple[float, ...]:
        answer = tuple((((self.seed + index * 7919) % 2001) - 1000) / 1000 for index in range(steps))
        self._record(query, 0, steps, False, 0)
        return answer

    def update(self, episode: Episode, target: object = None) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class DenseLinearStateSpace(ContinuousCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.weights = np.zeros(1)
        self.active = 0

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        design = np.column_stack((episode.channels, np.ones(len(episode.targets))))
        self.weights = np.linalg.lstsq(design, episode.targets, rcond=None)[0]
        self.active = int(np.argmax(np.abs(self.weights[:-1])))
        rows, width = episode.channels.shape
        self.fit_ops = rows * width * width + width ** 3

    def query(self, query: ForecastQuery, steps: int) -> tuple[float, ...]:
        output, current = [], float(query.channels[0, self.active])
        for source in query.channels[:steps]:
            row = source.copy()
            row[self.active] = current
            current = float(np.r_[row, 1.0] @ self.weights)
            output.append(current)
        width = query.channels.shape[1]
        self._record(query, width * steps, width * steps, False, width * steps)
        return tuple(output)

    def update(self, episode: Episode, target: object = None) -> None:
        self.fit(episode, episode.channels.shape[1], len(episode.targets))
        self.update_ops = self.fit_ops

    def state_bytes(self) -> int:
        return 72 + self.weights.nbytes


class EchoStateForecaster(ContinuousCandidate):
    hidden = 12

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.input_weights = self.recurrent = self.readout = np.zeros((1, 1))
        self.active = 0

    def fit(self, episode: Episode, universe_size: int, max_depth: int) -> None:
        rng, width = np.random.default_rng(self.seed), episode.channels.shape[1]
        self.input_weights = rng.normal(0, 0.18, (width, self.hidden))
        self.recurrent = rng.normal(0, 0.08, (self.hidden, self.hidden))
        state, states = np.zeros(self.hidden), []
        for row in episode.channels:
            state = np.tanh(row @ self.input_weights + state @ self.recurrent)
            states.append(np.r_[state, 1.0])
        design = np.asarray(states)
        self.readout = np.linalg.solve(design.T @ design + np.eye(self.hidden + 1) * 1e-3, design.T @ episode.targets)
        self.active = int(np.argmax(_linear_scores(episode)))
        rows = len(episode.targets)
        self.fit_ops = rows * (width * self.hidden + self.hidden ** 2) + rows * self.hidden ** 2 + self.hidden ** 3

    def query(self, query: ForecastQuery, steps: int) -> tuple[float, ...]:
        state, output, current = np.zeros(self.hidden), [], float(query.channels[0, self.active])
        for source in query.channels[:steps]:
            row = source.copy()
            row[self.active] = current
            state = np.tanh(row @ self.input_weights + state @ self.recurrent)
            current = float(np.r_[state, 1.0] @ self.readout)
            output.append(current)
        width = query.channels.shape[1]
        ops = steps * (width * self.hidden + self.hidden ** 2)
        self._record(query, ops, steps * self.hidden, False, width * steps)
        return tuple(output)

    def update(self, episode: Episode, target: object = None) -> None:
        self.fit(episode, episode.channels.shape[1], len(episode.targets))
        self.update_ops = self.fit_ops

    def state_bytes(self) -> int:
        return 96 + self.input_weights.nbytes + self.recurrent.nbytes + self.readout.nbytes


class OracleSparseDynamics(SwitchingAR):
    def fit(self, wrapped: OracleEpisode, universe_size: int, max_depth: int) -> None:
        self.active, self.context = wrapped.active_index, wrapped.context_index
        self.models = {regime: wrapped.coefficients[regime + 1] for regime in (-1, 0, 1)}
        self.fit_ops = 6

    def update(self, wrapped: OracleEpisode, target: object = None) -> None:
        self.fit(wrapped, 0, 0)
        self.update_ops = 2

    def state_bytes(self) -> int:
        return 96
