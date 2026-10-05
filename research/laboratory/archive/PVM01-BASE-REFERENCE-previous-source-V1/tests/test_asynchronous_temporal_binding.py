from nextai_autoresearch.benchmarks.asynchronous_temporal_binding_v1 import (
    MOTIFS,
    UPDATE_SIGNATURES,
    make_episode,
    make_tasks,
    make_world,
    render,
    run_trial,
)
from nextai_autoresearch.temporal_binding_core import (
    CalendarEventTransducer,
    Demo,
    Episode,
    HeapEventTransducer,
    LearnedPolychronousBinder,
    TimedAutomatonMatcher,
    TimedQuery,
)


def test_motifs_have_matched_rates_but_distinct_timing():
    assert len(set(MOTIFS.values())) == 4
    assert {sum(signature) for signature in MOTIFS.values()} == {6}
    world = make_world(32, 1103)
    assert len(render((1,), world, MOTIFS, 1)) == len(render((4,), world, MOTIFS, 2))


def test_strong_controls_decode_heldout_temporal_compositions():
    world = make_world(8, 1103)
    episode, tasks = make_episode(world, 1103), make_tasks(world, 6, 1103, 4)
    for candidate in (TimedAutomatonMatcher(), HeapEventTransducer(), CalendarEventTransducer(), LearnedPolychronousBinder()):
        candidate.fit(episode, 8, 6)
        assert candidate.active == world.active_channel
        assert all(candidate.query(task.cold, 6) == task.target for task in tasks)
        assert all(candidate.query(task.near, 6) == task.near_target for task in tasks)


def test_local_delay_update_retains_unchanged_binding():
    world = make_world(8, 1103)
    candidate = LearnedPolychronousBinder()
    candidate.fit(make_episode(world, 1103), 8, 6)
    changed = dict(MOTIFS)
    changed[1] = UPDATE_SIGNATURES[0]
    candidate.update(Episode((Demo(render((1,), world, changed, 2207), (1,)),)))
    assert candidate.query(TimedQuery(render((1,), world, changed, 17)), 1) == (1,)
    assert candidate.query(TimedQuery(render((4,), world, changed, 19)), 1) == (4,)


def test_irrelevant_event_growth_is_charged():
    small = run_trial("timed_automaton_matcher", 8, 4, 4, 1103, 6)
    large = run_trial("timed_automaton_matcher", 32, 4, 4, 1103, 6)
    assert large["mean_delivered_events"] > small["mean_delivered_events"]
    assert large["mean_query_ops"] > small["mean_query_ops"]


def test_trial_reports_exact_safe_reuse_for_temporal_controls():
    for name in ("timed_automaton_matcher", "calendar_event_transducer", "learned_polychronous_binder"):
        trial = run_trial(name, 8, 4, 4, 1103, 6)
        assert trial["accuracy"] == trial["warm_accuracy"] == trial["near_equivalent_accuracy"] == 1.0
        assert trial["continual_new_fact_accuracy"] == trial["continual_retention"] == 1.0
        assert trial["reuse_precision"] == trial["reuse_coverage"] == 1.0
        assert trial["false_reuse_rate"] == 0.0
