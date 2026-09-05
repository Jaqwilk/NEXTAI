from __future__ import annotations

import importlib

import numpy as np
import pytest

from nextai_autoresearch.candidates.orthogonal_reservoir_core import (
    ALPHABET, EMBEDDING_SCALE, FEATURES, INIT_XOR, LEARNING_RATE,
    RECURRENT_SCALE, WIDTH, ReservoirByteLearner,
)
from nextai_autoresearch.repository_sequence_contract import (
    ByteContext, ByteFile, CompressionTraining,
)


ROLES = (
    "orthogonal_reservoir_byte",
    "source_identical_no_recurrence_byte",
    "source_identical_frozen_readout_reservoir_byte",
)


def _candidate(name: str, seed: int = 17) -> ReservoirByteLearner:
    return importlib.import_module(
        f"nextai_autoresearch.candidates.{name}"
    ).Candidate(seed)


def _training() -> CompressionTraining:
    data = tuple(([1, 2, 3, 1, 2, 4] * 24))
    return CompressionTraining((ByteFile(11, data),), (), len(data))


def test_roles_share_frozen_constants_initialization_and_orthogonal_matrix() -> None:
    assert (WIDTH, FEATURES, ALPHABET) == (16, 17, 256)
    assert (RECURRENT_SCALE, EMBEDDING_SCALE, LEARNING_RATE, INIT_XOR) == (
        0.9, 0.25, 0.05, 0x45534E31,
    )
    roles = [_candidate(name) for name in ROLES]
    for field in ("recurrent", "embedding", "readout"):
        assert all(np.array_equal(getattr(roles[0], field), getattr(role, field))
                   for role in roles[1:])
    assert np.allclose(roles[0].recurrent.T @ roles[0].recurrent,
                       np.eye(WIDTH), atol=1e-6)


def test_recurrence_is_the_only_history_memory_intervention() -> None:
    recurrent, memoryless = _candidate(ROLES[0]), _candidate(ROLES[1])
    first = ByteContext(1, (9, 4, 7))
    second = ByteContext(2, (3, 8, 7))
    recurrent.query(first, 1)
    recurrent.query(second, 1)
    memoryless.query(first, 1)
    memoryless.query(second, 1)
    assert not np.array_equal(recurrent.slots[1], recurrent.slots[2])
    assert np.array_equal(memoryless.slots[1], memoryless.slots[2])


def test_readout_learning_and_frozen_ablation_are_exact() -> None:
    recurrent, memoryless, frozen = [_candidate(name, 23) for name in ROLES]
    for role in (recurrent, memoryless, frozen):
        role.fit(_training(), 8, 64)
    assert np.any(recurrent.readout != 0.0)
    assert np.any(memoryless.readout != 0.0)
    assert np.all(frozen.readout == 0.0)
    assert recurrent.fit_ops == memoryless.fit_ops == frozen.fit_ops


def test_predict_then_reveal_update_is_slot_local_and_slow_weights_are_frozen() -> None:
    candidate = _candidate(ROLES[0], 31)
    candidate.fit(_training(), 8, 64)
    slow = candidate.readout.copy()
    row = candidate.query(ByteContext(41, (1, 2, 3)), 1)
    candidate.query(ByteContext(42, (4, 5, 6)), 1)
    untouched = candidate.slots[42].copy()
    candidate.update(ByteContext(41, (1, 2, 3)), 4)
    assert len(row) == 256 and sum(row) == pytest.approx(1.0, abs=1e-6)
    assert np.array_equal(candidate.readout, slow)
    assert np.array_equal(candidate.slots[42], untouched)
    assert candidate.update_ops > 0 and candidate.last_update_bytes > 0
    assert candidate.state_bytes() < 4_194_304
