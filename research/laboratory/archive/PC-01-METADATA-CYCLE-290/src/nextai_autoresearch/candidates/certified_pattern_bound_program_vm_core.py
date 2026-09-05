from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

from nextai_autoresearch.candidates.amortized_constraint_order_vm_core import (
    AmortizedConstraintOrderVM,
)
from nextai_autoresearch.whole_io_vm_core import (
    IOQuery,
    TrainingExample,
    execute_tape,
    run_program,
    support_key,
)


Pair = tuple[tuple[int, ...], tuple[int, ...]]


class CertifiedPatternBoundProgramVM(AmortizedConstraintOrderVM):
    """Exact fixed-order search with one certified two-constraint abstraction."""

    PATTERN_COUNT = 1
    BRANCH_ORDER = tuple(range(8))
    VALUE_ORDER = ((0, 1),) * 8

    def __init__(self, seed: int = 0, pattern_source: str = "meta") -> None:
        super().__init__(seed, "frozen")
        if pattern_source not in {"meta", "support", "frozen"}:
            raise ValueError("unknown pattern source")
        self.pattern_source = pattern_source
        self.pattern_ranking: tuple[Pair, ...] = ()
        self.source_rows: tuple[dict[tuple[int, ...], int], ...] = ()
        self.pattern_cache: dict[tuple[Pair, int, int], frozenset[tuple[int, int]]] = {}
        self.last_pattern: Pair | None = None
        self.last_certificate_rejections = 0
        self.last_strict_bound_nodes = 0

    @staticmethod
    def _rank_pairs(
        available: tuple[tuple[int, ...], ...],
        rows: tuple[dict[tuple[int, ...], int], ...],
    ) -> tuple[tuple[Pair, ...], int]:
        ranked, operations = [], 0
        for first, second in combinations(sorted(available), 2):
            same = coobserved = 0
            for row in rows:
                operations += 3
                if first in row and second in row:
                    coobserved += 1
                    same += row[first] == row[second]
            ranked.append((-same, -coobserved, first, second))
            operations += 1
        ranked.sort()
        operations += len(ranked)
        return tuple((row[2], row[3]) for row in ranked), operations

    def fit(self, facts: Iterable[TrainingExample], universe_size: int, max_depth: int) -> None:
        if self.pattern_source != "meta":
            self.fit_ops = 0
            return
        unique: dict[tuple[Any, ...], dict[tuple[int, ...], int]] = {}
        operations = 0
        for item in facts:
            key, reads = support_key(item.query.support)
            operations += reads + len(key)
            unique.setdefault(key, dict(key))
        self.source_rows = tuple(unique.values())
        universe = tuple(sorted({bits for row in self.source_rows for bits in row}))
        self.pattern_ranking, used = self._rank_pairs(universe, self.source_rows)
        self.fit_ops = operations + used

    def _select_pattern(self, key) -> tuple[Pair | None, int]:
        labels = dict(key)
        available = tuple(sorted(labels))
        if len(available) < 2:
            return None, 1
        if self.pattern_source == "meta":
            for pair in self.pattern_ranking:
                if pair[0] in labels and pair[1] in labels:
                    return pair, 1
            ranking, used = self._rank_pairs(available, ())
            return ranking[0], used
        rows = (labels,) if self.pattern_source == "support" else ()
        ranking, used = self._rank_pairs(available, rows)
        return ranking[0], used

    @staticmethod
    def _enumerate_mask(pair: Pair, partial: dict[int, int]):
        missing = tuple(bit for bit in range(8) if bit not in partial)
        mask: set[tuple[int, int]] = set()
        operations = 0
        for code in range(1 << len(missing)):
            program = [0] * 8
            for bit, value in partial.items():
                program[bit] = value
            for offset, bit in enumerate(missing):
                program[bit] = (code >> offset) & 1
            first, first_ops = run_program(tuple(program), pair[0])
            second, second_ops = run_program(tuple(program), pair[1])
            mask.add((first, second))
            operations += 10 + first_ops + second_ops
        return frozenset(mask), 1 << len(missing), operations

    @classmethod
    def _check_certificate(
        cls,
        pair: Pair,
        partial: dict[int, int],
        claimed_mask: frozenset[tuple[int, int]],
        claimed_count: int,
    ) -> tuple[bool, int]:
        checked_mask, checked_count, operations = cls._enumerate_mask(pair, partial)
        return (
            checked_mask == claimed_mask and checked_count == claimed_count,
            operations + len(checked_mask) + 2,
        )

    def _certified_mask(self, pair: Pair, partial: dict[int, int]):
        depth = len(partial)
        if tuple(sorted(partial)) != self.BRANCH_ORDER[:depth]:
            raise RuntimeError("pattern certificate requires the frozen prefix branch order")
        code = sum(value << bit for bit, value in partial.items())
        cache_key = (pair, depth, code)
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key], 1
        mask, count, build_ops = self._enumerate_mask(pair, partial)
        valid, check_ops = self._check_certificate(pair, partial, mask, count)
        if not valid:
            self.last_certificate_rejections += 1
            return None, build_ops + check_ops + 1
        self.pattern_cache[cache_key] = mask
        return mask, build_ops + check_ops + 1

    def _certified_bound(self, key, pair: Pair | None, partial, best):
        base, operations = self._bound(key, partial, best)
        if pair is None:
            return base, operations + 1
        mask, used = self._certified_mask(pair, partial)
        operations += used
        if mask is None:
            return base, operations + 1
        labels = dict(key)
        first_target, second_target = labels[pair[0]], labels[pair[1]]
        joint = min(
            (first != first_target) + (second != second_target)
            for first, second in mask
        )
        first_possible = {first for first, _ in mask}
        second_possible = {second for _, second in mask}
        independent = (first_target not in first_possible) + (second_target not in second_possible)
        increment = joint - independent
        if increment < 0:
            raise RuntimeError("certified joint bound cannot weaken independent projections")
        self.last_strict_bound_nodes += increment > 0
        return (base[0] + increment, base[1], base[2]), operations + len(mask) + 5

    @staticmethod
    def _score_program(key, program: tuple[int, ...]):
        mismatches = operations = 0
        for bits, target in key:
            output, used = run_program(program, bits)
            mismatches += output != target
            operations += used + 1
        code = sum(value << bit for bit, value in enumerate(program))
        return (mismatches, 1 + sum(program), code, program), operations

    def _induce(self, key, pair: Pair | None):
        best, controller_ops = self._score_program(key, (0,) * 8)
        nodes = leaves = 0
        self.last_certificate_rejections = 0
        self.last_strict_bound_nodes = 0

        def visit(depth: int, partial: dict[int, int]) -> None:
            nonlocal best, nodes, leaves, controller_ops
            nodes += 1
            bound, used = self._certified_bound(key, pair, partial, best)
            controller_ops += used + 1
            if bound >= best[:3]:
                return
            if depth == 8:
                program = tuple(partial[bit] for bit in self.BRANCH_ORDER)
                leaves += 1
                best = (*bound, program)
                return
            bit = self.BRANCH_ORDER[depth]
            for value in self.VALUE_ORDER[bit]:
                partial[bit] = value
                visit(depth + 1, partial)
            partial.pop(bit)

        visit(0, {})
        return best[3], nodes, controller_ops, leaves + 1

    def query(self, source: IOQuery, steps: int) -> int:
        key, support_reads = support_key(source.support)
        if key in self.cache:
            program, nodes, controller_ops, evaluations = self.cache[key], 1, 1, 0
        else:
            pattern, selection_ops = self._select_pattern(key)
            self.last_pattern = pattern
            program, nodes, controller_ops, evaluations = self._induce(key, pattern)
            controller_ops += selection_ops
            self.cache[key] = program
        output, execution_ops, test_reads, _ = execute_tape(program, source.tape)
        self.last_program = program
        self.last_program_evaluations = evaluations
        self.last_nodes = nodes
        self._record(
            support_reads,
            nodes,
            controller_ops + execution_ops,
            support_reads + test_reads,
        )
        return output

    def update(self, source: TrainingExample, target: int) -> None:
        self.query(source.query, len(source.query.tape))
        self.update_ops = self.last_ops

    def state_bytes(self) -> int:
        rows = sum(sum(len(bits) + 2 for bits in row) for row in self.source_rows)
        ranking = sum(len(first) + len(second) + 8 for first, second in self.pattern_ranking)
        patterns = sum(
            len(pair[0]) + len(pair[1]) + 24 + 2 * len(mask)
            for (pair, _, _), mask in self.pattern_cache.items()
        )
        return super().state_bytes() + rows + ranking + patterns


class Candidate(CertifiedPatternBoundProgramVM):
    """Audit-visible default; scored roles use explicit source wrappers."""
