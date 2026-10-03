from __future__ import annotations

import numpy as np

from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v1 as wt
from nextai_autoresearch.candidates.wt_action_conditioned_predictive_state_v1 import Candidate as Predictive
from nextai_autoresearch.candidates.wt_source_identical_frozen_predictive_state_v1 import Candidate as Frozen
from nextai_autoresearch.candidates.wt_source_identical_observation_history_v1 import Candidate as History
from nextai_autoresearch.candidates.wt_temporal_predictive_state_core import (
    CLIP, FEATURES, RANK, RIDGE, UPDATE_ETA, WINDOW, TemporalPredictiveState, _dct_basis,
)
from nextai_autoresearch.wt_prequential_contract import WTEpisode, WTQuery, WTReveal, WTTraining


ROLES = (Predictive, Frozen, History)


def _training(count: int = 32, permutation: np.ndarray | None = None) -> WTTraining:
    basis = _dct_basis(8)
    rows = []
    for index in range(count):
        signal = -1.0 if index & 1 else 1.0
        nuisance = np.asarray([1.0 if (index >> (bit + 1)) & 1 else -1.0 for bit in range(4)])
        history = sum(4.0 * nuisance[bit] * basis[:, bit] for bit in range(4))
        history = history + 0.2 * signal * basis[:, 4]
        matrix = np.column_stack([(1.0 + channel / 20.0) * history for channel in range(10)])
        target = matrix[-1] + signal * basis[:, 5, None] * np.linspace(0.8, 1.2, 10)
        if permutation is not None:
            matrix, target = matrix[:, permutation], target[:, permutation]
        rows.append(WTEpisode(tuple(map(tuple, matrix)), float(index & 1), tuple(map(tuple, target))))
    return WTTraining(tuple(rows), 0, 0)


def test_roles_share_one_implementation_and_frozen_constants() -> None:
    assert {role.__mro__[1] for role in ROLES} == {TemporalPredictiveState}
    assert [role.mode for role in ROLES] == ["predictive", "frozen", "history"]
    assert (WINDOW, RANK, FEATURES, RIDGE, UPDATE_ETA, CLIP) == (32, 4, 10, 0.001, 0.25, 8.0)


def test_future_supervision_selects_low_variance_predictive_direction() -> None:
    training = _training()
    predictive, history, frozen = Predictive(1), History(1), Frozen(1)
    for candidate in (predictive, history, frozen):
        candidate.fit(training, len(training.episodes), 96)
    direction = _dct_basis(8)[:, 4]
    overlap = lambda candidate: float(np.sum(np.square(direction @ candidate.projection)))
    assert overlap(predictive) > 0.95
    assert overlap(history) < 1e-8
    assert overlap(frozen) < 1e-8


def test_channel_permutation_equivariance() -> None:
    permutation = np.asarray([7, 2, 9, 0, 5, 1, 8, 4, 6, 3])
    original, permuted = Predictive(2), Predictive(2)
    original.fit(_training(24), 24, 96)
    permuted.fit(_training(24, permutation), 24, 96)
    history = np.asarray(_training(24).episodes[0].history)
    direct = np.asarray(original.query(WTQuery(700, tuple(map(tuple, history)), 1.0, 32), 32))
    changed = np.asarray(permuted.query(
        WTQuery(700, tuple(map(tuple, history[:, permutation])), 1.0, 32), 32,
    ))
    np.testing.assert_allclose(changed, direct[:, permutation], atol=1e-9, rtol=1e-9)


def test_recursive_rollout_and_post_reveal_update_are_slot_local() -> None:
    training = _training()
    candidate = Predictive(3)
    candidate.fit(training, len(training.episodes), 96)
    episode = training.episodes[-1]
    query_a = WTQuery(701, episode.history, episode.control, 96)
    query_b = WTQuery(702, episode.history, episode.control, 96)
    before_a = np.asarray(candidate.query(query_a, 96))
    before_b = np.asarray(candidate.query(query_b, 96))
    assert before_a.shape == (96, 10) and np.isfinite(before_a).all()
    np.testing.assert_allclose(before_a, before_b)
    candidate.update(WTReveal(701, episode.history, episode.control, episode.target))
    after_a = np.asarray(candidate.query(query_a, 96))
    after_b = np.asarray(candidate.query(query_b, 96))
    assert float(np.max(np.abs(after_a - before_a))) > 1e-9
    np.testing.assert_allclose(after_b, before_b)


def test_all_roles_complete_real_file_development_smoke() -> None:
    for name in (
        "wt_action_conditioned_predictive_state_v1",
        "wt_source_identical_frozen_predictive_state_v1",
        "wt_source_identical_observation_history_v1",
    ):
        rows = wt._run_trial(name, 54, 96, 117031, wt.DEVELOPMENT_SEEDS, 16_777_216)
        assert len(rows) == 2
        assert all(row["status"] == "complete" and row["stable_rollout_rate"] == 1.0 for row in rows)
