from __future__ import annotations

import numpy as np

from .tensor_indexed_local_operator_core import (
    BUCKET_CAP, BUCKET_COUNT, CODE_BITS, IndexedLocalOperator, _canonical, _operator, _order,
)
from ..three_family_tensor_contract import Tensor, Training


REPRESENTATION_RIDGE = 0.125


def _features(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    key = np.where(np.isfinite(_canonical(x, mask)), _canonical(x, mask), 0.0)
    return np.column_stack((key, np.square(key)))


def _moments(y: np.ndarray, mask: np.ndarray) -> np.ndarray:
    result = np.zeros((len(y), CODE_BITS), dtype=np.float64)
    for index, (row, visible) in enumerate(zip(y, mask)):
        values = row[visible]
        if len(values):
            result[index] = (
                values.mean(), np.square(values).mean(), np.power(values, 3).mean(),
                values.min(), values.max(),
            )
    return result


class Candidate(IndexedLocalOperator):
    """Five-bit future-predictive code with fixed-cap local operator lookup."""

    def __init__(self, seed: int) -> None:
        super().__init__(seed, "random")
        self.variant = "learned"

    def _bucket(self, row: np.ndarray, mask: np.ndarray, model: dict[str, object]) -> int:
        feature = _features(row[None, :], mask[None, :])[0]
        bits = np.asarray(model["projection"]) @ np.r_[1.0, feature] >= 0.0
        return int(sum((1 << index) for index, value in enumerate(bits) if value))

    def _build(self, x: np.ndarray, y: np.ndarray,
               xm: np.ndarray, ym: np.ndarray) -> dict[str, object]:
        order = _order(x, xm, y, ym) if len(x) else np.empty(0, dtype=int)
        feature = _features(x, xm)
        design = np.column_stack((np.ones(len(x)), feature))
        target = _moments(y, ym)
        if len(x):
            gram = design.T @ design + REPRESENTATION_RIDGE * np.eye(design.shape[1])
            projection = np.linalg.solve(gram, design.T @ target).T
            self.fit_ops += float(
                len(x) * (32 + 5 * 32 + 2 * 65 * 65 + 2 * 65 * CODE_BITS)
                + 65 ** 3
            )
        else:
            projection = np.zeros((CODE_BITS, 65), dtype=np.float64)
        model: dict[str, object] = {
            "prototypes": np.empty((0, 32), dtype=np.float64),
            "prototype_masks": np.empty((0, 32), dtype=bool),
            "projection": projection,
            "buckets": [],
        }
        assignments = np.array([self._bucket(x[index], xm[index], model) for index in order])
        buckets = []
        for bucket in range(BUCKET_COUNT):
            chosen = order[assignments == bucket][:BUCKET_CAP]
            bx, by, bxm, bym = x[chosen], y[chosen], xm[chosen], ym[chosen]
            buckets.append({
                "x": bx, "y": by, "xm": bxm, "ym": bym,
                "weights": _operator(bx, by, bxm, bym),
            })
            self.fit_ops += float(len(chosen) * 33 * 32 * 2)
        model["buckets"] = buckets
        return model

    def adapt(self, support_input: Tensor, support_target: Tensor) -> dict[str, object]:
        model = super().adapt(support_input, support_target)
        self.adaptation_ops += float(len(support_input.values) * (32 + 2 * 65 * CODE_BITS))
        return model

    def predict(self, session: dict[str, object], history: Tensor,
                future_public: Tensor) -> np.ndarray:
        output = super().predict(session, history, future_public)
        self.last_ops += float(50 * (32 + 65 * CODE_BITS))
        return output
