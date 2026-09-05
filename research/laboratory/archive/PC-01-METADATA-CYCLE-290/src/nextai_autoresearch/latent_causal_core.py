from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata


Observation = tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class Episode:
    pair_id: int
    intervention_code: int | None
    forced_value: int | None
    observations: Observation


@dataclass(frozen=True)
class LatentQuery:
    context: Observation
    interventions: tuple[tuple[int, int], ...]
    target_code: int


def effect_sets(episodes: tuple[Episode, ...]):
    pairs: dict[tuple[int, int], dict[int, dict[int, int]]] = {}
    operations = 0
    for episode in episodes:
        if episode.intervention_code is None:
            continue
        key = episode.intervention_code, episode.pair_id
        pairs.setdefault(key, {})[int(episode.forced_value)] = dict(episode.observations)
        operations += 2 * len(episode.observations)
    effects: dict[int, set[int]] = {}
    for (token, _), values in pairs.items():
        if set(values) != {0, 1}:
            continue
        common = values[0].keys() & values[1].keys()
        effects.setdefault(token, set()).update(code for code in common if values[0][code] != values[1][code])
        operations += 2 * len(common)
    return effects, operations


def infer_targets(effects: dict[int, set[int]]):
    targets, operations = {}, 0
    for token, effect in effects.items():
        explained: set[int] = set()
        for other in effects.values():
            operations += len(effect) + len(other)
            if other < effect:
                explained.update(other)
        remaining = effect - explained
        if len(remaining) == 1:
            targets[token] = next(iter(remaining))
    return targets, operations


def infer_parents(effects: dict[int, set[int]], targets: dict[int, int]):
    parents: dict[int, tuple[int, ...]] = {}
    operations = 0
    for token, target in targets.items():
        supersets = []
        for other_token, other in effects.items():
            operations += len(effects[token]) + len(other)
            if effects[token] < other and other_token in targets:
                supersets.append((len(other), targets[other_token]))
        if not supersets:
            parents[target] = ()
            continue
        smallest = min(size for size, _ in supersets)
        parents[target] = tuple(sorted(parent for size, parent in supersets if size == smallest))
    return parents, operations


def infer_flips(episodes: tuple[Episode, ...], targets: dict[int, int]):
    votes: dict[int, list[int]] = {token: [] for token in targets}
    operations = 0
    for episode in episodes:
        token = episode.intervention_code
        if token not in targets:
            continue
        observed = dict(episode.observations)
        operations += 2 * len(observed)
        sensor = targets[token]
        if sensor in observed:
            votes[token].append(observed[sensor] ^ int(episode.forced_value))
    flips = {
        token: int(sum(values) * 2 >= len(values))
        for token, values in votes.items()
        if values
    }
    return flips, operations


def infer_biases(episodes: tuple[Episode, ...], parents: dict[int, tuple[int, ...]]):
    baselines = [dict(episode.observations) for episode in episodes if episode.intervention_code is None]
    biases, operations = {}, 0
    for child, sources in parents.items():
        if not sources:
            continue
        votes = []
        for observed in baselines:
            operations += len(sources) + 1
            if child in observed and all(parent in observed for parent in sources):
                value = observed[child]
                for parent in sources:
                    value ^= observed[parent]
                votes.append(value)
        if votes:
            biases[child] = int(sum(votes) * 2 >= len(votes))
    return biases, operations


class FactorizedLatent(CandidateBase):
    metadata = CandidateMetadata("latent_factorized_causal", "causal", "Factorization from opaque partial observations")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.parents: dict[int, tuple[int, ...]] = {}
        self.biases: dict[int, int] = {}
        self.token_targets: dict[int, int] = {}
        self.token_flips: dict[int, int] = {}
        self.last_visited_nodes = 0
        self.last_perception_ops = 0
        self.last_local_ops = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        episodes = tuple(facts)
        effects, first = effect_sets(episodes)
        self.token_targets, second = infer_targets(effects)
        self.parents, third = infer_parents(effects, self.token_targets)
        self.token_flips, fourth = infer_flips(episodes, self.token_targets)
        self.biases, fifth = infer_biases(episodes, self.parents)
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
                else:
                    values = [solve(parent) for parent in parents]
                    operations += len(parents) + 1
                    memo[node] = None if any(value is None for value in values) else self.biases.get(node, 0)
                    if memo[node] is not None:
                        for value in values:
                            memo[node] ^= int(value)
            return memo[node]

        answer = solve(source.target_code)
        self.last_visited_nodes = len(memo)
        self.last_local_ops = operations - self.last_perception_ops
        self.last_ops = operations
        return answer

    def update(self, source: Episode, target: int) -> None:
        self.update_ops = 2 * len(source.observations) + 1

    def state_bytes(self) -> int:
        edges = sum(len(value) for value in self.parents.values())
        return 128 + 24 * (len(self.parents) + len(self.biases)) + 16 * edges + 24 * len(self.token_targets)


class OracleRepresentation(FactorizedLatent):
    metadata = CandidateMetadata("oracle_representation_causal", "oracle_representation", "Known sensor and intervention identities; learned dynamics")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        representation, episodes = tuple(facts)
        sensors, tokens, polarities = representation
        self.token_targets = {tokens[index]: sensors[index] for index in range(len(sensors))}
        self.token_flips = {tokens[index]: polarities[index] for index in range(len(sensors))}
        effects, first = effect_sets(tuple(episodes))
        self.parents, second = infer_parents(effects, self.token_targets)
        self.biases, third = infer_biases(tuple(episodes), self.parents)
        self.fit_ops = first + second + third


class OracleLatent(FactorizedLatent):
    metadata = CandidateMetadata("oracle_latent_causal", "oracle", "True latent model with charged raw observation parsing")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        parents, biases, targets, flips = tuple(facts)[0]
        self.parents = dict(parents)
        self.biases = dict(biases)
        self.token_targets = dict(targets)
        self.token_flips = dict(flips)
        self.fit_ops = 0

    def update(self, source: Episode, target: int) -> None:
        self.update_ops = 1


class RawEpisodePredictor(CandidateBase):
    metadata = CandidateMetadata("raw_episode_predictor", "black_box", "Nearest single-intervention raw episode")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.episodes: tuple[Episode, ...] = ()
        self.last_visited_nodes = 0
        self.last_perception_ops = 0
        self.last_local_ops = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.episodes = tuple(facts)
        self.fit_ops = sum(2 * len(episode.observations) + 2 for episode in self.episodes)

    def query(self, source: LatentQuery, steps: int) -> int:
        context, interventions = dict(source.context), dict(source.interventions)
        self.last_perception_ops = 2 * len(source.context)
        operations, best_score, answer = self.last_perception_ops, 10**9, context.get(source.target_code, 0)
        visited = 0
        for episode in self.episodes:
            observed = dict(episode.observations)
            operations += 2 * len(episode.observations) + len(context) + 3
            if source.target_code not in observed or episode.intervention_code is None:
                continue
            visited += 1
            matches = episode.intervention_code in interventions and interventions[episode.intervention_code] == episode.forced_value
            mismatch = sum(observed[code] != value for code, value in context.items() if code in observed)
            score = mismatch + (0 if matches else len(context) + 1)
            if score < best_score:
                best_score, answer = score, observed[source.target_code]
        self.last_visited_nodes = visited
        self.last_local_ops = operations - self.last_perception_ops
        self.last_ops = operations
        return answer

    def update(self, source: Episode, target: int) -> None:
        self.episodes += (source,)
        self.update_ops = 2 * len(source.observations) + 2

    def state_bytes(self) -> int:
        return 64 + sum(48 + 24 * len(episode.observations) for episode in self.episodes)


class RandomLatent(CandidateBase):
    metadata = CandidateMetadata("random_latent_guess", "random", "Deterministic binary control")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_visited_nodes = 0
        self.last_perception_ops = 0
        self.last_local_ops = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: LatentQuery, steps: int) -> int:
        self.last_ops = 1
        return (self.seed + source.target_code + sum(token + value for token, value in source.interventions)) & 1

    def update(self, source: Episode, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64
