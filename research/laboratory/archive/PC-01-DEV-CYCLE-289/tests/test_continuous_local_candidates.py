import math

import numpy as np

from nextai_autoresearch.benchmarks import continuous_local_cellular_v1 as bench
from nextai_autoresearch.candidates.continuous_local_controls_core import (
    BIN_WIDTH, NEIGHBORS, KernelEvent, LocalRidge, Persistence, PrivilegedSupport, QuantizedFSM,
)
from nextai_autoresearch.candidates.continuous_local_rule_core import (
    OUTPUT_BOUND, REPAIR_Z, RIDGE, UPDATE_ETA, ContinuousLocalRule, quadratic_width,
)
from nextai_autoresearch.candidates.learned_sparse_continuous_local_rule import Candidate as Sparse
from nextai_autoresearch.candidates.source_identical_dense_continuous_local_rule import Candidate as Dense
from nextai_autoresearch.candidates.source_identical_frozen_continuous_local_rule import Candidate as Frozen


def _fit(candidate):
    world = bench.make_world(1103)
    candidate.fit(world.training, 64, 16)
    return world


def test_source_identical_roles_share_constants_and_clean_outputs() -> None:
    sparse, dense, frozen = Sparse(1), Dense(1), Frozen(1)
    assert type(sparse).__mro__[1] is type(dense).__mro__[1] is type(frozen).__mro__[1] is ContinuousLocalRule
    assert (RIDGE, REPAIR_Z, UPDATE_ETA, OUTPUT_BOUND, quadratic_width()) == (0.001, 6.0, 0.05, 1.5, 91)
    world = _fit(sparse)
    _fit(dense)
    _fit(frozen)
    assert np.array_equal(sparse.weights, dense.weights)
    task = bench.make_task(world, 64, 8, 2207, 3)
    assert np.allclose(sparse.query(task, 8), dense.query(task, 8), rtol=0, atol=1e-12)
    assert sparse.mode == "sparse" and dense.mode == "dense" and frozen.mode == "frozen"


def test_learned_consistency_repairs_a_large_single_channel_outlier() -> None:
    candidate = Sparse(1)
    world = _fit(candidate)
    clean = world.training[0].center
    errors = []
    for channel in range(4):
        damaged = list(clean)
        damaged[channel] += 0.75
        repaired = candidate._repair(tuple(damaged))
        errors.append(abs(repaired[channel] - clean[channel]))
    assert sum(errors) / len(errors) < 0.20


def test_persistence_is_a_true_no_dynamics_control() -> None:
    world = bench.make_world(1103)
    task = bench.make_task(world, 64, 4, 2207, 0)
    candidate = Persistence(1)
    candidate.fit(world.training, 64, 16)
    assert candidate.query(task, 4) == dict(task.initial).get(task.target, (0.0,) * 4)
    assert candidate.fit_ops == candidate.update_ops == 0


def test_raw_ridge_is_affine_not_quadratic() -> None:
    candidate = LocalRidge(1)
    world = _fit(candidate)
    assert candidate.weights.shape == (13, 4)
    task = bench.make_task(world, 64, 4, 2207, 1)
    assert all(math.isfinite(value) for value in candidate.query(task, 4))


def test_quantized_fsm_uses_frozen_bins_and_center_fallback() -> None:
    assert BIN_WIDTH == 0.25
    candidate = QuantizedFSM(1)
    world = _fit(candidate)
    assert candidate.key(np.zeros(12)) != candidate.key(np.full(12, 0.26))
    unknown = (9.0,) * 4
    value, _, _ = candidate._transition(unknown, unknown, unknown)
    assert value == unknown


def test_kernel_event_uses_exactly_eight_nearest_training_rows() -> None:
    assert NEIGHBORS == 8
    candidate = KernelEvent(1)
    world = _fit(candidate)
    task = bench.make_task(world, 64, 4, 2207, 2)
    answer = candidate.query(task, 4)
    assert len(answer) == 4 and all(math.isfinite(value) for value in answer)
    assert candidate.last_ops > len(world.training)


def test_privileged_support_is_exact_on_clean_and_damaged_views() -> None:
    world = bench.make_world(1103)
    candidate = PrivilegedSupport(1)
    candidate.fit(bench.PrivilegedWorld(world), 64, 16)
    clean = bench.make_task(world, 64, 8, 2207, 1)
    damaged = bench.make_task(world, 64, 8, 2207, 1, damaged=True)
    expected = bench.oracle_target(world, clean, 8)
    assert np.allclose(candidate.query(clean, 8), expected, rtol=0, atol=1e-12)
    assert np.allclose(candidate.query(damaged, 8), expected, rtol=0, atol=1e-12)


def test_all_five_mandatory_controls_complete_tiny_real_evaluator_cell() -> None:
    for name in (
        "continuous_local_persistence", "continuous_local_ridge", "continuous_local_quantized_fsm",
        "continuous_local_kernel_event", "privileged_continuous_local_support",
    ):
        row = bench.run_trial(name, 64, 4, 1, 1103, 16)
        assert row["status"] == "complete"
        assert 0.0 <= row["accuracy"] <= 1.0
        assert math.isfinite(row["normalized_rmse"])
