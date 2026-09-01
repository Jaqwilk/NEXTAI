from __future__ import annotations

import inspect

import numpy as np

from nextai_autoresearch.candidates import invariant_residual_module_core as core
from nextai_autoresearch.candidates.frozen_partition_invariant_residual_module_v1 import Candidate as Frozen
from nextai_autoresearch.candidates.pooled_without_invariance_residual_module_v1 import Candidate as Pooled
from nextai_autoresearch.candidates.shared_invariant_residual_module_v1 import Candidate as Shared
from nextai_autoresearch.three_family_tensor_contract import Training, World, pad


def _world(slot: int, matrix: np.ndarray | None = None) -> World:
    x = np.linspace(-1.0, 1.0, 108)
    values = np.column_stack((x, np.sin(1.7 * x)))
    transform = np.asarray(matrix if matrix is not None else [[1.2, 0.1], [-0.2, 0.8]])
    targets = values @ transform.T
    history = np.tile(values[-1], (32, 1))
    return World(slot, pad(values, 108), pad(targets, 108), pad(history, 32),
                 pad(np.empty((50, 0)), 50), pad(np.zeros((50, 2)), 50))


def test_invariant_gate_requires_three_environments_while_pooled_keeps_singleton() -> None:
    stable = np.array([0.4, 0.0, -0.5])
    singleton = np.array([-0.8, 0.8, 1.0])
    records = [
        (stable.copy(), environment, 0, 0, 0.1) for environment in range(3)
    ] + [(singleton, 0, 1, 0, 0.2)]
    invariant, _ = core._learn_prototypes(records, 3, "invariant")
    pooled, _ = core._learn_prototypes(records, 3, "pooled")
    assert invariant.shape == (1, 3)
    assert pooled.shape == (2, 3)
    assert np.allclose(invariant[0], stable)


def test_frozen_partition_is_data_independent_and_exact() -> None:
    first, second = Frozen(1), Frozen(999)
    first.fit(Training((_world(10),)))
    second.fit(Training((_world(900), _world(901, [[-1, 0], [0, 1]]))))
    assert np.array_equal(first.prototypes, second.prototypes)
    assert first.prototypes.shape == (9, 3)
    assert first.fit_ops > 0 and second.fit_ops > first.fit_ops


def test_slots_and_world_order_do_not_change_learned_prototypes() -> None:
    worlds = (_world(1), _world(2), _world(3))
    relabeled = tuple(_world(800 + index) for index in reversed(range(3)))
    first, second = Shared(7), Shared(7)
    first.fit(Training(worlds))
    second.fit(Training(relabeled))
    assert np.allclose(first.prototypes, second.prototypes)
    assert ".slot" not in inspect.getsource(core)


def test_consistent_channel_permutation_commutes_with_adaptation_and_prediction() -> None:
    worlds = (_world(1), _world(2), _world(3))
    candidate = Pooled(3)
    candidate.fit(Training(worlds))
    base = worlds[0]
    prediction = candidate.predict(
        candidate.adapt(base.support_input, base.support_target), base.history, base.future_public
    )[:, :2]
    permutation = np.array([1, 0])
    permuted = World(
        77,
        pad(base.support_input.values[:, :2][:, permutation], 108),
        pad(base.support_target.values[:, :2][:, permutation], 108),
        pad(base.history.values[:, :2][:, permutation], 32),
        base.future_public,
        base.output,
    )
    permuted_prediction = candidate.predict(
        candidate.adapt(permuted.support_input, permuted.support_target),
        permuted.history,
        permuted.future_public,
    )[:, :2]
    assert np.allclose(prediction[:, permutation], permuted_prediction, atol=1e-5)


def test_all_modes_share_constants_and_account_finite_bounded_work() -> None:
    world = _world(1)
    for candidate in (Shared(5), Pooled(5), Frozen(5)):
        assert candidate.CONSTANTS == Shared.CONSTANTS
        candidate.fit(Training((world, world, world)))
        session = candidate.adapt(world.support_input, world.support_target)
        predicted = candidate.predict(session, world.history, world.future_public)
        assert predicted.shape == (50, 32)
        assert np.isfinite(predicted).all()
        assert np.max(np.abs(predicted)) <= core.OUTPUT_CLIP
        assert candidate.fit_ops > 0
        assert candidate.adaptation_ops > 0
        assert candidate.last_ops > 0
        assert candidate.last_bytes_touched > 0
        assert 0 < candidate.state_bytes() < 67_108_864
