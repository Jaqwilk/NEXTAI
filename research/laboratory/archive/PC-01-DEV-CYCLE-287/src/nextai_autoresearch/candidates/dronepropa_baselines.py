from __future__ import annotations

import math

import numpy as np


RIDGE = 0.001
VARIANCE_FLOOR = 1e-6


def affine_ridge(features: np.ndarray, targets: np.ndarray, ridge: float = RIDGE) -> np.ndarray:
    x = np.column_stack((np.ones(features.shape[0]), np.asarray(features, dtype=float)))
    penalty = np.eye(x.shape[1]) * ridge
    penalty[0, 0] = 0.0
    return np.linalg.solve(x.T @ x + penalty, x.T @ np.asarray(targets, dtype=float))


def affine_predict(coefficients: np.ndarray, features: np.ndarray) -> np.ndarray:
    x = np.asarray(features, dtype=float)
    return np.column_stack((np.ones(x.shape[0]), x)) @ coefficients


class Persistence:
    def fit(self, *_: object) -> None:
        return None

    def predict(self, last_state: np.ndarray) -> np.ndarray:
        return np.asarray(last_state, dtype=float).copy()


class RidgeARX:
    def __init__(self, ridge: float = RIDGE) -> None:
        self.ridge = ridge
        self.coefficients: np.ndarray | None = None

    def fit(self, features: np.ndarray, targets: np.ndarray) -> None:
        self.coefficients = affine_ridge(features, targets, self.ridge)

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self.coefficients is None:
            raise RuntimeError("fit must precede predict")
        return affine_predict(self.coefficients, features)


class RLSARX:
    def __init__(self, dimension: int, outputs: int = 6, covariance: float = 1000.0) -> None:
        self.weights = np.zeros((dimension + 1, outputs))
        self.covariance = np.eye(dimension + 1) * covariance

    def update(self, feature: np.ndarray, target: np.ndarray) -> None:
        x = np.concatenate(([1.0], np.asarray(feature, dtype=float)))
        px = self.covariance @ x
        gain = px / (1.0 + x @ px)
        error = np.asarray(target, dtype=float) - x @ self.weights
        self.weights += np.outer(gain, error)
        self.covariance -= np.outer(gain, x) @ self.covariance

    def fit(self, features: np.ndarray, targets: np.ndarray) -> None:
        for feature, target in zip(features, targets):
            self.update(feature, target)

    def predict(self, features: np.ndarray) -> np.ndarray:
        return affine_predict(self.weights, features)


class NearestOperatorTemplate:
    def __init__(self) -> None:
        self.templates: list[np.ndarray] = []

    def fit(self, flights: list[tuple[np.ndarray, np.ndarray]]) -> None:
        self.templates = [affine_ridge(features, targets) for features, targets in flights]

    def select(self, adaptation_features: np.ndarray, adaptation_targets: np.ndarray) -> int:
        if not self.templates:
            raise RuntimeError("fit must precede select")
        operator = affine_ridge(adaptation_features, adaptation_targets)
        return min(range(len(self.templates)), key=lambda index: (float(np.square(operator - self.templates[index]).sum()), index))


class IndependentARX(RidgeARX):
    """Source-identical full ARX fitted only from the held-out adaptation prefix."""


class PooledARX(RidgeARX):
    """One no-factorization ARX fitted over pooled anonymous training examples."""


class EmpiricalGaussianJoint:
    def __init__(self, ridge: float = RIDGE) -> None:
        self.ridge = ridge
        self.mean: np.ndarray | None = None
        self.covariance: np.ndarray | None = None
        self.feature_dimension = 0

    def fit(self, features: np.ndarray, targets: np.ndarray) -> None:
        joint = np.column_stack((features, targets)).astype(float)
        self.mean = joint.mean(axis=0)
        self.covariance = np.cov(joint, rowvar=False, bias=True) + np.eye(joint.shape[1]) * self.ridge
        self.feature_dimension = features.shape[1]

    def conditional(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self.mean is None or self.covariance is None:
            raise RuntimeError("fit must precede conditional")
        d = self.feature_dimension
        sxx, sxy = self.covariance[:d, :d], self.covariance[:d, d:]
        syy = self.covariance[d:, d:]
        gain = np.linalg.solve(sxx, sxy).T
        mean = self.mean[d:] + (np.asarray(features) - self.mean[:d]) @ gain.T
        covariance = syy - gain @ sxy
        return mean, covariance


def chow_liu_tree(residuals: np.ndarray) -> tuple[tuple[int, int], ...]:
    residuals = np.asarray(residuals, dtype=float)
    correlation = np.corrcoef(residuals, rowvar=False)
    weights = -0.5 * np.log(np.maximum(1.0 - np.square(np.clip(correlation, -0.999999, 0.999999)), 1e-12))
    selected = {0}
    edges: list[tuple[int, int]] = []
    while len(selected) < residuals.shape[1]:
        candidates = [(-float(weights[parent, child]), parent, child) for parent in selected for child in range(residuals.shape[1]) if child not in selected]
        _, parent, child = min(candidates)
        edges.append((parent, child))
        selected.add(child)
    return tuple(edges)


class ContextualGaussianChowLiu(RidgeARX):
    def __init__(self) -> None:
        super().__init__()
        self.tree: tuple[tuple[int, int], ...] = ()
        self.variance = np.ones(6)

    def fit(self, features: np.ndarray, targets: np.ndarray) -> None:
        super().fit(features, targets)
        residuals = targets - self.predict(features)
        self.tree = chow_liu_tree(residuals)
        self.variance = np.maximum(residuals.var(axis=0), VARIANCE_FLOOR)

    def log_probability(self, features: np.ndarray, targets: np.ndarray) -> np.ndarray:
        residuals = np.asarray(targets) - self.predict(features)
        return -0.5 * np.sum(np.log(2 * math.pi * self.variance) + np.square(residuals) / self.variance, axis=1)


class ConditionSpecialist:
    privileged = True

    def __init__(self) -> None:
        self.models: dict[int, RidgeARX] = {}

    def fit(self, rows: list[tuple[int, np.ndarray, np.ndarray]]) -> None:
        for condition in sorted({condition for condition, _, _ in rows}):
            features = np.concatenate([x for label, x, _ in rows if label == condition])
            targets = np.concatenate([y for label, _, y in rows if label == condition])
            model = RidgeARX()
            model.fit(features, targets)
            self.models[condition] = model

    def predict(self, condition: int, features: np.ndarray) -> np.ndarray:
        return self.models[condition].predict(features)


class ConditionOracle(ConditionSpecialist):
    """Privileged same-condition upper bound, excluded from implementable Pareto sets."""


class Candidate(PooledARX):
    """Auditable default export; scored protocols use the versioned wrappers."""
