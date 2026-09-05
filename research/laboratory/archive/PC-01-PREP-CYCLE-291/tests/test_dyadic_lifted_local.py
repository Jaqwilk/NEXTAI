import math

import numpy as np

from nextai_autoresearch.benchmarks import continuous_local_cellular_v1 as bench
from nextai_autoresearch.candidates.dyadic_lifted_local_core import (
    INPUT_WIDTH, LIFT_WIDTH, MAX_POWER, OUTPUT_BOUND, RIDGE, UPDATE_ETA,
    DyadicLiftedLocal, lift,
)
from nextai_autoresearch.candidates.learned_dyadic_lifted_local_propagator import Candidate as Dyadic
from nextai_autoresearch.candidates.source_identical_frozen_lift_dyadic_local_propagator import Candidate as Frozen
from nextai_autoresearch.candidates.source_identical_sequential_lifted_local_propagator import Candidate as Sequential


def _transform(vector, permutation, signs):
    return tuple(signs[index] * vector[source] for index, source in enumerate(permutation))


def test_all_roles_share_exact_core_constants_and_shapes() -> None:
    roles = (Dyadic(1), Sequential(1), Frozen(1))
    assert all(isinstance(role, DyadicLiftedLocal) for role in roles)
    assert [role.mode for role in roles] == ["dyadic", "sequential", "frozen"]
    assert (LIFT_WIDTH, INPUT_WIDTH, MAX_POWER) == (14, 42, 16)
    assert (RIDGE, UPDATE_ETA, OUTPUT_BOUND) == (0.001, 0.01, 1.5)
    assert all(role.weights.shape == (42, 14) for role in roles)
    assert np.array_equal(lift((0.0,) * 4), np.zeros(14))


def test_dyadic_and_sequential_are_same_operator_at_every_scored_depth() -> None:
    world = bench.make_world(1103)
    dyadic, sequential = Dyadic(1), Sequential(1)
    dyadic.fit(world.training, 64, 16)
    sequential.fit(world.training, 64, 16)
    assert np.allclose(dyadic.weights, sequential.weights)
    for depth in (4, 8, 16):
        task = bench.make_task(world, 64, depth, 2207, 3)
        assert np.allclose(dyadic.query(task, depth), sequential.query(task, depth), atol=1e-10)
        assert dyadic.last_ops < sequential.last_ops


def test_fit_and_query_commute_with_signed_channel_permutation() -> None:
    world = bench.make_world(1103)
    permutation, signs = (2, 0, 3, 1), (-1, 1, -1, 1)
    rows = tuple(bench.Transition(*(
        _transform(getattr(row, field), permutation, signs)
        for field in ("left", "center", "right", "target")
    )) for row in world.training)
    original, transformed = Dyadic(1), Dyadic(1)
    original.fit(world.training, 64, 16)
    transformed.fit(rows, 64, 16)
    task = bench.make_task(world, 64, 8, 3301, 2)
    changed = bench.Task(task.size, task.source, task.target, tuple(
        (position, _transform(vector, permutation, signs)) for position, vector in task.initial
    ))
    expected = _transform(original.query(task, 8), permutation, signs)
    assert np.allclose(transformed.query(changed, 8), expected, atol=1e-8)


def test_frozen_center_identity_and_updates_are_finite_and_local() -> None:
    world = bench.make_world(1103)
    candidate = Frozen(1)
    candidate.fit(world.training, 64, 16)
    task = bench.Task(64, 7, 7, ((7, (0.2, -0.4, 0.6, -0.8)),))
    assert np.allclose(candidate.query(task, 16), task.initial[0][1])
    before = candidate.weights.copy()
    candidate.update(world.training[-1], None)
    assert np.array_equal(candidate.weights, before)
    assert candidate.fit_ops > 0 and candidate.update_ops > 0
    assert all(math.isfinite(value) and abs(value) <= OUTPUT_BOUND for value in candidate.query(task, 16))


def test_dyadic_query_work_is_independent_of_dormant_ring_size() -> None:
    world = bench.make_world(1103)
    candidate = Dyadic(1)
    candidate.fit(world.training, 64, 16)
    work = []
    for size in (64, 256, 1024):
        candidate.query(bench.make_task(world, size, 16, 4409, 0), 16)
        work.append(candidate.last_ops)
    assert work[0] == work[1] == work[2]
