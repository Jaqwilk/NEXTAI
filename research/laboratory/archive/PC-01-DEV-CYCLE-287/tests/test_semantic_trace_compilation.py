from nextai_autoresearch.benchmarks.semantic_trace_compilation_v1 import make_tasks, mutate_leaf, run_trial
from nextai_autoresearch.semantic_trace_core import canonical_key, evaluate, internal_keys


def test_transfer_changes_raw_encoding_without_stable_names() -> None:
    task = make_tasks(8, 6, 1103, 1)[0]
    assert task.cold != task.warm
    assert {node.node_id for node in task.cold.nodes}.isdisjoint(node.node_id for node in task.warm.nodes)
    assert canonical_key(task.cold) == canonical_key(task.warm)
    assert evaluate(task.cold) == evaluate(task.warm) == task.target


def test_generator_has_exact_active_depth_and_total_size() -> None:
    task = make_tasks(32, 6, 1103, 1)[0]
    assert len(task.cold.nodes) == 32
    assert len(internal_keys(canonical_key(task.cold))) == 6


def test_semantic_controls_transfer_but_exact_key_does_not() -> None:
    exact = run_trial("exact_key_trace_cache", 8, 6, 2, 1103, 6)
    canonical = run_trial("canonical_result_cache", 8, 6, 2, 1103, 6)
    compiled = run_trial("dependency_trace_compiler", 8, 6, 2, 1103, 6)
    assert exact["cross_structure_hit_rate"] == 0.0
    assert canonical["cross_structure_hit_rate"] == compiled["cross_structure_hit_rate"] == 1.0
    assert canonical["warm_accuracy"] == compiled["warm_accuracy"] == 1.0


def test_dependency_update_is_local_and_retains_other_trace() -> None:
    whole = run_trial("canonical_result_cache", 32, 6, 8, 1103, 6)
    local = run_trial("dependency_trace_compiler", 32, 6, 8, 1103, 6)
    assert local["continual_new_fact_accuracy"] == local["continual_retention"] == 1.0
    assert local["invalidated_fraction"] <= 0.25
    assert local["update_ops"] < whole["update_ops"]


def test_warm_work_charges_input_and_beats_full_evaluation() -> None:
    full = run_trial("indexed_dag_planner", 32, 6, 2, 1103, 6)
    local = run_trial("dependency_trace_compiler", 32, 6, 2, 1103, 6)
    assert local["mean_warm_input_ops"] == 64.0
    assert local["mean_warm_query_ops"] / full["mean_warm_query_ops"] <= 0.55
    task = make_tasks(8, 4, 1103, 1)[0]
    assert evaluate(mutate_leaf(task.warm)) != task.target
