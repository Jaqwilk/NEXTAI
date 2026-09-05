from __future__ import annotations

from typing import Any, Iterator

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..repository_sequence_contract import ByteContext, CompressionTraining


CONTEXT = 64
INPUT = 128
HIDDEN = 8
LABELS = 256
BATCH = 128
LEARNING_RATE = 0.02
GOODNESS_THRESHOLD = 0.5
INIT_SCALE = 0.05
INIT_XOR = 0x46465744


def _features(history: tuple[int, ...]) -> np.ndarray:
    values = history[-CONTEXT:]
    size = len(values)
    output = np.zeros(INPUT, dtype=np.float32)
    if size:
        output[CONTEXT - size:CONTEXT] = np.asarray(values, dtype=np.float32) / 255.0
        output[INPUT - size:INPUT] = 1.0
    return output


def _wrong_label(history: tuple[int, ...], target: int) -> int:
    return (int(target) + 1 + ((sum(history) + 17 * len(history)) % 255)) % LABELS


class GoodnessByteLearner(CandidateBase):
    ROLE = "frozen"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        rng = np.random.default_rng(int(seed) ^ INIT_XOR)
        self.w1 = rng.normal(0.0, INIT_SCALE, (INPUT, HIDDEN)).astype(np.float32)
        self.labels = rng.normal(0.0, INIT_SCALE, (LABELS, HIDDEN)).astype(np.float32)
        self.b1 = np.zeros(HIDDEN, dtype=np.float32)
        self.w2 = rng.normal(0.0, INIT_SCALE, (HIDDEN, HIDDEN)).astype(np.float32)
        self.b2 = np.zeros(HIDDEN, dtype=np.float32)
        self.metadata = CandidateMetadata(self.ROLE, "byte_compression", "source-identical goodness byte learner")
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0

    @staticmethod
    def _batches(facts: CompressionTraining) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray]]:
        features: list[np.ndarray] = []
        targets: list[int] = []
        wrong: list[int] = []
        for item in facts.train_files:
            history: tuple[int, ...] = ()
            for target in item.data:
                public = history[-CONTEXT:]
                features.append(_features(public))
                targets.append(int(target))
                wrong.append(_wrong_label(public, int(target)))
                history = (*public, int(target))
                if len(features) == BATCH:
                    yield np.stack(features), np.asarray(targets), np.asarray(wrong)
                    features, targets, wrong = [], [], []
        if features:
            yield np.stack(features), np.asarray(targets), np.asarray(wrong)

    @staticmethod
    def _sigmoid(value: np.ndarray) -> np.ndarray:
        clipped = np.clip(value, -30.0, 30.0)
        return 1.0 / (1.0 + np.exp(-clipped))

    def _local_batch(self, x: np.ndarray, target: np.ndarray, wrong: np.ndarray) -> None:
        labels = np.concatenate((target, wrong))
        inputs = np.concatenate((x, x))
        truth = np.concatenate((np.ones(len(target)), np.zeros(len(target)))).astype(np.float32)
        h1 = np.tanh(inputs @ self.w1 + self.labels[labels] + self.b1)
        g1 = np.mean(h1 * h1, axis=1) - GOODNESS_THRESHOLD
        dz1 = ((self._sigmoid(g1) - truth)[:, None] / len(labels)) * (
            (2.0 * h1 / HIDDEN) * (1.0 - h1 * h1)
        )
        self.w1 -= LEARNING_RATE * (inputs.T @ dz1)
        self.b1 -= LEARNING_RATE * dz1.sum(axis=0)
        label_gradient = np.zeros_like(self.labels)
        np.add.at(label_gradient, labels, dz1)
        self.labels -= LEARNING_RATE * label_gradient

        h1 = np.tanh(inputs @ self.w1 + self.labels[labels] + self.b1)
        h2 = np.tanh(h1 @ self.w2 + self.b2)
        g2 = np.mean(h2 * h2, axis=1) - GOODNESS_THRESHOLD
        dz2 = ((self._sigmoid(g2) - truth)[:, None] / len(labels)) * (
            (2.0 * h2 / HIDDEN) * (1.0 - h2 * h2)
        )
        self.w2 -= LEARNING_RATE * (h1.T @ dz2)
        self.b2 -= LEARNING_RATE * dz2.sum(axis=0)
        self.fit_ops += len(labels) * (INPUT * HIDDEN * 3 + HIDDEN * HIDDEN * 3)

    def _global_batch(self, x: np.ndarray, target: np.ndarray) -> None:
        base = x @ self.w1 + self.b1
        h1 = np.tanh(base[:, None, :] + self.labels[None, :, :])
        h2 = np.tanh(h1 @ self.w2 + self.b2)
        score = np.mean(h1 * h1, axis=2) + np.mean(h2 * h2, axis=2)
        score -= score.max(axis=1, keepdims=True)
        probabilities = np.exp(score)
        probabilities /= probabilities.sum(axis=1, keepdims=True)
        probabilities[np.arange(len(target)), target] -= 1.0
        ds = probabilities / len(target)
        dh2 = ds[:, :, None] * (2.0 * h2 / HIDDEN)
        dz2 = dh2 * (1.0 - h2 * h2)
        dh1 = ds[:, :, None] * (2.0 * h1 / HIDDEN) + dz2 @ self.w2.T
        dz1 = dh1 * (1.0 - h1 * h1)
        self.w2 -= LEARNING_RATE * np.einsum("bli,blj->ij", h1, dz2)
        self.b2 -= LEARNING_RATE * dz2.sum(axis=(0, 1))
        summed = dz1.sum(axis=1)
        self.w1 -= LEARNING_RATE * (x.T @ summed)
        self.b1 -= LEARNING_RATE * summed.sum(axis=0)
        self.labels -= LEARNING_RATE * dz1.sum(axis=0)
        self.fit_ops += len(target) * LABELS * (
            INPUT * HIDDEN * 3 + HIDDEN * HIDDEN * 3
        )

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, CompressionTraining):
            raise TypeError("goodness learner requires CompressionTraining")
        self.fit_ops = 0
        for x, target, wrong in self._batches(facts):
            self.fit_ops += len(target) * INPUT
            if self.ROLE == "layer_local":
                self._local_batch(x, target, wrong)
            elif self.ROLE == "global_credit":
                self._global_batch(x, target)
        self.meta_fit_ops = self.fit_ops

    def query(self, source: Any, steps: int) -> list[float]:
        if not isinstance(source, ByteContext):
            raise TypeError("goodness learner requires ByteContext")
        x = _features(source.history)
        h1 = np.tanh(x @ self.w1 + self.b1 + self.labels)
        h2 = np.tanh(h1 @ self.w2 + self.b2)
        scores = np.mean(h1 * h1, axis=1) + np.mean(h2 * h2, axis=1)
        scores -= scores.max()
        probabilities = np.exp(scores)
        probabilities /= probabilities.sum()
        self.last_ops = INPUT * HIDDEN + LABELS * (HIDDEN * HIDDEN + 5 * HIDDEN)
        self.last_bytes_touched = self.state_bytes() + INPUT * 4
        return probabilities.tolist()

    def update(self, source: ByteContext, target: int) -> None:
        self.update_ops = self.last_update_bytes = 0

    def state_bytes(self) -> int:
        return sum(value.nbytes for value in (self.w1, self.labels, self.b1, self.w2, self.b2))


class Candidate(GoodnessByteLearner):
    pass
