from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.cross_family_only_bounded_recurrent_residual_v1 import Candidate as Cross
from nextai_autoresearch.candidates.independent_bounded_recurrent_residual_v1 import Candidate as Independent
from nextai_autoresearch.candidates.shared_bounded_recurrent_residual_v1 import (
    Candidate, RESIDUAL_BOUND, RIDGE,
)
from nextai_autoresearch.candidates.support_only_bounded_recurrent_residual_v1 import Candidate as Support
from nextai_autoresearch.three_family_tensor_contract import Training, World, pad


def _world(order=(0, 1)) -> World:
    control = np.linspace(-1, 1, 108)
    state = np.column_stack((np.sin(control), np.cos(control)))
    target = np.column_stack((state[:, 0] + .2 * control, state[:, 1] - .1 * control))
    state, target = state[:, order], target[:, order]
    history_control = np.linspace(-.5, .1, 32)
    history_state = np.column_stack((np.sin(history_control), np.cos(history_control)))[:, order]
    future = np.linspace(.11, .6, 50)[:, None]
    output = np.column_stack((np.sin(future[:, 0]) + .2 * future[:, 0],
                              np.cos(future[:, 0]) - .1 * future[:, 0]))
    output = output[:, order]
    return World(7, pad(np.column_stack((control, state)), 108), pad(target, 108),
                 pad(np.column_stack((history_control, history_state)), 32),
                 pad(future, 50), pad(output, 50))


def _predict(candidate: Candidate, world: World) -> np.ndarray:
    candidate.fit(Training((world,)))
    return candidate.predict(candidate.adapt(world.support_input, world.support_target),
                             world.history, world.future_public)


def test_all_causal_roles_inherit_exact_shared_source_and_constants() -> None:
    for role in (Independent, Cross, Support):
        assert Candidate in role.mro()
        assert (role.RIDGE, role.RESIDUAL_BOUND) == (RIDGE, RESIDUAL_BOUND)


def test_frozen_constants_bound_and_session_local_adaptation() -> None:
    assert (RIDGE, RESIDUAL_BOUND) == (1e-3, 4.0)
    world = _world()
    candidate = Candidate(11)
    candidate.fit(Training((world,)))
    grams, rhs = candidate._grams.copy(), candidate._rhs.copy()
    prediction = candidate.predict(candidate.adapt(world.support_input, world.support_target),
                                   world.history, world.future_public)
    assert np.array_equal(candidate._grams, grams) and np.array_equal(candidate._rhs, rhs)
    assert np.isfinite(prediction).all() and candidate.last_stable
    assert candidate.state_bytes() < 67_108_864
    base = world.history.values[-1, 1:3]
    assert np.max(np.abs(prediction[0, :2] - base)) <= RESIDUAL_BOUND + 1e-6


def test_consistent_state_output_permutation_is_equivariant() -> None:
    base, permuted = _predict(Candidate(19), _world()), _predict(Candidate(19), _world((1, 0)))
    assert np.allclose(permuted[:, :2], base[:, :2][:, ::-1], atol=2e-5)


def test_fit_order_and_query_work_do_not_depend_on_world_count() -> None:
    first, second = _world(), _world((1, 0))
    left, right = Candidate(23), Candidate(23)
    left.fit(Training((first, second)))
    right.fit(Training((second, first)))
    assert np.allclose(left._grams, right._grams) and np.allclose(left._rhs, right._rhs)
    observed = []
    for count in (1, 4, 9):
        candidate = Candidate(23)
        candidate.fit(Training((first,) * count))
        candidate.predict(candidate.adapt(first.support_input, first.support_target),
                          first.history, first.future_public)
        observed.append(candidate.last_ops)
    assert len(set(observed)) == 1
