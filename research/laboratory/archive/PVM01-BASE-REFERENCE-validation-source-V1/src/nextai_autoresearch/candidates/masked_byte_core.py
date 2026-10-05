from __future__ import annotations

import math
from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..masked_refinement_contract import MASK, MaskedQuery, MaskedTraining, PrivilegedMaskedQuery


A = 256


class MaskedByteCandidate(CandidateBase):
    MODE = "uniform"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata(self.MODE, "masked_byte", self.MODE)
        self.counts = np.full(A, 0.5, dtype=np.float64)
        self.transitions = np.full((A, A), 0.125, dtype=np.float64)
        self.lags: np.ndarray | None = None
        self.powers: list[np.ndarray] = []
        self.meta_fit_ops = 0
        self.last_bytes_touched = 0
        self.last_critical_path_steps = 1

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("masked-byte candidate requires MaskedTraining")
        self.fit_ops = 0
        if self.MODE in {"uniform", "oracle"}:
            return
        depth = min(5, max(1, int(max_depth)))
        if self.MODE == "dense":
            self.lags = np.full((depth, A, A), 0.125, dtype=np.float32)
        for item in facts.train_files:
            data = item.data
            for index, target in enumerate(data):
                self.counts[target] += 1
                self.fit_ops += 1
                if index:
                    self.transitions[data[index - 1], target] += 1
                    self.fit_ops += 1
                if self.lags is not None:
                    for lag in range(min(depth, index)):
                        self.lags[lag, data[index - lag - 1], target] += 1
                        self.fit_ops += 1
        self.transitions /= self.transitions.sum(axis=1, keepdims=True)
        if self.MODE == "parallel_bp":
            current = self.transitions.astype(np.float32)
            self.powers = [current]
            for _ in range(7):
                current = current @ current
                current /= current.sum(axis=1, keepdims=True)
                self.powers.append(current)
                self.fit_ops += A ** 3
        self.meta_fit_ops = self.fit_ops

    def _unigram(self) -> np.ndarray:
        return self.counts / self.counts.sum()

    @staticmethod
    def _known(snapshot: tuple[int, ...], position: int, direction: int) -> tuple[int | None, int]:
        distance = 0
        index = position + direction
        while 0 <= index < len(snapshot):
            distance += 1
            if snapshot[index] != MASK:
                return snapshot[index], distance
            index += direction
        return None, distance

    def _local(self, source: MaskedQuery, position: int) -> np.ndarray:
        left, left_distance = self._known(source.snapshot, position, -1)
        right, right_distance = self._known(source.snapshot, position, 1)
        answer = self._unigram().copy()
        if left is not None:
            weight = 1.0 / left_distance
            answer *= np.power(self.transitions[left], weight)
        if right is not None:
            weight = 1.0 / right_distance
            answer *= np.power(self.transitions[:, right], weight)
        total = answer.sum()
        return answer / total if total else self._unigram()

    def _dense(self, source: MaskedQuery) -> list[list[float]]:
        assert self.lags is not None
        snapshot = list(source.snapshot)
        output = []
        for position in source.masked_positions:
            distribution = self._unigram().copy()
            used = 0
            for lag in range(min(len(self.lags), position)):
                value = snapshot[position - lag - 1]
                if value == MASK:
                    break
                row = self.lags[lag, value].astype(np.float64)
                distribution *= row / row.sum()
                used += 1
            distribution /= distribution.sum()
            output.append(distribution.tolist())
            snapshot[position] = int(np.argmax(distribution))
        self.last_ops = len(output) * A * (3 + 3 * len(self.lags))
        self.last_bytes_touched = self.last_ops * 8
        self.last_critical_path_steps = max(1, len(output))
        return output

    @staticmethod
    def _segments(positions: tuple[int, ...]) -> list[list[tuple[int, int]]]:
        segments: list[list[tuple[int, int]]] = []
        for output_index, position in enumerate(positions):
            if not segments or position != segments[-1][-1][1] + 1:
                segments.append([])
            segments[-1].append((output_index, position))
        return segments

    def _exact_sequential(self, source: MaskedQuery) -> list[list[float]]:
        answers: list[np.ndarray | None] = [None] * len(source.masked_positions)
        maximum = 1
        for segment in self._segments(source.masked_positions):
            maximum = max(maximum, len(segment))
            first, last = segment[0][1], segment[-1][1]
            left = source.snapshot[first - 1] if first else None
            right = source.snapshot[last + 1] if last + 1 < len(source.snapshot) else None
            forward = self._unigram() if left is None else self.transitions[left].copy()
            forwards = [forward]
            for _ in range(1, len(segment)):
                forwards.append(forwards[-1] @ self.transitions)
            backward = np.ones(A) if right is None else self.transitions[:, right].copy()
            backwards = [backward]
            for _ in range(1, len(segment)):
                backwards.append(self.transitions @ backwards[-1])
            for index, (output_index, _) in enumerate(segment):
                distribution = forwards[index] * backwards[len(segment) - index - 1]
                distribution /= distribution.sum()
                answers[output_index] = distribution
        self.last_ops = len(source.masked_positions) * 2 * A * A
        self.last_bytes_touched = self.last_ops * 8
        self.last_critical_path_steps = 2 * maximum
        return [row.tolist() for row in answers if row is not None]

    def _power_message(self, value: int, distance: int, from_left: bool) -> np.ndarray:
        vector = np.zeros(A, dtype=np.float64)
        vector[value] = 1.0
        bit = 0
        while distance:
            if distance & 1:
                vector = vector @ self.powers[bit] if from_left else self.powers[bit] @ vector
            distance >>= 1
            bit += 1
        return vector

    def _parallel_exact(self, source: MaskedQuery) -> list[list[float]]:
        output = []
        maximum_distance = 1
        multiplications = 0
        for position in source.masked_positions:
            left, dl = self._known(source.snapshot, position, -1)
            right, dr = self._known(source.snapshot, position, 1)
            maximum_distance = max(maximum_distance, dl, dr)
            distribution = self._unigram().copy()
            if left is not None:
                distribution = self._power_message(left, dl, True)
                multiplications += dl.bit_count()
            if right is not None:
                distribution *= self._power_message(right, dr, False)
                multiplications += dr.bit_count()
            distribution /= distribution.sum()
            output.append(distribution.tolist())
        self.last_ops = multiplications * A * A + len(output) * A
        self.last_bytes_touched = self.last_ops * 4
        self.last_critical_path_steps = math.ceil(math.log2(maximum_distance)) + 2
        return output

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if self.MODE == "oracle":
            if not isinstance(source, PrivilegedMaskedQuery):
                raise TypeError("oracle requires privileged query")
            public = source.public
            start = (len(public.snapshot) - len(source.target)) // 2
            output = []
            for position in public.masked_positions:
                row = [0.0] * A
                row[source.target[position - start]] = 1.0
                output.append(row)
            self.last_ops = len(output)
            self.last_bytes_touched = len(output)
            self.last_critical_path_steps = 1
            return output
        if not isinstance(source, MaskedQuery):
            raise TypeError("public candidate requires MaskedQuery")
        if self.MODE == "uniform":
            self.last_ops = self.last_bytes_touched = len(source.masked_positions)
            self.last_critical_path_steps = 1
            return [[1.0 / A] * A for _ in source.masked_positions]
        if self.MODE == "unigram":
            row = self._unigram().tolist()
            self.last_ops = len(source.masked_positions) * A
            self.last_bytes_touched = self.last_ops * 8
            self.last_critical_path_steps = 1
            return [row[:] for _ in source.masked_positions]
        if self.MODE == "dense":
            return self._dense(source)
        if self.MODE == "bidirectional":
            return self._exact_sequential(source)
        if self.MODE == "parallel_bp":
            return self._parallel_exact(source)
        output = [self._local(source, position).tolist() for position in source.masked_positions]
        self.last_ops = len(output) * A * 5
        self.last_bytes_touched = self.last_ops * 8
        self.last_critical_path_steps = 1
        return output

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        total = self.counts.nbytes + self.transitions.nbytes
        if self.lags is not None:
            total += self.lags.nbytes
        total += sum(item.nbytes for item in self.powers)
        return int(total + 512)


class Candidate(MaskedByteCandidate):
    MODE = "uniform"
