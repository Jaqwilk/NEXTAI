from __future__ import annotations

import math

import numpy as np

from .base import CandidateBase, CandidateMetadata
from nextai_autoresearch.cross_family_transfer_v2_contract import (
    Example,
    PublicQuery,
    PublicTraining,
    PublicUpdate,
    TestWorld,
    TrainingWorld,
    encode,
)


WIDTH = 32
SLOTS = 32
TOP_K = 4
HEADS = 1
EPOCHS = 24
BATCH = 32
LEARNING_RATE = 0.001
ROUTING_DISTANCE = "squared_euclidean"
Template = tuple[tuple[str, float | int], ...]


def _symbols(tokens: tuple[int, ...], known: dict[int, int] | None = None,
             known_atoms: tuple[int, ...] = ()) -> tuple[
                 tuple[int, ...], dict[int, int], tuple[int, ...]
             ]:
    mapping = {} if known is None else dict(known)
    atoms = list(known_atoms)
    output: list[int] = []
    integer_value = False
    for token in tokens:
        if integer_value:
            if token not in mapping:
                mapping[token] = len(mapping)
                atoms.append(token)
            symbol = 32 + mapping[token]
        elif token < 0:
            symbol = -token
        else:
            symbol = 16 + abs(token) % 509
        output.append(symbol)
        integer_value = token == -5
    return tuple(output), mapping, tuple(atoms)


def _set_feature(symbols: tuple[int, ...]) -> tuple[np.ndarray, int]:
    feature = np.zeros(WIDTH, dtype=np.float64)
    for symbol in symbols:
        first = (17 * symbol + 3) % WIDTH
        second = (29 * symbol + 11) % WIDTH
        sign = 1.0 if ((symbol * 13) & 1) == 0 else -1.0
        feature[first] += sign
        feature[second] += 0.5
    norm = float(np.linalg.norm(feature))
    if norm > 0.0:
        feature /= norm
    return feature, 6 * len(symbols) + 3 * WIDTH


def _template(target: tuple[float, ...], mapping: dict[int, int]) -> Template:
    output: list[tuple[str, float | int]] = []
    for value in target:
        rounded = round(value)
        if abs(value - rounded) < 1e-9 and rounded in mapping:
            output.append(("pointer", mapping[rounded]))
        else:
            output.append(("scalar", float(value)))
    return tuple(output) or (("scalar", 0.0),)


def _decode(template: Template, atoms: tuple[int, ...]) -> tuple[float, ...]:
    return tuple(
        float(atoms[int(value)])
        if kind == "pointer" and int(value) < len(atoms) else float(value)
        for kind, value in template
    )


def _template_key(template: Template) -> tuple[tuple[str, float], ...]:
    return tuple((kind, float(value)) for kind, value in template)


class _Memory:
    def __init__(self, seed: int) -> None:
        rows = np.arange(SLOTS, dtype=np.float64)[:, None] + 1.0
        cols = np.arange(WIDTH, dtype=np.float64)[None, :] + 1.0
        phase = (seed % 104729) / 104729.0
        self.keys = np.sin(rows * cols * 0.173 + phase)
        self.keys /= np.maximum(np.linalg.norm(self.keys, axis=1, keepdims=True), 1e-12)
        self.values: tuple[Template, ...] = tuple(
            (("scalar", 0.0),) for _ in range(SLOTS)
        )


class SparseSetMemoryLearner(CandidateBase):
    metadata = CandidateMetadata(
        "sparse-set-memory",
        "permutation_equivariant_sparse_set_memory",
        "One source-identical 32-slot set memory with learned or frozen sparse routing.",
    )
    MODE = "pooled_sparse_learned_router"
    embedding_width = WIDTH
    memory_slots = SLOTS
    sparse_top_k = TOP_K
    attention_heads = HEADS
    fit_epochs = EPOCHS
    batch_size = BATCH
    learning_rate = LEARNING_RATE
    routing_distance = ROUTING_DISTANCE

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.mode = self.MODE
        self.memories: list[_Memory] = []
        self.slot_memory: dict[int, int] = {}
        self.support_features: dict[int, np.ndarray] = {}
        self.maps: dict[int, dict[int, int]] = {}
        self.atoms: dict[int, tuple[int, ...]] = {}
        self.memo: dict[tuple[int, tuple[int, ...]], tuple[float, ...]] = {}
        self.meta_fit_ops = 0.0
        self.last_bytes_touched = 0.0
        self.last_accessed_slots = 0

    def _example(self, support: tuple[int, ...], example: Example) -> tuple[
        np.ndarray, Template, int
    ]:
        support_symbols, mapping, atoms = _symbols(support)
        query_symbols, full_map, _ = _symbols(example.query, mapping, atoms)
        support_feature, support_ops = _set_feature(support_symbols)
        query_feature, query_ops = _set_feature(query_symbols)
        feature = query_feature + 0.5 * support_feature
        feature /= max(float(np.linalg.norm(feature)), 1e-12)
        return feature, _template(example.target, full_map), support_ops + query_ops

    def _fit_memory(self, examples: list[tuple[np.ndarray, Template]], seed: int,
                    learned: bool) -> tuple[_Memory, float]:
        memory = _Memory(seed)
        ordered = sorted(examples, key=lambda item: (_template_key(item[1]), tuple(item[0])))
        operations = float(SLOTS * WIDTH * 8)
        if not ordered:
            return memory, operations

        templates = sorted({_template_key(template): template for _, template in ordered}.items())
        target_slot = {key: index % SLOTS for index, (key, _) in enumerate(templates)}
        if learned:
            first = np.zeros_like(memory.keys)
            second = np.zeros_like(memory.keys)
            for epoch in range(EPOCHS):
                for begin in range(0, len(ordered), BATCH):
                    gradient = np.zeros_like(memory.keys)
                    batch = ordered[begin:begin + BATCH]
                    for feature, template in batch:
                        slot = target_slot[_template_key(template)]
                        gradient[slot] += 2.0 * (memory.keys[slot] - feature)
                    gradient /= max(1, len(batch))
                    first = 0.9 * first + 0.1 * gradient
                    second = 0.999 * second + 0.001 * gradient * gradient
                    first_hat = first / (1.0 - 0.9 ** (epoch + 1))
                    second_hat = second / (1.0 - 0.999 ** (epoch + 1))
                    memory.keys -= LEARNING_RATE * first_hat / (np.sqrt(second_hat) + 1e-8)
                    operations += float(len(batch) * WIDTH * 3 + SLOTS * WIDTH * 12)

        buckets: list[list[Template]] = [[] for _ in range(SLOTS)]
        for feature, template in ordered:
            if learned:
                slot = target_slot[_template_key(template)]
            else:
                slot = int(np.argmin(np.sum((memory.keys - feature) ** 2, axis=1)))
                operations += float(SLOTS * WIDTH * 3)
            buckets[slot].append(template)
        values: list[Template] = []
        for bucket in buckets:
            if not bucket:
                values.append((("scalar", 0.0),))
                continue
            counts: dict[Template, int] = {}
            for template in bucket:
                counts[template] = counts.get(template, 0) + 1
            values.append(min(counts, key=lambda item: (-counts[item], _template_key(item))))
        memory.values = tuple(values)
        return memory, operations + len(ordered) * WIDTH

    def fit(self, facts: PublicTraining, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        if not isinstance(facts, PublicTraining):
            raise TypeError("implementable learner accepts only PublicTraining")
        self.memories = []
        self.slot_memory = {}
        self.support_features = {}
        self.maps = {}
        self.atoms = {}
        self.memo = {}
        groups: list[tuple[np.ndarray, list[tuple[np.ndarray, Template]]]] = []
        operations = 0.0
        for world in facts.training_worlds:
            support_symbols, _, _ = _symbols(world.support)
            support_feature, used = _set_feature(support_symbols)
            items = []
            for example in world.examples:
                feature, template, item_ops = self._example(world.support, example)
                items.append((feature, template))
                operations += item_ops
            groups.append((support_feature, items))
            operations += used
        groups.sort(key=lambda item: (tuple(item[0]), tuple(
            (_template_key(template), tuple(feature)) for feature, template in item[1]
        )))

        frozen = self.mode == "pooled_sparse_frozen_router"
        if self.mode == "independent_sparse_learned_router":
            for index, (_, items) in enumerate(groups):
                memory, used = self._fit_memory(items, self.seed + index, True)
                self.memories.append(memory)
                operations += used
        else:
            pooled = [item for _, items in groups for item in items]
            memory, used = self._fit_memory(pooled, self.seed, not frozen)
            self.memories.append(memory)
            operations += used

        for world in facts.test_worlds:
            if not isinstance(world, TestWorld):
                raise TypeError("unexpected test-world type")
            symbols, mapping, atoms = _symbols(world.support)
            feature, used = _set_feature(symbols)
            self.support_features[world.slot] = feature
            self.maps[world.slot] = mapping
            self.atoms[world.slot] = atoms
            if self.mode == "independent_sparse_learned_router":
                distances = [float(np.sum((feature - support) ** 2)) for support, _ in groups]
                self.slot_memory[world.slot] = int(np.argmin(distances))
                operations += float(len(groups) * WIDTH * 3)
            else:
                self.slot_memory[world.slot] = 0
            operations += used
        self.fit_ops = self.meta_fit_ops = operations

    def query(self, source: PublicQuery, steps: int) -> tuple[float, ...]:
        del steps
        if not isinstance(source, PublicQuery):
            raise TypeError("implementable learner accepts only PublicQuery")
        memo_key = (source.slot, source.tokens)
        if memo_key in self.memo:
            answer = self.memo[memo_key]
            self.last_accessed_slots = 0
            self.last_ops = float(len(answer))
            self.last_bytes_touched = float(8 * len(answer))
            return answer
        symbols, _, atoms = _symbols(
            source.tokens, self.maps[source.slot], self.atoms[source.slot]
        )
        query_feature, operations = _set_feature(symbols)
        feature = query_feature + 0.5 * self.support_features[source.slot]
        feature /= max(float(np.linalg.norm(feature)), 1e-12)
        memory = self.memories[self.slot_memory[source.slot]]
        distances = np.sum((memory.keys - feature) ** 2, axis=1)
        count = SLOTS if self.mode == "pooled_dense_learned_router" else TOP_K
        selected = np.argsort(distances, kind="stable")[:count]
        votes: dict[Template, float] = {}
        for slot in selected:
            value = memory.values[int(slot)]
            votes[value] = votes.get(value, 0.0) + math.exp(-float(distances[int(slot)]))
        chosen = min(votes, key=lambda item: (-votes[item], _template_key(item)))
        answer = _decode(chosen, atoms)
        self.last_accessed_slots = count
        self.last_ops = float(operations + SLOTS * WIDTH * 3 + count * 8)
        self.last_bytes_touched = float(
            8 * (len(source.tokens) + WIDTH + SLOTS * WIDTH + count * 8)
        )
        return answer

    def update(self, source: PublicUpdate, target: object) -> None:
        del target
        if not isinstance(source, PublicUpdate):
            raise TypeError("implementable learner accepts only PublicUpdate")
        self.memo[source.query.slot, source.query.tokens] = tuple(source.target)
        self.update_ops += float(len(source.query.tokens) + len(source.target))

    def state_bytes(self) -> int:
        arrays = sum(memory.keys.nbytes for memory in self.memories)
        values = sum(
            sum(len(template) for template in memory.values) * 16
            for memory in self.memories
        )
        supports = sum(feature.nbytes for feature in self.support_features.values())
        maps = sum(len(mapping) * 16 for mapping in self.maps.values())
        return int(arrays + values + supports + maps + len(self.memo) * 96)


class Candidate(SparseSetMemoryLearner):
    pass


def semantic_conformance() -> dict[str, bool | int]:
    support, _ = encode((10, 20, 10, 30))
    relabeled_support, _ = encode((110, 120, 110, 130))
    first, _ = encode((10, 20, 10))
    second, _ = encode((20, 20, 10))
    relabeled_first, _ = encode((110, 120, 110))
    relabeled_second, _ = encode((120, 120, 110))
    worlds = (
        TrainingWorld(support, (
            Example(first, (10.0,)), Example(second, (20.0,)),
        )),
        TrainingWorld(support, (
            Example(second, (20.0,)), Example(first, (10.0,)),
        )),
    )
    facts = PublicTraining(worlds, (TestWorld(7, relabeled_support),), 0)
    reversed_facts = PublicTraining(tuple(reversed(worlds)), facts.test_worlds, 0)
    outputs = []
    for candidate_facts in (facts, reversed_facts):
        candidate = SparseSetMemoryLearner(17)
        candidate.fit(candidate_facts, 8, 1)
        outputs.append((
            candidate.query(PublicQuery(7, relabeled_first), 1),
            candidate.query(PublicQuery(7, relabeled_second), 1),
        ))
        if candidate.last_accessed_slots != TOP_K:
            raise AssertionError("sparse role did not touch exactly top-k slots")
    if outputs[0] != outputs[1]:
        raise AssertionError("training-world permutation changed predictions")
    dense = SparseSetMemoryLearner(17)
    dense.mode = "pooled_dense_learned_router"
    dense.fit(facts, 8, 1)
    dense.query(PublicQuery(7, relabeled_first), 1)
    if dense.last_accessed_slots != SLOTS:
        raise AssertionError("dense role did not touch every slot")
    return {
        "world_permutation_invariant": True,
        "consistent_atom_relabeling_executed": True,
        "sparse_slots": TOP_K,
        "dense_slots": SLOTS,
    }
