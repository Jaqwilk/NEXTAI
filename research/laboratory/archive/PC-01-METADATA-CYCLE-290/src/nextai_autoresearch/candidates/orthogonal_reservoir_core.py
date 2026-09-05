from __future__ import annotations

from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..repository_sequence_contract import ByteContext, CompressionTraining


WIDTH = 16
ALPHABET = 256
FEATURES = WIDTH + 1
RECURRENT_SCALE = 0.9
EMBEDDING_SCALE = 0.25
LEARNING_RATE = 0.05
INIT_XOR = 0x45534E31
TRANSITION_OPS = 2 * WIDTH * WIDTH + 3 * WIDTH
READOUT_OPS = 2 * FEATURES * ALPHABET + 4 * ALPHABET
TRAIN_STEP_OPS = READOUT_OPS + 2 * FEATURES * ALPHABET + TRANSITION_OPS


class ReservoirByteLearner(CandidateBase):
    ROLE = "reservoir"
    RHO = RECURRENT_SCALE
    TRAIN_READOUT = True

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        rng = np.random.default_rng(int(seed) ^ INIT_XOR)
        raw = rng.standard_normal((WIDTH, WIDTH))
        orthogonal, triangular = np.linalg.qr(raw)
        signs = np.where(np.diag(triangular) >= 0.0, 1.0, -1.0)
        self.recurrent = (orthogonal * signs[None, :]).astype(np.float32)
        self.embedding = rng.normal(
            0.0, EMBEDDING_SCALE, (ALPHABET, WIDTH)
        ).astype(np.float32)
        self.readout = np.zeros((FEATURES, ALPHABET), dtype=np.float32)
        self.slots: dict[int, np.ndarray] = {}
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0
        self.metadata = CandidateMetadata(
            self.ROLE, "byte_compression", "source-identical orthogonal reservoir"
        )

    def _transition(self, state: np.ndarray, byte: int) -> np.ndarray:
        return np.tanh(
            self.RHO * (state @ self.recurrent) + self.embedding[int(byte)]
        ).astype(np.float32)

    def _probabilities(self, state: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        features = np.empty(FEATURES, dtype=np.float32)
        features[0], features[1:] = 1.0, state
        logits = features @ self.readout
        logits -= float(logits.max())
        probabilities = np.exp(logits).astype(np.float32)
        probabilities /= float(probabilities.sum())
        return features, probabilities

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, CompressionTraining):
            raise TypeError("reservoir requires CompressionTraining")
        self.fit_ops = 0
        self.slots.clear()
        for item in facts.train_files:
            state = np.zeros(WIDTH, dtype=np.float32)
            for target in item.data:
                features, probabilities = self._probabilities(state)
                gradient = probabilities.copy()
                gradient[int(target)] -= 1.0
                delta = np.outer(features, gradient).astype(np.float32)
                if self.TRAIN_READOUT:
                    self.readout -= LEARNING_RATE * delta
                state = self._transition(state, int(target))
                self.fit_ops += TRAIN_STEP_OPS
        self.meta_fit_ops = self.fit_ops

    def _initial_state(self, source: ByteContext) -> tuple[np.ndarray, int]:
        state = np.zeros(WIDTH, dtype=np.float32)
        for byte in source.history:
            state = self._transition(state, int(byte))
        return state, len(source.history)

    def query(self, source: Any, steps: int) -> list[float]:
        if not isinstance(source, ByteContext):
            raise TypeError("reservoir requires ByteContext")
        folded = 0
        state = self.slots.get(source.slot)
        if state is None:
            state, folded = self._initial_state(source)
            self.slots[source.slot] = state
        _, probabilities = self._probabilities(state)
        self.last_ops = READOUT_OPS + folded * TRANSITION_OPS
        self.last_bytes_touched = (
            self.readout.nbytes + state.nbytes
            + folded * (self.recurrent.nbytes + WIDTH * 4)
        )
        return probabilities.tolist()

    def update(self, source: ByteContext, target: int) -> None:
        if not isinstance(source, ByteContext):
            raise TypeError("reservoir requires ByteContext")
        state = self.slots.get(source.slot)
        if state is None:
            state, _ = self._initial_state(source)
        self.slots[source.slot] = self._transition(state, int(target))
        self.update_ops = TRANSITION_OPS
        self.last_update_bytes = self.recurrent.nbytes + 3 * WIDTH * 4

    def state_bytes(self) -> int:
        return int(
            self.recurrent.nbytes + self.embedding.nbytes + self.readout.nbytes
            + len(self.slots) * WIDTH * 4
        )


class Candidate(ReservoirByteLearner):
    pass
