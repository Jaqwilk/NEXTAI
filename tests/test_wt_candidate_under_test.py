from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.wt_candidate_under_test import Candidate, RESIDUAL_BOUND
from nextai_autoresearch.wt_prequential_contract import WTEpisode, WTQuery, WTReveal, WTTraining


def _training(permutation=None) -> WTTraining:
    permutation = np.arange(10) if permutation is None else np.asarray(permutation)
    episodes = []
    for index in range(18):
        base = np.linspace(-0.3, 0.3, 10) + index / 100
        velocity = np.linspace(0.004, 0.02, 10)
        history = np.stack([base + (time - 31) * velocity for time in range(32)])
        target = np.stack([base + (time + 1) * velocity for time in range(32)])
        episodes.append(WTEpisode(
            tuple(map(tuple, history[:, permutation])), float(index % 3 - 1),
            tuple(map(tuple, target[:, permutation])),
        ))
    return WTTraining(tuple(episodes), 1, 1)


def _query(permutation=None, slot=101, horizon=96) -> WTQuery:
    permutation = np.arange(10) if permutation is None else np.asarray(permutation)
    base = np.linspace(-0.25, 0.35, 10)
    velocity = np.linspace(0.005, 0.018, 10)
    history = np.stack([base + (time - 31) * velocity for time in range(32)])
    return WTQuery(slot, tuple(map(tuple, history[:, permutation])), 0.0, horizon)


def test_wt_recurrent_residual_extrapolates_and_respects_bound() -> None:
    candidate = Candidate(7)
    candidate.fit(_training(), 18, 96)
    query = _query()
    prediction = np.asarray(candidate.query(query, 96))
    origin = np.asarray(query.history)[-1]
    assert prediction.shape == (96, 10)
    assert not np.allclose(prediction[31], prediction[95])
    assert np.max(np.abs(prediction - origin)) <= RESIDUAL_BOUND + 1e-12


def test_wt_recurrent_residual_is_channel_permutation_equivariant() -> None:
    permutation = np.array([7, 2, 9, 0, 4, 1, 8, 5, 3, 6])
    plain, permuted = Candidate(1), Candidate(1)
    plain.fit(_training(), 18, 96)
    permuted.fit(_training(permutation), 18, 96)
    expected = np.asarray(plain.query(_query(slot=202, horizon=32), 32))[:, permutation]
    observed = np.asarray(permuted.query(_query(permutation, slot=202, horizon=32), 32))
    assert np.allclose(observed, expected, atol=1e-8)


def test_wt_reveal_updates_only_one_slot() -> None:
    candidate = Candidate(2)
    candidate.fit(_training(), 18, 96)
    first, other = _query(slot=303, horizon=32), _query(slot=404, horizon=32)
    before_first = np.asarray(candidate.query(first, 32))
    before_other = np.asarray(candidate.query(other, 32))
    target = np.asarray(first.history)[-1] + np.linspace(0.02, 0.2, 32)[:, None]
    candidate.update(WTReveal(first.slot, first.history, first.control, tuple(map(tuple, target))))
    after_first = np.asarray(candidate.query(first, 32))
    after_other = np.asarray(candidate.query(other, 32))
    assert not np.allclose(after_first, before_first)
    assert np.allclose(after_other, before_other)
