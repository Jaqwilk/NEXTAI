from __future__ import annotations

import numpy as np

from .base import CandidateBase, CandidateMetadata
from .cross_family_learner_core import RANK, _feature, _row
from nextai_autoresearch.cross_family_contract import OUTPUT_WIDTH, PAD, PublicQuery, PublicTraining, PublicUpdate


Template = tuple[tuple[str, float | int], ...]


def _canonical(tokens: tuple[int, ...], known: dict[int, int] | None = None):
    """Rename serialized integer atoms by first occurrence, preserving syntax."""
    mapping = {} if known is None else dict(known)
    output: list[int] = []
    position = 0

    def walk() -> None:
        nonlocal position
        marker = tokens[position]
        position += 1
        output.append(marker)
        if marker in (-1, -3):
            count = tokens[position]
            position += 1
            output.append(count)
            for _ in range(count):
                walk()
        elif marker == -2:
            count = tokens[position]
            position += 1
            output.append(count)
            for _ in range(2 * count):
                walk()
        elif marker == -5:
            atom = tokens[position]
            position += 1
            if atom not in mapping:
                mapping[atom] = len(mapping)
            output.append(10_000 + mapping[atom])
        elif marker in (-4, -6):
            output.append(tokens[position])
            position += 1
        elif marker != -7:
            raise ValueError("invalid public serialization")

    try:
        walk()
    except (IndexError, ValueError):
        # Truncation is deterministic. Preserve its equality pattern without
        # attempting to infer missing syntax.
        output, mapping = [], {} if known is None else dict(known)
        for token in tokens:
            if token == PAD:
                break
            if token >= 0:
                if token not in mapping:
                    mapping[token] = len(mapping)
                output.append(10_000 + mapping[token])
            else:
                output.append(token)
    output.extend([PAD] * (len(tokens) - len(output)))
    atoms = [0] * len(mapping)
    for atom, index in mapping.items():
        atoms[index] = atom
    return tuple(output[:len(tokens)]), mapping, tuple(atoms), position + len(output)


def _template(target: tuple[float, ...], mapping: dict[int, int]) -> Template:
    result: list[tuple[str, float | int]] = []
    for value in target[:OUTPUT_WIDTH]:
        rounded = round(value)
        if abs(value - rounded) < 1e-9 and rounded in mapping:
            result.append(("pointer", mapping[rounded]))
        else:
            result.append(("scalar", float(value)))
    return tuple(result)


class PointerCrossFamilyLearner(CandidateBase):
    metadata = CandidateMetadata(
        "cross-family-pointer-learner", "cross_family_shared_representation",
        "One equality-canonicalized SVD representation and atom-pointer/scalar head.",
    )

    def __init__(self, seed: int = 0, independent: bool = False) -> None:
        super().__init__(seed)
        self.independent = independent
        self.supports: dict[int, np.ndarray] = {}
        self.support_maps: dict[int, dict[int, int]] = {}
        self.models: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray, tuple[Template, ...]]] = {}
        self.memo: dict[tuple[int, int], tuple[float, ...]] = {}
        self.meta_fit_ops = self.last_bytes_touched = 0.0

    def _fit_model(self, examples: list[tuple[np.ndarray, Template]], key: int) -> None:
        x = np.stack([row for row, _ in examples])
        center = x.mean(axis=0)
        centered = x - center
        _, _, right = np.linalg.svd(centered, full_matrices=False)
        basis = right[:min(RANK, len(right))].T
        encoded = centered @ basis
        templates = tuple(template for _, template in examples)
        self.models[key] = center, basis, encoded, templates
        self.meta_fit_ops += float(x.size * max(1, basis.shape[1]))

    def fit(self, facts: PublicTraining, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        if not isinstance(facts, PublicTraining):
            raise TypeError("pointer learner accepts only PublicTraining")
        self.supports, self.support_maps, self.models, self.memo = {}, {}, {}, {}
        self.meta_fit_ops = 0.0
        pooled: list[tuple[np.ndarray, Template]] = []
        worlds: list[list[tuple[np.ndarray, Template]]] = []
        meta_supports: list[np.ndarray] = []
        operations = 0
        for world in facts.meta_worlds:
            support_tokens, support_map, _, used = _canonical(world.support)
            support, feature_ops = _feature(support_tokens)
            operations += used + feature_ops
            local = []
            for example in world.examples:
                query_tokens, mapping, _, used = _canonical(example.query, support_map)
                query, feature_ops = _feature(query_tokens)
                pair = (_row(support, query), _template(example.target, mapping))
                operations += used + feature_ops
                local.append(pair)
                pooled.append(pair)
            meta_supports.append(support)
            worlds.append(local)
        for world in facts.test_worlds:
            tokens, mapping, _, used = _canonical(world.support)
            support, feature_ops = _feature(tokens)
            self.supports[world.slot], self.support_maps[world.slot] = support, mapping
            operations += used + feature_ops
        if self.independent:
            for slot, support in self.supports.items():
                nearest = max(range(len(meta_supports)), key=lambda index: float(support @ meta_supports[index]))
                self._fit_model(worlds[nearest], slot)
        else:
            self._fit_model(pooled, 0)
        self.fit_ops = operations + self.meta_fit_ops

    def query(self, source: PublicQuery, steps: int) -> tuple[float, ...]:
        del steps
        memo_key = (source.slot, source.signature)
        if memo_key in self.memo:
            self.last_ops = self.last_bytes_touched = OUTPUT_WIDTH
            return self.memo[memo_key]
        tokens, _, atoms, parse_ops = _canonical(source.tokens, self.support_maps[source.slot])
        query, feature_ops = _feature(tokens)
        row = _row(self.supports[source.slot], query)
        model = source.slot if self.independent else 0
        center, basis, examples, templates = self.models[model]
        encoded = (row - center) @ basis
        distances = np.sum((examples - encoded) ** 2, axis=1)
        template = templates[int(np.argmin(distances))]
        answer = []
        for kind, value in template:
            index = int(value)
            answer.append(float(atoms[index]) if kind == "pointer" and index < len(atoms) else float(value))
        self.last_ops = float(parse_ops + feature_ops + row.size * basis.shape[1] + examples.size)
        self.last_bytes_touched = float(8 * (row.size + basis.size + examples.size))
        return tuple(answer) or (0.0,)

    def update(self, source: PublicUpdate, target: object) -> None:
        del target
        self.memo[source.query.slot, source.query.signature] = tuple(source.target)
        self.update_ops += float(OUTPUT_WIDTH + len(source.query.tokens))

    def state_bytes(self) -> int:
        arrays = [*self.supports.values()]
        for center, basis, examples, _ in self.models.values():
            arrays.extend((center, basis, examples))
        maps = sum(len(mapping) for mapping in self.support_maps.values()) * 16
        templates = sum(sum(len(template) for template in model[3]) for model in self.models.values()) * 16
        return int(sum(value.nbytes for value in arrays) + maps + templates + len(self.memo) * 96)


class Candidate(PointerCrossFamilyLearner):
    pass
