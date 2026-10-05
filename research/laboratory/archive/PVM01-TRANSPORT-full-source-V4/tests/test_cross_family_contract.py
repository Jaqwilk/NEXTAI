from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.metrics import aggregate_trials
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


def _plan() -> dict:
    return {
        "schema_version": 1,
        "experiment_id": "EXP-20260830-9997",
        "parent_experiment_id": None,
        "created_at": "2026-08-30T12:15:00Z",
        "status": "planned",
        "hypothesis_id": "HYP-0015",
        "title": "Cross-family shared representation quick",
        "research_question": "Does one unchanged learner transfer across unseen worlds?",
        "architecture_family": "cross_family_shared_representation",
        "candidates": ["shared_candidate", "specialist_suite"],
        "benchmark": "cross_family_shared_representation_v1",
        "evaluator_sha256": "a" * 64,
        "budget": "quick",
        "matrix": {
            "knowledge_sizes": [8, 32],
            "reasoning_depths": [1, 4, 6],
            "queries_per_cell": 8,
            "seed_policy": {
                "method": "runner_random_v1",
                "count": 1,
                "minimum": 1_000_000,
                "maximum": 2_147_483_647,
            },
        },
        "primary_metrics": ["transfer_accuracy", "minimum_family_accuracy"],
        "metric_directions": {
            "transfer_accuracy": "maximize",
            "minimum_family_accuracy": "maximize",
        },
        "transfer_protocol": {
            "families": ["probabilistic", "predictive", "local", "program"],
            "training_world_seeds": [1103],
            "test_world_seed_source": "runner_scoring_seeds",
            "shared_candidate": "shared_candidate",
            "specialist_baselines": ["specialist_suite"],
            "family_specific_rules": "forbidden",
            "family_labels": "forbidden",
            "test_tuning": "forbidden",
            "declared_horizons": [1, 4, 16],
            "invalidation_rules": ["Invalidate on any train and test seed collision."],
        },
        "predicted_outcome": "The shared learner transfers without family-specific rules.",
        "falsification_criteria": ["Any family mean falls below the preregistered gate."],
        "promotion_criteria": ["A replicated screen is non-dominated across all families."],
        "alternative_explanations": ["Pooling more observations may explain the apparent benefit."],
        "confounds": ["Family identity may leak through serialization shape."],
        "outcome_policy": {
            "positive": "Run a replicated screen without promotion.",
            "null": "Keep the hypothesis proposed or make it dormant.",
            "negative": "Discard the implementation and preserve the result.",
        },
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }


def test_cross_family_plan_requires_transfer_protocol() -> None:
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    invalid = copy.deepcopy(plan)
    del invalid["transfer_protocol"]
    with pytest.raises(ValidationError, match="transfer_protocol"):
        validate_document("experiment_plan", invalid, project_root())


def test_cross_family_aggregation_exposes_weakest_family_and_costs() -> None:
    base = {
        "status": "complete", "knowledge_size": 8, "reasoning_depth": 1,
        "mean_query_ops": 10, "mean_warm_query_ops": 10, "accuracy": 1.0,
        "warm_accuracy": 1.0, "continual_retention": 1.0, "p50_latency_us": 1,
        "p95_latency_us": 1, "fit_seconds": 1, "state_bytes": 16,
        "update_ops": 1, "update_latency_us": 1, "seed": 7,
        "meta_fit_ops": 100, "data_acquisition_ops": 50,
    }
    trials = [dict(base, world_family="a"), dict(base, world_family="b", accuracy=0.5)]
    summary = aggregate_trials(trials)
    assert summary["transfer_accuracy"] == 0.75
    assert summary["minimum_family_accuracy"] == 0.5
    assert summary["family_count"] == 2
    assert summary["meta_fit_ops"] == 100
    assert summary["data_acquisition_ops"] == 50
