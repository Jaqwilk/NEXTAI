from nextai_autoresearch.benchmarks.continuous_event_predictive_state_v1 import (
    COEFFICIENTS,
    make_episode,
    make_tasks,
    make_world,
    run_trial,
)
from nextai_autoresearch.continuous_event_core import (
    EventPredictiveState,
    ExhaustiveSwitchingAR,
    ScreenedSwitchingAR,
    VarianceTriggeredKalman,
)


def test_stream_hides_two_stable_channels_among_continuous_distractors():
    world = make_world(32, 1103)
    episode = make_episode(world, 1103)
    assert episode.channels.shape == (108, 32)
    assert world.active_index != world.context_index
    assert set(episode.channels[:, world.context_index]) == {-1.0, 0.0, 1.0}


def test_strong_controls_recover_heldout_switching_forecasts():
    world = make_world(8, 1103)
    episode = make_episode(world, 1103)
    tasks = make_tasks(world, 6, 1103, 4)
    for candidate in (ExhaustiveSwitchingAR(), ScreenedSwitchingAR(), EventPredictiveState(), VarianceTriggeredKalman()):
        candidate.fit(episode, 8, 6)
        assert candidate.active == world.active_index
        assert candidate.context == world.context_index
        assert all(max(abs(a - b) for a, b in zip(candidate.query(task.cold, 6), task.target)) < 1e-5 for task in tasks)
        assert all(max(abs(a - b) for a, b in zip(candidate.query(task.near, 6), task.near_target)) < 1e-5 for task in tasks)


def test_screening_is_cheaper_than_exhaustive_pair_search_at_k32():
    episode = make_episode(make_world(32, 1103), 1103)
    screened, exhaustive = ScreenedSwitchingAR(), ExhaustiveSwitchingAR()
    screened.fit(episode, 32, 6)
    exhaustive.fit(episode, 32, 6)
    assert screened.fit_ops < exhaustive.fit_ops


def test_local_update_changes_one_regime_and_retains_another():
    world = make_world(8, 1103)
    candidate = EventPredictiveState()
    candidate.fit(make_episode(world, 1103), 8, 6)
    retained_model = candidate.models[1]
    changed = list(COEFFICIENTS)
    changed[0] = (0.58, -0.18)
    candidate.update(make_episode(world, 2207, tuple(changed), regime=-1, rows=36))
    assert candidate.models[1] == retained_model


def test_trial_reports_full_cost_and_safe_reuse_for_strong_controls():
    for name in ("screened_switching_ar", "variance_triggered_kalman", "event_predictive_state"):
        trial = run_trial(name, 8, 4, 4, 1103, 6)
        assert trial["accuracy"] == trial["warm_accuracy"] == trial["near_equivalent_accuracy"] == 1.0
        assert trial["continual_new_fact_accuracy"] == trial["continual_retention"] == 1.0
        assert trial["false_reuse_rate"] == 0.0
        assert trial["workload_ops"] > trial["fit_ops"]
