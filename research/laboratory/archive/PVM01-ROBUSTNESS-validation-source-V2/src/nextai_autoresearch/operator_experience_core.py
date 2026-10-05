from __future__ import annotations

import random

from .candidates.base import CandidateBase, CandidateMetadata
from .operator_experience_contract import (
    Mutation, Observation, Pattern, Query, Table, Term, Training, anti_unify,
    apply, canonical_table, flatten, input_ops, matches,
)


class OperatorBase(CandidateBase):
    metadata = CandidateMetadata("operator_base", "control", "Operator experience control")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_cache_hit = False
        self.last_input_ops = self.last_execution_ops = 0
        self.last_bytes_touched = 0

    def fit(self, facts: Training, universe_size: int, max_depth: int) -> None:
        self.fit_ops = self.meta_fit_ops = 0

    def _record(self, term: Term, execution: int, hit: bool) -> None:
        self.last_input_ops = input_ops(term)
        self.last_execution_ops = execution
        self.last_cache_hit = hit
        self.last_ops = self.last_input_ops + execution
        self.last_bytes_touched = 8 * self.last_input_ops + self.state_bytes()

    def update(self, source: Observation | Mutation, target: object = None) -> None:
        self.update_ops = 1


class OperatorInterpreter(OperatorBase):
    metadata = CandidateMetadata("operator_interpreter", "symbolic", "Exact recursive interpreter")

    def query(self, source: Query, steps: int) -> int:
        answer, execution = apply(source.term, source.state)
        self._record(source.term, execution, False)
        return answer

    def state_bytes(self) -> int:
        return 64


class _Cache(OperatorInterpreter):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.cache: dict[object, Table] = {}

    def _key(self, term: Term) -> tuple[object, int]:
        raise NotImplementedError

    def query(self, source: Query, steps: int) -> int:
        key, normalization = self._key(source.term)
        hit = key in self.cache
        if not hit:
            table, compilation = canonical_table(source.term)
            self.cache[key] = table
        else:
            compilation = 1
        self._record(source.term, normalization + compilation, hit)
        return self.cache[key][source.state]

    def update(self, source: Observation | Mutation, target: object = None) -> None:
        term = source.query.term if isinstance(source, Observation) else source.new
        key, normalization = self._key(term)
        table, compilation = canonical_table(term)
        self.cache[key] = table
        self.update_ops = input_ops(term) + normalization + compilation

    def state_bytes(self) -> int:
        return 64 + sum(32 + 8 * len(table) for table in self.cache.values())


class ExactKeyCache(_Cache):
    metadata = CandidateMetadata("operator_exact_key_cache", "memory", "Raw syntax exact-key cache")

    def _key(self, term: Term) -> tuple[object, int]:
        return term, 1


class StructuralResultCache(_Cache):
    metadata = CandidateMetadata("operator_structural_result_cache", "memory", "Flattened whole-result cache")

    def _key(self, term: Term) -> tuple[object, int]:
        values = flatten(term)
        return values, len(values)


class CanonicalTableCache(_Cache):
    metadata = CandidateMetadata("operator_canonical_table_cache", "symbolic", "Exact composite-table canonical cache")

    def _key(self, term: Term) -> tuple[object, int]:
        table, operations = canonical_table(term)
        return table, operations


class AntiUnificationCache(StructuralResultCache):
    metadata = CandidateMetadata("operator_anti_unification_cache", "symbolic", "Verified first-order anti-unification cache")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.positive: tuple[Pattern, ...] = ()
        self.negative: tuple[Pattern, ...] = ()

    def fit(self, facts: Training, universe_size: int, max_depth: int) -> None:
        positive, negative, operations = [], [], 0
        for pair in facts.pairs:
            pattern = anti_unify(pair.left, pair.right)
            operations += input_ops(pair.left) + input_ops(pair.right)
            if pattern is not None:
                (positive if pair.equivalent else negative).append(pattern)
        self.positive, self.negative = tuple(positive), tuple(negative)
        self.fit_ops = self.meta_fit_ops = operations

    def _key(self, term: Term) -> tuple[object, int]:
        checks = 0
        accepted: list[int] = []
        for index, pattern in enumerate(self.positive):
            checks += len(pattern)
            if matches(pattern, term):
                accepted.append(index)
        blocked = False
        for pattern in self.negative:
            checks += len(pattern)
            blocked |= matches(pattern, term)
        if len(accepted) == 1 and not blocked:
            canonical, verify = canonical_table(term)
            return ("pattern", accepted[0], canonical), checks + verify
        return ("raw", flatten(term)), checks

    def state_bytes(self) -> int:
        patterns = sum(len(pattern) for pattern in self.positive + self.negative)
        return super().state_bytes() + 16 * patterns


class NearestCanonical(OperatorBase):
    metadata = CandidateMetadata("operator_nearest_canonical", "memory", "Nearest canonical operator with exact fallback")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.tables: tuple[Table, ...] = ()

    def fit(self, facts: Training, universe_size: int, max_depth: int) -> None:
        tables, operations = [], 0
        for pair in facts.pairs:
            for term in (pair.left, pair.right):
                table, work = canonical_table(term)
                tables.append(table)
                operations += input_ops(term) + work
        self.tables = tuple(dict.fromkeys(tables))
        self.fit_ops = self.meta_fit_ops = operations

    def query(self, source: Query, steps: int) -> int:
        table, compilation = canonical_table(source.term)
        comparisons = sum(len(table) for _ in self.tables)
        exact = table in self.tables
        self._record(source.term, compilation + comparisons + (0 if exact else 1), exact)
        return table[source.state]

    def state_bytes(self) -> int:
        return 64 + 8 * sum(len(table) for table in self.tables)


class RandomOperator(OperatorBase):
    metadata = CandidateMetadata("operator_random", "random", "Deterministic random state")

    def query(self, source: Query, steps: int) -> int:
        self._record(source.term, 1, False)
        return random.Random(self.seed ^ source.state ^ source.term.node_id).randrange(
            len(flatten(source.term, strip_identity=False)[0])
        )

    def state_bytes(self) -> int:
        return 64
