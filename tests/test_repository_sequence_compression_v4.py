from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v3 as v3
from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v4 as v4
from nextai_autoresearch.cli import _compression_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


ROLES = [
    "learned_conditional_execution_byte",
    "source_identical_all_experts_byte",
    "source_identical_frozen_router_byte",
]


def _plan() -> dict:
    active = load_config(project_root())
    raw = copy.deepcopy(active.raw)
    raw["project"]["benchmark_version"] = v4.BENCHMARK_VERSION
    config = ResearchConfig(raw, active.path)
    protocol = _compression_protocol(config)
    metrics = protocol["pareto_capability_metrics"]
    return {
        "schema_version": 1, "experiment_id": "EXP-20990101-9998",
        "parent_experiment_id": None, "created_at": "2026-09-01T00:00:00Z",
        "status": "planned", "hypothesis_id": "HYP-9998", "title": "v4 fixture",
        "research_question": "Does the prospective source-identical contract validate?",
        "architecture_family": "conditional_execution", "candidates": [
            *ROLES, *raw["compression"]["classical_baselines"],
        ], "benchmark": v4.BENCHMARK_VERSION, "evaluator_sha256": "a" * 64,
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
            "null": "Keep maintenance.", "negative": "Do not activate v4."},
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }


def test_v4_is_additive_reexport_with_only_prospective_roles_changed() -> None:
    assert v4.CORPUS == v3.CORPUS
    assert v4.SEGMENT_MULTIPLIER == v3.SEGMENT_MULTIPLIER
    assert v4.make_training is v3.make_training
    assert v4.run_suite is v3.run_suite
    assert v4.verify_static_contract() == v3.verify_static_contract()
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    assert plan["compression_protocol"]["causal_roles"] == ROLES


def test_v4_schema_rejects_old_or_mislabeled_causal_roles() -> None:
    plan = _plan()
    plan["compression_protocol"]["causal_roles"][0] = "orthogonal_reservoir_byte"
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", plan, project_root())
