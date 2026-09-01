from nextai_autoresearch.benchmarks.program_induction_from_whole_io_v2 import (
    make_tasks,
    meta_programs,
    run_trial,
    support_scores,
)
from nextai_autoresearch.benchmarks import program_induction_from_whole_io_v3 as v3
from nextai_autoresearch.baseline_semantics import required_baseline_names
from nextai_autoresearch.config import load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root
from nextai_autoresearch.whole_io_vm_core import PROGRAMS, active_bits, run_program


def test_scored_query_exposes_no_program_or_trace() -> None:
    task = make_tasks(8, 6, 1103, 1)[0]
    assert not hasattr(task.query, "program")
    assert not hasattr(task.query, "trace")
    assert task.program not in meta_programs(8, 1103)


def test_support_has_one_corruption_and_unique_true_mdl_program() -> None:
    task = make_tasks(8, 4, 1103, 1)[0]
    errors = sum(
        run_program(task.program, active_bits(item.tape)[0])[0] != item.target
        for item in task.query.support
    )
    winner, margin = support_scores(task.query.support)
    assert errors == 1
    assert PROGRAMS[winner] == task.program
    assert margin >= 1
    assert active_bits(task.query.tape)[0] not in {
        active_bits(item.tape)[0] for item in task.query.support
    }


def test_mdl_and_oracle_recover_heldout_length_six_programs() -> None:
    mdl = run_trial("enumerative_mdl_vm", 8, 6, 2, 1103, 6)
    oracle = run_trial("oracle_latent_vm", 8, 6, 2, 1103, 6)
    assert mdl["accuracy"] == mdl["program_induction_accuracy"] == 1.0
    assert oracle["accuracy"] == oracle["program_induction_accuracy"] == 1.0
    assert mdl["trace_supervision_rate"] == mdl["supplied_program_rate"] == 0.0


def test_compiled_mdl_warm_path_keeps_raw_support_routing_cost() -> None:
    result = run_trial("enumerative_mdl_vm", 8, 4, 2, 1103, 6)
    assert result["mean_warm_query_ops"] < result["mean_query_ops"]
    assert result["mean_warm_memory_reads"] > 4


def test_dense_control_reads_padding_while_oracle_stops_at_sentinel() -> None:
    dense = run_trial("dense_whole_io", 32, 4, 2, 1103, 6)
    oracle = run_trial("oracle_latent_vm", 32, 4, 2, 1103, 6)
    assert dense["mean_memory_reads"] > 32
    assert oracle["mean_memory_reads"] == 5


def test_random_nearest_and_dense_controls_have_distinct_work_semantics() -> None:
    random = run_trial("random_whole_io", 8, 4, 2, 1103, 6)
    nearest = run_trial("nearest_whole_io", 8, 4, 2, 1103, 6)
    dense = run_trial("dense_whole_io", 8, 4, 2, 1103, 6)
    assert random["mean_query_ops"] < nearest["mean_query_ops"] < dense["mean_query_ops"]
    assert random["state_bytes"] < dense["state_bytes"]


def test_v3_preserves_v2_tasks_and_adds_full_cost_accounting() -> None:
    row = v3.run_trial("enumerative_mdl_vm", 8, 4, 2, 1103, 6)
    assert row["accuracy"] == row["program_induction_accuracy"] == 1.0
    assert row["data_acquisition_ops"] > 0
    assert row["peak_state_bytes"] >= row["state_bytes"]
    assert row["workload_ops_r1"] < row["workload_ops_r4"] < row["workload_ops_r16"]


def test_v3_plan_contract_freezes_roles_matrix_and_exact_controls() -> None:
    root = project_root()
    config = load_config(root).raw["whole_io_search"]
    plan = load_json(root / "research" / "plans" / "EXP-20260901-0034.json")
    plan["experiment_id"] = "EXP-20990101-0003"
    plan["benchmark"] = v3.BENCHMARK_VERSION
    plan["matrix"].update({
        "knowledge_sizes": list(config["knowledge_sizes"]),
        "reasoning_depths": list(config["reasoning_depths"]),
        "queries_per_cell": config["queries_per_cell"],
    })
    roles = [config["shared_candidate"], config["support_only_ablation"], config["frozen_ablation"]]
    plan["candidates"] = [*roles, *config["classical_baselines"]]
    plan["primary_metrics"] = list(config["pareto_capability_metrics"])
    directions = load_config(root).raw["metrics"]
    plan["metric_directions"] = {
        metric: "maximize" if metric in directions["maximize"] else "minimize"
        for metric in plan["primary_metrics"]
    }
    plan.pop("continuous_local_protocol", None)
    plan["whole_io_search_protocol"] = {
        "shared_candidate": roles[0],
        "support_only_ablation": roles[1],
        "frozen_ablation": roles[2],
        "classical_baselines": list(config["classical_baselines"]),
        "source_identical_contract": "complete_solver_objective_ties_support_execution_output_identical_except_meta_support_or_frozen_search_priority_v1",
        "state_budget_bytes": config["state_budget_bytes"],
        "pareto_capability_metrics": list(config["pareto_capability_metrics"]),
        "invalidation_rules": list(config["invalidation_rules"]),
    }
    validate_document("experiment_plan", plan, root)
    assert required_baseline_names(plan) == list(config["classical_baselines"])
