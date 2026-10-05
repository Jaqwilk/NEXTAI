from __future__ import annotations

from typing import Any

import numpy as np
import pyamg
from scipy.sparse import csr_matrix


RELAXATION_STEPS = 8
RELAXATION_WEIGHT = 2.0 / 3.0
RIDGE = 1e-3
_EPS = 1e-12


def _csr(operator: Any) -> csr_matrix:
    return csr_matrix(
        (np.asarray(operator.data), np.asarray(operator.indices),
         np.asarray(operator.indptr)), shape=operator.shape,
    )


def _standardize(values: np.ndarray) -> np.ndarray:
    centered = values - np.mean(values, axis=0, keepdims=True)
    scale = np.sqrt(np.mean(centered * centered, axis=0, keepdims=True))
    return centered / np.where(scale > _EPS, scale, 1.0)


def _unit_rms(values: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    centered = np.asarray(values, dtype=np.float64) - float(np.mean(values))
    scale = float(np.sqrt(np.mean(centered * centered)))
    if not np.isfinite(scale) or scale <= _EPS:
        centered = np.asarray(fallback, dtype=np.float64) - float(np.mean(fallback))
        scale = float(np.sqrt(np.mean(centered * centered)))
    if not np.isfinite(scale) or scale <= _EPS:
        centered = np.linspace(-1.0, 1.0, centered.size, dtype=np.float64)
        scale = float(np.sqrt(np.mean(centered * centered)))
    return centered / scale


def local_features(operator: Any) -> np.ndarray:
    matrix = _csr(operator)
    absolute = matrix.copy()
    absolute.data = np.abs(absolute.data)
    squared = matrix.copy()
    squared.data = squared.data * squared.data
    degree = np.diff(matrix.indptr).astype(np.float64)
    absolute_sum = np.asarray(absolute.sum(axis=1)).ravel()
    signed_sum = np.asarray(matrix.sum(axis=1)).ravel()
    row_l2 = np.sqrt(np.asarray(squared.sum(axis=1)).ravel())
    denominator = np.maximum(absolute_sum, _EPS)
    raw = np.column_stack((
        np.log1p(degree),
        np.log1p(absolute_sum),
        matrix.diagonal() / denominator,
        signed_sum / denominator,
        np.log1p(row_l2),
    ))
    base = _standardize(raw)
    neighbours = np.asarray(absolute @ base) / denominator[:, None]
    return np.column_stack((np.ones(matrix.shape[0]), base, neighbours))


def _label(operator: Any, features: np.ndarray) -> np.ndarray:
    matrix = _csr(operator)
    diagonal = np.asarray(matrix.diagonal(), dtype=np.float64)
    safe = np.where(np.abs(diagonal) > _EPS, diagonal, 1.0)
    values = features[:, 3] + 0.25 * features[:, 4]
    for _ in range(RELAXATION_STEPS):
        values = values - RELAXATION_WEIGHT * np.asarray(matrix @ values).ravel() / safe
    return _unit_rms(values, features[:, 1])


def _solver_size(solver: Any) -> tuple[int, int]:
    total_bytes = 0
    total_nnz = 0
    for level in solver.levels:
        for key in ("A", "P", "R"):
            value = getattr(level, key, None)
            if value is None:
                continue
            total_nnz += int(value.nnz)
            total_bytes += int(value.data.nbytes + value.indices.nbytes + value.indptr.nbytes)
    return total_bytes, total_nnz


class Candidate:
    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        self.coefficients = np.zeros(11, dtype=np.float64)
        self.fit_ops = 0.0
        self.build_ops = 0.0
        self._hierarchy_bytes = 0

    def fit(self, operators: tuple[Any, ...]) -> None:
        if not operators:
            raise ValueError("at least one source operator is required")
        normal = np.zeros((11, 11), dtype=np.float64)
        target = np.zeros(11, dtype=np.float64)
        operations = 0.0
        for operator in operators:
            matrix = _csr(operator)
            features = local_features(operator)
            label = _label(operator, features)
            rows = max(1, matrix.shape[0])
            normal += (features.T @ features) / rows
            target += (features.T @ label) / rows
            operations += (
                14.0 * matrix.nnz
                + RELAXATION_STEPS * (2.0 * matrix.nnz + 4.0 * rows)
                + 2.0 * rows * features.shape[1] * features.shape[1]
            )
        normal /= len(operators)
        target /= len(operators)
        self.coefficients = np.linalg.solve(
            normal + RIDGE * np.eye(normal.shape[0]), target,
        )
        self.fit_ops = operations + (2.0 / 3.0) * normal.shape[0] ** 3

    def candidate_vectors(self, operator: Any) -> np.ndarray:
        features = local_features(operator)
        learned = _unit_rms(features @ self.coefficients, features[:, 1])
        return np.column_stack((np.ones(features.shape[0]), learned))

    def build(self, operator: Any) -> Any:
        matrix = _csr(operator)
        vectors = self.candidate_vectors(operator)
        solver = pyamg.smoothed_aggregation_solver(
            matrix, B=vectors, symmetry="symmetric",
        )
        self._hierarchy_bytes, hierarchy_nnz = _solver_size(solver)
        self.build_ops = float(14 * matrix.nnz + matrix.shape[0] * 11 + hierarchy_nnz)
        return solver

    def state_bytes(self) -> int:
        return int(self.coefficients.nbytes + self._hierarchy_bytes)
