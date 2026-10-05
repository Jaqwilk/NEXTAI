from __future__ import annotations

from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..masked_refinement_contract import MASK, MaskedQuery, MaskedTraining


A = 256


class Candidate(CandidateBase):
    """Batch Re-Pair grammar with a frozen, public masked-completion adapter."""

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata(
            "re_pair_grammar_masked_byte", "grammar_transform", "batch Re-Pair grammar"
        )
        self.counts = np.full(A, 0.5, dtype=np.float64)
        self.rules: dict[int, tuple[int, int]] = {}
        self.expansions: tuple[tuple[int, ...], ...] = ()
        self.max_rule_depth = 0
        self.last_bytes_touched = 0
        self.last_critical_path_steps = 1

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("Re-Pair baseline requires MaskedTraining")
        sequences = [list(item.data) for item in facts.train_files]
        self.fit_ops = 0
        for sequence in sequences:
            for value in sequence:
                self.counts[value] += 1
                self.fit_ops += 1

        for _ in range(64):
            counts: dict[tuple[int, int], int] = {}
            first: dict[tuple[int, int], int] = {}
            order = 0
            for sequence in sequences:
                for pair in zip(sequence, sequence[1:]):
                    counts[pair] = counts.get(pair, 0) + 1
                    first.setdefault(pair, order)
                    order += 1
                    self.fit_ops += 1
            repeated = [pair for pair, count in counts.items() if count >= 2]
            if not repeated:
                break
            chosen = min(repeated, key=lambda pair: (-counts[pair], first[pair]))
            symbol = A + len(self.rules)
            self.rules[symbol] = chosen
            for sequence in sequences:
                rewritten: list[int] = []
                index = 0
                while index < len(sequence):
                    if index + 1 < len(sequence) and tuple(sequence[index : index + 2]) == chosen:
                        rewritten.append(symbol)
                        index += 2
                    else:
                        rewritten.append(sequence[index])
                        index += 1
                    self.fit_ops += 1
                sequence[:] = rewritten

        expanded: dict[int, tuple[int, ...]] = {}
        depths: dict[int, int] = {}
        for symbol, (left, right) in self.rules.items():
            left_values = expanded.get(left, (left,))
            right_values = expanded.get(right, (right,))
            expanded[symbol] = left_values + right_values
            depths[symbol] = 1 + max(depths.get(left, 0), depths.get(right, 0))
            self.fit_ops += len(expanded[symbol])
        self.expansions = tuple(expanded.values())
        self.max_rule_depth = max(depths.values(), default=0)

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, MaskedQuery):
            raise TypeError("Re-Pair baseline requires MaskedQuery")
        prior = self.counts / self.counts.sum()
        output: list[list[float]] = []
        ops = 0
        for position in source.masked_positions:
            distribution = prior.copy()
            for expansion in self.expansions:
                for offset, expected in enumerate(expansion):
                    start = position - offset
                    if start < 0 or start + len(expansion) > len(source.snapshot):
                        continue
                    anchors = 0
                    matches = True
                    for index, value in enumerate(expansion):
                        observed = source.snapshot[start + index]
                        ops += 1
                        if observed != MASK:
                            anchors += 1
                            if observed != value:
                                matches = False
                                break
                    if matches and anchors >= 2:
                        distribution[expected] += anchors / len(expansion)
            distribution /= distribution.sum()
            output.append(distribution.tolist())
        self.last_ops = ops + len(output) * A
        self.last_bytes_touched = self.last_ops * 8
        self.last_critical_path_steps = max(1, self.max_rule_depth + 1)
        return output

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        grammar = sum(16 + len(expansion) for expansion in self.expansions)
        return int(self.counts.nbytes + grammar + 512)
