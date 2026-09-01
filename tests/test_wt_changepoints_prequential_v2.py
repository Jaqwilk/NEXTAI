from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v1 as v1
from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v2 as v2
from nextai_autoresearch.cli import _wt_prequential_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


ROLES = [
    "wt_multiresolution_lifting_v1",
    "wt_source_identical_single_scale_lifting_v1",
    "wt_source_identical_frozen_lifting_v1",
]
SOURCE_CONTRACT = (
    "dyadic_representation_constants_initialization_fit_order_update_schedule_output_"
    "identical_except_preregistered_cross_scale_composition_and_lifting_learning_v1"
)


def _plan() -> dict:
    config = load_config(project_root())
    wt = config.raw["wt_prequential"]
    metrics = [
        "stable_rollout_rate", "normalized_rmse", "worst_file_normalized_rmse",
        "worst_transition_normalized_rmse", "rollout_16_nrmse", "rollout_32_nrmse",
        "rollout_96_nrmse", "data_acquisition_ops", "preprocessing_ops", "fit_ops",
        "adaptation_ops", "mean_query_ops", "update_ops", "state_bytes",
        "peak_state_bytes", "mean_bytes_touched", "workload_ops_r1",
        "workload_ops_r4", "workload_ops_r16",
    ]
    protocol = {
        "corpus_id": wt["corpus_id"], "manifest_sha256": wt["manifest_sha256"],
        "split_unit": "whole_csv_file_sha256", "train_files": wt["train_files"],
        "development_files": wt["development_files"], "test_files": wt["test_files"],
        "candidate_metadata": "anonymous_permuted_tensors_and_random_slot_only",
        "predict_then_atomic_artifact_then_reveal": True,
        "shared_candidate": wt["shared_candidate"], "causal_roles": ROLES,
        "source_identical_contract": SOURCE_CONTRACT,
        "classical_baselines": wt["classical_baselines"],
        "knowledge_sizes": wt["knowledge_sizes"], "fit_depth": wt["fit_depth"],
        "fit_horizon": wt["fit_horizon"], "declared_horizons": wt["horizons"],
        "runner_random_channel_permutation": True,
        "normalization": "train_files_only_mechanical_partition",
        "state_budget_bytes": wt["state_budget_bytes"],
        "declared_reuses": wt["declared_reuses"],
        "minimum_meaningful_nrmse_effect": 0.1325268421060828,
        "saturation_nrmse": wt["saturation_nrmse"],
        "saturation_worst_file_nrmse": wt["saturation_worst_file_nrmse"],
        "pareto_capability_metrics": metrics,
        "invalidation_rules": wt["invalidation_rules"],
    }
    return {
        "schema_version": 1, "experiment_id": "EXP-20990101-9997",
        "parent_experiment_id": None, "created_at": "2099-01-01T00:00:00Z",
        "status": "planned", "hypothesis_id": "HYP-9997", "title": "WT v2 fixture",
        "research_question": "Can the future lifting causal contract validate?",
        "architecture_family": "multiresolution_lifting", "candidates": [
            *ROLES, *v2.BASELINES,
        ], "benchmark": v2.BENCHMARK_VERSION, "evaluator_sha256": "a" * 64,
        "budget": "quick", "matrix": {"knowledge_sizes": [18, 36, 54],
            "reasoning_depths": [16, 32, 96], "queries_per_cell": 18,
            "seed_policy": {"method": "runner_random_v1", "count": 1,
                "minimum": 1_000_000, "maximum": 2_147_483_647}},
        "primary_metrics": metrics,
        "metric_directions": {name: "maximize" if name == "stable_rollout_rate"
                              else "minimize" for name in metrics},
        "wt_prequential_protocol": protocol,
        "predicted_outcome": "No candidate or score exists in this migration fixture.",
        "falsification_criteria": ["Reject any changed historical WT behavior."],
        "promotion_criteria": ["A service fixture cannot promote a learner."],
        "alternative_explanations": ["Role wiring could be incomplete."],
        "confounds": ["No candidate exists yet."],
        "outcome_policy": {"positive": "Allow later preregistration only.",
            "null": "Keep the cohort in maintenance.",
            "negative": "Do not activate the v2 cohort."},
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }


def test_v2_reexports_v1_numerics_and_freezes_only_future_roles() -> None:
    assert v2.run_suite is v1.run_suite
    assert v2.development_smoke is v1.development_smoke
    assert v2.BASELINES == v1.BASELINES
    assert v2.verify_static_contract() == v1.verify_static_contract()
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    assert plan["wt_prequential_protocol"]["causal_roles"] == ROLES
    active = load_config(project_root())
    raw = copy.deepcopy(active.raw)
    raw["project"]["benchmark_version"] = v2.BENCHMARK_VERSION
    assert _wt_prequential_protocol(ResearchConfig(raw, active.path)) == (
        plan["wt_prequential_protocol"]
    )


def test_v2_schema_rejects_missing_or_mislabeled_causal_role() -> None:
    for mutation in ("missing", "mislabeled"):
        plan = copy.deepcopy(_plan())
        if mutation == "missing":
            plan["candidates"].remove(ROLES[1])
        else:
            plan["wt_prequential_protocol"]["causal_roles"][1] = "wt_lms_v1"
        with pytest.raises(ValidationError):
            validate_document("experiment_plan", plan, project_root())
