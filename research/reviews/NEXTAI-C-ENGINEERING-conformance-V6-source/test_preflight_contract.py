from __future__ import annotations

import copy
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.config import load_config
from nextai_autoresearch import baseline_semantics
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.runner import _frontier
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


def test_final_schema_accepts_all_supervisor_outcomes_and_missing_metrics() -> None:
    root = project_root()
    result = load_json(root / "research/results/EXP-20260830-0059.json")
    template = copy.deepcopy(result["candidates"][0])
    candidates = []
    for name, status in (
        ("complete", "complete"), ("timeout", "timeout"), ("crash", "crash"),
        ("budget", "memory_limit"), ("missing", "complete"),
    ):
        row = copy.deepcopy(template)
        row["candidate"] = f"probe_{name}"
        row["status"] = status
        if status != "complete":
            row["trials"] = []
            row["summary"] = {"status": "failed", "completed_trials": 0, "total_trials": 0}
        elif name == "missing":
            row["trials"] = []
            row["summary"] = {"status": "complete", "completed_trials": 0, "total_trials": 0}
        candidates.append(row)
    result["candidates"] = candidates
    validate_document("experiment_result", result, root)


def test_metric_domains_are_central_and_conditional_log_loss_can_be_negative() -> None:
    root = project_root()
    result = load_json(root / "research/results/EXP-20260830-0059.json")
    result["candidates"][0]["summary"]["conditional_log_loss"] = -12.5
    validate_document("experiment_result", result, root)
    result["candidates"][0]["summary"]["accuracy"] = 1.01
    with pytest.raises(ValidationError, match="maximum of 1"):
        validate_document("experiment_result", result, root)


def test_timeout_and_missing_metrics_do_not_erase_declared_pareto_axes() -> None:
    plan = {
        "benchmark": "heldout_dronepropa_factor_recombination_v6",
        "primary_metrics": ["accuracy", "mean_query_ops"],
        "metric_directions": {"accuracy": "maximize", "mean_query_ops": "minimize"},
    }
    rows = [
        {"candidate": "complete", "status": "complete", "summary": {
            "status": "complete", "accuracy": 1.0, "mean_query_ops": 2.0,
        }},
        {"candidate": "timeout", "status": "timeout", "summary": {"status": "failed"}},
        {"candidate": "missing", "status": "complete", "summary": {
            "status": "complete", "accuracy": 1.0,
        }},
    ]
    frontier, axes = _frontier(rows, plan, load_config(project_root()))
    assert axes == {"maximize": ["accuracy"], "minimize": ["mean_query_ops"]}
    assert frontier == ["complete"]


def test_three_family_v2_pareto_uses_universal_capability_axes() -> None:
    capability = [
        "transfer_accuracy", "minimum_family_accuracy", "stable_rollout_rate",
        "normalized_rmse", "data_acquisition_ops", "preprocessing_ops", "fit_ops",
        "adaptation_ops", "mean_query_ops", "state_bytes", "peak_state_bytes",
        "mean_bytes_touched", "workload_ops_r1", "workload_ops_r4", "workload_ops_r16",
    ]
    directions = {
        name: "maximize" if name in {
            "transfer_accuracy", "minimum_family_accuracy", "stable_rollout_rate"
        } else "minimize" for name in capability
    }
    plan = {
        "benchmark": "heldout_three_family_continuous_transfer_v2",
        "primary_metrics": [*capability, "shared_vs_independent_gain", "cross_family_transfer_gain"],
        "metric_directions": {
            **directions, "shared_vs_independent_gain": "maximize",
            "cross_family_transfer_gain": "maximize",
        },
        "continuous_transfer_protocol": {"pareto_capability_metrics": capability},
    }
    def summary(accuracy: float, cost: float) -> dict:
        row = {name: cost for name in capability}
        row.update({
            "status": "complete", "accuracy": accuracy,
            "transfer_accuracy": accuracy, "minimum_family_accuracy": accuracy,
            "stable_rollout_rate": 1.0, "normalized_rmse": 1.0 - accuracy,
        })
        return row
    rows = [
        {"candidate": "shared", "status": "complete", "summary": {
            **summary(.99, 2.0), "shared_vs_independent_gain": .1,
        }},
        {"candidate": "baseline", "status": "complete", "summary": summary(.98, 1.0)},
    ]
    frontier, axes = _frontier(rows, plan, load_config(project_root()))
    assert frontier == ["shared", "baseline"]
    assert axes == {
        "maximize": capability[:3],
        "minimize": capability[3:],
    }
    assert "shared_vs_independent_gain" not in axes["maximize"]


def test_preflight_certificate_detects_any_covered_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = project_root()
    certificate = verify_preflight_certificate(root)
    original = baseline_semantics._preflight_payload
    monkeypatch.setattr(
        baseline_semantics, "_preflight_payload",
        lambda base: {**original(base), "evaluator_sha256": "0" * 64},
    )
    with pytest.raises(RuntimeError, match="does not match"):
        verify_preflight_certificate(root)
