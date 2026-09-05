from nextai_autoresearch.benchmarks.semantic_trace_compilation_adversarial_v2 import make_task, run_trial
from nextai_autoresearch.semantic_trace_adversarial_core import normal_form
from nextai_autoresearch.semantic_trace_core import canonical_key, evaluate, scan


def _normal(query):
    index, _, _, _ = scan(query)
    return normal_form(index, query.sink)[0]


def test_rewrites_change_ids_and_tree_but_preserve_complete_normal_form() -> None:
    task = make_task(8, 6, 1103, 0)
    assert {node.node_id for node in task.cold.nodes}.isdisjoint(node.node_id for node in task.warm.nodes)
    assert canonical_key(task.cold) != canonical_key(task.warm)
    assert _normal(task.cold) == _normal(task.warm)
    assert evaluate(task.cold) == evaluate(task.warm) == task.target
    assert _normal(task.near) != _normal(task.warm)
    assert task.near_target != task.target


def test_k_counts_charged_distractors_and_split_changes_raw_topology() -> None:
    task = make_task(32, 8, 1103, 0)
    assert len(task.cold.nodes) == 32 + 2 * 8 - 2
    assert len(task.warm.nodes) == 32 + 2 * 8 + 1


def test_normal_form_transfers_without_false_near_reuse() -> None:
    tree = run_trial("canonical_result_cache", 8, 6, 3, 1103, 8)
    rewrite = run_trial("rewrite_normal_form_result_cache", 8, 6, 3, 1103, 8)
    assert tree["cross_structure_hit_rate"] == 0.0
    assert rewrite["cross_structure_hit_rate"] == 1.0
    assert rewrite["near_equivalent_accuracy"] == 1.0
    assert rewrite["false_reuse_rate"] == 0.0


def test_dependency_granularity_saves_update_work_at_a_state_cost() -> None:
    for depth in (4, 6, 8):
        whole = run_trial("rewrite_normal_form_result_cache", 32, depth, 3, 1103, 8)
        trace = run_trial("rewrite_normal_form_dependency_trace", 32, depth, 3, 1103, 8)
        assert trace["accuracy"] == trace["warm_accuracy"] == trace["continual_retention"] == 1.0
        assert trace["update_ops"] < whole["update_ops"]
        assert trace["workload_ops"] < whole["workload_ops"]
        assert trace["peak_state_bytes"] > whole["peak_state_bytes"]


def test_peak_trace_state_is_independent_of_irrelevant_k() -> None:
    small = run_trial("rewrite_normal_form_dependency_trace", 8, 6, 3, 1103, 8)
    large = run_trial("rewrite_normal_form_dependency_trace", 128, 6, 3, 1103, 8)
    assert small["peak_state_bytes"] == large["peak_state_bytes"]
    assert large["mean_input_ops"] > small["mean_input_ops"]
