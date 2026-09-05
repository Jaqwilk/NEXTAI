from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


RIDGE = 0.001
BIN_WIDTH = 0.25
NEIGHBORS = 8
CHANNELS = 4
RAW_WIDTH = 12


def _raw(left: tuple[float, ...], center: tuple[float, ...], right: tuple[float, ...]) -> np.ndarray:
    return np.asarray((*left, *center, *right), dtype=float)


def _sparse_rollout(task: Any, steps: int, transition) -> tuple[tuple[float, ...], int, int]:
    zero = (0.0,) * CHANNELS
    state = dict(task.initial)
    operations = 0
    touched = len(state) * CHANNELS * 8
    for _ in range(steps):
        active = set(state)
        positions = active | {(position - 1) % task.size for position in active} \
            | {(position + 1) % task.size for position in active}
        next_state = {}
        for position in positions:
            value, ops, byte_count = transition(
                state.get((position - 1) % task.size, zero), state.get(position, zero),
                state.get((position + 1) % task.size, zero),
            )
            next_state[position] = value
            operations += ops
            touched += byte_count
        state = next_state
    return state.get(task.target, zero), operations, touched


class Persistence(CandidateBase):
    metadata = CandidateMetadata("continuous_local_persistence", "baseline", "No-dynamics persistence")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        if not all(hasattr(source, field) for field in ("target", "initial")):
            raise TypeError
        values = dict(source.initial)
        self.last_ops = len(values) * CHANNELS
        self.last_bytes_touched = self.last_ops * 8
        return values.get(source.target, (0.0,) * CHANNELS)

    def update(self, source: Any, target: Any) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return 64


class LocalRidge(CandidateBase):
    metadata = CandidateMetadata("continuous_local_ridge", "baseline", "Raw affine local ridge")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.weights = np.zeros((RAW_WIDTH + 1, CHANNELS))
        self.last_bytes_touched = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        rows = tuple(facts)
        x = np.asarray([[1.0, *_raw(row.left, row.center, row.right)] for row in rows])
        y = np.asarray([row.target for row in rows])
        self.weights = np.linalg.solve(x.T @ x + RIDGE * np.eye(x.shape[1]), x.T @ y)
        self.fit_ops = int(len(rows) * ((RAW_WIDTH + 1) ** 2 + (RAW_WIDTH + 1) * CHANNELS)
                           + (RAW_WIDTH + 1) ** 3)

    def _transition(self, left, center, right):
        value = np.clip(np.asarray((1.0, *_raw(left, center, right))) @ self.weights, -1.5, 1.5)
        ops = (RAW_WIDTH + 1) * CHANNELS + RAW_WIDTH
        return tuple(map(float, value)), ops, (RAW_WIDTH + self.weights.size) * 8

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        answer, self.last_ops, self.last_bytes_touched = _sparse_rollout(source, steps, self._transition)
        return answer

    def update(self, source: Any, target: Any) -> None:
        features = np.asarray((1.0, *_raw(source.left, source.center, source.right)))
        error = np.asarray(source.target) - features @ self.weights
        self.weights += 0.05 / (1 + features @ features) * np.outer(features, error)
        self.update_ops = int((RAW_WIDTH + 1) * CHANNELS * 3)

    def state_bytes(self) -> int:
        return int(self.weights.nbytes + 64)


class QuantizedFSM(CandidateBase):
    metadata = CandidateMetadata("continuous_local_quantized_fsm", "baseline", "Quantized local transition table")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.table: dict[tuple[int, ...], tuple[float, ...]] = {}
        self.last_bytes_touched = 0

    @staticmethod
    def key(raw: np.ndarray) -> tuple[int, ...]:
        return tuple(int(round(float(value) / BIN_WIDTH)) for value in raw)

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        buckets: dict[tuple[int, ...], list[tuple[float, ...]]] = {}
        rows = tuple(facts)
        for row in rows:
            buckets.setdefault(self.key(_raw(row.left, row.center, row.right)), []).append(row.target)
        self.table = {key: tuple(map(float, np.mean(values, axis=0))) for key, values in buckets.items()}
        self.fit_ops = len(rows) * (RAW_WIDTH + CHANNELS)

    def _transition(self, left, center, right):
        key = self.key(_raw(left, center, right))
        value = self.table.get(key, tuple(center))
        return value, RAW_WIDTH + 1, (RAW_WIDTH + CHANNELS) * 8

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        answer, self.last_ops, self.last_bytes_touched = _sparse_rollout(source, steps, self._transition)
        return answer

    def update(self, source: Any, target: Any) -> None:
        self.table[self.key(_raw(source.left, source.center, source.right))] = tuple(source.target)
        self.update_ops = RAW_WIDTH + CHANNELS

    def state_bytes(self) -> int:
        return int(len(self.table) * (RAW_WIDTH * 4 + CHANNELS * 8 + 72) + 64)


class KernelEvent(CandidateBase):
    metadata = CandidateMetadata("continuous_local_kernel_event", "baseline", "Eight-neighbor event simulation")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.inputs = np.empty((0, RAW_WIDTH))
        self.targets = np.empty((0, CHANNELS))
        self.last_bytes_touched = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        rows = tuple(facts)
        self.inputs = np.asarray([_raw(row.left, row.center, row.right) for row in rows])
        self.targets = np.asarray([row.target for row in rows])
        self.fit_ops = len(rows) * (RAW_WIDTH + CHANNELS)

    def _transition(self, left, center, right):
        raw = _raw(left, center, right)
        distances = np.sum((self.inputs - raw) ** 2, axis=1)
        count = min(NEIGHBORS, len(distances))
        selected = np.argpartition(distances, count - 1)[:count]
        weights = 1.0 / np.maximum(distances[selected], 1e-9)
        value = np.average(self.targets[selected], axis=0, weights=weights)
        ops = len(self.inputs) * (RAW_WIDTH * 3 + 1) + count * CHANNELS * 2
        return tuple(map(float, value)), ops, int(self.inputs.nbytes + self.targets.nbytes + RAW_WIDTH * 8)

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        answer, self.last_ops, self.last_bytes_touched = _sparse_rollout(source, steps, self._transition)
        return answer

    def update(self, source: Any, target: Any) -> None:
        self.inputs = np.vstack((self.inputs, _raw(source.left, source.center, source.right)))
        self.targets = np.vstack((self.targets, np.asarray(source.target)))
        self.update_ops = RAW_WIDTH + CHANNELS

    def state_bytes(self) -> int:
        return int(self.inputs.nbytes + self.targets.nbytes + 64)


def _privileged_decode(world, vector: tuple[float, ...]) -> tuple[float, float]:
    raw = [0.0] * CHANNELS
    for index, source in enumerate(world.permutation):
        raw[source] = world.signs[index] * vector[index]
    difference = math.atanh(max(-0.999999, min(0.999999, raw[3])))
    proposals = ((raw[1] + difference, raw[1]), (raw[0], raw[0] - difference), (raw[0], raw[1]))
    best = None
    for x, y in proposals:
        expected = (x, y, 0.5 * x + 0.25 * y + 0.1 * x * y, math.tanh(x - y))
        residuals = sorted((expected[index] - raw[index]) ** 2 for index in range(CHANNELS))
        score = sum(residuals[:3])
        if best is None or score < best[0]:
            best = score, (x, y)
    return best[1]


def _encode(world, latent: tuple[float, float]) -> tuple[float, ...]:
    x, y = latent
    raw = (x, y, 0.5 * x + 0.25 * y + 0.1 * x * y, math.tanh(x - y))
    return tuple(world.signs[index] * raw[source] for index, source in enumerate(world.permutation))


def _step(left, center, right):
    x, y = center
    return (
        math.tanh(0.62 * x + 0.28 * (left[0] + right[0]) + 0.14 * math.tanh(y) + 0.06 * x * y),
        math.tanh(0.65 * y + 0.24 * (left[1] + right[1]) - 0.12 * math.tanh(x) + 0.05 * (left[0] - right[0])),
    )


class PrivilegedSupport(CandidateBase):
    metadata = CandidateMetadata("privileged_continuous_local_support", "privileged", "Hidden-rule support control")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        if not hasattr(facts, "world"):
            raise TypeError("privileged support required")
        self.world = facts.world
        self.fit_ops = 0
        self.last_bytes_touched = 0

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        zero = (0.0,) * CHANNELS
        state = {position: _privileged_decode(self.world, vector) for position, vector in source.initial}
        operations = len(state) * 32
        for _ in range(steps):
            active = set(state)
            positions = active | {(position - 1) % source.size for position in active} \
                | {(position + 1) % source.size for position in active}
            state = {position: _step(
                state.get((position - 1) % source.size, (0.0, 0.0)),
                state.get(position, (0.0, 0.0)),
                state.get((position + 1) % source.size, (0.0, 0.0)),
            ) for position in positions}
            operations += len(positions) * 24
        self.last_ops = operations
        self.last_bytes_touched = operations * 8
        return _encode(self.world, state.get(source.target, (0.0, 0.0))) if source.target in state else zero

    def update(self, source: Any, target: Any) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return 128


class Candidate(Persistence):
    """Auditable default entry for this shared control module."""
