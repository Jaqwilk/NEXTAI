from nextai_autoresearch.benchmarks.program_library_adversarial_v2 import (
    DISTRACTOR_MACRO,
    make_task,
    make_training_corpus,
    run_trial,
)
from nextai_autoresearch.candidates.learned_library_search import Candidate as Learned
from nextai_autoresearch.program_search import TARGET_MACRO


def test_adversarial_corpus_is_deterministic_and_contains_competition() -> None:
    corpus = make_training_corpus(32, 1103)
    assert corpus == make_training_corpus(32, 1103)
    count = lambda program, fragment: sum(
        program[index : index + len(fragment)] == fragment
        for index in range(len(program) - len(fragment) + 1)
    )
    assert sum(count(program, TARGET_MACRO) for program in corpus) == 32
    assert sum(count(program, DISTRACTOR_MACRO) for program in corpus) >= 16


def test_extractor_selects_target_across_screen_corpora() -> None:
    for seed in (1103, 2207, 3301):
        for size in (8, 32, 128):
            candidate = Learned(seed)
            candidate.fit(make_training_corpus(size, seed), size, 8)
            assert candidate.library == (TARGET_MACRO,)


def test_tasks_mix_one_and_two_macro_uses() -> None:
    one_use = make_task(8, 1103, 1).program
    two_use = make_task(8, 1103, 0).program
    assert sum(one_use[index : index + 2] == TARGET_MACRO for index in range(7)) == 1
    assert sum(two_use[index : index + 2] == TARGET_MACRO for index in range(7)) == 2


def test_small_adversarial_trial_keeps_exactness_and_average_gain() -> None:
    primitive = run_trial("primitive_program_search", 8, 6, 4, 1103, 8)
    learned = run_trial("learned_library_search", 8, 6, 4, 1103, 8)
    assert primitive["accuracy"] == learned["accuracy"] == 1.0
    assert learned["macro_selection_accuracy"] == 1.0
    assert learned["mean_query_ops"] < primitive["mean_query_ops"]
