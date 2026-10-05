from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata


@dataclass(frozen=True)
class VSAQuery:
    source: int
    noise_seed: int = 0
    noise_rate: float = 0.0


@dataclass(frozen=True)
class OracleVSAQuery(VSAQuery):
    path: tuple[int, ...] = ()


def query_source(value: int | VSAQuery) -> int:
    return value.source if isinstance(value, VSAQuery) else int(value)


class RandomVSACapacity(CandidateBase):
    metadata = CandidateMetadata("random_vsa_capacity", "random_control", "Deterministic random answer control.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.size, self.fit_ops = universe_size, 0

    def query(self, source: int | VSAQuery, steps: int) -> int | None:
        source = query_source(source)
        self.last_ops, self.last_comparisons, self.last_bytes_touched = 2, 0, 8
        return None if self.size <= 0 else (source * 1103515245 + steps * 12345 + self.seed) % self.size

    def update(self, source: int, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 128


class ExactTupleStoreVSA(CandidateBase):
    metadata = CandidateMetadata("exact_tuple_store_vsa", "symbolic_control", "Exact successor dictionary.")

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.transitions = dict(facts)
        self.fit_ops = len(self.transitions)

    def query(self, source: int | VSAQuery, steps: int) -> int | None:
        current = query_source(source)
        for _ in range(steps):
            current = self.transitions.get(current)
            if current is None:
                break
        self.last_ops = self.last_comparisons = steps
        self.last_bytes_touched = 16 * steps
        return current

    def update(self, source: int, target: int) -> None:
        self.transitions[source] = target
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 256 + 16 * len(self.transitions)


class RoutedVSA(CandidateBase):
    ratio = 32
    mode = "global"
    metadata = CandidateMetadata("routed_vsa", "hyperdimensional_computing", "Bipolar VSA relation store.")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.dimension = self.size = self.bucket_count = 0
        self.codebook = np.zeros((0, 0), dtype=np.int8)
        self.memory = np.zeros(0, dtype=np.int32)
        self.prototypes = np.zeros((0, 0), dtype=np.int32)
        self.centroids = np.zeros((0, 0), dtype=np.float32)
        self.dense_memory = np.zeros((0, 0), dtype=np.int8)
        self.members: tuple[np.ndarray, ...] = ()
        self.transitions: dict[int, int] = {}
        self.representation_signature = self.memory_signature = 0.0

    def _codes(self, size: int) -> np.ndarray:
        rng = np.random.default_rng(self.seed)
        return rng.integers(0, 2, (size, self.dimension), dtype=np.int8) * np.int8(2) - np.int8(1)

    def _binding(self, source: int, target: int) -> np.ndarray:
        return np.roll(self.codebook[source], 1).astype(np.int32) * self.codebook[target]

    def _retrieved(self, source: int, noise_seed: int = 0, noise_rate: float = 0.0) -> np.ndarray:
        if self.mode == "dense":
            return self.dense_memory[source].astype(np.int32)
        role = np.roll(self.codebook[source], 1).astype(np.int32)
        if noise_rate:
            stride = max(1, round(1.0 / noise_rate))
            role[(np.arange(self.dimension) + noise_seed) % stride == 0] *= -1
        return role * self.memory

    def _build_router(self) -> int:
        self.bucket_count = max(1, math.ceil(math.sqrt(self.size)))
        self.members = tuple(np.flatnonzero(np.arange(self.size) % self.bucket_count == bucket)
                             for bucket in range(self.bucket_count))
        if self.mode == "bucket":
            self.prototypes = np.stack([self.codebook[indexes].sum(axis=0, dtype=np.int32)
                                        for indexes in self.members])
            return self.size * self.dimension
        if self.mode == "learned":
            sums = np.zeros((self.bucket_count, self.dimension), dtype=np.float32)
            counts = np.zeros(self.bucket_count, dtype=np.int32)
            for source, target in self.transitions.items():
                bucket = target % self.bucket_count
                sums[bucket] += self._retrieved(source)
                counts[bucket] += 1
            self.centroids = (sums / np.maximum(counts, 1)[:, None]).astype(np.float32)
            return self.size * 4 * self.dimension + self.bucket_count * self.dimension
        return 0

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        self.size, self.dimension = universe_size, self.ratio * universe_size
        self.transitions = dict(facts)
        self.codebook = self._codes(self.size)
        if self.mode == "dense":
            self.dense_memory = np.zeros_like(self.codebook)
            for source, target in self.transitions.items():
                self.dense_memory[source] = self.codebook[target]
            memory_ops = self.size * self.dimension
        else:
            self.memory = np.zeros(self.dimension, dtype=np.int32)
            for source, target in self.transitions.items():
                self.memory += self._binding(source, target)
            memory_ops = 4 * self.size * self.dimension
        router_ops = self._build_router() if self.mode in {"bucket", "learned", "oracle"} else 0
        self.fit_ops = self.size * self.dimension + memory_ops + router_ops
        width = min(32, self.dimension)
        weights = np.arange(1, width + 1, dtype=np.int64)
        self.representation_signature = float(np.sum(self.codebook[:, :width].astype(np.int64) * weights))
        self.memory_signature = (float(np.sum(self.memory[:width].astype(np.int64) * weights))
                                 if self.memory.size else 0.0)

    def _cleanup(self, retrieved: np.ndarray, oracle_target: int | None) -> tuple[int, int, int]:
        d = self.dimension
        if self.mode in {"global", "dense"}:
            indexes, route_ops, route_bytes = np.arange(self.size), 0, 0
            comparisons = self.size
        else:
            if self.mode == "oracle":
                if oracle_target is None:
                    return -1, 1, 0
                bucket, route_ops, route_bytes = oracle_target % self.bucket_count, 0, 0
            else:
                router = self.prototypes if self.mode == "bucket" else self.centroids
                bucket = int(np.argmax(router @ retrieved))
                route_ops = self.bucket_count * (2 * d - 1) + self.bucket_count
                route_bytes = router.nbytes
            indexes = self.members[bucket]
            comparisons = self.bucket_count + len(indexes) if self.mode != "oracle" else len(indexes)
        scores = self.codebook[indexes] @ retrieved
        answer = int(indexes[int(np.argmax(scores))])
        cleanup_ops = len(indexes) * (2 * d - 1) + len(indexes)
        return answer, route_ops + cleanup_ops, route_bytes + int(len(indexes)) * d

    def query(self, source: int | VSAQuery, steps: int) -> int | None:
        value = source if isinstance(source, VSAQuery) else VSAQuery(int(source))
        current, operations, comparisons, touched = value.source, 0, 0, 0
        for step in range(steps):
            if current < 0 or current >= self.size:
                self.last_ops, self.last_comparisons, self.last_bytes_touched = 1, 0, 0
                return None
            target = value.path[step] if isinstance(value, OracleVSAQuery) and step < len(value.path) else None
            retrieved = self._retrieved(current, value.noise_seed + step, value.noise_rate)
            answer, cleanup_ops, cleanup_bytes = self._cleanup(retrieved, target)
            if answer < 0:
                self.last_ops, self.last_comparisons, self.last_bytes_touched = 1, 0, 0
                return None
            local = len(self.members[target % self.bucket_count]) if self.mode == "oracle" and target is not None else 0
            step_comparisons = (self.size if self.mode in {"global", "dense"} else
                                local if self.mode == "oracle" else self.bucket_count + len(self.members[answer % self.bucket_count]))
            operations += (self.dimension if self.mode == "dense" else 2 * self.dimension) + cleanup_ops
            operations += self.dimension if value.noise_rate and self.mode != "dense" else 0
            comparisons += step_comparisons
            touched += (self.dimension if self.mode == "dense" else 5 * self.dimension) + cleanup_bytes
            current = answer
        self.last_ops, self.last_comparisons, self.last_bytes_touched = operations, comparisons, touched
        return current

    def update(self, source: int, target: int) -> None:
        old = self.transitions[source]
        self.transitions[source] = target
        if self.mode == "dense":
            self.dense_memory[source] = self.codebook[target]
            self.update_ops = self.dimension
            return
        self.memory += self._binding(source, target) - self._binding(source, old)
        self.update_ops = 7 * self.dimension
        if self.mode == "learned":
            self.update_ops += self._build_router()

    def state_bytes(self) -> int:
        arrays = (self.codebook, self.memory, self.prototypes, self.centroids, self.dense_memory)
        return 512 + 16 * len(self.transitions) + sum(array.nbytes for array in arrays) + sum(x.nbytes for x in self.members)


class GlobalVSA8(RoutedVSA):
    ratio = 8
    metadata = CandidateMetadata("global_vsa_r8", "hyperdimensional_computing", "Ratio-8 global cleanup VSA.")


class GlobalVSA32(RoutedVSA):
    metadata = CandidateMetadata("global_vsa_r32", "hyperdimensional_computing", "Ratio-32 global cleanup VSA.")


class BucketedVSA32(RoutedVSA):
    mode = "bucket"
    metadata = CandidateMetadata("bucketed_vsa_r32", "classical_index_control", "Prototype bucket routing over the matched VSA.")


class LearnedRoutedVSA32(RoutedVSA):
    mode = "learned"
    metadata = CandidateMetadata("learned_routed_vsa_r32", "learned_routing", "Learned centroid routing over the matched VSA.")


class DenseAssociativeVSA32(RoutedVSA):
    mode = "dense"
    metadata = CandidateMetadata("dense_associative_vsa_r32", "dense_associative_control", "Per-source dense vector memory with global cleanup.")


class OracleRoutedVSA32(RoutedVSA):
    mode = "oracle"
    metadata = CandidateMetadata("oracle_routed_vsa_r32", "oracle_control", "Correct-bucket cleanup bound over the matched VSA.")
