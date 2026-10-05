from __future__ import annotations

from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..masked_refinement_contract import MASK, MaskedQuery, MaskedTraining


ALPHABET = 256
PATCH = 16
LATENT = 32
ACTIVE = 4
LEARNING_RATE = 0.025
SEED_SALT = 0x4C504331


class Candidate(CandidateBase):
    ROLE = "local_sparse_predictive_code_masked_byte"
    LEARN_CODE = True

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata(self.ROLE, "masked_byte", self.ROLE)
        rng = np.random.Generator(np.random.PCG64(int(seed) ^ SEED_SALT))
        self.code = rng.normal(0.0, 0.05, (LATENT, PATCH, ALPHABET)).astype(np.float32)
        self._normalize(self.code)
        self.meta_fit_ops = 0
        self.last_bytes_touched = 0
        self.last_critical_path_steps = 1

    @staticmethod
    def _normalize(rows: np.ndarray) -> None:
        flat = rows.reshape(rows.shape[0], -1)
        flat /= np.maximum(np.linalg.norm(flat, axis=1, keepdims=True), 1e-12)

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - logits.max(axis=-1, keepdims=True)
        values = np.exp(shifted)
        return values / values.sum(axis=-1, keepdims=True)

    def _active(self, patch: np.ndarray, visible: np.ndarray) -> np.ndarray:
        positions = np.flatnonzero(visible)
        scores = self.code[:, positions, patch[positions]].sum(axis=1)
        return np.argsort(scores, kind="stable")[-ACTIVE:]

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("sparse predictive code requires MaskedTraining")
        self.fit_ops = 0
        positions = np.arange(PATCH)
        for item in facts.train_files:
            data = np.asarray(item.data, dtype=np.int16)
            for start in range(0, len(data) - PATCH + 1, PATCH):
                patch = data[start:start + PATCH]
                active = self._active(patch, np.ones(PATCH, dtype=bool))
                logits = self.code[active].mean(axis=0)
                residual = -self._softmax(logits)
                residual[positions, patch] += 1.0
                proposed = self.code[active] + (LEARNING_RATE / ACTIVE) * residual
                self._normalize(proposed)
                if self.LEARN_CODE:
                    self.code[active] = proposed
                self.fit_ops += LATENT * PATCH + PATCH * ACTIVE * ALPHABET
                self.fit_ops += PATCH * ALPHABET * 4 + ACTIVE * PATCH * ALPHABET * 3
        self.meta_fit_ops = self.fit_ops

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, MaskedQuery):
            raise TypeError("sparse predictive code requires MaskedQuery")
        snapshot = np.asarray(source.snapshot, dtype=np.int16)
        outputs: list[list[float]] = []
        touched = operations = 0
        for position in source.masked_positions:
            start = min(max(0, position - PATCH // 2), len(snapshot) - PATCH)
            patch = snapshot[start:start + PATCH]
            visible = patch != MASK
            safe = np.where(visible, patch, 0)
            active = self._active(safe, visible)
            local = position - start
            distribution = self._softmax(self.code[active, local].mean(axis=0))
            outputs.append(distribution.astype(np.float64).tolist())
            operations += LATENT * int(visible.sum()) + ACTIVE * ALPHABET + 4 * ALPHABET
            touched += LATENT * int(visible.sum()) * 4 + ACTIVE * ALPHABET * 4
        self.last_ops = operations
        self.last_bytes_touched = touched
        self.last_critical_path_steps = 4
        return outputs

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return int(self.code.nbytes + 512)
