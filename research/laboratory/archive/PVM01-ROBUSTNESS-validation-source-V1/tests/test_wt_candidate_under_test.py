from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.wt_candidate_under_test import Candidate, POPULATION
from nextai_autoresearch.wt_prequential_contract import WTEpisode, WTQuery, WTReveal, WTTraining


def _training(permutation=None) -> WTTraining:
    permutation = np.arange(10) if permutation is None else np.asarray(permutation)
    episodes = []
    for index in range(18):
        base = np.linspace(-0.3, 0.3, 10) + index / 100
        velocity = np.linspace(0.004, 0.02, 10)
        history = np.stack([base + (time - 31) * velocity for time in range(32)])
        target = np.stack([base + (time + 1) * velocity for time in range(32)])
        episodes.append(WTEpisode(tuple(map(tuple, history[:, permutation])), float(index % 3 - 1),
                                  tuple(map(tuple, target[:, permutation]))))
    return WTTraining(tuple(episodes), 1, 1)


def _query(permutation=None, slot=101, horizon=96, tied=False) -> WTQuery:
    permutation = np.arange(10) if permutation is None else np.asarray(permutation)
    base = np.linspace(-0.25, 0.35, 10)
    velocity = np.full(10, 0.01) if tied else np.linspace(0.005, 0.018, 10)
    history = np.stack([base + (time - 31) * velocity for time in range(32)])
    return WTQuery(slot, tuple(map(tuple, history[:, permutation])), 0.0, horizon)


def test_wt_event_population_emits_direct_trajectory_with_sparse_state_touch() -> None:
    candidate = Candidate(7)
    candidate.fit(_training(), 18, 96)
    query = _query()
    prediction = np.asarray(candidate.query(query, 96))
    assert prediction.shape == (96, 10)
    assert not np.allclose(prediction[0], prediction[-1])
    assert candidate._weights.shape == (POPULATION, 10)
    assert candidate.last_update_bytes == 0.0


def test_wt_event_population_is_permutation_equivariant_even_on_ties() -> None:
    permutation = np.array([7, 2, 9, 0, 4, 1, 8, 5, 3, 6])
    plain, permuted = Candidate(1), Candidate(1)
    plain.fit(_training(), 18, 96)
    permuted.fit(_training(permutation), 18, 96)
    expected = np.asarray(plain.query(_query(slot=202, horizon=32, tied=True), 32))[:, permutation]
    observed = np.asarray(permuted.query(_query(permutation, slot=202, horizon=32, tied=True), 32))
    assert np.allclose(observed, expected, atol=1e-12)


def test_wt_event_reveal_updates_only_active_rows_in_one_slot() -> None:
    candidate = Candidate(2)
    candidate.fit(_training(), 18, 96)
    first, other = _query(slot=303, horizon=32), _query(slot=404, horizon=32)
    candidate.query(first, 32)
    candidate.query(other, 32)
    first_before = candidate._slots[first.slot][0].copy()
    other_before = candidate._slots[other.slot][0].copy()
    target = np.asarray(first.history)[-1] + np.linspace(0.02, 0.2, 32)[:, None]
    candidate.update(WTReveal(first.slot, first.history, first.control, tuple(map(tuple, target))))
    changed = np.flatnonzero(np.any(candidate._slots[first.slot][0] != first_before, axis=1))
    assert 0 < len(changed) <= 11
    assert np.array_equal(candidate._slots[other.slot][0], other_before)
    assert candidate.last_update_bytes < 24 * 960 * 8
