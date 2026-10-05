from nextai_autoresearch.benchmarks.cellular_propagation_v1 import (
    make_task,
    run_trial,
    training_cases,
)
from nextai_autoresearch.cellular_core import LearnedEventQueue


def test_tasks_separate_redundant_and_blocked_paths() -> None:
    for depth in (1, 4, 6):
        assert make_task(8, depth, 1103, 0).expected is True
        assert make_task(8, depth, 1103, 1).expected is False


def test_local_rule_is_learned_exactly() -> None:
    candidate = LearnedEventQueue(1103)
    candidate.fit(training_cases(1103), 8, 6)
    assert [candidate._fires(*features) for features, _ in training_cases(1103)] == [
        bool(target) for _, target in training_cases(1103)
    ]


def test_event_queue_is_exact_and_ignores_dormant_area() -> None:
    small = run_trial("learned_event_queue_ca", 8, 4, 4, 1103, 6)
    large = run_trial("learned_event_queue_ca", 32, 4, 4, 1103, 6)
    sweep = run_trial("learned_synchronous_ca", 32, 4, 4, 1103, 6)
    assert small["accuracy"] == large["accuracy"] == sweep["accuracy"] == 1.0
    assert small["mean_cell_updates"] == large["mean_cell_updates"]
    assert large["mean_query_ops"] < sweep["mean_query_ops"] / 2
