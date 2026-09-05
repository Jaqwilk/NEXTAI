from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.tensor_baseline_core import _rls_weights


def _scalar_reference(design: np.ndarray, values: np.ndarray, visible: np.ndarray) -> np.ndarray:
    weights = np.zeros((design.shape[1], values.shape[1]))
    for target in range(values.shape[1]):
        precision = np.eye(design.shape[1]) * 1000.0
        for row, value in zip(design[visible[:, target]], values[visible[:, target], target]):
            gain = precision @ row / (1.0 + row @ precision @ row)
            weights[:, target] += gain * (value - row @ weights[:, target])
            precision -= np.outer(gain, row @ precision)
    return weights


def test_grouped_rls_matches_original_scalar_recurrence_with_mixed_masks() -> None:
    rng = np.random.default_rng(1103)
    design = np.column_stack((np.ones(96), rng.normal(size=(96, 8))))
    values = rng.normal(size=(96, 7))
    visible = np.zeros((96, 7), dtype=bool)
    visible[:, :3] = True
    visible[::2, 3:5] = True
    visible[1::3, 5:] = True
    expected = _scalar_reference(design, values, visible)
    actual = _rls_weights(design, values, visible)
    assert np.array_equal(actual, expected)
