from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .base import CandidateBase, CandidateMetadata
from nextai_autoresearch.cross_family_transfer_v2_contract import (
    PublicQuery, PublicTraining, PublicUpdate,
)


FEATURES = 64
RANK = 12


def _mix(value: int) -> int:
    value = (value ^ (value >> 16)) * 0x45D9F3B
    value = (value ^ (value >> 16)) * 0x45D9F3B
    return value ^ (value >> 16)


def _features(tokens: tuple[int, ...], known: dict[int, int] | None = None,
              known_atoms: tuple[int, ...] = ()):
    mapping = {} if known is None else known
    new: dict[int, int] = {}
    atoms = list(known_atoms)
    vector = np.zeros(FEATURES, dtype=float)
    previous = 0
    integer_value = False
    for position, token in enumerate(tokens):
        if integer_value:
            if token in mapping:
                identity = mapping[token]
            elif token in new:
                identity = new[token]
            else:
                identity = len(mapping) + len(new)
                new[token] = identity
                atoms.append(token)
            symbol = 31 + identity
        elif token < 0:
            symbol = -token
        else:
            symbol = 17 + abs(token) % 257
        bucket = _mix(symbol + 131 * (position % 17)) % (FEATURES - 4) + 4
        pair = _mix(previous * 65537 + symbol) % (FEATURES - 4) + 4
        vector[bucket] += 1.0
        vector[pair] += 0.5
        if integer_value and symbol < len(mapping) + 35:
            vector[2] += 1.0
        previous = symbol
        integer_value = token == -5
    vector[0] = math.log1p(len(tokens))
    vector[1] = math.log1p(len(mapping) + len(new))
    vector[3] = 1.0
    norm = float(np.linalg.norm(vector))
    if norm:
        vector /= norm
    if known is None:
        mapping = new
    elif new:
        mapping = {**mapping, **new}
    return vector, mapping, tuple(atoms), len(tokens) * 3 + len(new)


def _row(support: np.ndarray, query: np.ndarray) -> np.ndarray:
    return np.concatenate((support, query, support * query, np.abs(support - query)))


Template = tuple[tuple[str, float | int], ...]


def _template(target: tuple[float, ...], mapping: dict[int, int]) -> Template:
    output = []
    for value in target:
        rounded = round(value)
        if abs(value - rounded) < 1e-9 and rounded in mapping:
            output.append(("pointer", mapping[rounded]))
        else:
            output.append(("scalar", float(value)))
    return tuple(output)


def _decode(template: Template, atoms: tuple[int, ...]) -> tuple[float, ...]:
    output = []
    for kind, value in template:
        index = int(value)
        output.append(float(atoms[index]) if kind == "pointer" and index < len(atoms)
                      else float(value))
    return tuple(output) or (0.0,)


@dataclass
class _Model:
    center: np.ndarray
    basis: np.ndarray
    examples: np.ndarray
    templates: tuple[Template, ...]


class MultiverseLocalLearner(CandidateBase):
    metadata = CandidateMetadata(
        "multiverse-local-learner", "lossless_cross_family_local_representation",
        "One pooled local-relation representation over anonymous lossless worlds.",
    )

    def __init__(self, seed: int = 0, mode: str = "shared") -> None:
        super().__init__(seed)
        self.mode = mode
        self.supports: dict[int, np.ndarray] = {}
        self.maps: dict[int, dict[int, int]] = {}
        self.atoms: dict[int, tuple[int, ...]] = {}
        self.models: dict[int, _Model] = {}
        self.memo: dict[tuple[int, tuple[int, ...]], tuple[float, ...]] = {}
        self.meta_fit_ops = self.last_bytes_touched = 0.0

    def _fit_model(self, examples: list[tuple[np.ndarray, Template]], key: int) -> None:
        x = np.stack([row for row, _ in examples])
        center = x.mean(axis=0)
        centered = x - center
        if self.mode in {"joint", "autoregressive"}:
            basis = np.eye(x.shape[1])
        elif self.mode == "contextual":
            binary = (centered > 0).astype(float)
            covariance = (np.abs(np.cov(binary, rowvar=False))
                          if len(binary) > 1 else np.eye(x.shape[1]))
            selected = [int(np.argmax(np.diag(covariance)))]
            while len(selected) < min(RANK, x.shape[1]):
                remaining = [index for index in range(x.shape[1]) if index not in selected]
                selected.append(max(remaining, key=lambda index: float(
                    covariance[index, selected].max()
                )))
            basis = np.eye(x.shape[1])[:, selected]
            self.meta_fit_ops += float(binary.shape[0] * binary.shape[1] ** 2)
        else:
            _, _, right = np.linalg.svd(centered, full_matrices=False)
            basis = right[:min(RANK, len(right))].T
        encoded = centered @ basis
        self.models[key] = _Model(
            center, basis, encoded, tuple(template for _, template in examples)
        )
        self.meta_fit_ops += float(x.size * max(1, basis.shape[1]))

    def fit(self, facts: PublicTraining, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        if not isinstance(facts, PublicTraining):
            raise TypeError("implementable learner accepts only PublicTraining")
        self.supports, self.maps, self.atoms, self.models, self.memo = {}, {}, {}, {}, {}
        self.meta_fit_ops = 0.0
        pooled: list[tuple[np.ndarray, Template]] = []
        world_examples: list[list[tuple[np.ndarray, Template]]] = []
        training_supports: list[np.ndarray] = []
        operations = 0
        for world in facts.training_worlds:
            support, mapping, atoms, used = _features(world.support)
            operations += used
            local = []
            for example in world.examples:
                query, new, _, query_ops = _features(
                    example.query, mapping, atoms
                )
                full_map = dict(mapping)
                full_map.update(new)
                pair = (_row(support, query), _template(example.target, full_map))
                local.append(pair)
                pooled.append(pair)
                operations += query_ops + len(example.target)
            training_supports.append(support)
            world_examples.append(local)
        for world in facts.test_worlds:
            support, mapping, atoms, used = _features(world.support)
            self.supports[world.slot] = support
            self.maps[world.slot] = mapping
            self.atoms[world.slot] = atoms
            operations += used

        if self.mode == "independent":
            for slot, support in self.supports.items():
                nearest = sorted(
                    range(len(training_supports)),
                    key=lambda index: float(support @ training_supports[index]),
                    reverse=True,
                )[:3]
                self._fit_model(
                    [item for index in nearest for item in world_examples[index]], slot
                )
        else:
            self._fit_model(pooled, 0)
        self.fit_ops = float(operations) + self.meta_fit_ops

    def query(self, source: PublicQuery, steps: int) -> tuple[float, ...]:
        del steps
        key = (source.slot, source.tokens)
        if key in self.memo:
            self.last_ops = self.last_bytes_touched = len(self.memo[key])
            return self.memo[key]
        query, new, new_atoms, operations = _features(
            source.tokens, self.maps[source.slot], self.atoms[source.slot]
        )
        atoms = self.atoms[source.slot] + new_atoms[len(self.atoms[source.slot]):]
        row = _row(self.supports[source.slot], query)
        model = self.models[source.slot if self.mode == "independent" else 0]
        encoded = (row - model.center) @ model.basis
        if self.mode == "joint":
            distances = np.sum(np.abs(model.examples - encoded), axis=1)
        elif self.mode == "autoregressive":
            distances = -model.examples @ encoded
        else:
            distances = np.sum((model.examples - encoded) ** 2, axis=1)
        index = int(np.argmin(distances))
        answer = _decode(model.templates[index], atoms)
        self.last_ops = float(
            operations + row.size * model.basis.shape[1] + model.examples.size
        )
        self.last_bytes_touched = float(
            8 * (row.size + model.basis.size + model.examples.size)
        )
        return answer

    def update(self, source: PublicUpdate, target: object) -> None:
        del target
        self.memo[source.query.slot, source.query.tokens] = tuple(source.target)
        self.update_ops += float(len(source.query.tokens) + len(source.target))

    def state_bytes(self) -> int:
        arrays = [*self.supports.values()]
        for model in self.models.values():
            arrays.extend((model.center, model.basis, model.examples))
        maps = sum(len(mapping) for mapping in self.maps.values()) * 16
        templates = sum(sum(len(template) for template in model.templates)
                        for model in self.models.values()) * 16
        return int(sum(array.nbytes for array in arrays) + maps + templates
                   + len(self.memo) * 96)


class Candidate(MultiverseLocalLearner):
    pass
