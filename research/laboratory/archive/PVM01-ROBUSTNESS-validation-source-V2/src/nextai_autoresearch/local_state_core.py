from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .candidates.base import CandidateBase, CandidateMetadata


Feature = tuple[int, ...]
Target = tuple[int, int]


def bits(value: int, width: int) -> tuple[int, ...]:
    return tuple((value >> index) & 1 for index in range(width))


def feature(descriptor: int, state: int, pulse: int) -> Feature:
    return (*bits(descriptor, 3), *bits(state, 3), *bits(pulse, 2))


def local_rule(kind: int, state: int, pulse: int) -> Target:
    memory = int(state.bit_count() >= 2)
    next_memory = memory ^ ((pulse >> 1) & 1) ^ (kind & 1)
    outgoing = (pulse + 1 + kind + memory * (kind + 1)) & 3
    return 7 * next_memory, outgoing


@dataclass(frozen=True)
class OracleSpec:
    kind_by_descriptor: dict[int, int]


class LocalStateBase(CandidateBase):
    dense = False

    def _transition(self, raw: Feature) -> tuple[Target, int]:
        raise NotImplementedError

    def query(self, source: Any, steps: int) -> Target | tuple[int, int, int]:
        task, size = source, len(source.descriptors)
        node, pulse, states = task.source, task.pulse, list(task.states)
        operations, evaluations = 6 * size, 0
        for _ in range(steps):
            raw = feature(task.descriptors[node], states[node], pulse)
            (next_state, pulse), rule_ops = self._transition(raw)
            if self.dense:
                operations += size * (rule_ops + 1)
                evaluations += size
            else:
                operations += rule_ops + 8
                evaluations += 1
            states[node] = next_state
            node = task.edges[node][pulse & 1]
        self.last_ops = operations
        self.last_rule_evaluations = evaluations
        self.last_active_cells = steps
        self.last_rounds = steps
        self.last_irregular_bytes = steps * (0 if self.dense else 32)
        return node, pulse, states[node]


class ExactFiniteState(LocalStateBase):
    metadata = CandidateMetadata("exact_finite_state_propagation", "finite_state", "Exact learned local transition table.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        cases = tuple(facts)
        self.table = dict(cases)
        self.fit_ops = len(cases) * 10

    def _transition(self, raw: Feature) -> tuple[Target, int]:
        return self.table[raw], 10

    def update(self, source, target: Target) -> None:
        self.table[tuple(source)] = tuple(target)
        self.update_ops = 10

    def state_bytes(self) -> int:
        return 256 + 24 * len(self.table)


class IndicatorNCA(LocalStateBase):
    metadata = CandidateMetadata("learned_sparse_event_nca", "neural_cellular", "Sparse one-hidden-layer local indicator rule.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        cases = dict(facts)
        self.prototypes, self.targets = tuple(cases), tuple(cases.values())
        self.fit_ops = 20 * len(cases)

    def _transition(self, raw: Feature) -> tuple[Target, int]:
        answer = None
        for prototype, target in zip(self.prototypes, self.targets):
            if sum(left != right for left, right in zip(prototype, raw)) == 0:
                answer = target
        if answer is None:
            raise KeyError("unseen local state")
        return answer, len(self.prototypes) * 18

    def update(self, source, target: Target) -> None:
        table = dict(zip(self.prototypes, self.targets))
        table[tuple(source)] = tuple(target)
        self.prototypes, self.targets = tuple(table), tuple(table.values())
        self.update_ops = 20 * len(table)

    def state_bytes(self) -> int:
        return 256 + 80 * len(self.prototypes)


class DenseNCA(IndicatorNCA):
    metadata = CandidateMetadata("learned_dense_nca", "neural_cellular", "Dense synchronous local neural sweep.")
    dense = True


class StatelessGraph(LocalStateBase):
    metadata = CandidateMetadata("stateless_graph_bfs", "graph_control", "State-ablated learned graph propagation.")

    @staticmethod
    def _key(raw: Feature) -> Feature:
        return (*raw[:3], *raw[-2:])

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        votes: dict[Feature, Counter[Target]] = defaultdict(Counter)
        cases = tuple(facts)
        for raw, target in cases:
            votes[self._key(raw)][tuple(target)] += 1
        self.table = {key: counts.most_common(1)[0][0] for key, counts in votes.items()}
        self.fit_ops = 7 * len(cases)

    def _transition(self, raw: Feature) -> tuple[Target, int]:
        return self.table[self._key(raw)], 7

    def update(self, source, target: Target) -> None:
        self.table[self._key(tuple(source))] = tuple(target)
        self.update_ops = 7

    def state_bytes(self) -> int:
        return 256 + 20 * len(self.table)


class OracleLocalRule(LocalStateBase):
    metadata = CandidateMetadata("oracle_local_state_rule", "oracle_control", "Privileged local transition law.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.kind_by_descriptor = dict(tuple(facts)[0].kind_by_descriptor)
        self.fit_ops = 0

    def _transition(self, raw: Feature) -> tuple[Target, int]:
        descriptor = sum(bit << index for index, bit in enumerate(raw[:3]))
        state = sum(bit << index for index, bit in enumerate(raw[3:6]))
        pulse = sum(bit << index for index, bit in enumerate(raw[6:]))
        return local_rule(self.kind_by_descriptor[descriptor], state, pulse), 12

    def update(self, source, target: Target) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 192


class RandomLocalState(CandidateBase):
    metadata = CandidateMetadata("random_local_state", "random_control", "Seeded random output control.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: Any, steps: int) -> tuple[int, int, int]:
        task = source
        rng = random.Random(self.seed ^ task.signature ^ steps)
        self.last_ops, self.last_rule_evaluations = 6 * len(task.states) + 3, 0
        self.last_active_cells = self.last_rounds = self.last_irregular_bytes = 0
        return rng.randrange(len(task.states)), rng.randrange(4), rng.randrange(8)

    def update(self, source, target: Target) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 128
