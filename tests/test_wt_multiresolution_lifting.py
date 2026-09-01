from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.wt_multiresolution_lifting_core import (
    FEATURES, RETAINED, LiftingCandidate, haar, inverse_haar,
)
from nextai_autoresearch.wt_prequential_contract import WTEpisode, WTQuery, WTReveal, WTTraining


ROLES = {
    "wt_multiresolution_lifting_v1": "multiresolution",
    "wt_source_identical_single_scale_lifting_v1": "single_scale",
    "wt_source_identical_frozen_lifting_v1": "frozen_lifting",
}


def _training(permutation=None) -> WTTraining:
    permutation = np.arange(10) if permutation is None else np.asarray(permutation)
    episodes = []
    for index in range(18):
        phase = np.linspace(0.0, 2.0 * np.pi, 32, endpoint=False)
        base = np.linspace(-0.4, 0.4, 10) + index / 100.0
        amplitude = np.linspace(0.03, 0.12, 10)
        history = base + np.sin(phase[:, None]) * amplitude
        target = base + 0.1 + np.sin((phase + np.pi / 4)[:, None]) * amplitude
        episodes.append(WTEpisode(
            tuple(map(tuple, history[:, permutation])), float(index % 3 - 1),
            tuple(map(tuple, target[:, permutation])),
        ))
    return WTTraining(tuple(episodes), 1, 1)


def _query(permutation=None, slot=101, horizon=96) -> WTQuery:
    permutation = np.arange(10) if permutation is None else np.asarray(permutation)
    phase = np.linspace(0.0, 2.0 * np.pi, 32, endpoint=False)
    history = np.linspace(-0.3, 0.5, 10) + np.sin(phase[:, None]) * np.linspace(0.04, 0.1, 10)
    return WTQuery(slot, tuple(map(tuple, history[:, permutation])), 0.0, horizon)


def _candidate(name: str, permutation=None):
    module = __import__(f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"])
    candidate = module.Candidate(7)
    candidate.fit(_training(permutation), 18, 96)
    return candidate


def test_haar_round_trip_and_source_identical_roles() -> None:
    values = np.arange(320, dtype=float).reshape(32, 10) / 100.0
    assert np.allclose(inverse_haar(haar(values)), values, atol=1e-12)
    for name, mode in ROLES.items():
        candidate = _candidate(name)
        assert isinstance(candidate, LiftingCandidate)
        assert candidate.mode == mode
        assert candidate._weights.shape == (FEATURES, RETAINED)


def test_lifting_roles_are_permutation_equivariant_and_recursive() -> None:
    permutation = np.array([7, 2, 9, 0, 4, 1, 8, 5, 3, 6])
    for name in ROLES:
        plain, permuted = _candidate(name), _candidate(name, permutation)
        expected = np.asarray(plain.query(_query(), 96))[:, permutation]
        observed = np.asarray(permuted.query(_query(permutation), 96))
        assert observed.shape == (96, 10)
        assert np.isfinite(observed).all()
        assert np.allclose(observed, expected, atol=1e-10)


def test_lifting_update_is_slot_local_and_cheaper_than_lms_rls() -> None:
    candidate = _candidate("wt_multiresolution_lifting_v1")
    first, other = _query(slot=303, horizon=32), _query(slot=404, horizon=32)
    candidate.query(first, 32)
    candidate.query(other, 32)
    first_before = candidate._slots[first.slot].copy()
    other_before = candidate._slots[other.slot].copy()
    target = np.asarray(first.history) + 0.2
    candidate.update(WTReveal(first.slot, first.history, first.control, tuple(map(tuple, target))))
    assert not np.array_equal(candidate._slots[first.slot], first_before)
    assert np.array_equal(candidate._slots[other.slot], other_before)
    assert candidate.update_ops < 2 * 32 * 320
    assert candidate.last_update_bytes < 32 * 320 * 8


def test_frozen_lifting_charges_but_does_not_mutate() -> None:
    candidate = _candidate("wt_source_identical_frozen_lifting_v1")
    query = _query(slot=505, horizon=32)
    before = candidate._slot(query.slot).copy()
    target = np.asarray(query.history) + 0.5
    candidate.update(WTReveal(query.slot, query.history, query.control, tuple(map(tuple, target))))
    assert candidate.update_ops > 0
    assert candidate.last_update_bytes > 0
    assert np.array_equal(candidate._slots[query.slot], before)

