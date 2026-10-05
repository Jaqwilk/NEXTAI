from __future__ import annotations

import numpy as np

from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v1 as bench
from nextai_autoresearch.candidates.wt_predictive_state_controls_core import (
    CSSR_MAX_SUFFIX, CSSR_TV_THRESHOLD, RANK, RIDGE, DiscretizedCSSR, SpectralPSR,
)
from nextai_autoresearch.wt_prequential_contract import WTEpisode, WTQuery, WTReveal, WTTraining


def _episode(control: float, sequence: list[float], response: float) -> WTEpisode:
    history = np.zeros((32, 10), dtype=float)
    history[:, 0] = np.resize(np.asarray(sequence, dtype=float), 32)
    target = np.repeat(history[-1][None, :], 32, axis=0)
    target[:, 0] += response
    return WTEpisode(tuple(map(tuple, history)), control, tuple(map(tuple, target)))


def _training(duplicate_low: int = 1) -> WTTraining:
    low = [
        _episode(-1.0, [-1.0, -1.0, 1.0, -1.0], -0.5),
        _episode(-1.0, [1.0, 1.0, -1.0, 1.0], -0.8),
    ]
    episodes = low * duplicate_low + [
        _episode(1.0, [1.0, -1.0, 1.0, -1.0], 0.5),
        _episode(1.0, [-1.0, 1.0, -1.0, 1.0], 0.8),
    ]
    return WTTraining(tuple(episodes), 100, 200)


def test_spectral_psr_matches_direct_coverage_balanced_two_stage_reference() -> None:
    assert (RANK, RIDGE) == (4, 0.001)
    candidate = SpectralPSR(7)
    training = _training()
    candidate.fit(training, len(training.episodes), 96)
    controls = np.asarray([episode.control for episode in training.episodes])
    weights = candidate.coverage_weights(controls)
    assert np.isclose(weights[controls == -1].sum(), weights[controls == 1].sum())
    histories = np.stack([
        np.concatenate(([1.0], np.asarray(ep.history)[-1], np.asarray(ep.history).mean(0),
                        np.asarray(ep.history)[-1] - np.asarray(ep.history)[0]))
        for ep in training.episodes
    ])
    futures = np.stack([
        (np.asarray(ep.target) - np.asarray(ep.history)[-1]).reshape(-1)
        for ep in training.episodes
    ])
    cross = (histories - weights @ histories).T @ (weights[:, None] * (futures - weights @ futures))
    left, singular, _ = np.linalg.svd(cross, full_matrices=False)
    rank = max(1, min(RANK, int(np.sum(singular > 1e-12))))
    assert np.allclose(np.abs(candidate.projection), np.abs(left[:, :rank]))


def test_spectral_coverage_balance_is_invariant_to_identical_stratum_duplication() -> None:
    base, duplicated = SpectralPSR(7), SpectralPSR(7)
    left, right = _training(1), _training(5)
    base.fit(left, len(left.episodes), 96)
    duplicated.fit(right, len(right.episodes), 96)
    query = WTQuery(11, left.episodes[0].history, -1.0, 32)
    assert np.allclose(base.query(query, 32), duplicated.query(query, 32), atol=1e-9)


def test_cssr_uses_variable_order_predictive_states_not_first_order_aliases() -> None:
    assert (CSSR_MAX_SUFFIX, CSSR_TV_THRESHOLD) == (3, 0.15)
    candidate = DiscretizedCSSR(7)
    episodes = [
        _episode(0.0, [-1.0, 1.0, -1.0, -1.0], -0.5),
        _episode(0.0, [1.0, -1.0, 1.0, -1.0], 0.5),
    ] * 4
    training = WTTraining(tuple(episodes), 100, 200)
    candidate.fit(training, len(training.episodes), 96)
    first = np.asarray(training.episodes[0].history)
    second = np.asarray(training.episodes[1].history)
    # Both histories end in the same discretized symbol; their length-two contexts differ.
    assert candidate._symbol(first[-1]) == candidate._symbol(second[-1])
    assert candidate.state_for_history(first, 0.0) != candidate.state_for_history(second, 0.0)
    first_order_key = candidate._symbol(first[-1])
    assert first_order_key == candidate._symbol(second[-1])


def test_both_controls_update_only_the_revealed_slot() -> None:
    for cls in (SpectralPSR, DiscretizedCSSR):
        candidate = cls(7)
        training = _training()
        candidate.fit(training, len(training.episodes), 96)
        episode = training.episodes[0]
        first = WTQuery(11, episode.history, episode.control, 32)
        other = WTQuery(22, episode.history, episode.control, 32)
        untouched = np.asarray(candidate.query(other, 32))
        target = np.asarray(episode.target) + 2.0
        candidate.update(WTReveal(first.slot, first.history, first.control, tuple(map(tuple, target))))
        assert not np.allclose(candidate.query(first, 32), untouched)
        assert np.allclose(candidate.query(other, 32), untouched)


def test_both_controls_are_anonymous_channel_permutation_equivariant() -> None:
    permutation = np.asarray([3, 1, 8, 0, 4, 9, 2, 6, 5, 7])
    training = _training()
    permuted = WTTraining(tuple(WTEpisode(
        tuple(map(tuple, np.asarray(ep.history)[:, permutation])), ep.control,
        tuple(map(tuple, np.asarray(ep.target)[:, permutation])),
    ) for ep in training.episodes), training.acquisition_ops, training.preprocessing_ops)
    for cls in (SpectralPSR, DiscretizedCSSR):
        left, right = cls(7), cls(7)
        left.fit(training, len(training.episodes), 96)
        right.fit(permuted, len(permuted.episodes), 96)
        episode = training.episodes[0]
        query = WTQuery(11, episode.history, episode.control, 32)
        permuted_query = WTQuery(11, tuple(map(tuple, np.asarray(episode.history)[:, permutation])),
                                 episode.control, 32)
        assert np.allclose(np.asarray(left.query(query, 32))[:, permutation],
                           right.query(permuted_query, 32), atol=1e-8)


def test_both_controls_complete_real_file_development_cell() -> None:
    for name in ("wt_coverage_aware_spectral_psr_v1", "wt_train_only_discretized_cssr_v1"):
        rows = bench._run_trial(name, 18, 16, 1_170_311, bench.DEVELOPMENT_SEEDS, 16_777_216)
        assert len(rows) == 2
        assert all(row["status"] == "complete" and row["stable_rollout_rate"] == 1.0 for row in rows)
