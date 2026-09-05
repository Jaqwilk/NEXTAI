from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


CHANNELS = 4
CENTER_WIDTH = 15
PAIR_WIDTH = 24
FEATURE_WIDTH = CENTER_WIDTH + PAIR_WIDTH
RIDGE = 0.001
UPDATE_ETA = 0.05
OUTPUT_BOUND = 1.5


def _vector(values: tuple[float, ...]) -> np.ndarray:
    return np.asarray(values, dtype=float)


def center_features(center: tuple[float, ...]) -> np.ndarray:
    values = _vector(center)
    features = [1.0, *values]
    features.extend(values[i] * values[j] for i in range(CHANNELS) for j in range(i, CHANNELS))
    return np.asarray(features, dtype=float)


def pair_features(source: tuple[float, ...], destination: tuple[float, ...]) -> np.ndarray:
    left, right = _vector(source), _vector(destination)
    return np.concatenate((left, right, np.outer(left, right).ravel()))


def exchange_features(first: tuple[float, ...], second: tuple[float, ...]) -> np.ndarray:
    return 0.5 * (pair_features(first, second) - pair_features(second, first))


def _feature_ops(mode: str) -> int:
    return 10 + (4 * 16 + 4 * PAIR_WIDTH if mode in {"factorized", "frozen"} else 2 * 16 + PAIR_WIDTH)


def _features(left: tuple[float, ...], center: tuple[float, ...], right: tuple[float, ...], mode: str) -> np.ndarray:
    if mode in {"factorized", "frozen"}:
        interaction = exchange_features(left, center) + exchange_features(right, center)
    else:
        interaction = pair_features(left, center) + pair_features(right, center)
    return np.concatenate((center_features(center), interaction))


class FactorizedFluxReaction(CandidateBase):
    metadata = CandidateMetadata(
        "factorized_flux_reaction", "continuous_cellular", "Source-identical anonymous reaction/exchange learner"
    )

    def __init__(self, seed: int = 0, *, mode: str = "factorized") -> None:
        super().__init__(seed)
        if mode not in {"factorized", "monolithic", "frozen"}:
            raise ValueError(mode)
        self.mode = mode
        self.weights = np.zeros((FEATURE_WIDTH, CHANNELS), dtype=float)
        self.last_bytes_touched = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        rows = tuple(facts)
        if not rows or not all(all(hasattr(row, field) for field in ("left", "center", "right", "target")) for row in rows):
            raise TypeError("factorized local learner requires Transition rows")
        design = np.asarray([_features(row.left, row.center, row.right, self.mode) for row in rows])
        targets = np.asarray([_vector(row.target) - _vector(row.center) for row in rows])
        construction = len(rows) * _feature_ops(self.mode)
        if self.mode != "frozen":
            gram = design.T @ design
            self.weights = np.linalg.solve(
                gram + RIDGE * np.eye(FEATURE_WIDTH), design.T @ targets
            )
            construction += len(rows) * (FEATURE_WIDTH * FEATURE_WIDTH + FEATURE_WIDTH * CHANNELS) \
                + FEATURE_WIDTH ** 3
        self.fit_ops = int(construction)

    def _predict(self, left: tuple[float, ...], center: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
        raw = np.asarray((*left, *center, *right), dtype=float)
        if not np.any(raw):
            return (0.0,) * CHANNELS
        features = _features(left, center, right, self.mode)
        prediction = np.clip(_vector(center) + features @ self.weights, -OUTPUT_BOUND, OUTPUT_BOUND)
        return tuple(float(value) for value in prediction)

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        if not all(hasattr(source, field) for field in ("size", "target", "initial")):
            raise TypeError("factorized local learner requires Task")
        zero = (0.0,) * CHANNELS
        state = dict(source.initial)
        operations = 0
        touched = len(state) * CHANNELS * 8
        for _ in range(steps):
            active = set(state)
            positions = active | {(position - 1) % source.size for position in active} \
                | {(position + 1) % source.size for position in active}
            next_state = {}
            for position in positions:
                next_state[position] = self._predict(
                    state.get((position - 1) % source.size, zero),
                    state.get(position, zero),
                    state.get((position + 1) % source.size, zero),
                )
                operations += _feature_ops(self.mode) + FEATURE_WIDTH * CHANNELS + CHANNELS
                touched += (3 * CHANNELS + FEATURE_WIDTH + CHANNELS) * 8
            state = next_state
        self.last_ops = int(operations)
        self.last_bytes_touched = int(touched)
        return state.get(source.target, zero)

    def update(self, source: Any, target: Any) -> None:
        if not all(hasattr(source, field) for field in ("left", "center", "right", "target")):
            raise TypeError("factorized local update requires Transition")
        features = _features(source.left, source.center, source.right, self.mode)
        prediction = _vector(source.center) + features @ self.weights
        error = _vector(source.target) - prediction
        rate = UPDATE_ETA / (1.0 + float(features @ features))
        if self.mode != "frozen":
            self.weights += rate * np.outer(features, error)
        self.update_ops = int(_feature_ops(self.mode) + FEATURE_WIDTH * CHANNELS * 3 + FEATURE_WIDTH)

    def state_bytes(self) -> int:
        return int(self.weights.nbytes + 64)


class Candidate(FactorizedFluxReaction):
    """Auditable default entry for the shared implementation module."""

