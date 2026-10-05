from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata


MODULUS, OP_COST = 251, 32
Key = tuple[Any, ...]


@dataclass(frozen=True)
class Node:
    node_id: int
    op: int = -1
    value: int = 0
    children: tuple[int, ...] = ()


@dataclass(frozen=True)
class GraphQuery:
    nodes: tuple[Node, ...]
    sink: int


@dataclass(frozen=True)
class Mutation:
    old: GraphQuery
    new: GraphQuery


@dataclass(frozen=True)
class OracleInput:
    query: GraphQuery
    target: int


def apply_op(op: int, left: int, right: int) -> int:
    return ((left + right) if op == 0 else (left ^ right) if op == 1 else (left * right)) % MODULUS


def scan(query: GraphQuery):
    index = {node.node_id: node for node in query.nodes}
    if len(index) != len(query.nodes) or query.sink not in index:
        raise ValueError("invalid graph identifiers")
    return index, 2 * len(index), len(index), sum(16 + 8 * len(node.children) for node in query.nodes)


def canonicalize(index: dict[int, Node], sink: int):
    memo: dict[int, Key] = {}

    def visit(node_id: int) -> Key:
        if node_id in memo:
            return memo[node_id]
        node = index[node_id]
        if node.op < 0:
            key: Key = (0, node.value)
        else:
            left, right = (visit(child) for child in node.children)
            key = (1, node.op, *sorted((left, right)))
        memo[node_id] = key
        return key

    root = visit(sink)
    return root, 4 * len(memo)


def canonical_key(query: GraphQuery) -> Key:
    index, _, _, _ = scan(query)
    return canonicalize(index, query.sink)[0]


def evaluate_indexed(index: dict[int, Node], sink: int):
    memo: dict[int, int] = {}
    executed = 0

    def visit(node_id: int) -> int:
        nonlocal executed
        if node_id in memo:
            return memo[node_id]
        node = index[node_id]
        if node.op < 0:
            value = node.value
        else:
            value = apply_op(node.op, *(visit(child) for child in node.children))
            executed += 1
        memo[node_id] = value
        return value

    return visit(sink), OP_COST * executed, executed


def evaluate(query: GraphQuery) -> int:
    index, _, _, _ = scan(query)
    return evaluate_indexed(index, query.sink)[0]


def internal_keys(root: Key) -> set[Key]:
    if root[0] == 0:
        return set()
    return {root, *internal_keys(root[2]), *internal_keys(root[3])}


def key_size(key: Key) -> int:
    return 16 if key[0] == 0 else 24 + key_size(key[2]) + key_size(key[3])


class TraceBase(CandidateBase):
    metadata = CandidateMetadata("trace_base", "control", "Semantic trace control")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_input_ops = self.last_canonical_ops = self.last_execution_ops = 0
        self.last_memory_reads = self.last_bytes_loaded = 0
        self.last_cache_hit = False
        self.last_compiled_nodes = self.last_recomputed_nodes = 0
        self.last_invalidated_entries = 0
        self.last_invalidated_fraction = 0.0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def _prepare(self, query: GraphQuery):
        index, self.last_input_ops, self.last_memory_reads, self.last_bytes_loaded = scan(query)
        self.last_canonical_ops = self.last_execution_ops = 0
        self.last_cache_hit = False
        self.last_compiled_nodes = self.last_recomputed_nodes = 0
        return index

    def _finish(self, canonical: int, execution: int, hit: bool, compiled: int = 0, recomputed: int = 0):
        self.last_canonical_ops, self.last_execution_ops = canonical, execution
        self.last_cache_hit, self.last_compiled_nodes = hit, compiled
        self.last_recomputed_nodes = recomputed
        self.last_ops = self.last_input_ops + canonical + execution


class RandomTraceGuess(TraceBase):
    metadata = CandidateMetadata("random_trace_guess", "random", "Deterministic random modular guess")

    def query(self, source: GraphQuery, steps: int) -> int:
        self._prepare(source)
        self._finish(0, 1, False)
        return random.Random(self.seed ^ source.sink ^ len(source.nodes)).randrange(MODULUS)

    def update(self, source: Mutation, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class IndexedDAGPlanner(TraceBase):
    metadata = CandidateMetadata("indexed_dag_planner", "symbolic", "Full indexed DAG evaluation")

    def query(self, source: GraphQuery, steps: int) -> int:
        index = self._prepare(source)
        answer, operations, executed = evaluate_indexed(index, source.sink)
        self._finish(0, operations, False, recomputed=executed)
        return answer

    def update(self, source: Mutation, target: int) -> None:
        index, input_ops, _, _ = scan(source.new)
        _, execution, _ = evaluate_indexed(index, source.new.sink)
        self.update_ops = input_ops + execution

    def state_bytes(self) -> int:
        return 64


class ExactKeyTraceCache(IndexedDAGPlanner):
    metadata = CandidateMetadata("exact_key_trace_cache", "memory", "Byte-exact graph result cache")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.cache: dict[GraphQuery, int] = {}

    def query(self, source: GraphQuery, steps: int) -> int:
        index = self._prepare(source)
        hit = source in self.cache
        if hit:
            answer, operations, executed = self.cache[source], 1, 0
        else:
            answer, operations, executed = evaluate_indexed(index, source.sink)
            self.cache[source] = answer
        self._finish(0, operations, hit, int(not hit), executed)
        return answer

    def update(self, source: Mutation, target: int) -> None:
        invalidated = len(self.cache)
        self.cache.clear()
        index, input_ops, _, _ = scan(source.new)
        answer, execution, _ = evaluate_indexed(index, source.new.sink)
        self.cache[source.new] = answer
        self.last_invalidated_entries = invalidated
        self.last_invalidated_fraction = float(bool(invalidated))
        self.update_ops = invalidated + input_ops + execution

    def state_bytes(self) -> int:
        return 64 + sum(24 + sum(16 + 8 * len(node.children) for node in query.nodes) for query in self.cache)


class CanonicalResultCache(TraceBase):
    metadata = CandidateMetadata("canonical_result_cache", "symbolic", "Canonical whole-result cache")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.cache: dict[Key, int] = {}

    def query(self, source: GraphQuery, steps: int) -> int:
        index = self._prepare(source)
        root, canonical_ops = canonicalize(index, source.sink)
        hit = root in self.cache
        if hit:
            answer, execution, executed = self.cache[root], 1, 0
        else:
            answer, execution, executed = evaluate_indexed(index, source.sink)
            self.cache[root] = answer
        self._finish(canonical_ops, execution, hit, int(not hit), executed)
        return answer

    def update(self, source: Mutation, target: int) -> None:
        old_index, old_input, _, _ = scan(source.old)
        new_index, new_input, _, _ = scan(source.new)
        old_root, old_canonical = canonicalize(old_index, source.old.sink)
        new_root, new_canonical = canonicalize(new_index, source.new.sink)
        before = len(self.cache)
        invalidated = int(self.cache.pop(old_root, None) is not None)
        answer, execution, _ = evaluate_indexed(new_index, source.new.sink)
        self.cache[new_root] = answer
        self.last_invalidated_entries = invalidated
        self.last_invalidated_fraction = invalidated / before if before else 0.0
        self.last_recomputed_nodes = execution // OP_COST
        self.update_ops = old_input + new_input + old_canonical + new_canonical + execution

    def state_bytes(self) -> int:
        return 64 + sum(16 + key_size(key) for key in self.cache)


class DependencyTraceCompiler(CanonicalResultCache):
    metadata = CandidateMetadata("dependency_trace_compiler", "compiled", "Canonical dependency-subtrace cache")

    @staticmethod
    def _eval_key(key: Key, cache: dict[Key, int]):
        if key[0] == 0:
            return key[1], 0
        if key in cache:
            return cache[key], 0
        left, left_count = DependencyTraceCompiler._eval_key(key[2], cache)
        right, right_count = DependencyTraceCompiler._eval_key(key[3], cache)
        cache[key] = apply_op(key[1], left, right)
        return cache[key], left_count + right_count + 1

    def query(self, source: GraphQuery, steps: int) -> int:
        index = self._prepare(source)
        root, canonical_ops = canonicalize(index, source.sink)
        hit = root in self.cache
        answer, compiled = self._eval_key(root, self.cache)
        self._finish(canonical_ops, 1 if hit else OP_COST * compiled, hit, compiled, compiled)
        return answer

    def update(self, source: Mutation, target: int) -> None:
        old_index, old_input, _, _ = scan(source.old)
        new_index, new_input, _, _ = scan(source.new)
        old_root, old_canonical = canonicalize(old_index, source.old.sink)
        new_root, new_canonical = canonicalize(new_index, source.new.sink)
        before = len(self.cache)
        obsolete = internal_keys(old_root) - internal_keys(new_root)
        invalidated = sum(key in self.cache for key in obsolete)
        for key in obsolete:
            self.cache.pop(key, None)
        _, recomputed = self._eval_key(new_root, self.cache)
        self.last_invalidated_entries = invalidated
        self.last_invalidated_fraction = invalidated / before if before else 0.0
        self.last_recomputed_nodes = recomputed
        self.update_ops = old_input + new_input + old_canonical + new_canonical + OP_COST * recomputed

    def state_bytes(self) -> int:
        return 64 + sum(16 + key_size(key) for key in self.cache)


class OracleTraceCompiler(TraceBase):
    metadata = CandidateMetadata("oracle_trace_compiler", "oracle", "Supplied semantic result lower bound")

    def query(self, source: OracleInput, steps: int) -> int:
        self.last_input_ops = self.last_memory_reads = self.last_bytes_loaded = 0
        self._finish(0, 1, True)
        return source.target

    def update(self, source: Mutation, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64
