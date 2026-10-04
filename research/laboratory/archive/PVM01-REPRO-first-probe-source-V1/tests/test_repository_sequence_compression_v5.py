from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v4 as v4
from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v5 as v5
from nextai_autoresearch.cli import _compression_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


ROLES = [
    "surprise_gated_transition_machine_byte",
    "source_identical_dense_transition_machine_byte",
    "source_identical_frozen_transition_machine_byte",
]
CONTRACT = (
    "state_width_transition_map_constants_initialization_data_order_context_input_"
    "update_output_identical_except_preregistered_surprise_gate_dense_clock_and_"
    "transition_learning_v1"
)


def _plan() -> dict:
    active = load_config(project_root())
    raw = copy.deepcopy(active.raw)
    raw["project"]["benchmark_version"] = v5.BENCHMARK_VERSION
    config = ResearchConfig(raw, active.path)
    protocol = _compression_protocol(config)
    metrics = protocol["pareto_capability_metrics"]
    return {
        "schema_version": 1, "experiment_id": "EXP-20990101-9997",
        "parent_experiment_id": None, "created_at": "2026-09-01T00:00:00Z",
        "status": "planned", "hypothesis_id": "HYP-9997", "title": "v5 fixture",
        "research_question": "Does the prospective source-identical contract validate?",
        "architecture_family": "event_driven_transition_machine", "candidates": [
            *ROLES, *raw["compression"]["classical_baselines"],
        ], "benchmark": v5.BENCHMARK_VERSION, "evaluator_sha256": "a" * 64,
        "budget": "quick", "matrix": {"knowledge_sizes": [8, 20, 32],
            "reasoning_depths": [4, 16, 64], "queries_per_cell": 8,
            "seed_policy": {"method": "runner_random_v1", "count": 1,
                "minimum": 1_000_000, "maximum": 2_147_483_647}},
        "primary_metrics": metrics,
        "metric_directions": {
            name: ("maximize" if name == "accuracy" else "minimize")
            for name in metrics
        },
        "compression_protocol": protocol, "predicted_outcome": "No score in migration.",
        "falsification_criteria": ["Reject any changed historical behavior."],
        "promotion_criteria": ["A service fixture cannot promote."],
        "alternative_explanations": ["Role wiring could be incomplete."],
        "confounds": ["No candidate exists yet."],
        "outcome_policy": {"positive": "Allow later preregistration.",
            "null": "Keep maintenance.", "negative": "Do not activate v5."},
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }


def test_v5_reexports_v4_and_changes_only_prospective_roles() -> None:
    assert v5.CORPUS == v4.CORPUS
    assert v5.SEGMENT_MULTIPLIER == v4.SEGMENT_MULTIPLIER
    assert v5.make_training is v4.make_training
    assert v5.run_suite is v4.run_suite
    assert v5.verify_static_contract() == v4.verify_static_contract()
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    assert plan["compression_protocol"]["causal_roles"] == ROLES
    assert plan["compression_protocol"]["source_identical_contract"] == CONTRACT


def test_v5_schema_rejects_historical_v4_roles() -> None:
    plan = _plan()
    plan["compression_protocol"]["causal_roles"] = [
        "learned_conditional_execution_byte",
        "source_identical_all_experts_byte",
        "source_identical_frozen_router_byte",
    ]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", plan, project_root())


def test_service_cycle_did_not_create_transition_machine_candidate() -> None:
    check = load_json(
        project_root()
        / "research/checks/repository_transition_machine_v5_service_cycle_170.json"
    )
    assert check["service_only"] is True
    assert check["candidate_created"] is False
    assert check["scoring_performed"] is False
