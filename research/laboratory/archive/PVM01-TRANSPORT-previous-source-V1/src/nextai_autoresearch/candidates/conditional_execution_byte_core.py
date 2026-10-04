from __future__ import annotations

from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..repository_sequence_contract import ByteContext, CompressionTraining


ALPHABET = 256
FEATURE_DIM = 8
FEATURES = FEATURE_DIM + 1
EXPERTS = 4
ACTIVE = 2
EXPERT_LR = 0.05
ROUTER_LR = 0.01
SEED_SALT = 0x43455831


class Candidate(CandidateBase):
    ROLE = "learned_conditional_execution_byte"
    ACTIVE_EXPERTS = ACTIVE
    LEARN_ROUTER = True

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        rng = np.random.Generator(np.random.PCG64(int(seed) ^ SEED_SALT))
        self.embedding = rng.choice((-1.0, 1.0), (ALPHABET, FEATURE_DIM)).astype(np.float32)
        self.embedding /= np.sqrt(FEATURE_DIM)
        self.router = rng.normal(0.0, 0.05, (FEATURES, EXPERTS)).astype(np.float32)
        self.expert = np.zeros((EXPERTS, FEATURES, ALPHABET), dtype=np.float32)
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0
        self.metadata = CandidateMetadata(
            self.ROLE, "byte_compression", "anonymous source-identical conditional execution"
        )

    @staticmethod
    def _softmax(values: np.ndarray) -> np.ndarray:
        shifted = values - values.max(axis=-1, keepdims=True)
        answer = np.exp(shifted)
        return answer / answer.sum(axis=-1, keepdims=True)

    def _features(self, history: tuple[int, ...] | list[int]) -> np.ndarray:
        features = np.empty(FEATURES, dtype=np.float32)
        features[0] = 1.0
        features[1:] = self.embedding[np.asarray(history, dtype=np.int16)].mean(axis=0)
        return features

    def _forward(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        router_logits = features @ self.router
        if self.ACTIVE_EXPERTS == EXPERTS:
            active = np.arange(EXPERTS)
        else:
            active = np.argsort(router_logits, kind="stable")[-self.ACTIVE_EXPERTS:]
        gates = self._softmax(router_logits[active][None, :])[0]
        logits = np.einsum("f,efa->ea", features, self.expert[active])
        probabilities = self._softmax(logits)
        mixture = gates @ probabilities
        return active, gates, probabilities, mixture

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, CompressionTraining):
            raise TypeError("conditional execution requires CompressionTraining")
        self.fit_ops = 0
        depth = max(1, int(max_depth))
        for item in facts.train_files:
            data = item.data
            for index in range(1, len(data)):
                history = data[max(0, index - depth):index]
                features = self._features(history)
                active, gates, probabilities, _ = self._forward(features)
                target = int(data[index])
                losses = -np.log(np.maximum(probabilities[:, target], 1e-12))
                router_gradient = gates * (losses - float(gates @ losses))
                router_delta = np.outer(features, router_gradient).astype(np.float32)
                for local, expert_index in enumerate(active):
                    residual = probabilities[local].copy()
                    residual[target] -= 1.0
                    self.expert[expert_index] -= (
                        EXPERT_LR * gates[local] * np.outer(features, residual)
                    ).astype(np.float32)
                if self.LEARN_ROUTER:
                    self.router[:, active] -= ROUTER_LR * router_delta
                count = len(active)
                self.fit_ops += len(history) * FEATURE_DIM + 2 * FEATURES * EXPERTS
                self.fit_ops += count * (2 * FEATURES * ALPHABET + 5 * ALPHABET)
                self.fit_ops += 4 * count + 2 * FEATURES * count
        self.meta_fit_ops = self.fit_ops

    def query(self, source: Any, steps: int) -> list[float]:
        if not isinstance(source, ByteContext):
            raise TypeError("conditional execution requires ByteContext")
        features = self._features(source.history)
        active, _, _, mixture = self._forward(features)
        count = len(active)
        self.last_ops = (
            len(source.history) * FEATURE_DIM + 2 * FEATURES * EXPERTS
            + count * (2 * FEATURES * ALPHABET + 5 * ALPHABET)
        )
        self.last_bytes_touched = (
            len(source.history) * FEATURE_DIM * 4 + self.router.nbytes
            + count * FEATURES * ALPHABET * 4
        )
        return mixture.astype(np.float64).tolist()

    def update(self, source: Any, target: int) -> None:
        if not isinstance(source, ByteContext):
            raise TypeError("conditional execution requires ByteContext")
        self.update_ops = self.last_update_bytes = 0

    def state_bytes(self) -> int:
        return int(self.embedding.nbytes + self.router.nbytes + self.expert.nbytes)
