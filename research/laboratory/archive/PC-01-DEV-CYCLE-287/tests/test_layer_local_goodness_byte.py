from __future__ import annotations

import importlib

import numpy as np
import pytest

from nextai_autoresearch.candidates.layer_local_goodness_core import (
    BATCH, CONTEXT, GOODNESS_THRESHOLD, HIDDEN, INIT_SCALE, INPUT, LABELS,
    LEARNING_RATE, GoodnessByteLearner, _features, _wrong_label,
)
from nextai_autoresearch.repository_sequence_contract import (
    ByteContext, ByteFile, CompressionTraining,
)


ROLES = (
    "layer_local_goodness_byte",
    "source_identical_end_to_end_gradient_byte",
    "source_identical_frozen_hidden_byte",
)


def _training() -> CompressionTraining:
    data = tuple(([1, 2, 3, 4] * 40) + ([1, 2, 5, 4] * 40))
    return CompressionTraining((ByteFile(11, data),), (), len(data))


def test_roles_share_exact_source_constants_initialization_and_query() -> None:
    assert (CONTEXT, INPUT, HIDDEN, LABELS, BATCH) == (64, 128, 8, 256, 128)
    assert (LEARNING_RATE, GOODNESS_THRESHOLD, INIT_SCALE) == (0.02, 0.5, 0.05)
    instances = [importlib.import_module(
        f"nextai_autoresearch.candidates.{name}"
    ).Candidate(17) for name in ROLES]
    assert all(GoodnessByteLearner in type(item).mro() for item in instances)
    for name in ("w1", "labels", "b1", "w2", "b2"):
        assert all(np.array_equal(getattr(instances[0], name), getattr(item, name))
                   for item in instances[1:])
    query = ByteContext(3, (1, 2, 3, 4))
    assert instances[0].query(query, 1) == instances[1].query(query, 1)
    assert instances[0].query(query, 1) == instances[2].query(query, 1)


def test_wrong_byte_is_deterministic_public_and_never_target() -> None:
    for length in (0, 4, 16, 64):
        history = tuple(range(length))
        for target in (0, 1, 127, 255):
            observed = _wrong_label(history, target)
            expected = (target + 1 + ((sum(history) + 17 * len(history)) % 255)) % 256
            assert observed == expected and observed != target
    assert _features((1, 2, 3, 4)).shape == (128,)


def test_earlier_layer_update_does_not_read_later_layer_weights() -> None:
    left = GoodnessByteLearner(23)
    right = GoodnessByteLearner(23)
    left.ROLE = right.ROLE = "layer_local"
    right.w2[:] = 1000.0
    x = np.stack([_features((1, 2, 3, 4)), _features((4, 3, 2, 1))])
    target = np.asarray([5, 6])
    wrong = np.asarray([7, 8])
    left._local_batch(x, target, wrong)
    right._local_batch(x, target, wrong)
    assert np.array_equal(left.w1, right.w1)
    assert np.array_equal(left.labels, right.labels)
    assert np.array_equal(left.b1, right.b1)


def test_fit_roles_are_finite_matched_and_local_is_cheaper() -> None:
    candidates = [importlib.import_module(
        f"nextai_autoresearch.candidates.{name}"
    ).Candidate(31) for name in ROLES]
    for candidate in candidates:
        candidate.fit(_training(), 8, 64)
        row = candidate.query(ByteContext(91, (1, 2, 3, 4)), 1)
        assert len(row) == 256 and sum(row) == pytest.approx(1.0, abs=1e-6)
        before = candidate.state_bytes()
        candidate.update(ByteContext(91, (1, 2, 3, 4)), 5)
        assert candidate.state_bytes() == before and candidate.update_ops == 0
    assert candidates[0].fit_ops < candidates[1].fit_ops
    assert candidates[0].last_ops == candidates[1].last_ops == candidates[2].last_ops
    assert candidates[0].state_bytes() == candidates[1].state_bytes() == candidates[2].state_bytes()
