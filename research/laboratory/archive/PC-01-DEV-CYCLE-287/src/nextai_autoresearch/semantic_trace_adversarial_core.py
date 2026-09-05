from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .candidates.base import CandidateMetadata
from .semantic_trace_core import (
    MODULUS,
    OP_COST,
    GraphQuery,
    Key,
    Mutation,
    TraceBase,
    evaluate_indexed,
    scan,
)


NormalKey = tuple[int, tuple[tuple[int, int], ...], int]


@dataclass(frozen=True)
class RewriteOracleInput:
    query: GraphQuery
    target: int


def normal_form(index, sink: int):
    atoms, constant, visits = [], 0, 0

    def visit(node_id: int) -> None:
        nonlocal constant, visits
        node = index[node_id]
        visits += 1
        if node.op < 0:
            symbol, value = divmod(node.value, MODULUS)
            if symbol:
                atoms.append((symbol, value))
            else:
                constant = (constant + value) % MODULUS
        else:
            if node.op != 0:
                raise ValueError("adversarial normal form supports addition only")
            for child in node.children:
                visit(child)

    visit(sink)
    atoms.sort()
    sort_ops = len(atoms) * max(1, math.ceil(math.log2(len(atoms) + 1)))
    return (2, tuple(atoms), constant), 6 * visits + sort_ops


def reduction_key(normal: NormalKey) -> Key:
    terms: list[Key] = [(0, symbol, value) for symbol, value in normal[1]]
    if normal[2]:
        terms.append((0, 0, normal[2]))
    terms.sort()
    if not terms:
        return (0, 0, 0)
    while len(terms) > 1:
        terms = [(1, terms[i], terms[i + 1]) if i + 1 < len(terms) else terms[i] for i in range(0, len(terms), 2)]
    return terms[0]


def reduction_keys(key: Key) -> set[Key]:
    return set() if key[0] == 0 else {key, *reduction_keys(key[1]), *reduction_keys(key[2])}


def reduction_size(key: Key) -> int:
    return 20 if key[0] == 0 else 24 + reduction_size(key[1]) + reduction_size(key[2])


class RewriteResultCache(TraceBase):
    metadata = CandidateMetadata("rewrite_normal_form_result_cache", "symbolic", "Complete additive-normal-form result cache")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.cache: dict[NormalKey, int] = {}
        self.last_equivalence_ops = self.last_update_equivalence_ops = 0
        self.last_update_execution_ops = 0

    def query(self, source: GraphQuery, steps: int) -> int:
        index = self._prepare(source)
        key, equivalence = normal_form(index, source.sink)
        hit = key in self.cache
        if hit:
            answer, execution, executed = self.cache[key], 1, 0
        else:
            answer, execution, executed = evaluate_indexed(index, source.sink)
            self.cache[key] = answer
        self.last_equivalence_ops = equivalence
        self._finish(equivalence, execution, hit, int(not hit), executed)
        return answer

    def update(self, source: Mutation, target: int) -> None:
        old_index, old_input, _, _ = scan(source.old)
        new_index, new_input, _, _ = scan(source.new)
        old_key, old_equivalence = normal_form(old_index, source.old.sink)
        new_key, new_equivalence = normal_form(new_index, source.new.sink)
        before = len(self.cache)
        invalidated = int(self.cache.pop(old_key, None) is not None)
        answer, execution, executed = evaluate_indexed(new_index, source.new.sink)
        self.cache[new_key] = answer
        self.last_invalidated_entries = invalidated
        self.last_invalidated_fraction = invalidated / before if before else 0.0
        self.last_recomputed_nodes = executed
        self.last_update_equivalence_ops = old_equivalence + new_equivalence
        self.last_update_execution_ops = execution
        self.update_ops = old_input + new_input + self.last_update_equivalence_ops + execution

    def state_bytes(self) -> int:
        return 64 + sum(32 + 16 * len(key[1]) for key in self.cache)


class RewriteDependencyTrace(RewriteResultCache):
    metadata = CandidateMetadata("rewrite_normal_form_dependency_trace", "compiled", "Dependency trace over additive normal form")

    @staticmethod
    def _evaluate(key: Key, cache: dict[Key, int]):
        if key[0] == 0:
            return key[2], 0
        if key in cache:
            return cache[key], 0
        left, left_count = RewriteDependencyTrace._evaluate(key[1], cache)
        right, right_count = RewriteDependencyTrace._evaluate(key[2], cache)
        cache[key] = (left + right) % MODULUS
        return cache[key], left_count + right_count + 1

    def __init__(self, seed: int = 0) -> None:
        TraceBase.__init__(self, seed)
        self.cache: dict[Key, int] = {}
        self.last_equivalence_ops = self.last_update_equivalence_ops = 0
        self.last_update_execution_ops = 0

    def query(self, source: GraphQuery, steps: int) -> int:
        index = self._prepare(source)
        normal, equivalence = normal_form(index, source.sink)
        key = reduction_key(normal)
        hit = key in self.cache
        answer, compiled = self._evaluate(key, self.cache)
        self.last_equivalence_ops = equivalence
        self._finish(equivalence, 1 if hit else OP_COST * compiled, hit, compiled, compiled)
        return answer

    def update(self, source: Mutation, target: int) -> None:
        old_index, old_input, _, _ = scan(source.old)
        new_index, new_input, _, _ = scan(source.new)
        old_normal, old_equivalence = normal_form(old_index, source.old.sink)
        new_normal, new_equivalence = normal_form(new_index, source.new.sink)
        old_key, new_key = reduction_key(old_normal), reduction_key(new_normal)
        before = len(self.cache)
        obsolete = reduction_keys(old_key) - reduction_keys(new_key)
        invalidated = sum(key in self.cache for key in obsolete)
        for key in obsolete:
            self.cache.pop(key, None)
        _, recomputed = self._evaluate(new_key, self.cache)
        self.last_invalidated_entries = invalidated
        self.last_invalidated_fraction = invalidated / before if before else 0.0
        self.last_recomputed_nodes = recomputed
        self.last_update_equivalence_ops = old_equivalence + new_equivalence
        self.last_update_execution_ops = OP_COST * recomputed
        self.update_ops = old_input + new_input + self.last_update_equivalence_ops + self.last_update_execution_ops

    def state_bytes(self) -> int:
        return 64 + sum(16 + reduction_size(key) for key in self.cache)


class OracleEquivalenceTrace(TraceBase):
    metadata = CandidateMetadata("oracle_equivalence_trace", "oracle", "Supplied rewrite-equivalence answer lower bound")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_equivalence_ops = self.last_update_equivalence_ops = 0
        self.last_update_execution_ops = 0

    def query(self, source: RewriteOracleInput, steps: int) -> int:
        self.last_input_ops = self.last_memory_reads = self.last_bytes_loaded = 0
        self.last_cache_hit = False
        self._finish(0, 1, False)
        return source.target

    def update(self, source: Mutation, target: int) -> None:
        self.update_ops = self.last_update_execution_ops = 1

    def state_bytes(self) -> int:
        return 64
