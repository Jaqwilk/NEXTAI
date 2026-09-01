from __future__ import annotations

import math
from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..masked_refinement_contract import MASK, MaskedQuery, MaskedTraining


ALPHABET = 256
LAGS = (1, 2, 4, 8)
SMOOTHING = 0.5
LOG_FACTOR_CLIP = 4.0
MAX_SWEEPS = 6


class Candidate(CandidateBase):
    ROLE = "sparse_learned_energy_factor_graph_masked_byte"
    LEARN_FACTORS = True
    ONE_SWEEP = False

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata(self.ROLE, "masked_byte", self.ROLE)
        self.prior = np.full(ALPHABET, 1.0 / ALPHABET, dtype=np.float64)
        self.factors = np.zeros((len(LAGS), ALPHABET, ALPHABET), dtype=np.float32)
        self.fit_ops = self.meta_fit_ops = 0
        self.last_ops = self.last_bytes_touched = 0
        self.last_critical_path_steps = 1
        self.last_energy_trace: tuple[float, ...] = ()

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("energy-factor candidate requires MaskedTraining")
        counts = np.full(ALPHABET, SMOOTHING, dtype=np.float64)
        pairs = np.full(
            (len(LAGS), ALPHABET, ALPHABET), SMOOTHING, dtype=np.float64
        )
        operations = 0
        for item in facts.train_files:
            data = item.data
            for index, target in enumerate(data):
                counts[target] += 1.0
                operations += 1
                for factor_index, lag in enumerate(LAGS):
                    if index >= lag:
                        pairs[factor_index, data[index - lag], target] += 1.0
                        operations += 1
        self.prior = counts / counts.sum()
        proposed = np.empty_like(self.factors)
        for factor_index in range(len(LAGS)):
            conditional = pairs[factor_index] / pairs[factor_index].sum(
                axis=1, keepdims=True
            )
            log_ratio = np.log(conditional) - np.log(self.prior)[None, :]
            proposed[factor_index] = np.clip(
                log_ratio, -LOG_FACTOR_CLIP, LOG_FACTOR_CLIP
            )
            operations += ALPHABET * ALPHABET * 5
        if self.LEARN_FACTORS:
            self.factors[:] = proposed
        self.fit_ops = self.meta_fit_ops = operations

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - logits.max()
        values = np.exp(shifted)
        return values / values.sum()

    @staticmethod
    def _value(
        snapshot: tuple[int, ...], assignments: dict[int, int], position: int
    ) -> int | None:
        if not 0 <= position < len(snapshot):
            return None
        value = snapshot[position]
        return assignments[position] if value == MASK else value

    def _distribution(
        self, source: MaskedQuery, assignments: dict[int, int], position: int
    ) -> tuple[np.ndarray, int]:
        logits = np.log(self.prior)
        used = 0
        for factor_index, lag in enumerate(LAGS):
            left = self._value(source.snapshot, assignments, position - lag)
            right = self._value(source.snapshot, assignments, position + lag)
            if left is not None:
                logits = logits + self.factors[factor_index, left]
                used += 1
            if right is not None:
                logits = logits + self.factors[factor_index, :, right]
                used += 1
        return self._softmax(logits), used

    def _energy(self, source: MaskedQuery, assignments: dict[int, int]) -> tuple[float, int]:
        energy = -sum(math.log(self.prior[value]) for value in assignments.values())
        edges = 0
        masked = set(assignments)
        for left in range(len(source.snapshot)):
            left_value = self._value(source.snapshot, assignments, left)
            if left_value is None:
                continue
            for factor_index, lag in enumerate(LAGS):
                right = left + lag
                if right >= len(source.snapshot) or not ({left, right} & masked):
                    continue
                right_value = self._value(source.snapshot, assignments, right)
                if right_value is not None:
                    energy -= float(self.factors[factor_index, left_value, right_value])
                    edges += 1
        return energy, edges

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, MaskedQuery):
            raise TypeError("energy-factor candidate requires MaskedQuery")
        positions = source.masked_positions
        mode = int(np.argmax(self.prior))
        assignments = {position: mode for position in positions}
        outputs = {position: self.prior.copy() for position in positions}
        energy, energy_edges = self._energy(source, assignments)
        trace = [energy]
        operations = energy_edges + len(positions)
        factor_reads = 0
        attempted = 0
        limit = 1 if self.ONE_SWEEP else min(MAX_SWEEPS, max(1, int(steps)))
        for _ in range(limit):
            attempted += 1
            proposed: dict[int, int] = {}
            distributions: dict[int, np.ndarray] = {}
            for position in positions:
                distribution, used = self._distribution(source, assignments, position)
                distributions[position] = distribution
                proposed[position] = int(np.argmax(distribution))
                factor_reads += used * ALPHABET
                operations += used * ALPHABET + 4 * ALPHABET
            proposed_energy, proposed_edges = self._energy(source, proposed)
            operations += proposed_edges + len(positions)
            if proposed_energy > energy + 1e-12:
                break
            assignments, outputs, energy = proposed, distributions, proposed_energy
            trace.append(energy)
            if len(trace) > 1 and trace[-1] == trace[-2]:
                break
        self.last_energy_trace = tuple(trace)
        self.last_ops = operations
        self.last_bytes_touched = factor_reads * self.factors.itemsize + len(positions) * 8
        reduction = math.ceil(math.log2(max(2, len(positions))))
        self.last_critical_path_steps = attempted * (
            math.ceil(math.log2(len(LAGS) * 2)) + reduction + 4
        )
        return [outputs[position].tolist() for position in positions]

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return int(self.prior.nbytes + self.factors.nbytes + 512)
