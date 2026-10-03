from __future__ import annotations

import random
from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata
from .latent_causal_core import (
    Episode,
    FactorizedLatent,
    LatentQuery,
    effect_sets,
    infer_flips,
    infer_parents,
    infer_targets,
)


def apply_table(table: int, inputs: tuple[int, ...]) -> int:
    index = 0
    for value in inputs:
        index = (index << 1) | value
    return (table >> index) & 1


def infer_tables(episodes: tuple[Episode, ...], parents: dict[int, tuple[int, ...]]):
    baselines = [dict(item.observations) for item in episodes if item.intervention_code is None]
    models, operations = {}, 0
    for child, sources in parents.items():
        if not sources:
            continue
        scored = []
        for table in range(1 << (1 << len(sources))):
            errors = samples = 0
            for observed in baselines:
                operations += len(sources) + 2
                if child not in observed or not all(parent in observed for parent in sources):
                    continue
                errors += apply_table(table, tuple(observed[parent] for parent in sources)) != observed[child]
                samples += 1
            scored.append((errors, -samples, table))
        scored.sort()
        if scored[0][:2] < scored[1][:2]:
            models[child] = scored[0][2]
    return models, operations


class MixedFactorized(FactorizedLatent):
    metadata = CandidateMetadata("latent_factorized_mixed", "causal", "Mixed-gate factorization from opaque observations")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.models: dict[int, int] = {}

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        episodes = tuple(facts)
        effects, first = effect_sets(episodes)
        self.token_targets, second = infer_targets(effects)
        self.parents, third = infer_parents(effects, self.token_targets)
        self.token_flips, fourth = infer_flips(episodes, self.token_targets)
        self.models, fifth = infer_tables(episodes, self.parents)
        self.fit_ops = first + second + third + fourth + fifth

    def query(self, source: LatentQuery, steps: int) -> int | None:
        context = dict(source.context)
        self.last_perception_ops = 2 * len(source.context)
        operations = self.last_perception_ops
        forced: dict[int, int] = {}
        for token, value in source.interventions:
            operations += 3
            if token not in self.token_targets or token not in self.token_flips:
                self.last_ops = operations
                return None
            forced[self.token_targets[token]] = value ^ self.token_flips[token]
        memo: dict[int, int | None] = {}

        def solve(node: int) -> int | None:
            nonlocal operations
            if node in memo:
                operations += 1
                return memo[node]
            operations += 2
            if node in forced:
                memo[node] = forced[node]
            else:
                parents = self.parents.get(node)
                if parents is None:
                    memo[node] = None
                elif not parents:
                    memo[node] = context.get(node)
                elif node not in self.models:
                    memo[node] = None
                else:
                    values = tuple(solve(parent) for parent in parents)
                    operations += len(parents) + 1
                    memo[node] = None if any(value is None for value in values) else apply_table(
                        self.models[node], tuple(int(value) for value in values)
                    )
            return memo[node]

        answer = solve(source.target_code)
        self.last_visited_nodes = len(memo)
        self.last_local_ops = operations - self.last_perception_ops
        self.last_ops = operations
        return answer

    def state_bytes(self) -> int:
        return super().state_bytes() + 24 * len(self.models)


class OracleRepresentationMixed(MixedFactorized):
    metadata = CandidateMetadata("oracle_representation_mixed", "oracle_representation", "Known opaque identities; learned mixed dynamics")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        representation, episodes = tuple(facts)
        sensors, tokens, polarities = representation
        self.token_targets = {tokens[index]: sensors[index] for index in range(len(sensors))}
        self.token_flips = {tokens[index]: polarities[index] for index in range(len(sensors))}
        effects, first = effect_sets(tuple(episodes))
        self.parents, second = infer_parents(effects, self.token_targets)
        self.models, third = infer_tables(tuple(episodes), self.parents)
        self.fit_ops = first + second + third


class OracleMixed(MixedFactorized):
    metadata = CandidateMetadata("oracle_latent_mixed", "oracle", "True mixed causal model")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        parents, models, targets, flips = tuple(facts)[0]
        self.parents = dict(parents)
        self.models = dict(models)
        self.token_targets = dict(targets)
        self.token_flips = dict(flips)
        self.fit_ops = 0

    def update(self, source: Episode, target: int) -> None:
        self.update_ops = 1


class IndependentRandom(CandidateBase):
    metadata = CandidateMetadata("random_latent_independent", "random", "Seeded predictions independent of query fields")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.rng = random.Random(seed)
        self.last_visited_nodes = self.last_perception_ops = self.last_local_ops = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.rng = random.Random(self.seed)
        self.fit_ops = 0

    def query(self, source: LatentQuery, steps: int) -> int:
        self.last_ops = 1
        return self.rng.randrange(2)

    def update(self, source: Episode, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class MajorityGuess(IndependentRandom):
    metadata = CandidateMetadata("latent_majority_guess", "heuristic", "Constant majority control")

    def query(self, source: LatentQuery, steps: int) -> int:
        self.last_ops = 1
        return 0


class ParityShortcut(IndependentRandom):
    metadata = CandidateMetadata("latent_parity_shortcut", "heuristic", "EXP-0014 arithmetic shortcut control")

    def query(self, source: LatentQuery, steps: int) -> int:
        self.last_ops = 1 + 2 * len(source.interventions)
        return (self.seed + source.target_code + sum(token + value for token, value in source.interventions)) & 1
