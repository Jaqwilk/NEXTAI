from __future__ import annotations

from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata


COPY, NOT, XOR, XNOR, AND, OR = range(6)
MIN_MARGIN = 0.05


def apply_gate(gate: int, inputs: tuple[int, ...]) -> int:
    if gate == COPY:
        return inputs[0]
    if gate == NOT:
        return 1 - inputs[0]
    if gate == XOR:
        return inputs[0] ^ inputs[1]
    if gate == XNOR:
        return 1 - (inputs[0] ^ inputs[1])
    if gate == AND:
        return inputs[0] & inputs[1]
    return inputs[0] | inputs[1]


def candidate_specs(pool: tuple[int, ...]):
    specs = [(gate, (parent,)) for parent in pool for gate in (COPY, NOT)]
    specs.extend(
        (gate, tuple(sorted((pool[left], pool[right]))))
        for left in range(len(pool))
        for right in range(left + 1, len(pool))
        for gate in (XOR, XNOR, AND, OR)
    )
    return specs


def fit_models(pools: tuple[tuple[int, ...], ...], episodes: tuple[Any, ...], ignore_labels: bool):
    models: list[Any] = [None] * len(pools)
    margins = [0.0] * len(pools)
    operations = 0
    for node, pool in enumerate(pools):
        if not pool:
            continue
        scores = []
        for spec in candidate_specs(pool):
            gate, parents = spec
            errors = samples = 0
            for _, interventions, values in episodes:
                operations += 1
                if not ignore_labels and any(target == node for target, _ in interventions):
                    continue
                prediction = apply_gate(gate, tuple(values[parent] for parent in parents))
                errors += int(prediction != values[node])
                samples += 1
                operations += len(parents) + 2
            scores.append((errors / max(1, samples), spec))
        scores.sort(key=lambda item: (item[0], item[1]))
        margins[node] = scores[1][0] - scores[0][0]
        if margins[node] >= MIN_MARGIN:
            models[node] = scores[0][1]
    return tuple(models), tuple(margins), operations


class FactorizedModel(CandidateBase):
    metadata = CandidateMetadata("factorized_causal", "causal", "Robust local mechanism factorization")
    ignore_intervention_labels = False

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.models: tuple[Any, ...] = ()
        self.margins: tuple[float, ...] = ()
        self.root_count = 0
        self.last_visited_nodes = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        pools, episodes = tuple(facts)
        self.root_count = next(index for index, pool in enumerate(pools) if pool)
        self.models, self.margins, self.fit_ops = fit_models(
            pools, episodes, self.ignore_intervention_labels
        )

    def _relevant_nodes(self, task: Any) -> set[int] | None:
        forced = dict(task.interventions)
        relevant, stack = set(), [task.target]
        while stack:
            node = stack.pop()
            if node in relevant:
                continue
            relevant.add(node)
            if node < self.root_count or node in forced:
                continue
            spec = self.models[node]
            if spec is None:
                return None
            stack.extend(spec[1])
        return relevant

    def _evaluate(self, task: Any, nodes: Iterable[int]) -> int | None:
        forced = dict(task.interventions)
        values: dict[int, int] = {}
        operations = 2 * len(forced)
        ordered = sorted(nodes)
        for node in ordered:
            operations += 2
            if node in forced:
                values[node] = forced[node]
            elif node < self.root_count:
                values[node] = task.root_values[node]
            else:
                spec = self.models[node]
                if spec is None:
                    values[node] = 0
                    continue
                gate, parents = spec
                operations += len(parents) + 1
                values[node] = apply_gate(gate, tuple(values[parent] for parent in parents))
        self.last_visited_nodes = len(ordered)
        self.last_ops = operations
        return values.get(task.target)

    def update(self, source: Any, target: int) -> None:
        _, interventions, values = source
        intervened = {node for node, _ in interventions}
        self.update_ops = len(interventions)
        for node, spec in enumerate(self.models):
            if spec is None or node in intervened:
                continue
            gate, parents = spec
            self.update_ops += len(parents) + 2
            apply_gate(gate, tuple(values[parent] for parent in parents))

    def state_bytes(self) -> int:
        edges = sum(len(spec[1]) for spec in self.models if spec is not None)
        return 128 + 16 * len(self.models) + 16 * edges


class RobustLocalCausal(FactorizedModel):
    def query(self, source: Any, steps: int) -> int | None:
        relevant = self._relevant_nodes(source)
        if relevant is None:
            self.last_ops = self.last_visited_nodes = 0
            return None
        return self._evaluate(source, relevant)


class RobustDenseCausal(FactorizedModel):
    def query(self, source: Any, steps: int) -> int | None:
        return self._evaluate(source, range(len(self.models)))


class NonInvariantLocalCausal(RobustLocalCausal):
    ignore_intervention_labels = True


class OracleAdversarialCausal(RobustLocalCausal):
    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.models, self.root_count = tuple(facts)[0]
        self.margins = tuple(1.0 for _ in self.models)
        self.fit_ops = 0

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1


class AdversarialObservational(CandidateBase):
    metadata = CandidateMetadata("adversarial_observational", "correlation", "Nearest observational state")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.episodes: tuple[Any, ...] = ()
        self.last_visited_nodes = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        _, episodes = tuple(facts)
        self.episodes = tuple(item for item in episodes if not item[1])
        self.fit_ops = sum(len(item[2]) for item in self.episodes)

    def query(self, source: Any, steps: int) -> int:
        best_score, best_values, operations = 10**9, self.episodes[0][2], 0
        for roots, _, values in self.episodes:
            score = sum(left != right for left, right in zip(roots, source.root_values))
            score += 2 * sum(values[node] != value for node, value in source.interventions)
            operations += len(roots) + 2 * len(source.interventions)
            if score < best_score:
                best_score, best_values = score, values
        self.last_ops = operations
        self.last_visited_nodes = len(self.episodes)
        return best_values[source.target]

    def update(self, source: Any, target: int) -> None:
        self.episodes += (source,)
        self.update_ops = len(source[2])

    def state_bytes(self) -> int:
        return 64 + sum(16 + 8 * (len(roots) + len(values)) for roots, _, values in self.episodes)


class NearestIntervention(AdversarialObservational):
    metadata = CandidateMetadata("nearest_intervention", "memory", "Nearest interventional episode")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        _, episodes = tuple(facts)
        self.episodes = tuple(episodes)
        self.fit_ops = sum(len(item[1]) + len(item[2]) for item in self.episodes)

    def query(self, source: Any, steps: int) -> int:
        query_interventions = dict(source.interventions)
        best_score, best_values, operations = 10**9, self.episodes[0][2], 0
        for roots, interventions, values in self.episodes:
            trained = dict(interventions)
            score = sum(left != right for left, right in zip(roots, source.root_values))
            score += 3 * len(set(trained) ^ set(query_interventions))
            score += sum(trained[node] != value for node, value in query_interventions.items() if node in trained)
            operations += len(roots) + len(trained) + 4 * len(query_interventions)
            if score < best_score:
                best_score, best_values = score, values
        self.last_ops = operations
        self.last_visited_nodes = len(self.episodes)
        return best_values[source.target]
