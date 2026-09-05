"""Source-identical WT-01 factorial core.

R controls recursive self-feeding, U controls post-reveal slot-local RLS, and C
controls the historical origin-relative +/-4 saturation.  Fit is identical for
all eight roles and to the historical candidate frozen at commit 4952515.
"""
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


class FactorialCandidate(CandidateBase):
    RECURSIVE = True
    UPDATE_ENABLED = True
    CLIP_ENABLED = True

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0.0
        self._slots: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    @property
    def factors(self) -> tuple[bool, bool, bool]:
        return self.RECURSIVE, self.UPDATE_ENABLED, self.CLIP_ENABLED

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
        evaluated_steps = int(steps) if self.RECURSIVE else 1
        for _ in range(evaluated_steps):
            with np.errstate(over="ignore", invalid="ignore"):
                proposed = _feature(current, delta, source.control) @ weights
            residual = current - origin + proposed
            if self.CLIP_ENABLED:
                residual = np.clip(residual, -RESIDUAL_BOUND, RESIDUAL_BOUND)
            following = origin + residual
            if not np.isfinite(following).all():
                raise ValueError("WT residual query diverged without a finite prediction")
            prediction.append(following.copy())
            delta, current = following - current, following
        if not self.RECURSIVE:
            prediction *= int(steps)
        result = np.stack(prediction)
        if not np.isfinite(result).all():
            raise ValueError("WT residual query produced a non-finite prediction")
        if self.CLIP_ENABLED and np.max(np.abs(result - origin)) > RESIDUAL_BOUND + 1e-12:
            raise ValueError("WT residual query violated the frozen correction bound")
        dimension = len(_feature(current, delta, source.control))
        self.last_ops = float(evaluated_steps * (2 * dimension * WIDTH + 3 * WIDTH))
        self.last_bytes_touched = float(
            history.nbytes + result.nbytes + weights.nbytes + precision.nbytes
        )
        return result.tolist()

    def update(self, source: WTReveal) -> None:
        if not isinstance(source, WTReveal):
            raise ValueError("WT residual update requires a post-prediction reveal")
        if not self.UPDATE_ENABLED:
            self.update_ops = self.last_update_bytes = 0.0
            return
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


class VAR2RLSBoundCandidate(FactorialCandidate):
    """Same fitted rule expressed directly as a controlled affine VAR(2)."""

    def query(self, source: WTQuery, steps: int):
        if not isinstance(source, WTQuery) or int(steps) != source.horizon:
            raise ValueError("invalid WT VAR(2)/ARX query")
        history = _matrix(source.history)
        precision, weights = self._state(source.slot)
        origin = history[-1].copy()
        previous, current = history[-2].copy(), origin.copy()
        identity = np.eye(WIDTH)
        intercept, a, b, control_weight = weights[0], weights[1:11], weights[11:21], weights[21]
        transition = identity + a + b
        prediction = []
        for _ in range(int(steps)):
            with np.errstate(over="ignore", invalid="ignore"):
                following = (intercept + current @ transition - previous @ b
                             + float(source.control) * control_weight)
            following = origin + np.clip(following - origin, -RESIDUAL_BOUND, RESIDUAL_BOUND)
            if not np.isfinite(following).all():
                raise ValueError("WT VAR(2)/ARX query produced a non-finite prediction")
            prediction.append(following.copy())
            previous, current = current, following
        result = np.stack(prediction)
        dimension = weights.shape[0]
        self.last_ops = float(int(steps) * (2 * dimension * WIDTH + 3 * WIDTH))
        self.last_bytes_touched = float(
            history.nbytes + result.nbytes + weights.nbytes + precision.nbytes
        )
        return result.tolist()
