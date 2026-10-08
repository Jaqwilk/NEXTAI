from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..masked_refinement_contract import MASK, MaskedQuery, MaskedTraining


ALPHABET = 256
SMOOTHING = 0.5
MIN_SUPPORT = 3
MAX_RULES = 64
MAX_DEPTH = 6
MAX_EXPANSION = 32
MIN_ANCHORS = 2


@dataclass(frozen=True)
class Rule:
    expansion: tuple[int, ...]
    depth: int
    support: int


class Candidate(CandidateBase):
    ROLE = "recursive_equality_grammar_masked_byte"
    MODE = "recursive"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata(self.ROLE, "masked_byte", self.ROLE)
        self.prior = np.full(ALPHABET, 1.0 / ALPHABET, dtype=np.float64)
        self.rules: tuple[Rule, ...] = ()
        self.fit_ops = self.meta_fit_ops = 0
        self.last_ops = self.last_bytes_touched = 0
        self.last_critical_path_steps = 1

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("equality grammar requires MaskedTraining")
        sequences = [list(item.data) for item in facts.train_files]
        counts = np.full(ALPHABET, SMOOTHING, dtype=np.float64)
        operations = 0
        for sequence in sequences:
            for value in sequence:
                counts[value] += 1.0
                operations += 1
        self.prior = counts / counts.sum()

        expansions: dict[int, tuple[int, ...]] = {}
        depths: dict[int, int] = {}
        learned: list[Rule] = []
        for _ in range(MAX_RULES):
            pair_counts: dict[tuple[int, int], int] = {}
            first_seen: dict[tuple[int, int], int] = {}
            order = 0
            for sequence in sequences:
                for pair in zip(sequence, sequence[1:]):
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1
                    first_seen.setdefault(pair, order)
                    order += 1
                    operations += 1
            eligible = [pair for pair, count in pair_counts.items()
                        if count >= MIN_SUPPORT]
            if not eligible:
                break
            chosen = min(eligible, key=lambda pair: (-pair_counts[pair], first_seen[pair]))
            symbol = ALPHABET + len(learned)
            left, right = chosen
            expansion = expansions.get(left, (left,)) + expansions.get(right, (right,))
            depth = 1 + max(depths.get(left, 0), depths.get(right, 0))
            expansions[symbol], depths[symbol] = expansion, depth
            learned.append(Rule(expansion, depth, pair_counts[chosen]))
            operations += len(expansion)
            for sequence in sequences:
                rewritten: list[int] = []
                index = 0
                while index < len(sequence):
                    if index + 1 < len(sequence) and tuple(sequence[index:index + 2]) == chosen:
                        rewritten.append(symbol)
                        index += 2
                    else:
                        rewritten.append(sequence[index])
                        index += 1
                    operations += 1
                sequence[:] = rewritten
        self.rules = tuple(learned)
        self.fit_ops = self.meta_fit_ops = operations

    @staticmethod
    def _segments(positions: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
        if not positions:
            return ()
        output: list[tuple[int, int]] = []
        start = previous = positions[0]
        for position in positions[1:]:
            if position != previous + 1:
                output.append((start, previous))
                start = position
            previous = position
        output.append((start, previous))
        return tuple(output)

    def _eligible_rules(self) -> tuple[Rule, ...]:
        if self.MODE == "frozen":
            return ()
        if self.MODE == "flat":
            return tuple(rule for rule in self.rules if rule.depth == 1)
        return tuple(rule for rule in self.rules
                     if rule.depth <= MAX_DEPTH and len(rule.expansion) <= MAX_EXPANSION)

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, MaskedQuery):
            raise TypeError("equality grammar requires MaskedQuery")
        positions = source.masked_positions
        distributions = {position: self.prior.copy() for position in positions}
        masked = set(positions)
        operations = len(positions) * ALPHABET
        reads = 0
        maximum_depth = 0
        for rule in self._eligible_rules():
            expansion = rule.expansion
            length = len(expansion)
            maximum_depth = max(maximum_depth, rule.depth)
            weight_scale = math.log1p(rule.support) / length
            for segment_start, segment_end in self._segments(positions):
                low = max(0, segment_start - length + 1)
                high = min(segment_end, len(source.snapshot) - length)
                for start in range(low, high + 1):
                    anchors = 0
                    matches = True
                    for offset, expected in enumerate(expansion):
                        observed = source.snapshot[start + offset]
                        operations += 1
                        reads += 1
                        if observed != MASK:
                            anchors += 1
                            if observed != expected:
                                matches = False
                                break
                    if not matches or anchors < MIN_ANCHORS:
                        continue
                    vote = weight_scale * anchors
                    for offset, expected in enumerate(expansion):
                        position = start + offset
                        if position in masked:
                            distributions[position][expected] += vote
                            operations += 1
        output = []
        for position in positions:
            row = distributions[position]
            row /= row.sum()
            output.append(row.tolist())
        self.last_ops = operations
        self.last_bytes_touched = reads + len(positions) * ALPHABET * 8
        self.last_critical_path_steps = max(1, maximum_depth + 2)
        return output

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        grammar = sum(24 + len(rule.expansion) for rule in self.rules)
        return int(self.prior.nbytes + grammar + 512)
