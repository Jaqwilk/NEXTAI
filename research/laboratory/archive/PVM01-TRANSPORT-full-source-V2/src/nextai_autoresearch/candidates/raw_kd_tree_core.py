from __future__ import annotations

import math

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata
from nextai_autoresearch.entity_addressing_contract import OBSERVATION_DIMENSION, RawQuery, TransitionBurst
from nextai_autoresearch.entity_addressing_core import split_burst


class RawBalancedKDTree(CandidateBase):
    metadata = CandidateMetadata(
        "raw_balanced_kd_tree_v1", "nearest_neighbour",
        "Exact raw-space nearest neighbour through a balanced k-d tree.",
    )

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        records = tuple(facts)
        pairs = tuple(split_burst(record) for record in records)
        self.capacity = universe_size + 1
        self.sources = np.empty((self.capacity, OBSERVATION_DIMENSION), dtype=np.float64)
        self.targets = np.empty_like(self.sources)
        self.values = np.empty(self.capacity, dtype=np.int64)
        self.sources[:universe_size] = [pair[0] for pair in pairs]
        self.targets[:universe_size] = [pair[1] for pair in pairs]
        self.values[:universe_size] = [record.value for record in records]
        self.left = np.full(self.capacity, -1, dtype=np.int32)
        self.right = np.full(self.capacity, -1, dtype=np.int32)
        self.axis = np.zeros(self.capacity, dtype=np.int8)
        self.count = universe_size
        self._build_ops = 0
        self.root = self._build(list(range(universe_size)))
        self.fit_ops = universe_size * OBSERVATION_DIMENSION * 16 + self._build_ops

    def _build(self, indices: list[int]) -> int:
        if not indices:
            return -1
        rows = self.sources[indices]
        variances = rows.var(axis=0)
        axis = int(np.argmax(variances))
        indices.sort(key=lambda index: (self.sources[index, axis], index))
        middle = len(indices) // 2
        node = indices[middle]
        self.axis[node] = axis
        self._build_ops += len(indices) * OBSERVATION_DIMENSION * 3
        self._build_ops += max(1, math.ceil(len(indices) * math.log2(max(len(indices), 2))))
        self.left[node] = self._build(indices[:middle])
        self.right[node] = self._build(indices[middle + 1:])
        return node

    def _nearest(self, query: np.ndarray) -> tuple[int, int, int]:
        best_index, best_distance, visited = -1, math.inf, 0

        def search(node: int) -> None:
            nonlocal best_index, best_distance, visited
            if node < 0:
                return
            visited += 1
            delta = self.sources[node] - query
            distance = float(delta @ delta)
            if (distance, node) < (best_distance, best_index if best_index >= 0 else self.capacity):
                best_index, best_distance = node, distance
            axis = int(self.axis[node])
            offset = float(query[axis] - self.sources[node, axis])
            near, far = (int(self.left[node]), int(self.right[node])) if offset < 0 else (int(self.right[node]), int(self.left[node]))
            search(near)
            if offset * offset <= best_distance:
                search(far)

        search(int(self.root))
        return best_index, visited, visited * (3 * OBSERVATION_DIMENSION + 4)

    def query(self, source: RawQuery, steps: int) -> int:
        current = np.asarray(source.observation, dtype=np.float64)
        comparisons, operations, answer = 0, OBSERVATION_DIMENSION, -1
        for _ in range(steps):
            index, visited, lookup_ops = self._nearest(current)
            comparisons += visited
            operations += lookup_ops
            current, answer = self.targets[index], int(self.values[index])
        self.last_comparisons = comparisons
        self.last_ops = operations
        self.last_bytes_touched = (
            OBSERVATION_DIMENSION * 8
            + comparisons * (OBSERVATION_DIMENSION * 8 + 9)
            + steps * (OBSERVATION_DIMENSION * 8 + 8)
        )
        return answer

    def update(self, source: TransitionBurst, target: int) -> None:
        left, right = split_burst(source)
        index, node, comparisons = self.count, int(self.root), 0
        self.sources[index], self.targets[index], self.values[index] = left, right, target
        while True:
            comparisons += 1
            axis = int(self.axis[node])
            branch = self.left if (left[axis], index) < (self.sources[node, axis], node) else self.right
            child = int(branch[node])
            if child < 0:
                branch[node] = index
                self.axis[index] = (axis + 1) % OBSERVATION_DIMENSION
                break
            node = child
        self.count += 1
        self.update_ops = OBSERVATION_DIMENSION * 16 + 3 * comparisons

    def state_bytes(self) -> int:
        return int(
            self.sources.nbytes + self.targets.nbytes + self.values.nbytes
            + self.left.nbytes + self.right.nbytes + self.axis.nbytes
        )


class Candidate(RawBalancedKDTree):
    pass
