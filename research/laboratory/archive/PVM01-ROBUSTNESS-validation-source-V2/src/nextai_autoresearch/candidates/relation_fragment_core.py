from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from .base import CandidateBase, CandidateMetadata
from nextai_autoresearch.cross_family_transfer_v2_contract import (
    PublicQuery, PublicTraining, PublicUpdate,
)


CAPACITY = 64
RULE = "typed_equality_join_then_component_emit_v1"
Component = tuple[str, float | int]
Edge = tuple[int, int, int, int]
Signature = frozenset[Edge]
Node = tuple[int, int | tuple["Node", ...]]


def _parse(tokens: tuple[int, ...], known: dict[int, int] | None = None,
           known_atoms: tuple[int, ...] = ()):
    mapping = {} if known is None else dict(known)
    atoms = list(known_atoms)
    cursor = 0

    def read() -> Node:
        nonlocal cursor
        marker = tokens[cursor]
        cursor += 1
        if marker in (-1, -3):
            count = tokens[cursor]
            cursor += 1
            return (-marker, tuple(read() for _ in range(count)))
        if marker == -2:
            count = tokens[cursor]
            cursor += 1
            return (2, tuple(read() for _ in range(2 * count)))
        if marker in (-4, -6):
            value = tokens[cursor]
            cursor += 1
            return (-marker, int(value))
        if marker == -5:
            value = tokens[cursor]
            cursor += 1
            if value not in mapping:
                mapping[value] = len(mapping)
                atoms.append(value)
            return (5, mapping[value])
        if marker == -7:
            return (7, 0)
        raise ValueError(f"invalid structural marker: {marker}")

    root = read()
    if cursor != len(tokens):
        raise ValueError("trailing structural tokens")
    return root, mapping, tuple(atoms), len(tokens)


def _edges(root: Node) -> Signature:
    output: set[Edge] = set()

    def walk(node: Node, parent: int, position: int) -> None:
        tag, value = node
        if isinstance(value, tuple):
            output.add((parent, position, tag, len(value)))
            for index, child in enumerate(value):
                walk(child, tag, index)
        else:
            output.add((parent, position, tag, int(value)))

    walk(root, 0, 0)
    return frozenset(output)


def _component(value: float, mapping: dict[int, int]) -> Component:
    rounded = round(value)
    if abs(value - rounded) < 1e-9 and rounded in mapping:
        return ("pointer", mapping[rounded])
    return ("scalar", float(value))


def _decode(component: Component, atoms: tuple[int, ...]) -> float:
    kind, value = component
    index = int(value)
    if kind == "pointer" and index < len(atoms):
        return float(atoms[index])
    return float(value)


def _similarity(left: Signature, right: Signature) -> float:
    union = len(left | right)
    return len(left & right) / union if union else 1.0


@dataclass(frozen=True)
class _Fragment:
    edges: Signature
    position: int
    length: int
    component: Component
    count: int

    @property
    def lexical(self) -> str:
        return repr((sorted(self.edges), self.position, self.length, self.component))


def _induce(items: list[tuple[Signature, int, int, Component]]) -> tuple[_Fragment, ...]:
    counts = Counter(items)
    fragments = [
        _Fragment(edges, position, length, component, count)
        for (edges, position, length, component), count in counts.items()
    ]
    fragments.sort(key=lambda item: (-item.count, len(item.edges), item.lexical))
    return tuple(fragments[:CAPACITY])


def _best(signature: Signature, fragments: tuple[_Fragment, ...],
          *, position: int | None = None, length: int | None = None) -> _Fragment:
    eligible = [
        item for item in fragments
        if (position is None or item.position == position)
        and (length is None or item.length == length)
    ]
    if not eligible and position is not None:
        eligible = [item for item in fragments if item.position == position]
    if not eligible:
        eligible = list(fragments)
    return max(eligible, key=lambda item: (
        _similarity(signature, item.edges), item.count, -len(item.edges),
        tuple(-ord(char) for char in item.lexical),
    ))


class RelationFragmentGraphLearner(CandidateBase):
    metadata = CandidateMetadata(
        "relation-fragment-graph", "anonymous_relation_fragment_graph_transfer",
        "Bounded anonymous structural fragments with equality-join composition.",
    )
    fragment_capacity = CAPACITY
    composition_rule = RULE

    def __init__(self, seed: int = 0, mode: str = "shared") -> None:
        super().__init__(seed)
        self.mode = mode
        self.models: dict[int, tuple[_Fragment, ...]] = {}
        self.slot_models: dict[int, int] = {}
        self.maps: dict[int, dict[int, int]] = {}
        self.atoms: dict[int, tuple[int, ...]] = {}
        self.memo: dict[tuple[int, tuple[int, ...]], tuple[float, ...]] = {}
        self.last_composition_trace: tuple[str, ...] = ()
        self.meta_fit_ops = self.last_bytes_touched = 0.0

    def fit(self, facts: PublicTraining, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        if not isinstance(facts, PublicTraining):
            raise TypeError("implementable learner accepts only PublicTraining")
        self.models, self.slot_models, self.maps, self.atoms, self.memo = {}, {}, {}, {}, {}
        pooled: list[tuple[Signature, int, int, Component]] = []
        groups: list[list[tuple[Signature, int, int, Component]]] = []
        training_supports: list[Signature] = []
        operations = 0
        for world in facts.training_worlds:
            support, mapping, atoms, used = _parse(world.support)
            support_edges = _edges(support)
            training_supports.append(support_edges)
            operations += used + len(support_edges)
            group = []
            for example in world.examples:
                query, full_map, _, used = _parse(example.query, mapping, atoms)
                signature = _edges(query)
                length = len(example.target)
                for position, value in enumerate(example.target):
                    item = (signature, position, length, _component(value, full_map))
                    group.append(item)
                    pooled.append(item)
                operations += used + len(signature) + length
            groups.append(group)

        if self.mode == "independent":
            for index, group in enumerate(groups):
                self.models[index] = _induce(group)
        else:
            self.models[0] = _induce(pooled)
        self.meta_fit_ops = float(sum(
            len(fragment.edges) for model in self.models.values() for fragment in model
        ))

        for world in facts.test_worlds:
            support, mapping, atoms, used = _parse(world.support)
            signature = _edges(support)
            self.maps[world.slot], self.atoms[world.slot] = mapping, atoms
            operations += used + len(signature)
            if self.mode == "independent":
                self.slot_models[world.slot] = max(
                    range(len(training_supports)),
                    key=lambda index: (_similarity(signature, training_supports[index]), -index),
                )
                operations += sum(
                    len(signature) + len(item) for item in training_supports
                )
        self.fit_ops = float(operations) + self.meta_fit_ops

    def _emit(self, signature: Signature, model: tuple[_Fragment, ...],
              atoms: tuple[int, ...]) -> tuple[float, ...]:
        first = _best(signature, model, position=0)
        selected = [first]
        for position in range(1, first.length):
            selected.append(_best(
                signature, model, position=position, length=first.length
            ))
        self.last_composition_trace = tuple(item.lexical for item in selected)
        return tuple(_decode(item.component, atoms) for item in selected)

    def query(self, source: PublicQuery, steps: int) -> tuple[float, ...]:
        del steps
        key = (source.slot, source.tokens)
        if key in self.memo:
            self.last_composition_trace = ("memo",)
            self.last_ops = self.last_bytes_touched = len(self.memo[key])
            return self.memo[key]
        root, _, atoms, used = _parse(
            source.tokens, self.maps[source.slot], self.atoms[source.slot]
        )
        model = self.models[self.slot_models.get(source.slot, 0)]
        children = root[1] if isinstance(root[1], tuple) else ()
        exact_children = []
        if len(children) > 1:
            for child in children:
                signature = _edges(child)
                matches = [item for item in model if item.edges == signature and item.length == 1]
                if not matches:
                    exact_children = []
                    break
                exact_children.append(max(matches, key=lambda item: (item.count, item.lexical)))
        if exact_children:
            selected = exact_children
            answer = tuple(_decode(item.component, atoms) for item in selected)
            self.last_composition_trace = tuple(item.lexical for item in selected)
            signature_size = sum(len(_edges(child)) for child in children)
        else:
            signature = _edges(root)
            answer = self._emit(signature, model, atoms)
            selected = [None] * len(answer)
            signature_size = len(signature)
        comparisons = len(model) * max(1, signature_size)
        self.last_ops = float(used + 3 * comparisons + 4 * len(selected))
        self.last_bytes_touched = float(
            8 * (len(source.tokens) + sum(len(item.edges) for item in model))
        )
        return answer

    def update(self, source: PublicUpdate, target: object) -> None:
        del target
        self.memo[source.query.slot, source.query.tokens] = tuple(source.target)
        self.update_ops += float(len(source.query.tokens) + len(source.target))

    def state_bytes(self) -> int:
        fragments = sum(
            64 + 32 * len(item.edges)
            for model in self.models.values() for item in model
        )
        maps = sum(len(mapping) for mapping in self.maps.values()) * 16
        atoms = sum(len(values) for values in self.atoms.values()) * 8
        return int(fragments + maps + atoms + len(self.memo) * 96)


class Candidate(RelationFragmentGraphLearner):
    pass
