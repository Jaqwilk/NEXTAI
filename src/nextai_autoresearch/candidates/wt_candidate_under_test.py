from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase
from nextai_autoresearch.wt_prequential_contract import WTQuery, WTReveal, WTTraining


RIDGE = 1e-3
RESIDUAL_BOUND = 4.0
WIDTH = 10


def _matrix(value) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != WIDTH or not np.isfinite(array).all():
        raise ValueError("WT residual tensors must be finite ten-channel matrices")
    return array


def _feature(current: np.ndarray, delta: np.ndarray, control: float) -> np.ndarray:
    return np.concatenate(([1.0], current, delta, [float(control)]))


class Candidate(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0.0
        self._slots: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    def fit(self, training: WTTraining, universe_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(universe_size):
            raise ValueError("WT residual fit requires exactly K frozen episodes")
        features: list[np.ndarray] = []
        targets: list[np.ndarray] = []
        for episode in training.episodes:
            history, target = _matrix(episode.history), _matrix(episode.target)
            current = history[-1].copy()
            delta = current - history[-2]
            for revealed in target:
                features.append(_feature(current, delta, episode.control))
                next_delta = revealed - current
                targets.append(next_delta)
                current, delta = revealed, next_delta
        design, response = np.stack(features), np.stack(targets)
        dimension = design.shape[1]
        self._precision = np.linalg.inv(design.T @ design + RIDGE * np.eye(dimension))
        self._weights = self._precision @ design.T @ response
        if not np.isfinite(self._weights).all():
            raise ValueError("WT residual fit produced non-finite state")
        rows = len(design)
        self.fit_ops = float(rows * (dimension * dimension + dimension * WIDTH))
        self.meta_fit_ops = self.fit_ops
        self._slots.clear()

    def _state(self, slot: int) -> tuple[np.ndarray, np.ndarray]:
        if slot not in self._slots:
            self._slots[slot] = (self._precision.copy(), self._weights.copy())
        return self._slots[slot]

    def query(self, source: WTQuery, steps: int):
        if not isinstance(source, WTQuery) or int(steps) != source.horizon:
            raise ValueError("invalid WT residual query")
        history = _matrix(source.history)
        precision, weights = self._state(source.slot)
        origin = history[-1].copy()
        current = origin.copy()
        delta = current - history[-2]
        prediction = []
        for _ in range(int(steps)):
            proposed = _feature(current, delta, source.control) @ weights
            residual = np.clip(current - origin + proposed, -RESIDUAL_BOUND, RESIDUAL_BOUND)
            following = origin + residual
            prediction.append(following.copy())
            delta, current = following - current, following
        result = np.stack(prediction)
        if not np.isfinite(result).all() or np.max(np.abs(result - origin)) > RESIDUAL_BOUND + 1e-12:
            raise ValueError("WT residual query violated the frozen correction bound")
        dimension = len(_feature(current, delta, source.control))
        self.last_ops = float(int(steps) * (2 * dimension * WIDTH + 3 * WIDTH))
        self.last_bytes_touched = float(
            history.nbytes + result.nbytes + weights.nbytes + precision.nbytes
        )
        return result.tolist()

    def update(self, source: WTReveal) -> None:
        if not isinstance(source, WTReveal):
            raise ValueError("WT residual update requires a post-prediction reveal")
        history, target = _matrix(source.history), _matrix(source.target)
        precision, weights = self._state(source.slot)
        current = history[-1].copy()
        delta = current - history[-2]
        operations = 0
        for revealed in target:
            feature = _feature(current, delta, source.control)
            projected = precision @ feature
            gain = projected / (1.0 + feature @ projected)
            next_delta = revealed - current
            error = next_delta - feature @ weights
            weights += gain[:, None] * error
            precision -= np.outer(gain, feature @ precision)
            current, delta = revealed, next_delta
            operations += 2 * len(feature) * WIDTH + 4 * len(feature) ** 2
        if not np.isfinite(weights).all() or not np.isfinite(precision).all():
            raise ValueError("WT residual update produced non-finite local state")
        self.update_ops = float(operations)
        self.last_update_bytes = float(history.nbytes + target.nbytes + weights.nbytes + precision.nbytes)

    def state_bytes(self) -> int:
        total = self._precision.nbytes + self._weights.nbytes
        total += sum(precision.nbytes + weights.nbytes for precision, weights in self._slots.values())
        return int(total)
