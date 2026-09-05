from nextai_autoresearch.benchmarks.program_library_identifiable_v3 import (
    make_task,
    run_trial,
)
from nextai_autoresearch.program_search import DOMAIN_SIZE


def test_task_specifies_every_input_except_the_heldout() -> None:
    task = make_task(8, 3301, 0)
    example_inputs = {value for value, _ in task.examples}
    assert len(task.examples) == DOMAIN_SIZE - 1
    assert task.test_input not in example_inputs
    assert example_inputs | {task.test_input} == set(range(DOMAIN_SIZE))


def test_prior_failure_cell_is_exact_with_identifiable_specification() -> None:
    for candidate in ("primitive_program_search", "oracle_library_search", "learned_library_search"):
        trial = run_trial(candidate, 128, 8, 12, 3301, 8)
        assert trial["accuracy"] == 1.0
