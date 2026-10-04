from __future__ import annotations

import math
from typing import Any

import numpy as np

from .base import CandidateBase, CandidateMetadata
from ..masked_refinement_contract import MASK, MaskedQuery, MaskedTraining


ALPHABET = 256
RANK = 2
DOUBLED = RANK * RANK
FLOOR = 1e-12
NORM_FLOOR = 1e-30


def _normalized(matrix: np.ndarray) -> np.ndarray:
    return matrix / max(float(np.linalg.norm(matrix)), NORM_FLOOR)


class _OrderedTree:
    def __init__(self, matrices: list[np.ndarray]) -> None:
        self.length = len(matrices)
        self.size = 1 << max(0, (self.length - 1).bit_length())
        identity = np.eye(DOUBLED, dtype=np.float64)
        self.nodes = [identity.copy() for _ in range(2 * self.size)]
        for index, matrix in enumerate(matrices):
            self.nodes[self.size + index] = _normalized(matrix)
        for index in range(self.size - 1, 0, -1):
            self.nodes[index] = _normalized(
                self.nodes[2 * index] @ self.nodes[2 * index + 1]
            )

    def product(self, start: int, stop: int) -> np.ndarray:
        left = right = np.eye(DOUBLED, dtype=np.float64)
        start += self.size
        stop += self.size
        while start < stop:
            if start & 1:
                left = _normalized(left @ self.nodes[start])
                start += 1
            if stop & 1:
                stop -= 1
                right = _normalized(self.nodes[stop] @ right)
            start //= 2
            stop //= 2
        return _normalized(left @ right)


class Candidate(CandidateBase):
    ROLE = "parallel_born_mps_masked_byte"
    LEARN_TENSOR = True
    PARALLEL_CONTRACTION = True

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata(self.ROLE, "masked_byte", self.ROLE)
        scale = math.sqrt(1.0 / ALPHABET)
        self.tensor = np.repeat(
            (scale * np.eye(RANK, dtype=np.float64))[None, :, :], ALPHABET, axis=0
        )
        boundary = np.ones(RANK, dtype=np.float64) / math.sqrt(RANK)
        self.boundary = np.kron(boundary, boundary)
        self.fit_ops = self.meta_fit_ops = 0
        self.last_bytes_touched = 0
        self.last_critical_path_steps = 1
        self._refresh_transfers()

    def _refresh_transfers(self) -> None:
        self.transfers = np.einsum(
            "xij,xkl->xikjl", self.tensor, self.tensor
        ).reshape(ALPHABET, DOUBLED, DOUBLED)
        self.mask_transfer = self.transfers.sum(axis=0)

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("Born-MPS requires MaskedTraining")
        unigram = np.ones(ALPHABET, dtype=np.float64)
        bigram = np.ones((ALPHABET, ALPHABET), dtype=np.float64)
        scanned = pairs = 0
        for item in facts.train_files:
            data = np.asarray(item.data, dtype=np.int16)
            np.add.at(unigram, data, 1.0)
            scanned += len(data)
            if len(data) > 1:
                np.add.at(bigram, (data[:-1], data[1:]), 1.0)
                pairs += len(data) - 1
        probability = unigram / unigram.sum()
        joint = bigram / bigram.sum()
        centered = joint - np.outer(probability, probability)
        left, singular, right = np.linalg.svd(centered, full_matrices=False)
        pivot = int(np.argmax(np.abs(left[:, 0])))
        sign = 1.0 if left[pivot, 0] >= 0 else -1.0
        factor = math.sqrt(float(singular[0]))
        learned = np.zeros_like(self.tensor)
        learned[:, 0, 0] = np.sqrt(probability)
        learned[:, 1, 1] = np.sqrt(probability)
        learned[:, 0, 1] = sign * factor * left[:, 0]
        learned[:, 1, 0] = sign * factor * right[0, :]
        if self.LEARN_TENSOR:
            self.tensor = learned
        self._refresh_transfers()
        self.fit_ops = int(
            scanned + pairs + ALPHABET * ALPHABET * 3
            + 8 * ALPHABET ** 3 + ALPHABET * RANK * RANK * 4
        )
        self.meta_fit_ops = self.fit_ops

    def _sequential_environments(
        self, matrices: list[np.ndarray]
    ) -> tuple[list[np.ndarray], list[np.ndarray]]:
        length = len(matrices)
        prefix = [np.eye(DOUBLED, dtype=np.float64)]
        for matrix in matrices:
            prefix.append(_normalized(prefix[-1] @ matrix))
        suffix = [np.eye(DOUBLED, dtype=np.float64) for _ in range(length + 1)]
        for index in range(length - 1, -1, -1):
            suffix[index] = _normalized(matrices[index] @ suffix[index + 1])
        return prefix, suffix

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, MaskedQuery):
            raise TypeError("Born-MPS requires MaskedQuery")
        matrices = [
            self.mask_transfer if token == MASK else self.transfers[token]
            for token in source.snapshot
        ]
        tree = _OrderedTree(matrices) if self.PARALLEL_CONTRACTION else None
        environments = None if tree else self._sequential_environments(matrices)
        output: list[list[float]] = []
        for position in source.masked_positions:
            if tree is not None:
                left_matrix = tree.product(0, position)
                right_matrix = tree.product(position + 1, len(matrices))
            else:
                assert environments is not None
                left_matrix = environments[0][position]
                right_matrix = environments[1][position + 1]
            left = self.boundary @ left_matrix
            right = right_matrix @ self.boundary
            scores = np.einsum("i,xij,j->x", left, self.transfers, right)
            scores = np.maximum(scores, 0.0)
            probabilities = (
                scores / scores.sum() if scores.sum() > 0
                else np.full(ALPHABET, 1.0 / ALPHABET)
            )
            probabilities += FLOOR
            output.append((probabilities / probabilities.sum()).tolist())
        length = len(matrices)
        masked = len(source.masked_positions)
        levels = max(1, math.ceil(math.log2(max(2, length))))
        products = (
            (2 * len(tree.nodes) + 4 * masked * levels)
            if self.PARALLEL_CONTRACTION else 2 * length
        )
        self.last_ops = int(
            products * 2 * DOUBLED ** 3
            + masked * ALPHABET * (2 * DOUBLED ** 2 + 3)
        )
        self.last_bytes_touched = int(
            (products * DOUBLED ** 2 + masked * ALPHABET * DOUBLED ** 2) * 8
        )
        self.last_critical_path_steps = (
            2 * levels + 3 if self.PARALLEL_CONTRACTION else 2 * length + 3
        )
        return output

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return int(
            self.tensor.nbytes + self.transfers.nbytes
            + self.mask_transfer.nbytes + self.boundary.nbytes + 512
        )
