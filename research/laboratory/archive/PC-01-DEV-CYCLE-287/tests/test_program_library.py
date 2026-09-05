from nextai_autoresearch.benchmarks.program_library_v1 import (
    make_task,
    make_training_corpus,
    run_trial,
)
from nextai_autoresearch.candidates.exact_program_memo import Candidate as Memo
from nextai_autoresearch.candidates.learned_library_search import Candidate as Learned
from nextai_autoresearch.program_search import TARGET_MACRO


def test_corpus_and_tasks_are_deterministic_and_held_out() -> None:
    corpus = make_training_corpus(8, 1103)
    assert corpus == make_training_corpus(8, 1103)
    task = make_task(6, 1103, 0)
    assert task == make_task(6, 1103, 0)
    assert task.program not in corpus
    assert len(task.program) == 6


def test_extractor_recovers_unlabelled_repeated_fragment() -> None:
    candidate = Learned(1103)
    candidate.fit(make_training_corpus(8, 1103), 8, 6)
    assert candidate.library == (TARGET_MACRO,)


def test_library_reduces_cold_search_and_mismatch_does_not() -> None:
    primitive = run_trial("primitive_program_search", 8, 6, 4, 1103, 6)
    learned = run_trial("learned_library_search", 8, 6, 4, 1103, 6)
    mismatch = run_trial("mismatched_library_search", 8, 6, 4, 1103, 6)
    assert primitive["accuracy"] == learned["accuracy"] == mismatch["accuracy"] == 1.0
    assert learned["mean_query_ops"] < 0.7 * primitive["mean_query_ops"]
    assert mismatch["mean_query_ops"] >= primitive["mean_query_ops"]
    assert learned["amortized_cold_ops"] < primitive["mean_query_ops"]


def test_exact_memo_only_reduces_exact_warm_queries() -> None:
    task = make_task(4, 1103, 0)
    candidate = Memo(1103)
    candidate.fit(make_training_corpus(8, 1103), 8, 6)
    assert candidate.query(task.examples, task.test_input, 4) == task.expected
    cold_ops = candidate.last_ops
    assert candidate.query(task.examples, task.test_input, 4) == task.expected
    assert candidate.last_ops == 1 < cold_ops
