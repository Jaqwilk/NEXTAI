from nextai_autoresearch.benchmarks.nonlinear_local_state_transfer_v1 import (
    damaged, make_task, make_world, oracle_answer, run_trial,
)
from nextai_autoresearch.local_state_core import local_rule


def test_majority_state_repairs_any_single_bit_damage() -> None:
    for kind in range(4):
        for pulse in range(4):
            assert {local_rule(kind, state, pulse) for state in (0, 1, 2, 4)} == {local_rule(kind, 0, pulse)}
            assert {local_rule(kind, state, pulse) for state in (7, 6, 5, 3)} == {local_rule(kind, 7, pulse)}


def test_registered_tasks_transfer_and_revisit() -> None:
    world = make_world(1103)
    for size in (8, 32):
        task = make_task(world, size, 1103 ^ 4, 0)
        assert oracle_answer(task, world, 4) == oracle_answer(damaged(task), world, 4)


def test_learned_sparse_dense_exact_and_oracle_are_exact() -> None:
    for candidate in ("exact_finite_state_propagation", "learned_dense_nca",
                      "learned_sparse_event_nca", "oracle_local_state_rule"):
        result = run_trial(candidate, 8, 6, 4, 1103, 6)
        assert result["accuracy"] == result["damage_recovery_accuracy"] == 1.0
        assert result["continual_new_fact_accuracy"] == result["continual_retention"] == 1.0


def test_sparse_neural_saves_sweeps_but_exact_control_is_cheaper() -> None:
    sparse = run_trial("learned_sparse_event_nca", 32, 6, 4, 1103, 6)
    dense = run_trial("learned_dense_nca", 32, 6, 4, 1103, 6)
    exact = run_trial("exact_finite_state_propagation", 32, 6, 4, 1103, 6)
    assert sparse["mean_rule_evaluations"] * 20 < dense["mean_rule_evaluations"]
    assert exact["state_bytes"] < sparse["state_bytes"]
    assert exact["workload_ops"] < sparse["workload_ops"]
