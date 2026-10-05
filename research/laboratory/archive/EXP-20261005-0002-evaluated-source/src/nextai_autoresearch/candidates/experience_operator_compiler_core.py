from __future__ import annotations

from .base import CandidateBase, CandidateMetadata
from ..operator_experience_contract import (
    Mutation, Observation, Query, Table, Term, Training, apply, flatten, input_ops,
)


PROBE_LIMIT = 3
EXPERIENCE_THRESHOLDS = (4, 16)
CONSTANTS = (PROBE_LIMIT, EXPERIENCE_THRESHOLDS)


def _behavior(term: Term) -> tuple[Table, int]:
    size = len(flatten(term, strip_identity=False)[0])
    values, work = [], 0
    for state in range(size):
        value, operations = apply(term, state)
        values.append(value)
        work += operations
    return tuple(values), work


class ExperienceOperatorCompiler(CandidateBase):
    """Counterexample-learned behavioral probes plus a local compiled cache."""

    metadata = CandidateMetadata(
        "experience_operator_compiler", "learned", "Counterexample probe compiler"
    )
    SCOPE = "pooled"
    CONSTANTS = CONSTANTS

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.probes: tuple[int, ...] = ()
        self.tables: list[Table] = []
        self.counts: list[int] = []
        self.raw_cache: dict[Term, Table] = {}
        self.last_cache_hit = False
        self.last_bytes_touched = 0
        self.meta_fit_ops = 0
        self.observations = 0

    def fit(self, facts: Training, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, Training):
            raise ValueError("operator compiler requires labeled operator pairs")
        differences: list[set[int]] = []
        operations = 0
        for pair in facts.pairs:
            left, left_work = _behavior(pair.left)
            right, right_work = _behavior(pair.right)
            operations += input_ops(pair.left) + input_ops(pair.right) + left_work + right_work
            changed = {state for state, values in enumerate(zip(left, right)) if values[0] != values[1]}
            if pair.equivalent and changed:
                raise ValueError("positive pair is not behaviorally equivalent")
            if not pair.equivalent and not changed:
                raise ValueError("negative pair does not change the operator")
            if not pair.equivalent and self.SCOPE != "no_pairing":
                differences.append(changed)

        probes: list[int] = []
        uncovered = list(differences)
        while uncovered and len(probes) < PROBE_LIMIT:
            scores = [sum(state in values for values in uncovered) for state in range(universe_size)]
            probe = max(range(universe_size), key=lambda state: (scores[state], -state))
            probes.append(probe)
            uncovered = [values for values in uncovered if probe not in values]
        for state in range(universe_size):
            if len(probes) == PROBE_LIMIT:
                break
            if state not in probes:
                probes.append(state)
        self.probes = tuple(probes)
        self.fit_ops = self.meta_fit_ops = operations

    def _probe_count(self) -> int:
        if self.observations >= EXPERIENCE_THRESHOLDS[1]:
            return 1
        if self.observations >= EXPERIENCE_THRESHOLDS[0]:
            return 2
        return PROBE_LIMIT

    def _record(self, term: Term, execution: int, hit: bool) -> None:
        scan = input_ops(term)
        self.last_ops = scan + execution
        self.last_cache_hit = hit
        self.last_bytes_touched = 8 * scan + self.state_bytes()

    def query(self, source: Query, steps: int) -> int:
        term = source.term
        if self.SCOPE != "pooled":
            cached = self.raw_cache.get(term)
            if cached is not None:
                self._record(term, 1, True)
                return cached[source.state]
            answer, work = apply(term, source.state)
            self._record(term, work, False)
            return answer

        probes = self.probes[: self._probe_count()]
        signature, work = [], 0
        for state in probes:
            value, operations = apply(term, state)
            signature.append(value)
            work += operations
        matches = [
            table for table in self.tables
            if all(table[state] == value for state, value in zip(probes, signature))
        ]
        if len(matches) == 1:
            self._record(term, work + 1, True)
            return matches[0][source.state]
        answer, fallback = apply(term, source.state)
        self._record(term, work + fallback, False)
        return answer

    def _store(self, term: Term) -> int:
        table, work = _behavior(term)
        if self.SCOPE == "pooled":
            try:
                index = self.tables.index(table)
                self.counts[index] += 1
            except ValueError:
                self.tables.append(table)
                self.counts.append(1)
        else:
            self.raw_cache[term] = table
        self.observations += 1
        return input_ops(term) + work

    def update(self, source: Observation | Mutation, target: object = None) -> None:
        term = source.query.term if isinstance(source, Observation) else source.new
        self.update_ops = self._store(term)

    def state_bytes(self) -> int:
        tables = self.tables if self.SCOPE == "pooled" else list(self.raw_cache.values())
        return 64 + 8 * len(self.probes) + sum(40 + 8 * len(table) for table in tables)


class Candidate(ExperienceOperatorCompiler):
    SCOPE = "pooled"
