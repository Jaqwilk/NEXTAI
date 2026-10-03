from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from .candidates.base import CandidateBase, CandidateMetadata


FEATURE_BITS, MODULUS = 16, 256
PROBES = (0, 1, 2, 3, 7, 15, 31, 63, 95, 127, 128, 159, 191, 223, 254, 255)


@dataclass(frozen=True)
class Demo:
    feature: tuple[int, ...]
    source: int
    target: int


@dataclass(frozen=True)
class ModularQuery:
    source: int
    features: tuple[tuple[int, ...], ...]
    route_ids: tuple[int, ...]


def _reverse_bits(value: int) -> int:
    return int(f"{value:08b}"[::-1], 2)


def apply_transform(spec: tuple[int, int], value: int) -> int:
    operation, parameter = spec
    if operation == 0:
        return (value + parameter) % MODULUS
    if operation == 1:
        return value ^ parameter
    if operation == 2:
        return (value * (parameter | 1)) % MODULUS
    if operation == 3:
        shift = parameter % 7 + 1
        return ((value << shift) | (value >> (8 - shift))) & 255
    if operation == 4:
        return _reverse_bits(value) ^ parameter
    swapped = ((value & 15) << 4) | (value >> 4)
    return (swapped + parameter) % MODULUS


def transform_ops(spec: tuple[int, int]) -> int:
    return (2, 1, 2, 3, 2, 3)[spec[0]]


def unique_specs() -> tuple[tuple[int, int], ...]:
    signatures, result = set(), []
    for operation in range(6):
        for parameter in range(256):
            spec = operation, parameter
            signature = tuple(apply_transform(spec, value) for value in PROBES)
            if signature not in signatures:
                signatures.add(signature)
                result.append(spec)
    return tuple(result)


SPECS = unique_specs()


def feature_variants(feature: tuple[int, ...]):
    yield feature
    for index in range(len(feature)):
        changed = list(feature)
        changed[index] ^= 1
        yield tuple(changed)


def learn_specs(demos: tuple[Demo, ...]):
    grouped: dict[tuple[int, ...], list[Demo]] = defaultdict(list)
    for demo in demos:
        grouped[demo.feature].append(demo)
    models, operations = {}, 0
    for feature, items in grouped.items():
        scores = []
        for spec in SPECS:
            errors = 0
            for item in items:
                errors += apply_transform(spec, item.source) != item.target
                operations += transform_ops(spec) + 1
            scores.append((errors, spec))
        models[feature] = min(scores)[1]
    return models, operations


class ProgramBase(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.models: dict[tuple[int, ...], tuple[int, int]] = {}
        self.last_routes: tuple[int, ...] = ()
        self.last_encoding_ops = self.last_router_ops = self.last_expert_ops = 0
        self.last_active_modules = self.last_full_expert_evaluations = self.last_bytes_loaded = 0

    def update(self, source: Demo, target: int) -> None:
        self.update_ops = FEATURE_BITS + 3


class DirectProgramIndex(ProgramBase):
    metadata = CandidateMetadata("direct_program_index", "direct_program", "Flat learned transform programs behind an error-correcting index")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.models, operations = learn_specs(tuple(facts))
        self.programs: dict[tuple[int, ...], tuple[int, tuple[int, int]]] = {}
        for route_id, (feature, spec) in enumerate(self.models.items()):
            for variant in feature_variants(feature):
                self.programs[variant] = route_id, spec
                operations += FEATURE_BITS + 1
        self.fit_ops = operations

    def query(self, source: ModularQuery, steps: int) -> int | None:
        value, routes = source.source, []
        self.last_encoding_ops = 1 + FEATURE_BITS * len(source.features)
        self.last_router_ops = self.last_expert_ops = self.last_bytes_loaded = 0
        for feature in source.features:
            routed = self.programs.get(feature)
            self.last_router_ops += 1
            self.last_bytes_loaded += FEATURE_BITS + 4
            if routed is None:
                self.last_routes = tuple(routes)
                self.last_ops = self.last_encoding_ops + self.last_router_ops + self.last_expert_ops
                return None
            route_id, spec = routed
            routes.append(route_id)
            value = apply_transform(spec, value)
            self.last_expert_ops += transform_ops(spec)
        self.last_routes = tuple(routes)
        self.last_active_modules = self.last_full_expert_evaluations = 0
        self.last_ops = self.last_encoding_ops + self.last_router_ops + self.last_expert_ops
        return value

    def state_bytes(self) -> int:
        return 96 + 20 * len(self.programs) + 12 * len(self.models)


class LearnedSparseModules(ProgramBase):
    metadata = CandidateMetadata("learned_sparse_modules", "sparse_modules", "Learned heterogeneous modules with indexed sparse dispatch")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.models, operations = learn_specs(tuple(facts))
        self.modules, self.router = [], {}
        for feature, spec in self.models.items():
            module_id = len(self.modules)
            self.modules.append(spec)
            for variant in feature_variants(feature):
                self.router[variant] = module_id
                operations += FEATURE_BITS + 1
        self.fit_ops = operations

    def query(self, source: ModularQuery, steps: int) -> int | None:
        value, routes = source.source, []
        self.last_encoding_ops = 1 + FEATURE_BITS * len(source.features)
        self.last_router_ops = self.last_expert_ops = self.last_bytes_loaded = 0
        self.last_active_modules = self.last_full_expert_evaluations = 0
        for feature in source.features:
            module_id = self.router.get(feature)
            self.last_router_ops += 1
            self.last_bytes_loaded += FEATURE_BITS + 8
            if module_id is None:
                self.last_routes = tuple(routes)
                self.last_ops = self.last_encoding_ops + self.last_router_ops + self.last_expert_ops
                return None
            routes.append(module_id)
            spec = self.modules[module_id]
            value = apply_transform(spec, value)
            self.last_expert_ops += transform_ops(spec) + 1
            self.last_active_modules += 1
            self.last_full_expert_evaluations += 1
        self.last_routes = tuple(routes)
        self.last_ops = self.last_encoding_ops + self.last_router_ops + self.last_expert_ops
        return value

    def update(self, source: Demo, target: int) -> None:
        self.update_ops = FEATURE_BITS + 4

    def state_bytes(self) -> int:
        return 160 + 20 * len(self.router) + 28 * len(self.modules)


class OracleSparseModules(LearnedSparseModules):
    metadata = CandidateMetadata("oracle_sparse_modules", "oracle", "True modules with exact error-correcting route index")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        specs, features = tuple(facts)[0]
        self.models = dict(zip(features, specs))
        self.modules, self.router = [], {}
        for feature, spec in self.models.items():
            module_id = len(self.modules)
            self.modules.append(spec)
            for variant in feature_variants(feature):
                self.router[variant] = module_id
        self.fit_ops = 0

    def update(self, source: Demo, target: int) -> None:
        self.update_ops = 1


class DenseExpertSweep(ProgramBase):
    metadata = CandidateMetadata("dense_expert_sweep", "dense_experts", "Evaluate and route across every learned expert")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.models, self.fit_ops = learn_specs(tuple(facts))
        self.features = tuple(self.models)
        self.modules = tuple(self.models[feature] for feature in self.features)

    def query(self, source: ModularQuery, steps: int) -> int:
        value, routes = source.source, []
        self.last_encoding_ops = 1 + FEATURE_BITS * len(source.features)
        self.last_router_ops = self.last_expert_ops = self.last_bytes_loaded = 0
        self.last_active_modules = self.last_full_expert_evaluations = 0
        for feature in source.features:
            scores, outputs = [], []
            for module_id, (prototype, spec) in enumerate(zip(self.features, self.modules)):
                score = sum(left != right for left, right in zip(feature, prototype))
                scores.append((score, module_id))
                outputs.append(apply_transform(spec, value))
                self.last_router_ops += 2 * FEATURE_BITS
                self.last_expert_ops += transform_ops(spec)
                self.last_bytes_loaded += FEATURE_BITS + 4
            module_id = min(scores)[1]
            routes.append(module_id)
            value = outputs[module_id]
            self.last_active_modules += len(self.modules)
            self.last_full_expert_evaluations += len(self.modules)
        self.last_routes = tuple(routes)
        self.last_ops = self.last_encoding_ops + self.last_router_ops + self.last_expert_ops
        return value

    def state_bytes(self) -> int:
        return 128 + (FEATURE_BITS + 12) * len(self.modules)


class RandomModuleRouter(LearnedSparseModules):
    metadata = CandidateMetadata("random_module_router", "random", "Random routing over learned transformations")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        super().fit(facts, universe_size, max_depth)
        self.rng = random.Random(self.seed)

    def query(self, source: ModularQuery, steps: int) -> int:
        value, routes = source.source, []
        self.last_encoding_ops = 1 + FEATURE_BITS * len(source.features)
        self.last_router_ops = self.last_expert_ops = self.last_bytes_loaded = 0
        for _ in source.features:
            module_id = self.rng.randrange(len(self.modules))
            routes.append(module_id)
            spec = self.modules[module_id]
            value = apply_transform(spec, value)
            self.last_router_ops += 1
            self.last_expert_ops += transform_ops(spec) + 1
            self.last_bytes_loaded += 4
        self.last_routes = tuple(routes)
        self.last_active_modules = self.last_full_expert_evaluations = len(routes)
        self.last_ops = self.last_encoding_ops + self.last_router_ops + self.last_expert_ops
        return value


class PrimitiveDemoMemorizer(ProgramBase):
    metadata = CandidateMetadata("primitive_demo_memorizer", "memory", "Exact single-demonstration lookup without composition")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        demos = tuple(facts)
        self.memory = {(item.feature, item.source): item.target for item in demos}
        self.fit_ops = 2 * len(demos)

    def query(self, source: ModularQuery, steps: int) -> int:
        value = source.source
        self.last_encoding_ops = 1 + FEATURE_BITS * len(source.features)
        self.last_router_ops = self.last_expert_ops = 0
        for feature in source.features:
            value = self.memory.get((feature, value), 0)
            self.last_router_ops += 1
        self.last_routes = ()
        self.last_active_modules = self.last_full_expert_evaluations = 0
        self.last_bytes_loaded = (FEATURE_BITS + 2) * len(source.features)
        self.last_ops = self.last_encoding_ops + self.last_router_ops
        return value

    def state_bytes(self) -> int:
        return 64 + (FEATURE_BITS + 18) * len(self.memory)


class DenseSharedTransform(ProgramBase):
    metadata = CandidateMetadata("dense_shared_transform", "dense_shared", "One nonlinear shared predictor for all transformations")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        demos = tuple(facts)
        rows, targets = [], []
        for demo in demos:
            for feature in feature_variants(demo.feature):
                rows.append(self._encode(feature, demo.source))
                targets.append(tuple((demo.target >> bit) & 1 for bit in range(8)))
        inputs = np.asarray(rows, dtype=np.float64)
        outputs = 2.0 * np.asarray(targets, dtype=np.float64) - 1.0
        width = 128
        rng = np.random.default_rng(self.seed)
        self.weights = rng.normal(0.0, 1.0 / math.sqrt(inputs.shape[1]), (inputs.shape[1], width))
        self.bias = rng.normal(0.0, 0.25, width)
        hidden = np.tanh(inputs @ self.weights + self.bias)
        ridge = hidden.T @ hidden + 0.1 * np.eye(width)
        self.readout = np.linalg.solve(ridge, hidden.T @ outputs)
        samples, dimension = inputs.shape
        self.fit_ops = int(samples * (2 * dimension * width + 2 * width * width) + 2 * width**3 / 3)

    @staticmethod
    def _encode(feature: tuple[int, ...], value: int):
        return tuple(2 * bit - 1 for bit in feature) + tuple(1.0 if (value >> bit) & 1 else -1.0 for bit in range(8))

    def query(self, source: ModularQuery, steps: int) -> int:
        value = source.source
        dimension, width = self.weights.shape
        self.last_encoding_ops = 1 + (FEATURE_BITS + 8) * len(source.features)
        self.last_router_ops = 0
        self.last_expert_ops = len(source.features) * (2 * dimension * width + 2 * width * 8)
        for feature in source.features:
            hidden = np.tanh(np.asarray(self._encode(feature, value)) @ self.weights + self.bias)
            bits = hidden @ self.readout >= 0.0
            value = sum(int(bit) << index for index, bit in enumerate(bits))
        self.last_routes = ()
        self.last_active_modules = self.last_full_expert_evaluations = 0
        self.last_bytes_loaded = len(source.features) * self.state_bytes()
        self.last_ops = self.last_encoding_ops + self.last_expert_ops
        return value

    def state_bytes(self) -> int:
        return int(self.weights.nbytes + self.bias.nbytes + self.readout.nbytes)
