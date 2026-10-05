from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .base import CandidateBase, CandidateMetadata
from .mechanism_recombination_core import _mapping, _merge_worlds, _mode
from ..mechanism_recombination_contract import PublicTraining, PublicUpdate


Equation = tuple[int, int, int]  # result = second(first(source))


def infer_equations(maps: list[dict[int, int]]) -> tuple[Equation, ...]:
    """Keep the strongest error-free observed composition for each result map."""
    by_result: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for result_index, result in enumerate(maps):
        for first_index, first in enumerate(maps):
            for second_index, second in enumerate(maps):
                matches = errors = 0
                for source, target in result.items():
                    middle = first.get(source)
                    if middle is None or middle not in second:
                        continue
                    if second[middle] == target:
                        matches += 1
                    else:
                        errors += 1
                if matches >= 2 and errors == 0:
                    by_result[result_index].append((matches, first_index, second_index))
    equations: list[Equation] = []
    for result_index, choices in by_result.items():
        best = max(matches for matches, _, _ in choices)
        equations.extend(
            (first, second, result_index)
            for matches, first, second in choices if matches == best
        )
    return tuple(sorted(equations))


def close_relations(
    maps: list[dict[int, int]], equations: tuple[Equation, ...]
) -> tuple[list[dict[int, int]], int]:
    """Propagate only unanimous consequences of partial permutation equations."""
    closed = [dict(mapping) for mapping in maps]
    operations = 0
    while True:
        proposals: dict[tuple[int, int], set[int]] = defaultdict(set)
        for first_index, second_index, result_index in equations:
            first, second, result = (
                closed[first_index], closed[second_index], closed[result_index]
            )
            inverse_second = {target: source for source, target in second.items()}
            for source, middle in first.items():
                operations += 1
                if middle in second and source not in result:
                    proposals[(result_index, source)].add(second[middle])
                if source in result and middle not in second:
                    proposals[(second_index, middle)].add(result[source])
            for source, target in result.items():
                operations += 1
                if source not in first and target in inverse_second:
                    proposals[(first_index, source)].add(inverse_second[target])
        additions = 0
        for (map_index, source), values in proposals.items():
            if source not in closed[map_index] and len(values) == 1:
                closed[map_index][source] = next(iter(values))
                additions += 1
        if additions == 0:
            return closed, operations


class OperatorAlgebraCandidate(CandidateBase):
    metadata = CandidateMetadata(
        "operator_algebra", "anonymous_relation_completion",
        "Permutation-equivariant closure of observable partial operator equations.",
    )

    def __init__(self, seed: int = 0, *, mode: str) -> None:
        super().__init__(seed)
        self.mode = mode
        self.maps: list[dict[int, int]] = []
        self.test: dict[int, int] = {}
        self.pairs: tuple[tuple[int, int], ...] = ()
        self.default = 0
        self.relations: tuple[Equation, ...] = ()
        self.update_ops = 0.0

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, PublicTraining):
            raise TypeError("operator candidates require PublicTraining")
        raw = [_mapping(world) for world in facts.training_worlds]
        self.test = {pair.source: pair.target for pair in facts.test_worlds[0].support}
        self.default = _mode([
            target for mapping in raw for target in mapping.values()
        ] + list(self.test.values()))
        self.maps = raw if self.mode == "independent" else _merge_worlds(facts.training_worlds)
        self.fit_ops = float(sum(len(mapping) for mapping in raw))
        search_ops = 0
        if self.mode == "relations":
            self.relations = infer_equations(self.maps)
            search_ops += sum(len(result) for result in self.maps) * len(self.maps) ** 2
            self.maps, closure_ops = close_relations(self.maps, self.relations)
            search_ops += closure_ops

        scored: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for first_index, first in enumerate(self.maps):
            for second_index, second in enumerate(self.maps):
                errors = known = 0
                for source, target in self.test.items():
                    search_ops += 1
                    middle = first.get(source)
                    if middle is not None and middle in second:
                        known += 1
                        errors += second[middle] != target
                scored.append(((errors, len(self.test) - known), (first_index, second_index)))
        best = min(score for score, _ in scored)
        self.pairs = tuple(pair for score, pair in scored if score == best)
        self.meta_fit_ops = self.fit_ops + float(search_ops)

    def _step(self, source: int) -> int:
        if source in self.test:
            return self.test[source]
        predictions: list[int] = []
        for first_index, second_index in self.pairs:
            middle = self.maps[first_index].get(source)
            if middle is not None and middle in self.maps[second_index]:
                predictions.append(self.maps[second_index][middle])
        return _mode(predictions) if predictions else self.default

    def query(self, source: Any, steps: int) -> int:
        state = int(source.source)
        for _ in range(steps):
            state = self._step(state)
        self.last_ops = float(max(1, steps) * max(1, 2 * len(self.pairs)))
        self.last_bytes_touched = 8.0 * self.last_ops
        return state

    def update(self, source: Any, target: Any) -> None:
        update = source if isinstance(source, PublicUpdate) else PublicUpdate(source, int(target))
        self.test[update.query.source] = update.target
        self.update_ops += 1.0

    def state_bytes(self) -> int:
        edges = len(self.test) + sum(len(mapping) for mapping in self.maps)
        return 16 * edges + 24 * len(self.relations) + 16 * len(self.pairs)


class Candidate(OperatorAlgebraCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="relations")
