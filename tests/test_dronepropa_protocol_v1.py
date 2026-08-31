from __future__ import annotations

import copy

import pytest

from nextai_autoresearch.baseline_semantics import verify_required_baselines
from nextai_autoresearch.benchmarks import heldout_dronepropa_factor_recombination_v2 as bench_v2
from nextai_autoresearch.benchmarks import heldout_dronepropa_factor_recombination_v3 as bench_v3
from nextai_autoresearch.benchmarks import heldout_dronepropa_factor_recombination_v4 as bench_v4
from nextai_autoresearch.config import load_config
from nextai_autoresearch.gates import GateViolation, ensure_can_create_plan
from nextai_autoresearch.metrics import aggregate_trials
from nextai_autoresearch.pareto import is_oracle_candidate
from nextai_autoresearch.runner import _apply_dronepropa_comparisons
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


def _protocol() -> dict:
    config = load_config().raw["dronepropa"]
    return {
        "corpus_id": config["corpus_id"],
        "split_unit": "whole_mat_file_sha256",
        "split_manifest_sha256": config["split_manifest_sha256"],
        "candidate_metadata": "anonymous_slots_only",
        "shared_candidate": config["shared_candidate"],
        "independent_ablation": config["independent_ablation"],
        "no_sharing_ablation": config["no_sharing_ablation"],
        "classical_baselines": config["classical_baselines"],
        "privileged_support_control": config["privileged_support_control"],
        "history_samples": config["history_samples"],
        "train_anchors_per_file": config["train_anchors_per_file"],
        "adaptation_anchors_per_file": config["adaptation_anchors_per_file"],
        "evaluation_anchors_per_file": config["evaluation_anchors_per_file"],
        "teacher_forced_horizon": config["teacher_forced_horizon"],
        "rollout_horizons": config["rollout_horizons"],
        "runner_random_evaluation_anchors": True,
        "future_controls": "evaluator_supplied_identically",
        "future_targets": "forbidden",
        "test_tuning": "forbidden",
        "state_budget_bytes": config["state_budget_bytes"],
        "declared_reuses": config["declared_reuses"],
        "invalidation_rules": config["invalidation_rules"],
    }


def test_dronepropa_plan_schema_requires_full_protocol_and_cost_axes() -> None:
    root = project_root()
    plan = copy.deepcopy(load_json(root / "research/plans/EXP-20260830-0057.json"))
    non_drone = copy.deepcopy(plan)
    non_drone["matrix"]["reasoning_depths"] = [1]
    with pytest.raises(Exception, match="too short"):
        validate_document("experiment_plan", non_drone, root)
    baselines = list(load_config().raw["dronepropa"]["classical_baselines"])
    plan["benchmark"] = "heldout_dronepropa_factor_recombination_v6"
    plan["matrix"]["reasoning_depths"] = [1]
    plan["candidates"] = ["shared_operator_subspace_arx", *baselines]
    plan.pop("mechanism_recombination_protocol")
    plan["dronepropa_protocol"] = _protocol()
    plan["primary_metrics"] = [
        "teacher_forced_nrmse", "rollout_10_nrmse", "rollout_50_nrmse",
        "worst_flight_normalized_rmse", "data_acquisition_ops", "preprocessing_ops",
        "fit_ops", "adaptation_ops", "mean_query_ops", "state_bytes",
        "peak_state_bytes", "mean_bytes_touched", "workload_ops_r1",
        "workload_ops_r4", "workload_ops_r16", "privileged_support_gain",
        "minimum_condition_transfer_gain", "minimum_trajectory_transfer_gain",
    ]
    directions = {name: "minimize" for name in plan["primary_metrics"]}
    plan["metric_directions"] = directions
    validate_document("experiment_plan", plan, root)
    minimize = set(load_config().raw["metrics"]["minimize"])
    assert {"workload_ops_r1", "workload_ops_r4"} <= minimize
    invalid = copy.deepcopy(plan)
    del invalid["dronepropa_protocol"]
    with pytest.raises(Exception, match="dronepropa_protocol"):
        validate_document("experiment_plan", invalid, root)


def test_v3_is_metric_metadata_only_and_reuses_v2_execution_boundary() -> None:
    assert bench_v3.SPLIT_MANIFEST == bench_v2.SPLIT_MANIFEST
    assert bench_v3.SPLIT_MANIFEST_SHA256 == bench_v2.SPLIT_MANIFEST_SHA256
    assert bench_v3.ROLE_COUNTS == bench_v2.ROLE_COUNTS
    assert bench_v3.verify_static_contract(project_root()) == bench_v2.verify_static_contract(project_root())
    assert bench_v4.SPLIT_MANIFEST_SHA256 == bench_v3.SPLIT_MANIFEST_SHA256
    assert bench_v4.verify_static_contract(project_root()) == bench_v3.verify_static_contract(project_root())


def test_dronepropa_semantic_gate_checks_all_ten_controls() -> None:
    names = list(load_config().raw["dronepropa"]["classical_baselines"])
    checked = verify_required_baselines(
        {"candidates": names, "dronepropa_protocol": {"classical_baselines": names}},
        run_tests=False,
    )
    assert checked["required"] == names
    assert len(checked["tests"]) == 10


def test_dronepropa_metrics_survive_aggregation() -> None:
    trial = {
        "status": "complete", "knowledge_size": 8, "reasoning_depth": 1,
        "seed": 7, "accuracy": 0.5, "warm_accuracy": 0.5,
        "continual_retention": 0.5, "mean_query_ops": 3, "mean_warm_query_ops": 3,
        "p50_latency_us": 1, "p95_latency_us": 2, "fit_seconds": 1,
        "state_bytes": 64, "update_ops": 2, "update_latency_us": 1,
        "teacher_forced_nrmse": 0.2, "rollout_10_nrmse": 0.3,
        "rollout_50_nrmse": 0.6, "worst_flight_normalized_rmse": 0.8,
        "worst_condition_normalized_rmse": 0.7, "stable_rollout_rate": 1.0,
        "preprocessing_ops": 100, "adaptation_ops": 50,
    }
    summary = aggregate_trials([trial])
    assert summary["teacher_forced_nrmse"] == 0.2
    assert summary["rollout_50_nrmse"] == 0.6
    assert summary["preprocessing_ops"] == 100
    assert summary["adaptation_ops"] == 50


def test_continuous_conditional_log_loss_may_be_negative() -> None:
    root = project_root()
    result = copy.deepcopy(load_json(root / "research/results/EXP-20260830-0057.json"))
    result["candidates"][0]["summary"]["conditional_log_loss"] = -0.2
    result["candidates"][0]["trials"][0]["conditional_log_loss"] = -0.2
    validate_document("experiment_result", result, root)


def test_dronepropa_cross_candidate_transfer_and_oracle_gaps_are_derived() -> None:
    def candidate(name: str, error: float) -> dict:
        trial = {
            "status": "complete", "knowledge_size": 8, "reasoning_depth": 1,
            "seed": 7, "accuracy": 1 / (1 + error), "warm_accuracy": 1 / (1 + error),
            "continual_retention": 1, "mean_query_ops": 3, "mean_warm_query_ops": 3,
            "p50_latency_us": 1, "p95_latency_us": 2, "fit_seconds": 1,
            "state_bytes": 64, "update_ops": 0, "update_latency_us": 0,
            "normalized_rmse": error, "condition_nrmse": {"c": error},
            "trajectory_nrmse": {"t": error},
        }
        return {"candidate": name, "status": "complete", "trials": [trial], "summary": {}}

    rows = [
        candidate("shared", 0.5),
        candidate("source_identical_independent_arx_v1", 0.8),
        candidate("no_sharing_pooled_arx_v1", 0.7),
        candidate("privileged_same_condition_oracle_arx_v2", 0.2),
    ]
    _apply_dronepropa_comparisons(rows, {
        "independent_ablation": "source_identical_independent_arx_v1",
        "no_sharing_ablation": "no_sharing_pooled_arx_v1",
    })
    summary = rows[0]["summary"]
    assert summary["minimum_condition_transfer_gain"] == pytest.approx(0.2)
    assert summary["minimum_trajectory_transfer_gain"] == pytest.approx(0.2)
    assert summary["oracle_gap_closed"] == pytest.approx(0.5)


def test_maintenance_status_blocks_plan_creation_and_scoring(tmp_path) -> None:
    (tmp_path / "config").mkdir()
    source = project_root() / "config" / "research.toml"
    text = source.read_text(encoding="utf-8").replace(
        'benchmark_status = "active"', 'benchmark_status = "maintenance"', 1
    )
    (tmp_path / "config" / "research.toml").write_text(text, encoding="utf-8")
    with pytest.raises(GateViolation, match="maintenance"):
        ensure_can_create_plan(tmp_path)


def test_privileged_specialist_and_oracle_are_excluded_from_implementable_frontier() -> None:
    assert is_oracle_candidate("oracle_charged_condition_specialist_arx_v2")
    assert is_oracle_candidate("privileged_same_condition_oracle_arx_v2")
    assert not is_oracle_candidate("contextual_gaussian_chow_liu_v1")
