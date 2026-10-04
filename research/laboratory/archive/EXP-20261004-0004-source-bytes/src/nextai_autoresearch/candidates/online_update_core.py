from __future__ import annotations

import math

import numpy as np

from .base import CandidateBase, CandidateMetadata
from nextai_autoresearch.online_update_contract import (
    OnlineObservation, OnlineTraining, PrivilegedObservation, PrivilegedTraining,
)


def _raw(values: tuple[float, ...]) -> np.ndarray:
    return np.r_[1.0, np.asarray(values, dtype=float)]


def _polynomial(values: tuple[float, ...]) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    products = np.asarray([x[i] * x[j] for i in range(len(x)) for j in range(i, len(x))])
    return np.r_[1.0, x / math.sqrt(len(x)), products / math.sqrt(max(1, len(products)))]


class OnlineCandidate(CandidateBase):
    metadata = CandidateMetadata("online-update", "meta_learned_online_state_update", "Bounded prequential state update.")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_bytes_touched = self.last_update_bytes = 0.0
        self.meta_fit_ops = 0.0

    def _public(self, facts):
        if isinstance(facts, PrivilegedTraining):
            return facts.public
        if not isinstance(facts, OnlineTraining):
            raise TypeError("online candidates require OnlineTraining")
        return facts

    def _record_query(self, operations: float, state_values: int) -> None:
        self.last_ops = float(operations)
        self.last_bytes_touched = float(8 * state_values)

    def _record_update(self, operations: float, state_values: int) -> None:
        self.update_ops = float(operations)
        self.last_update_bytes = float(8 * state_values)


class NoUpdate(OnlineCandidate):
    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        training = self._public(facts)
        targets = [item.target for stream in training.streams for item in stream.sequence]
        self.mean = float(np.mean(targets))
        self.fit_ops = self.meta_fit_ops = float(len(targets))

    def query(self, source: OnlineObservation, steps: int):
        del steps
        self._record_query(1, 1)
        return self.mean

    def update(self, source: OnlineObservation, target: float) -> None:
        del source, target
        self._record_update(0, 0)

    def state_bytes(self) -> int:
        return 16


class LMS(OnlineCandidate):
    def __init__(self, seed: int = 0, *, additive: bool = False, polynomial: bool = False) -> None:
        super().__init__(seed)
        self.additive, self.polynomial = additive, polynomial
        self.weights: dict[int, np.ndarray] = {}
        self.eta = 0.25 if polynomial else 0.35

    def _feature(self, source: OnlineObservation) -> np.ndarray:
        return _polynomial(source.values) if self.polynomial else _raw(source.values)

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        training = self._public(facts)
        self.weights = {}
        self.fit_ops = self.meta_fit_ops = float(sum(len(stream.sequence) for stream in training.streams))

    def query(self, source: OnlineObservation, steps: int):
        del steps
        phi = self._feature(source)
        weights = self.weights.setdefault(source.slot, np.zeros(len(phi)))
        self._record_query(2 * len(phi), 2 * len(phi))
        return float(phi @ weights)

    def update(self, source: OnlineObservation, target: float) -> None:
        phi = self._feature(source)
        weights = self.weights.setdefault(source.slot, np.zeros(len(phi)))
        prediction = 0.0 if self.additive else float(phi @ weights)
        weights += self.eta * (target - prediction) * phi / (float(phi @ phi) + 1e-6)
        self._record_update(5 * len(phi), 2 * len(phi))

    def state_bytes(self) -> int:
        return int(64 + sum(value.nbytes for value in self.weights.values()))


class RLS(OnlineCandidate):
    def __init__(self, seed: int = 0, *, polynomial: bool = False) -> None:
        super().__init__(seed)
        self.polynomial = polynomial
        self.states: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    def _feature(self, source: OnlineObservation) -> np.ndarray:
        return _polynomial(source.values) if self.polynomial else _raw(source.values)

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        training = self._public(facts)
        self.states = {}
        self.fit_ops = self.meta_fit_ops = float(sum(len(stream.sequence) for stream in training.streams))

    def _state(self, slot: int, size: int):
        if slot not in self.states:
            self.states[slot] = (np.zeros(size), np.full(size, 10.0) if self.polynomial else np.eye(size) * 10.0)
        return self.states[slot]

    def query(self, source: OnlineObservation, steps: int):
        del steps
        phi = self._feature(source)
        weights, covariance = self._state(source.slot, len(phi))
        self._record_query(2 * len(phi), weights.size + covariance.size)
        return float(phi @ weights)

    def update(self, source: OnlineObservation, target: float) -> None:
        phi = self._feature(source)
        weights, covariance = self._state(source.slot, len(phi))
        if covariance.ndim == 1:
            gain = covariance * phi / (0.99 + float(np.sum(covariance * phi * phi)))
            weights += gain * (target - float(phi @ weights))
            covariance[:] = (covariance - gain * phi * covariance) / 0.99
            operations = 10 * len(phi)
        else:
            projected = covariance @ phi
            gain = projected / (0.99 + float(phi @ projected))
            weights += gain * (target - float(phi @ weights))
            covariance[:] = (covariance - np.outer(gain, phi) @ covariance) / 0.99
            operations = 4 * len(phi) ** 2
        self._record_update(operations, weights.size + covariance.size)

    def state_bytes(self) -> int:
        return int(64 + sum(weights.nbytes + covariance.nbytes for weights, covariance in self.states.values()))


class KernelDictionary(OnlineCandidate):
    def __init__(self, seed: int = 0, *, nearest: bool = False) -> None:
        super().__init__(seed)
        self.nearest = nearest
        self.memory: dict[int, list[tuple[np.ndarray, float]]] = {}
        self.limit = 32

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        training = self._public(facts)
        self.memory = {}
        self.fit_ops = self.meta_fit_ops = float(sum(len(stream.sequence) for stream in training.streams))

    def query(self, source: OnlineObservation, steps: int):
        del steps
        x, rows = np.asarray(source.values), self.memory.setdefault(source.slot, [])
        if not rows:
            self._record_query(len(x), len(x))
            return 0.0
        distances = np.asarray([float(np.sum((x - item) ** 2)) for item, _ in rows])
        if self.nearest:
            selected = np.argsort(distances)[:min(8, len(rows))]
            answer = statistics_mean([rows[int(index)][1] for index in selected])
        else:
            weights = np.exp(-0.5 * distances)
            answer = float(sum(weight * rows[index][1] for index, weight in enumerate(weights)) / (weights.sum() + 1e-12))
        self._record_query(len(rows) * (3 * len(x) + 4), len(rows) * (len(x) + 1))
        return answer

    def update(self, source: OnlineObservation, target: float) -> None:
        rows = self.memory.setdefault(source.slot, [])
        rows.append((np.asarray(source.values).copy(), float(target)))
        if len(rows) > self.limit:
            rows.pop(0)
        self._record_update(len(source.values) + 2, len(rows) * (len(source.values) + 1))

    def state_bytes(self) -> int:
        return int(64 + sum(sum(item.nbytes + 8 for item, _ in rows) for rows in self.memory.values()))


def statistics_mean(values: list[float]) -> float:
    return sum(values) / len(values)


class ChangePointBank(OnlineCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.banks: dict[int, list[tuple[np.ndarray, np.ndarray]]] = {}
        self.active: dict[int, int] = {}

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        training = self._public(facts)
        self.banks, self.active = {}, {}
        self.fit_ops = self.meta_fit_ops = float(sum(len(stream.sequence) for stream in training.streams))

    def _bank(self, source: OnlineObservation):
        size = len(source.values) + 1
        if source.slot not in self.banks:
            self.banks[source.slot] = [(np.zeros(size), np.eye(size) * 10.0)]
            self.active[source.slot] = 0
        return self.banks[source.slot]

    def query(self, source: OnlineObservation, steps: int):
        del steps
        phi, bank = _raw(source.values), self._bank(source)
        weights = bank[self.active[source.slot]][0]
        self._record_query(2 * len(phi), sum(w.size + p.size for w, p in bank))
        return float(phi @ weights)

    def update(self, source: OnlineObservation, target: float) -> None:
        phi, bank = _raw(source.values), self._bank(source)
        errors = [abs(target - float(phi @ weights)) for weights, _ in bank]
        active = self.active[source.slot]
        best = int(np.argmin(errors))
        if errors[active] > 1.0:
            if errors[best] < 0.7 * errors[active]:
                active = best
            elif len(bank) < 3:
                bank.append((np.zeros(len(phi)), np.eye(len(phi)) * 10.0))
                active = len(bank) - 1
            self.active[source.slot] = active
        weights, covariance = bank[active]
        projected = covariance @ phi
        gain = projected / (1.0 + float(phi @ projected))
        weights += gain * (target - float(phi @ weights))
        covariance[:] = covariance - np.outer(gain, phi) @ covariance
        self._record_update(4 * len(phi) ** 2 + len(bank) * 2 * len(phi), sum(w.size + p.size for w, p in bank))

    def state_bytes(self) -> int:
        return int(96 + sum(sum(w.nbytes + p.nbytes for w, p in bank) for bank in self.banks.values()))


class MetaUpdate(OnlineCandidate):
    GRID = tuple((eta, threshold) for eta in (0.08, 0.25, 0.6) for threshold in (0.6, 1.2, 2.0))

    def __init__(self, seed: int = 0, *, independent: bool = False) -> None:
        super().__init__(seed)
        self.independent = independent
        self.params = (0.25, 1.2)
        self.banks: dict[int, list[np.ndarray]] = {}
        self.active: dict[int, int] = {}
        self.energy: dict[int, float] = {}

    def _loss(self, sequence, eta: float, threshold: float) -> tuple[float, float]:
        bank, active, energy, loss, operations = [None], 0, 1.0, 0.0, 0.0
        for item in sequence:
            phi = _polynomial(item.observation.values)
            if bank[0] is None:
                bank[0] = np.zeros(len(phi))
            prediction = float(phi @ bank[active])
            loss += (prediction - item.target) ** 2
            errors = [abs(item.target - float(phi @ weights)) for weights in bank]
            normalized = errors[active] / (math.sqrt(energy) + 0.1)
            best = int(np.argmin(errors))
            if normalized > threshold:
                if errors[best] < 0.7 * errors[active]:
                    active = best
                elif len(bank) < 3:
                    bank.append(np.zeros(len(phi)))
                    active = len(bank) - 1
            error = item.target - float(phi @ bank[active])
            bank[active] += eta * error * phi / (float(phi @ phi) + 1e-6)
            energy = 0.97 * energy + 0.03 * item.target ** 2
            operations += len(phi) * (7 + 2 * len(bank))
        scale = sum(item.target ** 2 for item in sequence) + 1e-12
        return loss / scale, operations

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        training = self._public(facts)
        grid = tuple(self.GRID)
        operations = 0.0
        if self.independent:
            winners = []
            for stream in training.streams:
                scored = []
                for params in grid:
                    loss, used = self._loss(stream.sequence, *params)
                    operations += used
                    scored.append((loss, params))
                winners.append(min(scored)[1])
            self.params = min(grid, key=lambda item: (-winners.count(item), item))
        else:
            scored = []
            for params in grid:
                losses = []
                for stream in training.streams:
                    loss, used = self._loss(stream.sequence, *params)
                    operations += used
                    losses.append(loss)
                scored.append((sum(losses) / len(losses), params))
            self.params = min(scored)[1]
        self.banks, self.active, self.energy = {}, {}, {}
        self.fit_ops = self.meta_fit_ops = operations

    def _bank(self, source: OnlineObservation):
        if source.slot not in self.banks:
            self.banks[source.slot] = [np.zeros(len(_polynomial(source.values)))]
            self.active[source.slot], self.energy[source.slot] = 0, 1.0
        return self.banks[source.slot]

    def query(self, source: OnlineObservation, steps: int):
        del steps
        phi, bank = _polynomial(source.values), self._bank(source)
        self._record_query(2 * len(phi), sum(value.size for value in bank))
        return float(phi @ bank[self.active[source.slot]])

    def update(self, source: OnlineObservation, target: float) -> None:
        eta, threshold = self.params
        phi, bank = _polynomial(source.values), self._bank(source)
        active = self.active[source.slot]
        errors = [abs(target - float(phi @ weights)) for weights in bank]
        normalized = errors[active] / (math.sqrt(self.energy[source.slot]) + 0.1)
        best = int(np.argmin(errors))
        if normalized > threshold:
            if errors[best] < 0.7 * errors[active]:
                active = best
            elif len(bank) < 3:
                bank.append(np.zeros(len(phi)))
                active = len(bank) - 1
            self.active[source.slot] = active
        error = target - float(phi @ bank[active])
        bank[active] += eta * error * phi / (float(phi @ phi) + 1e-6)
        self.energy[source.slot] = 0.97 * self.energy[source.slot] + 0.03 * target ** 2
        self._record_update(len(phi) * (7 + 2 * len(bank)), sum(value.size for value in bank))

    def state_bytes(self) -> int:
        return int(128 + sum(sum(value.nbytes for value in bank) for bank in self.banks.values()))


class Oracle(OnlineCandidate):
    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, PrivilegedTraining):
            raise TypeError("oracle requires privileged training envelope")
        self.fit_ops = self.meta_fit_ops = 0.0

    def query(self, source: PrivilegedObservation, steps: int):
        del steps
        x, first, second = np.asarray(source.public.values), np.asarray(source.first), np.asarray(source.second)
        projection = float(x @ first)
        if source.mechanism == "mixed_linear":
            answer = projection
        elif source.mechanism == "mixed_quadratic":
            answer = projection * float(x @ second)
        else:
            answer = math.sin(projection)
        self._record_query(2 * len(x) + 2, 2 * len(x))
        return answer

    def update(self, source: OnlineObservation, target: float) -> None:
        del source, target
        self._record_update(0, 0)

    def state_bytes(self) -> int:
        return 64


class Candidate(MetaUpdate):
    pass
