from __future__ import annotations

import numpy as np
import torch

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata
from nextai_autoresearch.entity_addressing_contract import OBSERVATION_DIMENSION, RawQuery, TransitionBurst
from nextai_autoresearch.local_torch import deterministic_device, parameter_bytes


WIDTH = 32
LATENT = 16
BATCH = 64
EPOCHS = 32
BUCKET_CAP = 8
VERIFIER_CAP = 8
FALLBACK_CAP = 32


class AddressEncoder(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(OBSERVATION_DIMENSION, WIDTH), torch.nn.Tanh(),
            torch.nn.Linear(WIDTH, LATENT), torch.nn.Tanh(),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.layers(values)


def _training_views(facts: tuple[TransitionBurst, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    first, second, sources, targets = [], [], [], []
    for record in facts:
        rows = np.asarray(record.observations, dtype=np.float32)
        cut = int(np.argmax(np.square(rows[1:] - rows[:-1]).sum(axis=1))) + 1
        left, right = rows[:cut], rows[cut:]
        sources.append(left.mean(axis=0))
        targets.append(right.mean(axis=0))
        for group in (left, right):
            first.extend(group)
            second.extend(np.roll(group, -1, axis=0))
    return tuple(np.stack(values) for values in (first, second, sources, targets))


class LearnedAddressingBase(CandidateBase):
    learning = "learned"
    access = "index"

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
        source_vectors, target_vectors = self._encode(raw_sources), self._encode(raw_targets)
        pair_distance = np.square(self._encode(pair_a) - self._encode(pair_b)).sum(axis=1)
        self.acceptance = max(1e-6, 9.0 * float(np.median(pair_distance)))
        self.thresholds = np.median(np.vstack((source_vectors, target_vectors)), axis=0)
        self.capacity = universe_size + 1
        self.sources = np.empty((self.capacity, LATENT), dtype=np.float32)
        self.targets = np.empty((self.capacity, LATENT), dtype=np.float32)
        self.values = np.empty(self.capacity, dtype=np.int64)
        self.sources[:universe_size], self.targets[:universe_size] = source_vectors, target_vectors
        self.values[:universe_size] = [record.value for record in records]
        self.count = universe_size
        self.buckets: dict[int, list[int]] = {}
        if self.access == "index":
            for index, vector in enumerate(source_vectors):
                bucket = self.buckets.setdefault(self._key(vector), [])
                if len(bucket) < BUCKET_CAP:
                    bucket.append(index)
        encode_ops = 2 * OBSERVATION_DIMENSION * WIDTH + WIDTH + 2 * WIDTH * LATENT + LATENT
        split_ops = universe_size * 7 * OBSERVATION_DIMENSION * 3
        training_ops = 0 if self.learning == "frozen" else EPOCHS * 2 * len(pair_a) * 3 * encode_ops
        calibration_ops = (2 * len(pair_a) + 2 * universe_size) * encode_ops
        index_ops = 0 if self.access == "dense" else universe_size * (LATENT + 1)
        self.fit_ops = split_ops + training_ops + calibration_ops + index_ops
        self.encoding_fit_ops = calibration_ops
        self.representation_fit_ops = training_ops
        self._encode_ops = encode_ops

    def _key(self, vector: np.ndarray) -> int:
        key = 0
        for index, value in enumerate(vector >= self.thresholds):
            key |= int(value) << index
        return key

    def _probes(self, vector: np.ndarray) -> tuple[int, ...]:
        key = self._key(vector)
        bits = np.argsort(np.abs(vector - self.thresholds), kind="stable")[:3]
        return (key, *(key ^ (1 << int(bit)) for bit in bits))

    def _nearest(self, vector: np.ndarray, indices: list[int]) -> tuple[int, float]:
        return min(
            ((index, float(np.square(self.sources[index] - vector).sum())) for index in indices),
            key=lambda item: (item[1], item[0]),
        )

    def _lookup(self, vector: np.ndarray) -> tuple[int, int, int]:
        if self.access == "dense":
            indices = list(range(self.count))
            index, _ = self._nearest(vector, indices)
            return index, len(indices), LATENT * 3 * len(indices)
        candidates = []
        for key in self._probes(vector):
            for index in self.buckets.get(key, ()):
                if index not in candidates:
                    candidates.append(index)
                if len(candidates) == VERIFIER_CAP:
                    break
            if len(candidates) == VERIFIER_CAP:
                break
        if candidates:
            index, distance = self._nearest(vector, candidates)
            if distance <= self.acceptance:
                return index, len(candidates), 35 + LATENT * 3 * len(candidates)
        fallback = [index for index in range(min(FALLBACK_CAP, self.count)) if index not in candidates]
        pool = fallback or candidates
        index, _ = self._nearest(vector, pool)
        comparisons = len(candidates) + len(fallback)
        return index, comparisons, 35 + LATENT * 3 * comparisons

    def query(self, source: RawQuery, steps: int) -> int:
        current = self._encode(np.asarray(source.observation, dtype=np.float32)[None])[0]
        comparisons, operations, bytes_touched = 0, self._encode_ops, parameter_bytes(self.encoder) + OBSERVATION_DIMENSION * 4
        answer = -1
        for _ in range(steps):
            index, compared, lookup_ops = self._lookup(current)
            comparisons += compared
            operations += lookup_ops
            bytes_touched += compared * LATENT * 4 + LATENT * 4 + 8
            current, answer = self.targets[index], int(self.values[index])
        self.last_comparisons = comparisons
        self.last_ops = operations
        self.last_bytes_touched = bytes_touched
        return answer

    def update(self, source: TransitionBurst, target: int) -> None:
        rows = np.asarray(source.observations, dtype=np.float32)
        cut = int(np.argmax(np.square(rows[1:] - rows[:-1]).sum(axis=1))) + 1
        encoded = self._encode(np.stack((rows[:cut].mean(axis=0), rows[cut:].mean(axis=0))))
        index = self.count
        self.sources[index], self.targets[index], self.values[index] = encoded[0], encoded[1], target
        if self.access == "index":
            bucket = self.buckets.setdefault(self._key(encoded[0]), [])
            if len(bucket) == BUCKET_CAP:
                bucket.pop(0)
            bucket.append(index)
        self.count += 1
        self.update_ops = 7 * OBSERVATION_DIMENSION * 3 + 2 * self._encode_ops + (LATENT + 1 if self.access == "index" else 0)

    def state_bytes(self) -> int:
        index_bytes = 8 * len(self.buckets) + 8 * sum(len(values) for values in self.buckets.values())
        return parameter_bytes(self.encoder) + self.sources.nbytes + self.targets.nbytes + self.values.nbytes + self.thresholds.nbytes + index_bytes


class LearnedIndexCandidate(LearnedAddressingBase):
    metadata = CandidateMetadata("learned_discrete_address_index_v1", "learned_addressing", "Learned binary address with bounded verification and fallback.")


class DenseScanCandidate(LearnedAddressingBase):
    metadata = CandidateMetadata("source_identical_dense_scan_v1", "learned_addressing_ablation", "Same learned representation with dense access.")
    access = "dense"


class FrozenIndexCandidate(LearnedAddressingBase):
    metadata = CandidateMetadata("source_identical_frozen_encoder_index_v1", "learned_addressing_ablation", "Same bounded index with encoder learning disabled.")
    learning = "frozen"


class ShuffledIndexCandidate(LearnedAddressingBase):
    metadata = CandidateMetadata("source_identical_shuffled_representation_index_v1", "learned_addressing_ablation", "Same bounded index trained on preregistered shuffled view pairs.")
    learning = "shuffled"


class Candidate(LearnedIndexCandidate):
    pass
