from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v5 as v5
from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v6 as v6
from nextai_autoresearch.cli import _compression_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


ROLES = [
    "selective_diagonal_state_space_byte_v1",
    "source_identical_fixed_selection_state_space_byte_v1",
    "source_identical_recurrence_disabled_state_space_byte_v1",
]
CONTRACT = (
    "embedding_state_width_diagonal_dynamics_readout_initialization_fit_order_"
    "context_input_update_output_constants_and_accounting_identical_except_"
    "preregistered_input_selection_and_recurrence_v1"
)


def _config(version: str) -> ResearchConfig:
    active = load_config(project_root())
    raw = copy.deepcopy(active.raw)
    raw["project"]["benchmark_version"] = version
    return ResearchConfig(raw, active.path)


def _plan() -> dict:
    config = _config(v6.BENCHMARK_VERSION)
    protocol = _compression_protocol(config)
    metrics = protocol["pareto_capability_metrics"]
    return {
        "schema_version": 1, "experiment_id": "EXP-20990101-9996",
        "parent_experiment_id": None, "created_at": "2026-09-01T00:00:00Z",
        "status": "planned", "hypothesis_id": "HYP-9996", "title": "v6 fixture",
        "research_question": "Does the prospective source-identical contract validate?",
        "architecture_family": "selective_diagonal_state_space", "candidates": [
            *ROLES, *config.raw["compression"]["classical_baselines"],
        ], "benchmark": v6.BENCHMARK_VERSION, "evaluator_sha256": "a" * 64,
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
            "null": "Keep maintenance.", "negative": "Do not activate v6."},
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }


def test_v6_reexports_v5_and_freezes_only_prospective_roles() -> None:
    assert v6.CORPUS == v5.CORPUS
    assert v6.SEGMENT_MULTIPLIER == v5.SEGMENT_MULTIPLIER
    assert v6.make_training is v5.make_training
    assert v6.run_suite is v5.run_suite
    assert v6.verify_static_contract() == v5.verify_static_contract()
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    assert plan["compression_protocol"]["causal_roles"] == ROLES
    assert plan["compression_protocol"]["role_implementation"] == (
        "selective_diagonal_state_space_byte_core_v1"
    )
    assert plan["compression_protocol"]["source_identical_contract"] == CONTRACT


def test_v6_schema_rejects_v5_roles() -> None:
    plan = _plan()
    plan["compression_protocol"]["causal_roles"] = [
        "surprise_gated_transition_machine_byte",
        "source_identical_dense_transition_machine_byte",
        "source_identical_frozen_transition_machine_byte",
    ]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", plan, project_root())


def test_v5_role_semantics_remain_unchanged() -> None:
    protocol = _compression_protocol(_config(v5.BENCHMARK_VERSION))
    assert protocol["causal_roles"] == [
        "surprise_gated_transition_machine_byte",
        "source_identical_dense_transition_machine_byte",
        "source_identical_frozen_transition_machine_byte",
    ]
    assert protocol["source_identical_contract"].startswith("state_width_transition_map_")
