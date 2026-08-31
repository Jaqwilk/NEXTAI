from __future__ import annotations

import math

import numpy as np

from .base import CandidateBase, CandidateMetadata
from nextai_autoresearch.cross_family_contract import OUTPUT_WIDTH, PAD, PublicQuery, PublicTraining, PublicUpdate


FEATURES = 48
RANK = 12


def _feature(tokens: tuple[int, ...]) -> tuple[np.ndarray, int]:
    vector = np.zeros(FEATURES, dtype=float)
    used = 0
    for position, token in enumerate(tokens):
        if token == PAD:
            continue
        used += 1
        bucket = (token * 1_000_003 + position * 97) % (FEATURES - 8) + 8
        vector[bucket] += 1.0 if ((token ^ position) & 1) else -1.0
        if -8 <= token < 0:
            vector[-token - 1] += 1.0
    vector[0] += used
    vector[1] += sum(abs(value) for value in tokens[: min(len(tokens), 64)] if value != PAD)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector, len(tokens) + used


def _row(support: np.ndarray, query: np.ndarray) -> np.ndarray:
    return np.concatenate((support, query, support * query))


def _target(values: tuple[float, ...]) -> np.ndarray:
    output = np.zeros(OUTPUT_WIDTH)
    output[: min(len(values), OUTPUT_WIDTH)] = values[:OUTPUT_WIDTH]
    return output


class CrossFamilyLearner(CandidateBase):
    metadata = CandidateMetadata(
        "cross-family-learner", "cross_family_shared_representation",
        "One family-neutral learned projection and local structured-output head.",
    )

    def __init__(self, seed: int = 0, mode: str = "shared") -> None:
        super().__init__(seed)
        self.mode = mode
        self.supports: dict[int, np.ndarray] = {}
        self.weights: dict[int, np.ndarray] = {}
        self.centers: dict[int, np.ndarray] = {}
        self.bases: dict[int, np.ndarray] = {}
        self.examples: list[tuple[np.ndarray, np.ndarray]] = []
        self.memo: dict[tuple[int, int], tuple[float, ...]] = {}
        self.last_bytes_touched = self.meta_fit_ops = 0.0

    def _fit_model(self, examples: list[tuple[np.ndarray, np.ndarray]], key: int) -> None:
        x = np.stack([row for row, _ in examples])
        y = np.stack([target for _, target in examples])
        center = x.mean(axis=0)
        centered = x - center
        if self.mode == "frozen":
            rng = np.random.default_rng(self.seed ^ key)
            basis = rng.normal(0, 1 / math.sqrt(x.shape[1]), (x.shape[1], RANK))
        elif self.mode in {"joint", "autoregressive"}:
            basis = np.eye(x.shape[1], min(RANK, x.shape[1]))
        else:
            _, _, right = np.linalg.svd(centered, full_matrices=False)
            basis = right[: min(RANK, len(right))].T
        encoded = centered @ basis
        design = np.column_stack((np.ones(len(encoded)), encoded))
        ridge = 1e-3 * np.eye(design.shape[1])
        weights = np.linalg.solve(design.T @ design + ridge, design.T @ y)
        self.centers[key], self.bases[key], self.weights[key] = center, basis, weights
        self.meta_fit_ops += float(x.size * max(1, basis.shape[1]) + design.size * OUTPUT_WIDTH)

    def fit(self, facts: PublicTraining, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        if not isinstance(facts, PublicTraining):
            raise TypeError("shared learner accepts only PublicTraining")
        self.supports, self.examples, self.memo = {}, [], {}
        self.weights, self.centers, self.bases = {}, {}, {}
        self.meta_fit_ops = 0.0
        meta_by_world: list[list[tuple[np.ndarray, np.ndarray]]] = []
        meta_supports = []
        operations = 0
        for world in facts.meta_worlds:
            support, used = _feature(world.support)
            operations += used
            local = []
            for example in world.examples:
                query, used = _feature(example.query)
                operations += used
                pair = (_row(support, query), _target(example.target))
                local.append(pair)
                self.examples.append(pair)
            meta_supports.append(support)
            meta_by_world.append(local)
        for world in facts.test_worlds:
            self.supports[world.slot], used = _feature(world.support)
            operations += used

        if self.mode == "independent":
            for slot, support in self.supports.items():
                nearest = max(range(len(meta_supports)), key=lambda index: float(support @ meta_supports[index]))
                self._fit_model(meta_by_world[nearest], slot)
        else:
            self._fit_model(self.examples, 0)
        self.fit_ops = operations + self.meta_fit_ops

    def query(self, source: PublicQuery, steps: int) -> tuple[float, ...]:
        del steps
        key = (source.slot, source.signature)
        if key in self.memo:
            self.last_ops = self.last_bytes_touched = OUTPUT_WIDTH
            return self.memo[key]
        query, operations = _feature(source.tokens)
        row = _row(self.supports[source.slot], query)
        if self.mode == "joint":
            distances = [(float(np.sum(np.abs(row - item))), target) for item, target in self.examples]
            answer = min(distances, key=lambda item: item[0])[1]
            operations += len(self.examples) * len(row)
        elif self.mode == "autoregressive":
            similarities = [(float(row @ item), target) for item, target in self.examples]
            nearest = sorted(similarities, key=lambda item: item[0], reverse=True)[:3]
            answer = sum((target for _, target in nearest), np.zeros(OUTPUT_WIDTH)) / len(nearest)
            operations += len(self.examples) * len(row) + OUTPUT_WIDTH * len(nearest)
        else:
            model = source.slot if self.mode == "independent" else 0
            encoded = (row - self.centers[model]) @ self.bases[model]
            answer = np.concatenate(([1.0], encoded)) @ self.weights[model]
            operations += len(row) * self.bases[model].shape[1] + self.weights[model].size
        self.last_ops = float(operations)
        self.last_bytes_touched = float(8 * (len(row) + OUTPUT_WIDTH))
        return tuple(map(float, answer))

    def update(self, source: PublicUpdate, target: object) -> None:
        del target
        self.memo[source.query.slot, source.query.signature] = tuple(source.target)
        self.update_ops += float(OUTPUT_WIDTH + len(source.query.tokens))

    def state_bytes(self) -> int:
        arrays = [*self.supports.values(), *self.weights.values(), *self.centers.values(), *self.bases.values()]
        return int(sum(value.nbytes for value in arrays) + len(self.memo) * 96)


class Candidate(CrossFamilyLearner):
    pass
