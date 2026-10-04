from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v2 as v2
from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v3 as v3
from nextai_autoresearch.cli import _wt_prequential_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


ROLES = [
    "wt_action_conditioned_predictive_state_v1",
    "wt_source_identical_frozen_predictive_state_v1",
    "wt_source_identical_observation_history_v1",
]
NEW_CONTROLS = ["wt_coverage_aware_spectral_psr_v1", "wt_train_only_discretized_cssr_v1"]
SOURCE_CONTRACT = (
    "history_future_windows_rank_features_control_conditioning_constants_initialization_"
    "fit_order_update_schedule_and_output_identical_except_preregistered_predictive_state_"
    "learning_freeze_or_observation_history_projection_v1"
)


def _plan() -> dict:
    active = load_config(project_root())
    raw = copy.deepcopy(active.raw)
    raw["project"]["benchmark_version"] = v3.BENCHMARK_VERSION
    config = ResearchConfig(raw, active.path)
    protocol = _wt_prequential_protocol(config)
    metrics = list(protocol["pareto_capability_metrics"])
    return {
        "schema_version": 1, "experiment_id": "EXP-20990101-9996",
        "parent_experiment_id": None, "created_at": "2099-01-01T00:00:00Z",
        "status": "planned", "hypothesis_id": "HYP-9996",
        "title": "WT predictive-state v3 fixture",
        "research_question": "Can a compact predictive state improve real changepoint forecasts?",
        "architecture_family": "causal_predictive_state",
        "candidates": [*ROLES, *v3.BASELINES],
        "benchmark": v3.BENCHMARK_VERSION, "evaluator_sha256": "a" * 64,
        "budget": "quick", "matrix": {
            "knowledge_sizes": [18, 36, 54], "reasoning_depths": [16, 32, 96],
            "queries_per_cell": 18, "seed_policy": {
                "method": "runner_random_v1", "count": 1,
                "minimum": 1_000_000, "maximum": 2_147_483_647,
            },
        },
        "primary_metrics": metrics,
        "metric_directions": {
            name: "maximize" if name == "stable_rollout_rate" else "minimize"
            for name in metrics
        },
        "wt_prequential_protocol": protocol,
        "predicted_outcome": "No candidate or score exists in this migration fixture.",
        "falsification_criteria": ["Reject any changed historical WT behavior."],
        "promotion_criteria": ["A service fixture cannot promote."],
        "alternative_explanations": ["Role wiring could be incomplete."],
        "confounds": ["No candidate exists yet."],
        "outcome_policy": {"positive": "Allow later preregistration only.",
                           "null": "Keep maintenance.",
                           "negative": "Do not activate v3."},
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }


def test_v3_preserves_v2_evaluator_and_adds_only_future_roles_and_controls() -> None:
    assert v3.run_suite is v2.run_suite
    assert v3.development_smoke is v2.development_smoke
    assert v3.verify_static_contract() == v2.verify_static_contract()
    assert v3.BASELINES == (*v2.BASELINES, *NEW_CONTROLS)
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    protocol = plan["wt_prequential_protocol"]
    assert protocol["causal_roles"] == ROLES
    assert protocol["source_identical_contract"] == SOURCE_CONTRACT
    assert protocol["classical_baselines"] == list(v3.BASELINES)


def test_v3_schema_rejects_missing_role_or_new_control() -> None:
    for missing in (ROLES[1], NEW_CONTROLS[0]):
        plan = copy.deepcopy(_plan())
        plan["candidates"].remove(missing)
        with pytest.raises(ValidationError):
            validate_document("experiment_plan", plan, project_root())
