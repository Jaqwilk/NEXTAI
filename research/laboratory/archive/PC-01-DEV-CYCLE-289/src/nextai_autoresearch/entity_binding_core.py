from __future__ import annotations

import random

from .candidates.base import CandidateBase, CandidateMetadata
from .entity_binding_contract import (
    BindingFact,
    DIMENSION,
    LATENT,
    OracleQuery,
    OracleSpec,
    OracleUpdate,
    View,
    ViewPair,
    ViewQuery,
)


def center(pair: ViewPair) -> View:
    return tuple((left + right) / 2.0 for left, right in zip(*pair))


def bundles(facts: tuple[BindingFact, ...]) -> tuple[ViewPair, ...]:
    return tuple(pair for fact in facts for pair in (fact.source, fact.target))


def stable_dimensions(facts: tuple[BindingFact, ...]) -> tuple[int, ...]:
    pairs = bundles(facts)
    variance = [sum((pair[0][d] - pair[1][d]) ** 2 for pair in pairs) for d in range(DIMENSION)]
    return tuple(sorted(range(DIMENSION), key=variance.__getitem__)[:LATENT])


class RandomViewBinding(CandidateBase):
    metadata = CandidateMetadata("random_view_binding", "random_control", "Seeded random payload control.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.values = tuple(fact.value for fact in facts)
        self.fit_ops = 0

    def query(self, source: ViewQuery, steps: int) -> int:
        self.last_ops, self.last_comparisons, self.last_bytes_touched = DIMENSION, 0, DIMENSION * 8
        return random.Random(self.seed ^ source.signature ^ steps).choice(self.values)

    def update(self, source: BindingFact, target: int) -> None:
        self.values += (source.value,)
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 128 + 8 * len(self.values)


class ScanLinkage(CandidateBase):
    weighted = False
    metadata = CandidateMetadata("raw_view_nearest", "scan_control", "Full raw-view nearest scan.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.facts = tuple(facts)
        self.sources = tuple(center(fact.source) for fact in self.facts)
        self.targets = tuple(center(fact.target) for fact in self.facts)
        pairs = bundles(self.facts)
        variance = [sum((pair[0][d] - pair[1][d]) ** 2 for pair in pairs) / len(pairs)
                    for d in range(DIMENSION)]
        self.weights = tuple(1.0 / (value + 0.01) for value in variance) if self.weighted else (1.0,) * DIMENSION
        self.fit_ops = len(pairs) * DIMENSION * (3 if self.weighted else 1)

    def _match(self, view: View) -> int:
        return min(range(len(self.sources)), key=lambda index: sum(
            weight * (left - right) ** 2
            for weight, left, right in zip(self.weights, view, self.sources[index])))

    def query(self, source: ViewQuery, steps: int) -> int:
        view, answer = source.view, -1
        for _ in range(steps):
            index = self._match(view)
            view, answer = self.targets[index], self.facts[index].value
        self.last_comparisons = len(self.facts) * steps
        self.last_ops = DIMENSION + self.last_comparisons * DIMENSION * 4
        self.last_bytes_touched = DIMENSION * 8 + self.last_comparisons * DIMENSION * 8
        return answer

    def update(self, source: BindingFact, target: int) -> None:
        self.facts += (source,)
        self.sources += (center(source.source),)
        self.targets += (center(source.target),)
        self.update_ops = 4 * DIMENSION

    def state_bytes(self) -> int:
        return 256 + len(self.facts) * (4 * DIMENSION * 8 + 8) + DIMENSION * 8


class ProbabilisticLinkage(ScanLinkage):
    weighted = True
    metadata = CandidateMetadata("probabilistic_linkage_scan", "record_linkage", "Learned full-scan diagonal linkage metric.")


class HashIndex(CandidateBase):
    metadata = CandidateMetadata("paired_stability_index", "classical_index", "Analytic invariant-coordinate hash.")

    def _select(self, facts: tuple[BindingFact, ...]) -> tuple[int, ...]:
        self.fit_ops = len(bundles(facts)) * DIMENSION * 3
        return stable_dimensions(facts)

    def _key(self, view: View) -> tuple[int, ...]:
        return tuple(int(view[index] >= 0) for index in self.dimensions)

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        facts = tuple(facts)
        self.dimensions = self._select(facts)
        self.index = {self._key(center(fact.source)): (self._key(center(fact.target)), fact.value)
                      for fact in facts}
        self.fit_ops += len(facts) * DIMENSION * 2

    def query(self, source: ViewQuery, steps: int) -> int:
        key, answer = self._key(source.view), -1
        for _ in range(steps):
            item = self.index.get(key)
            if item is None:
                answer = -1
                break
            key, answer = item
        self.last_ops = DIMENSION + 2 * steps
        self.last_comparisons = 0
        self.last_bytes_touched = DIMENSION * 8 + 24 * steps
        return answer

    def update(self, source: BindingFact, target: int) -> None:
        self.index[self._key(center(source.source))] = (self._key(center(source.target)), source.value)
        self.update_ops = 2 * DIMENSION

    def state_bytes(self) -> int:
        return 256 + 8 * len(self.dimensions) + 32 * len(self.index)


class ContrastiveHash(HashIndex):
    metadata = CandidateMetadata("contrastive_hash_index", "learned_metric_index", "Paired positive/negative contrastive hash.")

    def _select(self, facts: tuple[BindingFact, ...]) -> tuple[int, ...]:
        pairs = bundles(facts)
        positive = [sum((pair[0][d] - pair[1][d]) ** 2 for pair in pairs) for d in range(DIMENSION)]
        negative = [sum((pairs[i][0][d] - pairs[(i + 1) % len(pairs)][1][d]) ** 2
                        for i in range(len(pairs))) for d in range(DIMENSION)]
        score = [negative[d] - positive[d] for d in range(DIMENSION)]
        self.fit_ops = len(pairs) * DIMENSION * 10
        return tuple(sorted(range(DIMENSION), key=score.__getitem__, reverse=True)[:LATENT])


class RawSignLSH(HashIndex):
    metadata = CandidateMetadata("raw_sign_lsh", "lsh_control", "Unlearned all-coordinate sign hash.")

    def _select(self, facts: tuple[BindingFact, ...]) -> tuple[int, ...]:
        self.fit_ops = 0
        return tuple(range(DIMENSION))


class OracleIdentityIndex(CandidateBase):
    metadata = CandidateMetadata("oracle_identity_index", "oracle_control", "Supplied persistent entity identity.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        spec = tuple(facts)[0]
        self.transitions, self.values = dict(spec.transitions), dict(spec.values)
        self.fit_ops = 0

    def query(self, source: OracleQuery, steps: int) -> int:
        entity = source.entity
        for _ in range(steps):
            entity = self.transitions[entity]
        self.last_ops, self.last_comparisons = DIMENSION + steps, 0
        self.last_bytes_touched = DIMENSION * 8 + 16 * steps
        return self.values[entity]

    def update(self, source: OracleUpdate, target: int) -> None:
        self.transitions[source.entity] = source.target
        self.values[source.target] = source.value
        self.update_ops = 2

    def state_bytes(self) -> int:
        return 192 + 24 * len(self.transitions)
