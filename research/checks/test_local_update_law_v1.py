from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.cross_family_only_local_update_law_v1 import Candidate as Cross
from nextai_autoresearch.candidates.independent_local_update_law_v1 import Candidate as Independent
from nextai_autoresearch.candidates.shared_local_update_law_v1 import (
    BIN_EDGES, CONSTANTS, DEFAULT_RATE, RATE_GRID, Candidate,
)
from nextai_autoresearch.candidates.support_only_local_update_law_v1 import Candidate as Support
from nextai_autoresearch.three_family_tensor_contract import Training, World, pad


def _world(order=(0, 1)) -> World:
    control = np.linspace(-1, 1, 108)
    state_base = np.column_stack((np.sin(control), np.cos(control)))
    target_base = np.column_stack((state_base[:, 0] + .2 * control,
                                   state_base[:, 1] - .1 * control))
    state, target = state_base[:, order], target_base[:, order]
    history_control = np.linspace(-.5, .1, 32)
    history_state = np.column_stack((np.sin(history_control), np.cos(history_control)))[:, order]
    future = np.linspace(.11, .6, 50)[:, None]
    output = np.column_stack((np.sin(future[:, 0]) + .2 * future[:, 0],
                              np.cos(future[:, 0]) - .1 * future[:, 0]))[:, order]
    return World(7, pad(np.column_stack((control, state)), 108), pad(target, 108),
                 pad(np.column_stack((history_control, history_state)), 32),
                 pad(future, 50), pad(output, 50))


def _prediction(world: World) -> tuple[Candidate, np.ndarray]:
    candidate = Candidate(17)
    candidate.fit(Training((world,)))
    session = candidate.adapt(world.support_input, world.support_target)
    return candidate, candidate.predict(session, world.history, world.future_public)


def test_all_roles_share_source_and_frozen_constants() -> None:
    assert CONSTANTS == (tuple(BIN_EDGES), tuple(RATE_GRID), DEFAULT_RATE)
    for role in (Independent, Cross, Support):
        assert Candidate in role.mro() and role.CONSTANTS == CONSTANTS


def test_support_only_default_and_fit_transfer_only_six_rates() -> None:
    candidate = Candidate(3)
    candidate.fit(Training(()))
    assert np.array_equal(candidate.rates, np.ones(6))
    assert candidate.state_bytes() == candidate.rates.nbytes + 33 * 32 * 8
    trained = Candidate(3)
    trained.fit(Training((_world(),)))
    assert trained.rates.shape == (6,) and np.isfinite(trained.rates).all()
    assert not hasattr(trained, "_training") and not hasattr(trained, "weights")


def test_fresh_adaptation_is_session_local_and_costed() -> None:
    world = _world()
    candidate = Candidate(5)
    candidate.fit(Training((world,)))
    rates = candidate.rates.copy()
    first = candidate.adapt(world.support_input, world.support_target)
    second = candidate.adapt(world.support_input, world.support_target)
    assert np.array_equal(first["weights"], second["weights"])
    assert np.array_equal(candidate.rates, rates)
    assert candidate.adaptation_ops > 0


def test_consistent_state_output_permutation_is_equivariant() -> None:
    base_candidate, base = _prediction(_world())
    permuted_candidate, permuted = _prediction(_world((1, 0)))
    assert np.allclose(permuted[:, :2], base[:, :2][:, ::-1], atol=2e-5)
    assert np.allclose(permuted_candidate.rates, base_candidate.rates)
