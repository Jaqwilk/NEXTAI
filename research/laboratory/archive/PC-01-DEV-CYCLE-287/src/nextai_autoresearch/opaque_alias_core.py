from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from .candidates.base import CandidateMetadata
from .semantic_trace_adversarial_core import normal_form, reduction_key, reduction_keys, reduction_size
from .semantic_trace_core import (
    MODULUS,
    OP_COST,
    GraphQuery,
    Key,
    Node,
    TraceBase,
    evaluate_indexed,
    scan,
)


Rows = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class TrainingEpisode:
    reference_rows: Rows
    current_rows: Rows
    mapping: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class AliasQuery:
    graph: GraphQuery
    reference_rows: Rows
    current_rows: Rows


@dataclass(frozen=True)
class AliasMutation:
    old: AliasQuery
    new: AliasQuery


@dataclass(frozen=True)
class OracleAliasQuery:
    query: AliasQuery
    mapping: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class OracleAliasMutation:
    old: OracleAliasQuery
    new: OracleAliasQuery


@dataclass(frozen=True)
class Alignment:
    mapping: tuple[tuple[int, int], ...] | None
    operations: int
    verification_operations: int


@dataclass(frozen=True)
class Prepared:
    source: AliasQuery
    index: dict[int, Node]
    normal: tuple | None
    input_ops: int
    reads: int
    bytes_loaded: int
    alignment_ops: int
    verification_ops: int
    equivalence_ops: int


def support_input_ops(rows: Rows) -> int:
    return len(rows) + sum(len(row) for row in rows)


def signatures(rows: Rows) -> tuple[dict[int, tuple[int, ...]], int]:
    aliases = sorted({alias for row in rows for alias in row})
    positions = {alias: index for index, alias in enumerate(aliases)}
    bits = [[0] * len(rows) for _ in aliases]
    occurrences = 0
    for row_index, row in enumerate(rows):
        for alias in row:
            bits[positions[alias]][row_index] = 1
            occurrences += 1
    return {alias: tuple(bits[index]) for index, alias in enumerate(aliases)}, len(aliases) * len(rows) + occurrences


def exact_alignment(reference_rows: Rows, current_rows: Rows) -> Alignment:
    reference, left_ops = signatures(reference_rows)
    current, right_ops = signatures(current_rows)
    buckets: dict[tuple[int, ...], int | None] = {}
    for alias, signature in reference.items():
        buckets[signature] = None if signature in buckets else alias
    mapping: dict[int, int] = {}
    lookup_ops = 2 * len(reference) * len(reference_rows)
    for alias, signature in current.items():
        match = buckets.get(signature)
        if match is None or match in mapping.values():
            return Alignment(None, left_ops + right_ops + lookup_ops, 0)
        mapping[alias] = match
    verify = len(mapping) * len(reference_rows)
    if len(mapping) != len(reference) or any(current[a] != reference[b] for a, b in mapping.items()):
        return Alignment(None, left_ops + right_ops + lookup_ops, verify)
    return Alignment(tuple(sorted(mapping.items())), left_ops + right_ops + lookup_ops, verify)


class MetricAligner:
    def __init__(self, independent: bool = False) -> None:
        self.independent = independent
        self.weights: tuple[float, ...] = ()
        self.threshold = -1.0
        self.fit_ops = 0

    def _distance(self, left: tuple[int, ...], right: tuple[int, ...]) -> float:
        if self.independent:
            return float(abs(sum(left) - sum(right)))
        return sum(self.weights[index] for index, (a, b) in enumerate(zip(left, right)) if a != b)

    def fit(self, episodes: Iterable[TrainingEpisode]) -> None:
        prepared = []
        mismatches: list[int] = []
        for episode in episodes:
            left, left_ops = signatures(episode.reference_rows)
            right, right_ops = signatures(episode.current_rows)
            truth = dict(episode.mapping)
            prepared.append((left, right, truth))
            self.fit_ops += left_ops + right_ops
            if not mismatches:
                mismatches = [0] * len(episode.reference_rows)
            for current_alias, current_signature in right.items():
                for reference_alias, reference_signature in left.items():
                    self.fit_ops += 1 if self.independent else len(current_signature)
                    if truth[current_alias] != reference_alias and not self.independent:
                        for index, (a, b) in enumerate(zip(reference_signature, current_signature)):
                            mismatches[index] += int(a != b)
        self.weights = (1.0,) if self.independent else tuple(float(max(1, count)) for count in mismatches)
        positive, negative = [], []
        for left, right, truth in prepared:
            for current_alias, current_signature in right.items():
                for reference_alias, reference_signature in left.items():
                    distance = self._distance(reference_signature, current_signature)
                    self.fit_ops += 1 if self.independent else len(current_signature)
                    (positive if truth[current_alias] == reference_alias else negative).append(distance)
        if positive and negative and max(positive) < min(negative):
            self.threshold = (max(positive) + min(negative)) / 2.0

    def align(self, reference_rows: Rows, current_rows: Rows) -> Alignment:
        reference, left_ops = signatures(reference_rows)
        current, right_ops = signatures(current_rows)
        mapping: dict[int, int] = {}
        pair_ops = 0
        for current_alias, current_signature in current.items():
            scores = []
            for reference_alias, reference_signature in reference.items():
                scores.append((self._distance(reference_signature, current_signature), reference_alias))
                pair_ops += 1 if self.independent else len(current_signature)
            scores.sort()
            if self.threshold < 0 or scores[0][0] > self.threshold or (len(scores) > 1 and scores[0][0] == scores[1][0]):
                return Alignment(None, left_ops + right_ops + pair_ops, 0)
            mapping[current_alias] = scores[0][1]
        verify = len(mapping) * len(reference_rows)
        if len(set(mapping.values())) != len(mapping) or any(current[a] != reference[b] for a, b in mapping.items()):
            return Alignment(None, left_ops + right_ops + pair_ops, verify)
        return Alignment(tuple(sorted(mapping.items())), left_ops + right_ops + pair_ops, verify)

    def state_bytes(self) -> int:
        return 32 + 8 * len(self.weights)


def mapped_index(index: dict[int, Node], mapping: dict[int, int]) -> tuple[dict[int, Node], int]:
    mapped, operations = {}, 0
    for node_id, node in index.items():
        if node.op < 0:
            symbol, value = divmod(node.value, MODULUS)
            if symbol:
                if symbol not in mapping:
                    raise ValueError("opaque atom lacks an acquired mapping")
                symbol = mapping[symbol]
            node = Node(node.node_id, node.op, symbol * MODULUS + value, node.children)
            operations += 1
        mapped[node_id] = node
    return mapped, operations


class AliasBase(TraceBase):
    metadata = CandidateMetadata("alias_base", "control", "Opaque alias control")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_alignment_ops = self.last_verification_ops = self.last_equivalence_ops = 0
        self.last_update_alignment_ops = self.last_update_verification_ops = 0
        self.last_update_equivalence_ops = self.last_update_execution_ops = 0

    @staticmethod
    def _raw(source: AliasQuery) -> Prepared:
        index, graph_input, reads, bytes_loaded = scan(source.graph)
        support_input = support_input_ops(source.reference_rows) + support_input_ops(source.current_rows)
        support_reads = sum(map(len, source.reference_rows)) + sum(map(len, source.current_rows))
        return Prepared(source, index, None, graph_input + support_input, reads + support_reads,
                        bytes_loaded + 8 * support_reads, 0, 0, 0)

    def _record(self, prepared: Prepared, execution: int, hit: bool, compiled: int = 0) -> None:
        self.last_input_ops, self.last_memory_reads = prepared.input_ops, prepared.reads
        self.last_bytes_loaded = prepared.bytes_loaded
        self.last_alignment_ops, self.last_verification_ops = prepared.alignment_ops, prepared.verification_ops
        self.last_equivalence_ops, self.last_canonical_ops = prepared.equivalence_ops, prepared.equivalence_ops
        self.last_execution_ops, self.last_cache_hit = execution, hit
        self.last_compiled_nodes = self.last_recomputed_nodes = compiled
        self.last_ops = prepared.input_ops + prepared.alignment_ops + prepared.verification_ops + prepared.equivalence_ops + execution


class RandomAliasGuess(AliasBase):
    metadata = CandidateMetadata("random_alias_guess", "random", "Deterministic random modular guess")

    def query(self, source: AliasQuery, steps: int) -> int:
        prepared = self._raw(source)
        self._record(prepared, 1, False)
        return random.Random(self.seed ^ source.graph.sink ^ len(source.graph.nodes)).randrange(MODULUS)

    def update(self, source: AliasMutation, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class OpaqueFullEvaluator(AliasBase):
    metadata = CandidateMetadata("opaque_full_evaluator", "symbolic", "Full opaque graph evaluation")

    def query(self, source: AliasQuery, steps: int) -> int:
        prepared = self._raw(source)
        answer, execution, executed = evaluate_indexed(prepared.index, source.graph.sink)
        self._record(prepared, execution, False, executed)
        return answer

    def update(self, source: AliasMutation, target: int) -> None:
        prepared = self._raw(source.new)
        _, execution, executed = evaluate_indexed(prepared.index, source.new.graph.sink)
        self.last_recomputed_nodes = executed
        self.last_update_execution_ops = execution
        self.update_ops = prepared.input_ops + execution

    def state_bytes(self) -> int:
        return 64


class OpaqueExactKeyCache(OpaqueFullEvaluator):
    metadata = CandidateMetadata("opaque_exact_key_cache", "memory", "Exact opaque episode cache")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.cache: dict[AliasQuery, int] = {}

    def query(self, source: AliasQuery, steps: int) -> int:
        prepared = self._raw(source)
        hit = source in self.cache
        if hit:
            answer, execution, executed = self.cache[source], 1, 0
        else:
            answer, execution, executed = evaluate_indexed(prepared.index, source.graph.sink)
            self.cache[source] = answer
        self._record(prepared, execution, hit, executed)
        return answer

    def update(self, source: AliasMutation, target: int) -> None:
        before = len(self.cache)
        self.cache.pop(source.old, None)
        prepared = self._raw(source.new)
        answer, execution, executed = evaluate_indexed(prepared.index, source.new.graph.sink)
        self.cache[source.new] = answer
        self.last_invalidated_entries = int(before > len(self.cache) - 1)
        self.last_invalidated_fraction = self.last_invalidated_entries / before if before else 0.0
        self.last_recomputed_nodes = executed
        self.last_update_execution_ops = execution
        self.update_ops = prepared.input_ops + execution

    def state_bytes(self) -> int:
        return 64 + sum(
            32
            + sum(16 + 8 * len(node.children) for node in query.graph.nodes)
            + 8 * sum(map(len, query.reference_rows + query.current_rows))
            for query in self.cache
        )


class AlignedTrace(AliasBase):
    metadata = CandidateMetadata("aligned_trace", "control", "Acquired-alias semantic cache")
    alignment_kind = "exact"
    dependency = False

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.aligner = MetricAligner(self.alignment_kind == "independent")
        self.cache: dict[Key | tuple, int] = {}

    def fit(self, facts: Iterable[TrainingEpisode], universe_size: int, max_depth: int) -> None:
        if self.alignment_kind in {"pairwise", "independent"}:
            self.aligner.fit(facts)
            self.fit_ops = self.aligner.fit_ops
        else:
            self.fit_ops = 0

    def _prepare(self, source: AliasQuery | OracleAliasQuery) -> Prepared:
        supplied = isinstance(source, OracleAliasQuery)
        raw_source = source.query if supplied else source
        prepared = self._raw(raw_source)
        if supplied:
            alignment = Alignment(source.mapping, 0, 0)
        elif self.alignment_kind == "exact":
            alignment = exact_alignment(raw_source.reference_rows, raw_source.current_rows)
        else:
            alignment = self.aligner.align(raw_source.reference_rows, raw_source.current_rows)
        if alignment.mapping is None:
            return Prepared(raw_source, prepared.index, None, prepared.input_ops, prepared.reads,
                            prepared.bytes_loaded, alignment.operations, alignment.verification_operations, 0)
        mapped, map_ops = mapped_index(prepared.index, dict(alignment.mapping))
        normal, equivalence = normal_form(mapped, raw_source.graph.sink)
        return Prepared(raw_source, prepared.index, normal, prepared.input_ops, prepared.reads,
                        prepared.bytes_loaded, alignment.operations + map_ops,
                        alignment.verification_operations, equivalence)

    @staticmethod
    def _evaluate(key: Key, cache: dict[Key | tuple, int]) -> tuple[int, int]:
        if key[0] == 0:
            return key[2], 0
        if key in cache:
            return cache[key], 0
        left, left_count = AlignedTrace._evaluate(key[1], cache)
        right, right_count = AlignedTrace._evaluate(key[2], cache)
        cache[key] = (left + right) % MODULUS
        return cache[key], left_count + right_count + 1

    def query(self, source: AliasQuery | OracleAliasQuery, steps: int) -> int:
        prepared = self._prepare(source)
        if prepared.normal is None:
            answer, execution, executed = evaluate_indexed(prepared.index, prepared.source.graph.sink)
            self._record(prepared, execution, False, executed)
            return answer
        if self.dependency:
            key = reduction_key(prepared.normal)
            hit = key in self.cache
            answer, compiled = self._evaluate(key, self.cache)
            self._record(prepared, 1 if hit else OP_COST * compiled, hit, compiled)
            return answer
        hit = prepared.normal in self.cache
        if hit:
            answer, execution, executed = self.cache[prepared.normal], 1, 0
        else:
            answer, execution, executed = evaluate_indexed(prepared.index, prepared.source.graph.sink)
            self.cache[prepared.normal] = answer
        self._record(prepared, execution, hit, executed)
        return answer

    @staticmethod
    def _mutation(source: AliasMutation | OracleAliasMutation):
        return (source.old, source.new)

    def update(self, source: AliasMutation | OracleAliasMutation, target: int) -> None:
        old_source, new_source = self._mutation(source)
        old, new = self._prepare(old_source), self._prepare(new_source)
        before = len(self.cache)
        invalidated = recomputed = 0
        if old.normal is not None and new.normal is not None and self.dependency:
            old_key, new_key = reduction_key(old.normal), reduction_key(new.normal)
            obsolete = reduction_keys(old_key) - reduction_keys(new_key)
            invalidated = sum(key in self.cache for key in obsolete)
            for key in obsolete:
                self.cache.pop(key, None)
            _, recomputed = self._evaluate(new_key, self.cache)
            execution = OP_COST * recomputed
        elif old.normal is not None and new.normal is not None:
            invalidated = int(self.cache.pop(old.normal, None) is not None)
            answer, execution, recomputed = evaluate_indexed(new.index, new.source.graph.sink)
            self.cache[new.normal] = answer
        else:
            _, execution, recomputed = evaluate_indexed(new.index, new.source.graph.sink)
        self.last_invalidated_entries = invalidated
        self.last_invalidated_fraction = invalidated / before if before else 0.0
        self.last_recomputed_nodes = recomputed
        self.last_update_alignment_ops = old.alignment_ops + new.alignment_ops
        self.last_update_verification_ops = old.verification_ops + new.verification_ops
        self.last_update_equivalence_ops = old.equivalence_ops + new.equivalence_ops
        self.last_update_execution_ops = execution
        self.update_ops = (old.input_ops + new.input_ops + self.last_update_alignment_ops +
                           self.last_update_verification_ops + self.last_update_equivalence_ops + execution)

    def state_bytes(self) -> int:
        learned = self.aligner.state_bytes() if self.alignment_kind in {"pairwise", "independent"} else 0
        if self.dependency:
            return 64 + learned + sum(16 + reduction_size(key) for key in self.cache)
        return 64 + learned + sum(32 + 16 * len(key[1]) for key in self.cache)


class IndependentFrequencyCache(AlignedTrace):
    metadata = CandidateMetadata("independent_frequency_cache", "learned", "Learned independent-frequency safe cache")
    alignment_kind = "independent"


class SoftUnificationResultCache(AlignedTrace):
    metadata = CandidateMetadata("soft_unification_result_cache", "learned", "Learned pairwise soft-unification result cache")
    alignment_kind = "pairwise"


class SoftUnificationDependencyTrace(SoftUnificationResultCache):
    metadata = CandidateMetadata("soft_unification_dependency_trace", "learned", "Learned pairwise soft-unification dependency trace")
    dependency = True


class ExactConstraintResultCache(AlignedTrace):
    metadata = CandidateMetadata("exact_constraint_result_cache", "symbolic", "Exact relational-constraint result cache")


class ExactConstraintDependencyTrace(ExactConstraintResultCache):
    metadata = CandidateMetadata("exact_constraint_dependency_trace", "compiled", "Exact relational-constraint dependency trace")
    dependency = True


class MappingOracleDependencyTrace(ExactConstraintDependencyTrace):
    metadata = CandidateMetadata("mapping_oracle_dependency_trace", "oracle", "Supplied alias-mapping dependency lower bound")
    alignment_kind = "oracle"
