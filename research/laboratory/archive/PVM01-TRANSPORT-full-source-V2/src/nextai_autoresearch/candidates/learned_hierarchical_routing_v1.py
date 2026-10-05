from __future__ import annotations

import math

import numpy as np
import torch

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata
from nextai_autoresearch.candidates.learned_addressing_v1 import (
    AddressEncoder, BATCH, EPOCHS, LATENT, _training_views,
)
from nextai_autoresearch.entity_addressing_contract import OBSERVATION_DIMENSION, RawQuery, TransitionBurst
from nextai_autoresearch.local_torch import deterministic_device, parameter_bytes


BEAM = 4
VISIT_CAP = 64


class HierarchicalRoutingBase(CandidateBase):
    learning = "learned"
    access = "tree"

    def _encode(self, values: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            tensor = torch.as_tensor(values, dtype=torch.float32, device=self.device)
            return self.encoder(tensor).cpu().numpy()

    def _encoder_vector(self) -> np.ndarray:
        return torch.cat([value.detach().cpu().flatten() for value in self.encoder.parameters()]).numpy()

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        records = tuple(facts)
        pair_a, pair_b, raw_sources, raw_targets = _training_views(records)
        if self.learning == "shuffled":
            pair_b = np.roll(pair_b, len(pair_b) // 2, axis=0)
        self.device = deterministic_device(self.seed)
        self.encoder = AddressEncoder().to(self.device)
        if self.learning != "frozen":
            optimizer = torch.optim.Adam(self.encoder.parameters(), lr=0.001)
            for _ in range(EPOCHS):
                for start in range(0, len(pair_a), BATCH):
                    left = torch.as_tensor(pair_a[start:start + BATCH], dtype=torch.float32, device=self.device)
                    right = torch.as_tensor(pair_b[start:start + BATCH], dtype=torch.float32, device=self.device)
                    optimizer.zero_grad(set_to_none=True)
                    z_left, z_right = self.encoder(left), self.encoder(right)
                    joined = torch.cat((z_left, z_right), dim=0)
                    centered = joined - joined.mean(dim=0)
                    covariance = centered.T @ centered / max(len(joined) - 1, 1)
                    off_diagonal = covariance - torch.diag(torch.diagonal(covariance))
                    loss = (
                        torch.square(z_left - z_right).mean()
                        + 0.1 * torch.square(joined.mean(dim=0)).mean()
                        + 0.1 * torch.square(torch.relu(0.5 - joined.std(dim=0, unbiased=False))).mean()
                        + 0.01 * torch.square(off_diagonal).mean()
                        + 0.01 * torch.square(torch.abs(joined) - 1.0).mean()
                    )
                    loss.backward()
                    optimizer.step()
        self.encoder.eval()
        self.capacity = universe_size + 1
        self.sources = np.empty((self.capacity, LATENT), dtype=np.float32)
        self.targets = np.empty_like(self.sources)
        self.values = np.empty(self.capacity, dtype=np.int64)
        self.sources[:universe_size] = self._encode(raw_sources)
        self.targets[:universe_size] = self._encode(raw_targets)
        self.values[:universe_size] = [record.value for record in records]
        self.left = np.full(self.capacity, -1, dtype=np.int32)
        self.right = np.full(self.capacity, -1, dtype=np.int32)
        self.axis = np.zeros(self.capacity, dtype=np.int8)
        self.count = universe_size
        self._build_ops = 0
        self.root = self._build(list(range(universe_size)))
        encode_ops = 2 * OBSERVATION_DIMENSION * 32 + 32 + 2 * 32 * LATENT + LATENT
        split_ops = universe_size * 7 * OBSERVATION_DIMENSION * 3
        training_ops = 0 if self.learning == "frozen" else EPOCHS * 2 * len(pair_a) * 3 * encode_ops
        calibration_ops = (2 * len(pair_a) + 2 * universe_size) * encode_ops
        self.representation_fit_ops = training_ops
        self.fit_ops = split_ops + training_ops + calibration_ops + self._build_ops
        self._encode_ops = encode_ops

    def _build(self, indices: list[int]) -> int:
        if not indices:
            return -1
        rows = self.sources[indices]
        axis = int(np.argmax(rows.var(axis=0)))
        indices.sort(key=lambda index: (self.sources[index, axis], index))
        middle = len(indices) // 2
        node = indices[middle]
        self.axis[node] = axis
        self._build_ops += len(indices) * LATENT * 3
        self._build_ops += max(1, math.ceil(len(indices) * math.log2(max(len(indices), 2))))
        self.left[node] = self._build(indices[:middle])
        self.right[node] = self._build(indices[middle + 1:])
        return node

    def _tree_lookup(self, vector: np.ndarray) -> tuple[int, int, int]:
        frontier = [(0.0, int(self.root))]
        visited: list[int] = []
        frontier_peak = 1
        operations = 0
        while frontier and len(visited) < VISIT_CAP:
            bound, node = frontier.pop(0)
            visited.append(node)
            axis = int(self.axis[node])
            offset = float(vector[axis] - self.sources[node, axis])
            near, far = ((int(self.left[node]), int(self.right[node]))
                         if offset < 0 else (int(self.right[node]), int(self.left[node])))
            if near >= 0:
                frontier.append((bound, near))
            if far >= 0:
                frontier.append((max(bound, offset * offset), far))
            frontier.sort(key=lambda item: (item[0], item[1]))
            if len(frontier) > BEAM:
                del frontier[BEAM:]
            frontier_peak = max(frontier_peak, len(frontier))
            operations += 3 * LATENT + 4 + max(1, math.ceil(len(frontier) * math.log2(max(len(frontier), 2))))
        index = min(visited, key=lambda item: (float(np.square(self.sources[item] - vector).sum()), item))
        self.last_frontier_peak = frontier_peak
        return index, len(visited), operations

    def _lookup(self, vector: np.ndarray) -> tuple[int, int, int]:
        if self.access == "dense":
            indices = range(self.count)
            index = min(indices, key=lambda item: (float(np.square(self.sources[item] - vector).sum()), item))
            self.last_frontier_peak = 0
            return index, self.count, self.count * 3 * LATENT
        return self._tree_lookup(vector)

    def query(self, source: RawQuery, steps: int) -> int:
        current = self._encode(np.asarray(source.observation, dtype=np.float32)[None])[0]
        comparisons, operations = 0, self._encode_ops
        answer = -1
        for _ in range(steps):
            index, compared, lookup_ops = self._lookup(current)
            comparisons += compared
            operations += lookup_ops
            current, answer = self.targets[index], int(self.values[index])
        self.last_comparisons = comparisons
        self.last_ops = operations
        self.last_bytes_touched = (
            parameter_bytes(self.encoder) + OBSERVATION_DIMENSION * 4
            + comparisons * (LATENT * 4 + 9) + steps * (LATENT * 4 + 8)
        )
        return answer

    def update(self, source: TransitionBurst, target: int) -> None:
        rows = np.asarray(source.observations, dtype=np.float32)
        cut = int(np.argmax(np.square(rows[1:] - rows[:-1]).sum(axis=1))) + 1
        encoded = self._encode(np.stack((rows[:cut].mean(axis=0), rows[cut:].mean(axis=0))))
        index, node, comparisons = self.count, int(self.root), 0
        self.sources[index], self.targets[index], self.values[index] = encoded[0], encoded[1], target
        while True:
            comparisons += 1
            axis = int(self.axis[node])
            branch = self.left if (encoded[0, axis], index) < (self.sources[node, axis], node) else self.right
            child = int(branch[node])
            if child < 0:
                branch[node] = index
                self.axis[index] = (axis + 1) % LATENT
                break
            node = child
        self.count += 1
        self.update_ops = 7 * OBSERVATION_DIMENSION * 3 + 2 * self._encode_ops + 3 * comparisons

    def state_bytes(self) -> int:
        return int(
            parameter_bytes(self.encoder) + self.sources.nbytes + self.targets.nbytes
            + self.values.nbytes + self.left.nbytes + self.right.nbytes + self.axis.nbytes
        )


class HierarchicalCandidate(HierarchicalRoutingBase):
    metadata = CandidateMetadata("learned_balanced_hierarchical_router_v1", "learned_routing", "Learned node-conditional bounded hierarchical routing.")


class DenseCandidate(HierarchicalRoutingBase):
    metadata = CandidateMetadata("source_identical_dense_hierarchical_representation_v1", "learned_routing_ablation", "Same representation with dense access.")
    access = "dense"


class FrozenCandidate(HierarchicalRoutingBase):
    metadata = CandidateMetadata("source_identical_frozen_hierarchical_router_v1", "learned_routing_ablation", "Same hierarchy with encoder learning disabled.")
    learning = "frozen"


class ShuffledCandidate(HierarchicalRoutingBase):
    metadata = CandidateMetadata("source_identical_shuffled_hierarchical_router_v1", "learned_routing_ablation", "Same hierarchy with shuffled view pairs.")
    learning = "shuffled"


class Candidate(HierarchicalCandidate):
    pass
