from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from .base import CandidateBase, CandidateMetadata


CHANNELS = 4
LIFT_WIDTH = 14
INPUT_WIDTH = 3 * LIFT_WIDTH
RIDGE = 0.001
UPDATE_ETA = 0.01
OUTPUT_BOUND = 1.5
MAX_POWER = 16


def lift(vector: tuple[float, ...]) -> np.ndarray:
    values = np.asarray(vector, dtype=float)
    return np.asarray([
        *values,
        *(values[left] * values[right]
          for left in range(CHANNELS) for right in range(left, CHANNELS)),
    ])


def compose_kernel(kernel: dict[int, np.ndarray]) -> tuple[dict[int, np.ndarray], int]:
    result: dict[int, np.ndarray] = {}
    operations = 0
    for first_offset, first in kernel.items():
        for second_offset, second in kernel.items():
            offset = first_offset + second_offset
            product = first @ second
            if offset in result:
                result[offset] += product
                operations += LIFT_WIDTH * LIFT_WIDTH
            else:
                result[offset] = product
            operations += LIFT_WIDTH * LIFT_WIDTH * (2 * LIFT_WIDTH - 1)
    return result, operations


class DyadicLiftedLocal(CandidateBase):
    metadata = CandidateMetadata(
        "dyadic_lifted_local", "continuous_cellular", "Source-identical lifted local propagation"
    )

    def __init__(self, seed: int = 0, *, mode: str = "dyadic") -> None:
        super().__init__(seed)
        if mode not in {"dyadic", "sequential", "frozen"}:
            raise ValueError(mode)
        self.mode = mode
        self.weights = np.zeros((INPUT_WIDTH, LIFT_WIDTH), dtype=float)
        self.kernels: dict[int, dict[int, np.ndarray]] = {}
        self.last_bytes_touched = 0

    @staticmethod
    def _features(row: Any) -> np.ndarray:
        return np.concatenate((lift(row.left), lift(row.center), lift(row.right)))

    def _base_kernel(self) -> dict[int, np.ndarray]:
        if self.mode == "frozen":
            center = np.zeros((LIFT_WIDTH, LIFT_WIDTH), dtype=float)
            center[:CHANNELS, :CHANNELS] = np.eye(CHANNELS)
            zero = np.zeros_like(center)
            return {-1: zero.copy(), 0: center, 1: zero.copy()}
        left, center, right = np.split(self.weights, 3, axis=0)
        return {-1: right.T.copy(), 0: center.T.copy(), 1: left.T.copy()}

    def _rebuild(self) -> int:
        self.kernels = {1: self._base_kernel()}
        operations = 0
        if self.mode != "sequential":
            power = 1
            while power < MAX_POWER:
                composed, work = compose_kernel(self.kernels[power])
                power *= 2
                self.kernels[power] = composed
                operations += work
        return operations

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        del universe_size
        if max_depth != MAX_POWER:
            raise ValueError("lifted local propagator requires frozen maximum depth 16")
        rows = tuple(facts)
        if not rows:
            raise ValueError("lifted local propagator requires transition rows")
        design = np.asarray([self._features(row) for row in rows])
        targets = np.asarray([lift(row.target) for row in rows])
        feature_work = len(rows) * 4 * 10
        if self.mode != "frozen":
            gram = design.T @ design + RIDGE * np.eye(INPUT_WIDTH)
            self.weights = np.linalg.solve(gram, design.T @ targets)
            solve_work = (
                len(rows) * INPUT_WIDTH * INPUT_WIDTH
                + len(rows) * INPUT_WIDTH * LIFT_WIDTH
                + INPUT_WIDTH ** 3
            )
        else:
            solve_work = 0
        self.fit_ops = int(feature_work + solve_work + self._rebuild())

    @staticmethod
    def _offset(target: int, source: int, size: int) -> int:
        offset = (target - source) % size
        return offset - size if offset > size // 2 else offset

    def _dyadic_query(self, source: Any, steps: int) -> tuple[np.ndarray, int]:
        if steps not in self.kernels:
            raise ValueError("dyadic query requires a frozen power-of-two depth")
        kernel = self.kernels[steps]
        answer = np.zeros(LIFT_WIDTH)
        operations = 0
        for position, vector in source.initial:
            offset = self._offset(source.target, position, source.size)
            if offset in kernel:
                answer += kernel[offset] @ lift(vector)
                operations += 10 + LIFT_WIDTH * (2 * LIFT_WIDTH - 1) + LIFT_WIDTH
        return answer, operations

    def _sequential_query(self, source: Any, steps: int) -> tuple[np.ndarray, int]:
        state = {position: lift(vector) for position, vector in source.initial}
        base = self.kernels[1]
        operations = len(state) * 10
        for _ in range(steps):
            positions = set(state)
            positions |= {(position - 1) % source.size for position in state}
            positions |= {(position + 1) % source.size for position in state}
            updated: dict[int, np.ndarray] = {}
            for target in positions:
                value = np.zeros(LIFT_WIDTH)
                for displacement, matrix in base.items():
                    origin = (target - displacement) % source.size
                    if origin in state:
                        value += matrix @ state[origin]
                        operations += LIFT_WIDTH * (2 * LIFT_WIDTH - 1) + LIFT_WIDTH
                updated[target] = value
            state = updated
        return state.get(source.target, np.zeros(LIFT_WIDTH)), operations

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        if not all(hasattr(source, field) for field in ("size", "target", "initial")):
            raise TypeError("lifted local propagator requires a sparse public task")
        if self.mode == "sequential":
            encoded, operations = self._sequential_query(source, steps)
        else:
            encoded, operations = self._dyadic_query(source, steps)
        self.last_ops = int(operations + CHANNELS)
        self.last_bytes_touched = int(self.last_ops * 8)
        return tuple(float(value) for value in np.clip(encoded[:CHANNELS], -OUTPUT_BOUND, OUTPUT_BOUND))

    def update(self, source: Any, target: Any) -> None:
        del target
        features = self._features(source)
        expected = lift(source.target)
        prediction = features @ self.weights
        scale = UPDATE_ETA / (1.0 + float(features @ features))
        base_work = 4 * 10 + INPUT_WIDTH * (2 * LIFT_WIDTH - 1) \
            + INPUT_WIDTH * LIFT_WIDTH * 2 + INPUT_WIDTH
        if self.mode != "frozen":
            self.weights += scale * np.outer(features, expected - prediction)
            rebuild = self._rebuild()
        else:
            rebuild = 0
        self.update_ops = int(base_work + rebuild)

    def state_bytes(self) -> int:
        return int(self.weights.nbytes + sum(
            matrix.nbytes for kernel in self.kernels.values() for matrix in kernel.values()
        ))


class Candidate(DyadicLiftedLocal):
    """Auditable default entry for the shared implementation module."""
