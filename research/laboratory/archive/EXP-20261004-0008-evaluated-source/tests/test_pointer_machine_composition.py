from nextai_autoresearch.benchmarks.pointer_machine_composition_v1 import (
    make_task,
    run_trial,
    token_mapping,
    training_corpus,
)
from nextai_autoresearch.pointer_machine_core import LearnedPointer


def test_demos_identify_opaque_primitives_without_oracle_mapping() -> None:
    mapping = token_mapping(1103)
    candidate = LearnedPointer(1103)
    candidate.fit(training_corpus(8, 1103, mapping), 8, 6)
    assert candidate.mapping == mapping


def test_programs_are_unseen_compositions() -> None:
    mapping = token_mapping(1103)
    demo_programs = {(demo.token,) for demo in training_corpus(8, 1103, mapping)}
    task = make_task(8, 6, 1103, 5, 8, mapping)
    assert len(task.program) == 6
    assert task.program not in demo_programs
    assert task.mode == "adversarial"


def test_learned_hard_pointer_composes_but_trace_memory_does_not() -> None:
    learned = run_trial("learned_hard_pointer", 8, 6, 8, 1103, 6)
    memorizer = run_trial("pointer_trace_memorizer", 8, 6, 8, 1103, 6)
    assert learned["accuracy"] == learned["adversarial_accuracy"] == 1.0
    assert learned["identified_primitives"] == 4
    assert memorizer["accuracy"] < 0.5


def test_hard_access_ignores_distractors_while_dense_access_scans_them() -> None:
    small = run_trial("learned_hard_pointer", 8, 6, 8, 1103, 6)
    large = run_trial("learned_hard_pointer", 32, 6, 8, 1103, 6)
    dense = run_trial("dense_pointer_controller", 32, 6, 8, 1103, 6)
    assert small["mean_query_ops"] == large["mean_query_ops"]
    assert small["mean_memory_reads"] == large["mean_memory_reads"] == 6
    assert dense["mean_memory_reads"] == 32 * 6
    assert large["mean_query_ops"] < dense["mean_query_ops"] * 0.3
