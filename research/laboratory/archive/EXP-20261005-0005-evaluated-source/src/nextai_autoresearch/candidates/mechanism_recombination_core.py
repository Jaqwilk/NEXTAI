from __future__ import annotations

from collections import Counter
from typing import Any

from .base import CandidateBase, CandidateMetadata
from ..mechanism_recombination_contract import PublicTraining, PublicUpdate


def _mapping(world: Any) -> dict[int, int]:
    return {pair.source: pair.target for pair in (*world.support, *world.examples)}


def _mode(values: list[int]) -> int:
    counts = Counter(values)
    return min(counts, key=lambda value: (-counts[value], value)) if counts else 0


def _merge_worlds(worlds: tuple[Any, ...]) -> list[dict[int, int]]:
    """Greedily join the three anonymous samples of each deterministic map."""
    groups = [[_mapping(world)] for world in worlds]
    while len(groups) > 11:
        best: tuple[int, int, int] | None = None
        for left in range(len(groups)):
            a = {key: value for item in groups[left] for key, value in item.items()}
            for right in range(left + 1, len(groups)):
                b = {key: value for item in groups[right] for key, value in item.items()}
                overlap = set(a) & set(b)
                if any(a[key] != b[key] for key in overlap):
                    continue
                score = sum(a[key] == b[key] for key in overlap)
                candidate = (score, -left, -right)
                if best is None or candidate > best:
                    best = candidate
        if best is None:
            break
        left, right = -best[1], -best[2]
        groups[left].extend(groups.pop(right))
    return [{key: value for item in group for key, value in item.items()} for group in groups]


class RecombinationCandidate(CandidateBase):
    metadata = CandidateMetadata(
        "recombination", "anonymous_mechanism_library",
        "Bounded public-pair learner for held-out mechanism composition.",
    )

    def __init__(self, seed: int = 0, *, mode: str) -> None:
        super().__init__(seed)
        self.mode = mode
        self.maps: list[dict[int, int]] = []
        self.test: dict[int, int] = {}
        self.default = 0
        self.selected: tuple[dict[int, int], dict[int, int]] | None = None
        self.update_ops = 0

    @staticmethod
    def _composition_score(
        first: dict[int, int], second: dict[int, int], support: dict[int, int]
    ) -> tuple[int, int]:
        known = errors = 0
        for source, target in support.items():
            middle = first.get(source)
            if middle is not None and middle in second:
                known += 1
                errors += second[middle] != target
        return errors, -known

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, PublicTraining):
            raise TypeError("implementable recombination candidates require PublicTraining")
        raw = [_mapping(world) for world in facts.training_worlds]
        self.test = {pair.source: pair.target for pair in facts.test_worlds[0].support}
        targets = [target for mapping in raw for target in mapping.values()]
        self.default = _mode(targets + list(self.test.values()))
        self.maps = _merge_worlds(facts.training_worlds) if self.mode in {"shared", "mdl"} else raw
        self.fit_ops = float(sum(len(mapping) for mapping in raw))
        self.meta_fit_ops = self.fit_ops
        if self.mode in {"shared", "mdl"}:
            choices: list[tuple[tuple[int, ...], dict[int, int], dict[int, int]]] = []
            for left, first in enumerate(self.maps):
                for right, second in enumerate(self.maps):
                    errors, negative_known = self._composition_score(first, second, self.test)
                    known = -negative_known
                    # MDL: exact lexicographic minimization of errors, unexplained
                    # support, stored edges and stable library indices.
                    key = (errors, len(self.test) - known,
                           len(first) + len(second), left, right)
                    choices.append((key, first, second))
            if choices:
                _, first, second = min(choices, key=lambda item: item[0])
                self.selected = first, second
                search = len(self.maps) ** 2 * max(1, len(self.test))
                self.meta_fit_ops += float(search)

    def _step(self, source: int) -> int:
        if source in self.test:
            return self.test[source]
        if self.mode == "unigram" or self.mode == "no_cross":
            return self.default
        if self.mode == "markov":
            values = [mapping[source] for mapping in self.maps if source in mapping]
            return _mode(values) if values else self.default
        if self.mode in {"nearest", "independent"}:
            best = min(
                self.maps,
                key=lambda mapping: (
                    sum(mapping[key] != value for key, value in self.test.items() if key in mapping),
                    -sum(key in mapping for key in self.test),
                    len(mapping),
                ),
            )
            return best.get(source, self.default)
        if self.selected is not None:
            first, second = self.selected
            middle = first.get(source)
            if middle is not None and middle in second:
                return second[middle]
        return self.default

    def query(self, source: Any, steps: int) -> int:
        state = int(source.source)
        for _ in range(steps):
            state = self._step(state)
        multiplier = len(self.maps) if self.mode in {"markov", "nearest", "independent"} else 2
        self.last_ops = float(max(1, steps) * max(1, multiplier))
        self.last_bytes_touched = self.last_ops * 16.0
        return state

    def update(self, source: Any, target: Any) -> None:
        update = source if isinstance(source, PublicUpdate) else PublicUpdate(source, int(target))
        self.test[update.query.source] = update.target
        self.update_ops += 1.0

    def state_bytes(self) -> int:
        return 16 * (len(self.test) + sum(len(mapping) for mapping in self.maps))


class Candidate(RecombinationCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="shared")
