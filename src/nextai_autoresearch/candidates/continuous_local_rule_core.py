from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


RIDGE = 0.001
REPAIR_Z = 6.0
UPDATE_ETA = 0.05
OUTPUT_BOUND = 1.5
CHANNELS = 4
RAW_WIDTH = 12
QUAD_WIDTH = 1 + RAW_WIDTH + RAW_WIDTH * (RAW_WIDTH + 1) // 2


def _raw(left: tuple[float, ...], center: tuple[float, ...], right: tuple[float, ...]) -> np.ndarray:
    return np.asarray((*left, *center, *right), dtype=float)


def _linear(raw: np.ndarray) -> np.ndarray:
    return np.concatenate(([1.0], raw))


def _quadratic(raw: np.ndarray) -> np.ndarray:
    features = [1.0, *raw]
    features.extend(raw[i] * raw[j] for i in range(RAW_WIDTH) for j in range(i, RAW_WIDTH))
    return np.asarray(features, dtype=float)


def _solve(features: np.ndarray, targets: np.ndarray) -> np.ndarray:
    gram = features.T @ features
    return np.linalg.solve(gram + RIDGE * np.eye(gram.shape[0]), features.T @ targets)


class ContinuousLocalRule(CandidateBase):
    metadata = CandidateMetadata("continuous_local_rule", "continuous_cellular", "Source-identical anonymous local rule")

    def __init__(self, seed: int = 0, *, mode: str = "sparse") -> None:
        super().__init__(seed)
        if mode not in {"sparse", "dense", "frozen"}:
            raise ValueError(mode)
        self.mode = mode
        self.weights = np.zeros((QUAD_WIDTH, CHANNELS), dtype=float)
        for channel in range(CHANNELS):
            self.weights[1 + CHANNELS + channel, channel] = 1.0
        self.repair_weights = np.zeros((CHANNELS, CHANNELS), dtype=float)
        self.repair_scale = np.ones(CHANNELS, dtype=float)
        self.last_bytes_touched = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        rows = tuple(facts)
        if not rows or not all(all(hasattr(row, field) for field in ("left", "center", "right", "target")) for row in rows):
            raise TypeError("continuous local learner requires Transition rows")
        raw_rows = np.asarray([_raw(row.left, row.center, row.right) for row in rows])
        targets = np.asarray([row.target for row in rows], dtype=float)
        quad = np.asarray([_quadratic(row) for row in raw_rows])
        vectors = np.asarray([
            vector for row in rows for vector in (row.left, row.center, row.right, row.target)
        ], dtype=float)
        repair_ops = 0
        if self.mode != "frozen":
            self.weights = _solve(quad, targets)
            for channel in range(CHANNELS):
                others = [index for index in range(CHANNELS) if index != channel]
                design = np.column_stack((np.ones(len(vectors)), vectors[:, others]))
                coefficients = _solve(design, vectors[:, channel])
                self.repair_weights[channel] = coefficients
                residual = vectors[:, channel] - design @ coefficients
                self.repair_scale[channel] = max(float(np.sqrt(np.mean(residual * residual))), 1e-6)
                repair_ops += len(vectors) * (CHANNELS * CHANNELS + CHANNELS)
        self.fit_ops = int(len(rows) * (QUAD_WIDTH * QUAD_WIDTH + QUAD_WIDTH * CHANNELS)
                           + QUAD_WIDTH ** 3 + repair_ops)

    def _repair(self, vector: tuple[float, ...]) -> tuple[float, ...]:
        if self.mode == "frozen":
            return tuple(vector)
        values = np.asarray(vector, dtype=float)
        predictions = []
        scores = []
        for channel in range(CHANNELS):
            others = [index for index in range(CHANNELS) if index != channel]
            prediction = float(self.repair_weights[channel] @ np.asarray((1.0, *values[others])))
            predictions.append(prediction)
            scores.append(abs(values[channel] - prediction) / self.repair_scale[channel])
        order = np.argsort(scores)
        if scores[int(order[-1])] > REPAIR_Z and scores[int(order[-1])] > scores[int(order[-2])] + 1e-9:
            values[int(order[-1])] = predictions[int(order[-1])]
        return tuple(float(value) for value in values)

    def _predict(self, left: tuple[float, ...], center: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
        raw = _raw(left, center, right)
        # Sparse skipping and dense evaluation are the same intervention only if dormant zero
        # neighborhoods have exactly the same output in both schedules.
        if not np.any(raw):
            return (0.0,) * CHANNELS
        features = _quadratic(raw)
        prediction = np.clip(features @ self.weights, -OUTPUT_BOUND, OUTPUT_BOUND)
        return tuple(float(value) for value in prediction)

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        if not all(hasattr(source, field) for field in ("size", "target", "initial")):
            raise TypeError("continuous local learner requires Task")
        zero = (0.0,) * CHANNELS
        state = {position: self._repair(vector) for position, vector in source.initial}
        operations = len(source.initial) * (CHANNELS * CHANNELS + CHANNELS)
        touched = len(source.initial) * CHANNELS * 8
        for _ in range(steps):
            if self.mode == "dense":
                positions = range(source.size)
            else:
                active = set(state)
                positions = active | {(position - 1) % source.size for position in active} \
                    | {(position + 1) % source.size for position in active}
            next_state = {}
            for position in positions:
                value = self._predict(
                    state.get((position - 1) % source.size, zero),
                    state.get(position, zero),
                    state.get((position + 1) % source.size, zero),
                )
                next_state[position] = value
                operations += QUAD_WIDTH + QUAD_WIDTH * CHANNELS + CHANNELS
                touched += (RAW_WIDTH + QUAD_WIDTH + CHANNELS) * 8
            state = next_state
        self.last_ops = int(operations)
        self.last_bytes_touched = int(touched)
        return state.get(source.target, zero)

    def update(self, source: Any, target: Any) -> None:
        if not all(hasattr(source, field) for field in ("left", "center", "right", "target")):
            raise TypeError("continuous local update requires Transition")
        features = _quadratic(_raw(source.left, source.center, source.right))
        error = np.asarray(source.target) - features @ self.weights
        rate = UPDATE_ETA / (1.0 + float(features @ features))
        if self.mode != "frozen":
            self.weights += rate * np.outer(features, error)
        self.update_ops = int(QUAD_WIDTH * CHANNELS * 3 + QUAD_WIDTH)

    def state_bytes(self) -> int:
        return int(self.weights.nbytes + self.repair_weights.nbytes + self.repair_scale.nbytes + 64)


def quadratic_width() -> int:
    return QUAD_WIDTH


class Candidate(ContinuousLocalRule):
    """Auditable default entry for this shared implementation module."""
