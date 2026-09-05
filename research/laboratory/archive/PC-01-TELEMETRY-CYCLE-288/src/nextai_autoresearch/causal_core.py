from __future__ import annotations

import random
from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata


Episode = tuple[int, tuple[tuple[int, int], ...], tuple[int, ...]]


def infer_chain(episodes: tuple[Episode, ...], size: int):
    prepared = [({node for node, _ in interventions}, values) for _, interventions, values in episodes]
    parents = [-1] * size
    biases = [0] * size
    operations = sum(len(interventions) for _, interventions, _ in episodes)
    for node in range(size):
        matches: list[tuple[int, int]] = []
        for parent in range(size):
            if parent == node:
                continue
            for bias in (0, 1):
                valid = True
                for intervened, values in prepared:
                    operations += 1
                    if node in intervened:
                        continue
                    operations += 2
                    if values[node] != values[parent] ^ bias:
                        valid = False
                        break
                if valid:
                    matches.append((parent, bias))
        if len(matches) == 1:
            parents[node], biases[node] = matches[0]
        elif matches:
            raise RuntimeError(f"ambiguous parent for node {node}")

    roots = [node for node, parent in enumerate(parents) if parent == -1]
    if len(roots) != 1:
        raise RuntimeError("expected one identifiable root")
    children = {parent: node for node, parent in enumerate(parents) if parent != -1}
    order = [roots[0]]
    while order[-1] in children:
        order.append(children[order[-1]])
    if len(order) != size:
        raise RuntimeError("learned model is not a complete chain")
    return tuple(parents), tuple(biases), tuple(order), operations


class CausalModel(CandidateBase):
    metadata = CandidateMetadata("causal_model", "causal", "Factorized binary causal model")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.parents: tuple[int, ...] = ()
        self.biases: tuple[int, ...] = ()
        self.order: tuple[int, ...] = ()
        self.last_visited_nodes = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        episodes = tuple(facts)
        self.parents, self.biases, self.order, self.fit_ops = infer_chain(
            episodes, universe_size
        )

    def update(self, source: Any, target: int) -> None:
        _, interventions, values = source
        intervened = {node for node, _ in interventions}
        self.update_ops = len(interventions)
        for node in self.order:
            parent = self.parents[node]
            if parent != -1 and node not in intervened:
                self.update_ops += 3
                if values[node] != values[parent] ^ self.biases[node]:
                    raise ValueError("episode contradicts learned mechanism")

    def state_bytes(self) -> int:
        return 128 + 24 * len(self.parents)

    def _local_query(self, task: Any) -> int:
        interventions = dict(task.interventions)
        operations = 2 * len(interventions)
        chain, node = [], task.target
        while node != -1:
            chain.append(node)
            operations += 2
            node = self.parents[node]
        values: dict[int, int] = {}
        for node in reversed(chain):
            operations += 2
            if node in interventions:
                values[node] = interventions[node]
            elif self.parents[node] == -1:
                values[node] = task.root_value
            else:
                operations += 2
                values[node] = values[self.parents[node]] ^ self.biases[node]
        self.last_visited_nodes = len(chain)
        self.last_ops = operations
        return values[task.target]


class LearnedLocalCausal(CausalModel):
    def query(self, source: Any, steps: int) -> int:
        return self._local_query(source)


class LearnedDenseCausal(CausalModel):
    def query(self, source: Any, steps: int) -> int:
        task = source
        interventions = dict(task.interventions)
        values: dict[int, int] = {}
        operations = 2 * len(interventions)
        for node in self.order:
            operations += 2
            if node in interventions:
                values[node] = interventions[node]
            elif self.parents[node] == -1:
                values[node] = task.root_value
            else:
                operations += 2
                values[node] = values[self.parents[node]] ^ self.biases[node]
        self.last_visited_nodes = len(self.order)
        self.last_ops = operations
        return values[task.target]


class OracleLocalCausal(CausalModel):
    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.parents, self.biases, self.order = tuple(facts)[0]
        self.fit_ops = 0

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def query(self, source: Any, steps: int) -> int:
        return self._local_query(source)


class ObservationalConditioning(CandidateBase):
    metadata = CandidateMetadata("observational_conditioning", "correlation", "Condition observed states")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.observed: dict[int, tuple[int, ...]] = {}
        self.last_visited_nodes = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0
        for root_value, interventions, values in facts:
            if not interventions:
                self.observed[root_value] = values
                self.fit_ops += len(values)

    def query(self, source: Any, steps: int) -> int:
        matches, operations = [], 0
        for values in self.observed.values():
            valid = True
            for node, value in source.interventions:
                operations += 2
                if values[node] != value:
                    valid = False
                    break
            if valid:
                matches.append(values)
        self.last_visited_nodes = len(self.observed)
        self.last_ops = operations + 1
        values = matches[0] if len(matches) == 1 else self.observed[source.root_value]
        return values[source.target]

    def update(self, source: Any, target: int) -> None:
        root_value, interventions, values = source
        self.update_ops = 1
        if not interventions:
            self.observed[root_value] = values

    def state_bytes(self) -> int:
        return 64 + 8 * sum(len(values) for values in self.observed.values())


class InterventionMemorizer(CandidateBase):
    metadata = CandidateMetadata("intervention_memorizer", "memory", "Exact intervention episode lookup")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.memory: dict[tuple[int, tuple[tuple[int, int], ...]], tuple[int, ...]] = {}
        self.last_visited_nodes = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0
        for root_value, interventions, values in facts:
            self.memory[(root_value, interventions)] = values
            self.fit_ops += len(values) + len(interventions)

    def query(self, source: Any, steps: int) -> int:
        key = (source.root_value, source.interventions)
        values = self.memory.get(key) or self.memory[(source.root_value, ())]
        self.last_ops = 2
        self.last_visited_nodes = 1
        return values[source.target]

    def update(self, source: Any, target: int) -> None:
        root_value, interventions, values = source
        self.memory[(root_value, interventions)] = values
        self.update_ops = len(values) + len(interventions)

    def state_bytes(self) -> int:
        return 64 + sum(16 + 16 * len(key[1]) + 8 * len(values) for key, values in self.memory.items())


class RandomCausalGuess(CandidateBase):
    metadata = CandidateMetadata("random_causal_guess", "random", "Random binary control")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.rng = random.Random(seed)
        self.last_visited_nodes = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: Any, steps: int) -> int:
        self.last_ops = 1
        self.last_visited_nodes = 0
        return self.rng.randrange(2)

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64
