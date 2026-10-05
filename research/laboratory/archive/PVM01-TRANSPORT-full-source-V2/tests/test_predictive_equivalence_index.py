from __future__ import annotations

import importlib

import numpy as np

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.benchmarks.heldout_three_family_continuous_transfer_v1 import (
    FAMILIES, _assignment, build_worlds,
)
from nextai_autoresearch.config import load_config
from nextai_autoresearch.candidates.predictive_equivalence_index_core import (
    Candidate, REPRESENTATION_RIDGE,
)
from nextai_autoresearch.candidates.tensor_indexed_local_operator_core import BUCKET_CAP
from nextai_autoresearch.three_family_tensor_contract import Training, World, pad


ROLES = (
    "shared_predictive_index_v1", "independent_predictive_index_v1",
    "cross_family_only_predictive_index_v1", "support_only_predictive_index_v1",
)


def _world(scale: float = 1.0, slot: int = 1) -> World:
    x = np.linspace(-1, 1, 108, dtype=np.float32)
    support_x = np.column_stack((x, np.sin(x), np.cos(x))) * scale
    support_y = np.column_stack((x + np.square(x), x - np.square(x))) * scale
    history_x = np.linspace(-.4, .1, 32, dtype=np.float32)
    history = np.column_stack((history_x, np.sin(history_x), history_x + history_x ** 2))
    future = np.linspace(.11, .6, 50, dtype=np.float32)[:, None]
    output = np.column_stack((future[:, 0] + future[:, 0] ** 2,
                              future[:, 0] - future[:, 0] ** 2))
    return World(slot, pad(support_x, 108), pad(support_y, 108), pad(history, 32),
                 pad(future, 50), pad(output, 50))


def test_learned_code_solves_frozen_future_equivalence_counterexample() -> None:
    x = np.zeros((3, 32)); x[:, 0] = (0.0, 0.1, 2.0)
    y = np.zeros((3, 32)); y[:, 0] = (1.0, -1.0, 1.0)
    xm = np.zeros_like(x, dtype=bool); xm[:, 0] = True
    ym = np.zeros_like(y, dtype=bool); ym[:, 0] = True
    candidate = Candidate(7)
    model = candidate._build(x, y, xm, ym)
    query = np.zeros(32); query[0] = .06
    query_mask = np.zeros(32, dtype=bool); query_mask[0] = True
    codes = [candidate._bucket(row, mask, model) for row, mask in zip(x, xm)]
    assert REPRESENTATION_RIDGE == .125
    assert codes[0] == codes[2] == candidate._bucket(query, query_mask, model)
    assert codes[1] != codes[0]


def test_roles_are_source_identical_auditable_and_family_blind() -> None:
    classes = []
    for name in ROLES:
        assert audit_candidate(name, load_config()).ok
        classes.append(importlib.import_module(
            f"nextai_autoresearch.candidates.{name}"
        ).Candidate)
    assert all(Candidate in candidate.mro() for candidate in classes)


def test_world_order_channel_permutation_and_local_update_contract() -> None:
    left, right = Candidate(11), Candidate(11)
    first, second = _world(1.0, 1), _world(.7, 999)
    left.fit(Training((first, second)))
    right.fit(Training((second, first)))
    assert np.allclose(left._model["projection"], right._model["projection"])

    rng = np.random.default_rng(19)
    x, y = rng.normal(size=(40, 32)), rng.normal(size=(40, 32))
    xm, ym = np.ones_like(x, dtype=bool), np.ones_like(y, dtype=bool)
    input_order, output_order = rng.permutation(32), rng.permutation(32)
    base, permuted = Candidate(11), Candidate(11)
    base_model = base._build(x, y, xm, ym)
    permuted_model = permuted._build(
        x[:, input_order], y[:, output_order], xm[:, input_order], ym[:, output_order]
    )
    assert base._bucket(x[0], xm[0], base_model) == permuted._bucket(
        x[0, input_order], xm[0, input_order], permuted_model
    )

    global_projection = left._model["projection"].copy()
    session = left.adapt(first.support_input, first.support_target)
    assert np.array_equal(left._model["projection"], global_projection)
    assert max(len(bucket["x"]) for bucket in session["buckets"]) <= BUCKET_CAP
    assert left.state_bytes() < 67_108_864


def test_query_work_is_fixed_across_dormant_knowledge() -> None:
    world = _world()
    observed = []
    for count in (1, 4, 9):
        candidate = Candidate(23)
        candidate.fit(Training((world,) * count))
        prediction = candidate.predict(
            candidate.adapt(world.support_input, world.support_target),
            world.history, world.future_public,
        )
        assert prediction.shape == (50, 32) and np.isfinite(prediction).all()
        observed.append((candidate.last_ops, candidate.last_bytes_touched))
    assert len(set(observed)) == 1


def test_real_file_full_width_empty_bucket_fallback_is_output_safe() -> None:
    training, testing = build_worlds(4, 1, 1_500_003)
    family = "continuous_event"
    world = testing[family][0]
    assert int(world.history.mask.any(axis=0).sum()) == 32
    assert int(world.future_public.mask.any(axis=0).sum()) == 32
    assert int(world.output.mask.any(axis=0).sum()) >= 1

    roles = {"tensor_random_projection_hash_v1": "shared", **dict(zip(ROLES, (
        "shared", "independent", "cross_family_only", "support_only",
    )))}
    for name, role in roles.items():
        candidate = importlib.import_module(
            f"nextai_autoresearch.candidates.{name}"
        ).Candidate(41)
        candidate.fit(Training(_assignment(role, family, training)))
        session = candidate.adapt(world.support_input, world.support_target)
        bucket_id = candidate._bucket(
            world.history.values[-1], session["input_mask"], session
        )
        bucket = session["buckets"][bucket_id]
        for key in ("x", "y", "xm", "ym"):
            bucket[key] = bucket[key][:0]
        assert len(bucket["x"]) == 0
        prediction = candidate.predict(session, world.history, world.future_public)
        assert prediction.shape == (50, 32)
        assert np.isfinite(prediction).all()
