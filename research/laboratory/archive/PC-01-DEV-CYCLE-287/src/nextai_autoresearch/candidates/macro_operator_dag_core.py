from __future__ import annotations

from .base import CandidateBase, CandidateMetadata
from ..operator_experience_contract import (
    Mutation, Observation, Query, Table, Term, Training, compose, flatten,
    identity, input_ops,
)


MIN_COUNT = 2
CONSTANTS = (MIN_COUNT, "left_aligned_dyadic", "longest_first_exact_fallback")


def _segments(tables: tuple[Table, ...]):
    width = 2
    while width <= len(tables):
        for start in range(0, len(tables) - width + 1, width):
            yield tables[start:start + width]
        width *= 2


def _compile(key: tuple[Table, ...]) -> tuple[Table, int]:
    result = identity(len(key[0]))
    for table in key:
        result = compose(result, table)
    return result, len(result) * len(key)


class MacroOperatorDAG(CandidateBase):
    metadata = CandidateMetadata(
        "learned_macro_operator_dag", "learned", "Threshold-two exact macro DAG"
    )
    MODE = "persist"
    CONSTANTS = CONSTANTS

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.counts: dict[tuple[Table, ...], int] = {}
        self.admitted: set[tuple[Table, ...]] = set()
        self.macros: dict[tuple[Table, ...], Table] = {}
        self.meta_fit_ops = 0
        self.total_update_ops = 0
        self.last_cache_hit = False
        self.last_bytes_touched = 0

    def _learn(self, term: Term) -> int:
        tables = flatten(term)
        work = input_ops(term)
        for key in _segments(tables):
            work += len(key)
            count = self.counts.get(key, 0) + 1
            self.counts[key] = count
            if count == MIN_COUNT and self.MODE != "frozen":
                self.admitted.add(key)
                if self.MODE == "persist":
                    table, compile_work = _compile(key)
                    self.macros[key] = table
                    work += compile_work
        return work

    def fit(self, facts: Training, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, Training):
            raise ValueError("macro DAG requires anonymous labeled operator pairs")
        work = 0
        for pair in facts.pairs:
            work += self._learn(pair.left) + self._learn(pair.right)
        self.fit_ops = self.meta_fit_ops = work

    def _longest(self, tables: tuple[Table, ...], start: int) -> tuple[Table, ...] | None:
        width = 1
        limit = len(tables) - start
        while width * 2 <= limit:
            width *= 2
        while width >= 2:
            key = tables[start:start + width]
            if key in self.admitted:
                return key
            width //= 2
        return None

    def query(self, source: Query, steps: int) -> int:
        tables = flatten(source.term)
        state, position, execution = source.state, 0, 0
        hit = False
        while position < len(tables):
            key = self._longest(tables, position)
            if key is None:
                state = tables[position][state]
                position += 1
                execution += 1
                continue
            hit = True
            if self.MODE == "persist":
                table = self.macros[key]
                execution += 1
            else:
                table, work = _compile(key)
                execution += work + 1
            state = table[state]
            position += len(key)
        scan = input_ops(source.term)
        self.last_ops = scan + execution
        self.last_cache_hit = hit
        self.last_bytes_touched = 8 * scan + self.state_bytes()
        return state

    def update(self, source: Observation | Mutation, target: object = None) -> None:
        term = source.query.term if isinstance(source, Observation) else source.new
        self.total_update_ops += self._learn(term)
        self.update_ops = self.total_update_ops

    def state_bytes(self) -> int:
        keys = set(self.counts) | self.admitted | set(self.macros)
        key_bytes = sum(32 + 8 * sum(len(table) for table in key) for key in keys)
        table_bytes = sum(32 + 8 * len(table) for table in self.macros.values())
        return 64 + key_bytes + table_bytes + 16 * len(self.counts)


class Candidate(MacroOperatorDAG):
    MODE = "persist"
