from nextai_autoresearch.benchmarks.opaque_alias_acquisition_v1 import make_task, make_training, run_trial
from nextai_autoresearch.opaque_alias_core import exact_alignment, signatures


def test_support_identifies_mapping_without_singleton_rows_or_stable_aliases() -> None:
    task = make_task(8, 6, 1103, 0)
    inferred = exact_alignment(task.warm.reference_rows, task.warm.current_rows)
    assert inferred.mapping == tuple(sorted(task.warm_mapping))
    assert all(len(row) == 3 for row in task.warm.reference_rows + task.warm.current_rows)
    assert {sum(bits) for bits in signatures(task.warm.reference_rows)[0].values()} == {3}
    assert set(dict(task.warm_mapping)).isdisjoint(dict(task.warm_mapping).values())


def test_fit_and_query_codebooks_are_disjoint() -> None:
    training = make_training(32, 1103)
    task = make_task(32, 4, 1103, 0)
    fit_aliases = {alias for episode in training for row in episode.reference_rows + episode.current_rows for alias in row}
    query_aliases = {alias for row in task.warm.reference_rows + task.warm.current_rows for alias in row}
    assert fit_aliases.isdisjoint(query_aliases)
    assert task.target != task.near_target


def test_independent_frequency_ablation_abstains_and_falls_back_safely() -> None:
    result = run_trial("independent_frequency_cache", 8, 4, 3, 1103, 6)
    assert result["accuracy"] == result["warm_accuracy"] == result["near_equivalent_accuracy"] == 1.0
    assert result["reuse_coverage"] == result["reuse_precision"] == result["false_reuse_rate"] == 0.0


def test_soft_and_exact_alignment_reuse_without_false_hits() -> None:
    soft = run_trial("soft_unification_result_cache", 8, 4, 3, 1103, 6)
    exact = run_trial("exact_constraint_result_cache", 8, 4, 3, 1103, 6)
    for result in (soft, exact):
        assert result["accuracy"] == result["warm_accuracy"] == result["near_equivalent_accuracy"] == 1.0
        assert result["reuse_precision"] == result["reuse_coverage"] == 1.0
        assert result["false_reuse_rate"] == 0.0
    assert soft["fit_ops"] > 0 == exact["fit_ops"]
    assert soft["mean_alignment_ops"] > exact["mean_alignment_ops"]


def test_exact_constraint_dominates_pairwise_alignment_as_k_grows() -> None:
    for size in (8, 32):
        soft = run_trial("soft_unification_result_cache", size, 4, 3, 1103, 6)
        exact = run_trial("exact_constraint_result_cache", size, 4, 3, 1103, 6)
        assert soft["mean_query_ops"] > exact["mean_query_ops"]
        assert soft["mean_warm_query_ops"] > exact["mean_warm_query_ops"]


def test_exact_dependency_trace_saves_local_update_at_a_state_cost() -> None:
    for depth in (4, 6):
        whole = run_trial("exact_constraint_result_cache", 8, depth, 3, 1103, 6)
        trace = run_trial("exact_constraint_dependency_trace", 8, depth, 3, 1103, 6)
        assert trace["update_ops"] < whole["update_ops"]
        assert trace["workload_ops"] < whole["workload_ops"]
        assert trace["peak_state_bytes"] > whole["peak_state_bytes"]
