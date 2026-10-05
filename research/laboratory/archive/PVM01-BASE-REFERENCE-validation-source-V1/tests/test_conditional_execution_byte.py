from __future__ import annotations

import importlib

import numpy as np
import pytest

from nextai_autoresearch.candidates.conditional_execution_byte_core import (
    ACTIVE, EXPERTS, EXPERT_LR, FEATURE_DIM, ROUTER_LR, SEED_SALT,
    Candidate as ConditionalCore,
)
from nextai_autoresearch.repository_sequence_contract import (
    ByteContext, ByteFile, CompressionTraining,
)


ROLES = (
    "learned_conditional_execution_byte",
    "source_identical_all_experts_byte",
    "source_identical_frozen_router_byte",
)


def _candidate(name: str, seed: int = 17) -> ConditionalCore:
    return importlib.import_module(f"nextai_autoresearch.candidates.{name}").Candidate(seed)


def _training() -> CompressionTraining:
    data = tuple(([1, 2, 3, 1, 2, 4] * 16))
    return CompressionTraining((ByteFile(11, data),), (), len(data))


def test_roles_share_frozen_constants_and_initial_arrays() -> None:
    assert (FEATURE_DIM, EXPERTS, ACTIVE, EXPERT_LR, ROUTER_LR, SEED_SALT) == (
        8, 4, 2, 0.05, 0.01, 0x43455831,
    )
    roles = [_candidate(name) for name in ROLES]
    for field in ("embedding", "router", "expert"):
        assert all(np.array_equal(getattr(roles[0], field), getattr(role, field))
                   for role in roles[1:])
    assert all(role.__class__.__mro__[1] is ConditionalCore for role in roles)


def test_router_learning_and_frozen_ablation_are_exact() -> None:
    learned, all_experts, frozen = [_candidate(name, 23) for name in ROLES]
    initial = learned.router.copy()
    for role in (learned, all_experts, frozen):
        role.fit(_training(), 8, 16)
    assert not np.array_equal(learned.router, initial)
    assert not np.array_equal(all_experts.router, initial)
    assert np.array_equal(frozen.router, initial)
    assert learned.fit_ops == frozen.fit_ops < all_experts.fit_ops


def test_sparse_query_is_k_independent_and_cheaper_than_all_experts() -> None:
    sparse, dense = _candidate(ROLES[0]), _candidate(ROLES[1])
    query = ByteContext(41, tuple(range(16)))
    first, second = sparse.query(query, 1), dense.query(query, 1)
    assert len(first) == len(second) == 256
    assert sum(first) == pytest.approx(1.0, abs=1e-6)
    assert sparse.last_ops < 0.60 * dense.last_ops
    before = (sparse.embedding.copy(), sparse.router.copy(), sparse.expert.copy())
    sparse.update(query, 9)
    assert sparse.update_ops == 0
    assert all(np.array_equal(old, new) for old, new in zip(
        before, (sparse.embedding, sparse.router, sparse.expert)
    ))
    assert sparse.state_bytes() < 4_194_304
