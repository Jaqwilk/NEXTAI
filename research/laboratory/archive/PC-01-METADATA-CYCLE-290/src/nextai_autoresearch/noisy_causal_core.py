from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Any, Iterable

import numpy as np

from .candidates.base import CandidateBase, CandidateMetadata
from .latent_causal_core import Episode, LatentQuery, infer_flips, infer_parents, infer_targets
from .latent_causal_mixed_core import apply_table, infer_tables


EFFECT_MIN_RATE = 0.25


def aggregate_episodes(episodes: tuple[Episode, ...]):
    groups: dict[tuple[int, int | None, int | None], list[Episode]] = defaultdict(list)
    operations = 0
    for episode in episodes:
        groups[(episode.pair_id, episode.intervention_code, episode.forced_value)].append(episode)
        operations += len(episode.observations)
    aggregated = []
    for (pair_id, token, forced), items in groups.items():
        votes: dict[int, list[int]] = defaultdict(list)
        for item in items:
            for sensor, value in item.observations:
                votes[sensor].append(value)
        observations = tuple(sorted((sensor, int(sum(values) * 2 >= len(values))) for sensor, values in votes.items()))
        operations += sum(len(values) for values in votes.values())
        aggregated.append(Episode(pair_id, token, forced, observations))
    return tuple(aggregated), operations


def robust_effect_sets(episodes: tuple[Episode, ...]):
    paired: dict[tuple[int, int], dict[int, dict[int, int]]] = defaultdict(dict)
    operations = 0
    for episode in episodes:
        if episode.intervention_code is not None:
            paired[(episode.intervention_code, episode.pair_id)][int(episode.forced_value)] = dict(episode.observations)
            operations += len(episode.observations)
    changed: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    totals: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for (token, _), values in paired.items():
        if set(values) != {0, 1}:
            continue
        for sensor in values[0].keys() & values[1].keys():
            totals[token][sensor] += 1
            changed[token][sensor] += values[0][sensor] != values[1][sensor]
            operations += 2
    effects = {
        token: {sensor for sensor, count in per_sensor.items() if count / totals[token][sensor] >= EFFECT_MIN_RATE}
        for token, per_sensor in changed.items()
    }
    return effects, operations


def learn_factorization(episodes: tuple[Episode, ...]):
    clean, first = aggregate_episodes(episodes)
    effects, second = robust_effect_sets(clean)
    targets, third = infer_targets(effects)
    parents, fourth = infer_parents(effects, targets)
    flips, fifth = infer_flips(clean, targets)
    models, sixth = infer_tables(clean, parents)
    return targets, parents, flips, models, first + second + third + fourth + fifth + sixth


class NoisyFactorizedLocal(CandidateBase):
    metadata = CandidateMetadata("noisy_factorized_local", "causal", "Robust opaque factorization with local execution")
    dense_execution = False

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.token_targets: dict[int, int] = {}
        self.parents: dict[int, tuple[int, ...]] = {}
        self.token_flips: dict[int, int] = {}
        self.models: dict[int, int] = {}
        self.last_encoding_ops = self.last_representation_ops = self.last_local_ops = 0
        self.last_visited_nodes = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        episodes, _ = tuple(facts)
        learned = learn_factorization(tuple(episodes))
        self.token_targets, self.parents, self.token_flips, self.models, self.fit_ops = learned

    def query(self, source: LatentQuery, steps: int) -> int | None:
        context = dict(source.context)
        self.last_encoding_ops = 2 * len(source.context) + 2 * len(source.interventions) + 1
        self.last_representation_ops = 1
        forced: dict[int, int] = {}
        for token, value in source.interventions:
            self.last_representation_ops += 3
            if token not in self.token_targets or token not in self.token_flips:
                self.last_local_ops = self.last_visited_nodes = 0
                self.last_ops = self.last_encoding_ops + self.last_representation_ops
                return None
            forced[self.token_targets[token]] = value ^ self.token_flips[token]
        memo: dict[int, int | None] = {}
        local_ops = 0

        def solve(node: int) -> int | None:
            nonlocal local_ops
            if node in memo:
                local_ops += 1
                return memo[node]
            local_ops += 2
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
                    local_ops += len(parents) + 1
                    memo[node] = None if any(value is None for value in values) else apply_table(
                        self.models[node], tuple(int(value) for value in values)
                    )
            return memo[node]

        if self.dense_execution:
            for node in self.parents:
                solve(node)
        answer = solve(source.target_code)
        self.last_local_ops = local_ops
        self.last_visited_nodes = len(memo)
        self.last_ops = self.last_encoding_ops + self.last_representation_ops + local_ops
        return answer

    def update(self, source: Episode, target: int) -> None:
        self.update_ops = 2 * len(source.observations) + 1

    def state_bytes(self) -> int:
        edges = sum(len(value) for value in self.parents.values())
        return 128 + 24 * (len(self.parents) + len(self.models) + len(self.token_targets)) + 16 * edges


class NoisyFactorizedDense(NoisyFactorizedLocal):
    metadata = CandidateMetadata("noisy_factorized_dense", "causal_dense", "Same learned representation with dense execution")
    dense_execution = True


class OracleRepresentationNoisy(NoisyFactorizedLocal):
    metadata = CandidateMetadata("oracle_representation_noisy", "oracle_representation", "Known opaque alignment with noisy mechanism learning")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        representation, bundle = tuple(facts)
        sensors, tokens, polarities = representation
        episodes, _ = bundle
        self.token_targets = dict(zip(tokens, sensors))
        self.token_flips = dict(zip(tokens, polarities))
        clean, first = aggregate_episodes(tuple(episodes))
        effects, second = robust_effect_sets(clean)
        self.parents, third = infer_parents(effects, self.token_targets)
        self.models, fourth = infer_tables(clean, self.parents)
        self.fit_ops = first + second + third + fourth


class OracleNoisyCausal(NoisyFactorizedLocal):
    metadata = CandidateMetadata("oracle_noisy_causal", "oracle", "True causal model with charged raw encoding")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        parents, models, targets, flips = tuple(facts)[0]
        self.parents, self.models = dict(parents), dict(models)
        self.token_targets, self.token_flips = dict(targets), dict(flips)
        self.fit_ops = 0

    def update(self, source: Episode, target: int) -> None:
        self.update_ops = 1


class DenseRandomFeatureCausal(CandidateBase):
    metadata = CandidateMetadata("dense_random_feature_causal", "dense_learned", "Nonlinear dense random-feature predictor")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.context_codes: dict[int, int] = {}
        self.token_codes: dict[int, int] = {}
        self.target_codes: dict[int, int] = {}
        self.weights = self.bias = self.readout = np.empty(0)
        self.last_encoding_ops = self.last_representation_ops = self.last_local_ops = 0
        self.last_visited_nodes = 0

    def _encode(self, query: LatentQuery) -> np.ndarray:
        context_offset = len(self.context_codes)
        token_offset = 2 * context_offset
        target_offset = token_offset + 2 * len(self.token_codes)
        vector = np.zeros(target_offset + len(self.target_codes), dtype=np.float64)
        for code, value in query.context:
            if code in self.context_codes:
                index = self.context_codes[code]
                vector[index] = 1.0
                vector[context_offset + index] = 2.0 * value - 1.0
        for code, value in query.interventions:
            if code in self.token_codes:
                index = token_offset + 2 * self.token_codes[code]
                vector[index] = 1.0
                vector[index + 1] = 2.0 * value - 1.0
        if query.target_code in self.target_codes:
            vector[target_offset + self.target_codes[query.target_code]] = 1.0
        return vector

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        _, examples = tuple(facts)
        examples = tuple(examples)
        self.context_codes = {code: index for index, code in enumerate(sorted({code for query, _ in examples for code, _ in query.context}))}
        self.token_codes = {code: index for index, code in enumerate(sorted({code for query, _ in examples for code, _ in query.interventions}))}
        self.target_codes = {code: index for index, code in enumerate(sorted({query.target_code for query, _ in examples}))}
        inputs = np.stack([self._encode(query) for query, _ in examples])
        targets = np.asarray([2.0 * target - 1.0 for _, target in examples])
        width = min(128, max(32, 2 * inputs.shape[1]))
        rng = np.random.default_rng(self.seed)
        self.weights = rng.normal(0.0, 1.0 / math.sqrt(inputs.shape[1]), (inputs.shape[1], width))
        self.bias = rng.normal(0.0, 0.25, width)
        hidden = np.tanh(inputs @ self.weights + self.bias)
        ridge = hidden.T @ hidden + 0.1 * np.eye(width)
        self.readout = np.linalg.solve(ridge, hidden.T @ targets)
        samples, dimension = inputs.shape
        self.fit_ops = int(samples * (2 * dimension * width + 2 * width * width) + 2 * width**3 / 3)

    def query(self, source: LatentQuery, steps: int) -> int:
        vector = self._encode(source)
        width = int(self.readout.size)
        self.last_encoding_ops = 2 * len(source.context) + 2 * len(source.interventions) + 1
        self.last_representation_ops = 2 * vector.size * width + 2 * width
        self.last_local_ops = 0
        self.last_visited_nodes = width
        self.last_ops = self.last_encoding_ops + self.last_representation_ops
        return int(np.tanh(vector @ self.weights + self.bias) @ self.readout >= 0.0)

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        arrays = self.weights.nbytes + self.bias.nbytes + self.readout.nbytes
        return int(arrays + 48 * (len(self.context_codes) + len(self.token_codes) + len(self.target_codes)))
