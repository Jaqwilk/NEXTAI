"""Hash-bound authority and scope checks for the single WT-01 dev run."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import load_config
from .ledger import latest_plan_statuses, read_jsonl, research_dir
from .utils import load_json, sha256_file, sha256_json


AUTHORITY_PATH = "research/laboratory/WT-01-DEV1-20260905-V1.json"
AUTHORITY_SHA256 = "18c46d6cbc221e1e6c102842aed0b192ad962c4e2e4741a1237452427d112c1b"
ACTIVATION_PLAN_PATH = "research/plans/WT-01-DEV1-ACTIVATION-V1.json"
ACTIVATION_PLAN_SHA256 = "4ec7a549a08a69bb662be574633e0c5c326e3cfcc35b10dde87cfed2e585fe30"
PARENT_RECEIPT_PATH = "research/laboratory/WT-01-DATA-HARNESS-V1.receipt.json"
PARENT_RECEIPT_SHA256 = "a8bc516e98781e9d337469ccf8c6465e5a28b308581a51d86a6825fa57537b72"
BENCHMARK = "wt01_causal_factorial_diagnostic_v1"
FACTORIAL_CANDIDATES = tuple(
    f"wt01_r{r}_u{u}_c{c}_v1" for r in (0, 1) for u in (0, 1) for c in (0, 1)
)
CLASSICAL_CONTROL = "wt01_var2_rls_bound_v1"
CANDIDATES = (*FACTORIAL_CANDIDATES, CLASSICAL_CONTROL)
PRIMARY_METRICS = (
    "stable_rollout_rate", "normalized_rmse", "worst_file_normalized_rmse",
    "worst_transition_normalized_rmse", "rollout_16_nrmse",
    "rollout_32_nrmse", "rollout_96_nrmse", "data_acquisition_ops",
    "preprocessing_ops", "fit_ops", "adaptation_ops", "mean_query_ops",
    "update_ops", "state_bytes", "peak_state_bytes", "mean_bytes_touched",
    "workload_ops_r1", "workload_ops_r4", "workload_ops_r16",
)


def authority(base: Path) -> dict[str, Any] | None:
    """Return the immutable authority, rejecting any missing/repeated anchor."""
    events = [
        event for event in read_jsonl(base / "research/events.jsonl")
        if event.get("event") == "wt01_dev1_authorized"
    ]
    path = base / AUTHORITY_PATH
    if not path.exists() and not events:
        return None
    if (
        not path.is_file()
        or sha256_file(path) != AUTHORITY_SHA256
        or len(events) != 1
        or events[0].get("authority_path") != AUTHORITY_PATH
        or events[0].get("authority_sha256") != AUTHORITY_SHA256
        or events[0].get("plan_path") != ACTIVATION_PLAN_PATH
        or events[0].get("plan_sha256") != ACTIVATION_PLAN_SHA256
    ):
        raise ValueError("WT-01 DEV-1 authority is missing, changed or repeated")
    if sha256_file(base / ACTIVATION_PLAN_PATH) != ACTIVATION_PLAN_SHA256:
        raise ValueError("WT-01 DEV-1 activation plan changed")
    if sha256_file(base / PARENT_RECEIPT_PATH) != PARENT_RECEIPT_SHA256:
        raise ValueError("WT-01 DEV-1 parent harness receipt changed")
    value = load_json(path)
    if (
        value.get("parent_receipt") != PARENT_RECEIPT_PATH
        or value.get("parent_receipt_sha256") != PARENT_RECEIPT_SHA256
        or value.get("development_attempts_authorized") != 1
        or value.get("final_data_access_authorized") is not False
        or value.get("automatic_retry_authorized") is not False
    ):
        raise ValueError("WT-01 DEV-1 authority scope changed")
    return value


def expected_protocol() -> dict[str, Any]:
    return {
        "authority_path": AUTHORITY_PATH,
        "authority_sha256": AUTHORITY_SHA256,
        "activation_plan_path": ACTIVATION_PLAN_PATH,
        "activation_plan_sha256": ACTIVATION_PLAN_SHA256,
        "corpus_id": "causal_chambers_wt_changepoints_v1",
        "manifest_sha256": "3d91f9b82644a9e9d0092a0baec0c012ed6b790f8331bdbb3b044cb0cbd5091e",
        "data_role": "visible_development_only",
        "split_unit": "whole_csv_file_sha256",
        "fit_files": [0, 1, 2, 3, 4, 5],
        "evaluation_files": [6, 7],
        "forbidden_files": [8, 9],
        "hidden_holdout": False,
        "fresh_physical_replications": 0,
        "replication_claim_permitted": False,
        "candidate_metadata": "anonymous_permuted_tensors_and_random_slot_only",
        "predict_then_atomic_artifact_then_reveal": True,
        "factorial_candidates": list(FACTORIAL_CANDIDATES),
        "classical_control": CLASSICAL_CONTROL,
        "historical_cell": "wt01_r1_u1_c1_v1",
        "primary_contrast": list(("wt01_r0_u1_c1_v1", "wt01_r1_u1_c1_v1")),
        "causal_attribution_threshold": 0.03343253453162794,
        "equivalence_absolute_tolerance": 1e-12,
        "equivalence_relative_tolerance": 1e-12,
        "knowledge_sizes": [18, 36, 54],
        "fit_depth": 32,
        "fit_horizon": 32,
        "declared_horizons": [16, 32, 96],
        "runner_random_channel_permutation": True,
        "normalization": "fit_files_only_mechanical_partition",
        "state_budget_bytes": 16_777_216,
        "declared_reuses": [1, 4, 16],
        "pareto_capability_metrics": list(PRIMARY_METRICS),
        "invalidation_rules": [
            "Invalidate on any frozen manifest or visible fit/development CSV hash mismatch.",
            "Invalidate if any file outside fit files 0-5 and development files 6-7 is loaded.",
            "Invalidate if a candidate receives native channel names, file identity, marker, timestamp or future control schedule.",
            "Invalidate if a target is revealed before the complete prediction artifact is validated and frozen.",
            "Invalidate if normalization or mechanical channel discovery reads development outcomes.",
            "Invalidate if a reveal mutates shared slow state or another anonymous slot.",
            "Invalidate if any of the eight factorial roles or the VAR(2)/ARX control is omitted or changed.",
            "Invalidate on a second registration, second seed, retry, post-score tuning, external model/API use, state breach or evaluator-integrity change.",
        ],
    }


def validate_plan(plan: dict[str, Any]) -> None:
    """Reject every plan outside the one prospectively approved design."""
    if plan.get("benchmark") != BENCHMARK or plan.get("budget") != "quick":
        raise ValueError("WT-01 DEV-1 benchmark/budget changed")
    if tuple(plan.get("candidates", ())) != CANDIDATES:
        raise ValueError("WT-01 DEV-1 requires the exact nine frozen roles")
    matrix = plan.get("matrix", {})
    policy = matrix.get("seed_policy", {})
    if (
        matrix.get("knowledge_sizes") != [18, 36, 54]
        or matrix.get("reasoning_depths") != [16, 32, 96]
        or matrix.get("queries_per_cell") != 18
        or "seeds" in matrix
        or policy != {
            "method": "runner_random_v1", "count": 1,
            "minimum": 1_000_000, "maximum": 2_147_483_647,
        }
    ):
        raise ValueError("WT-01 DEV-1 matrix or one-seed policy changed")
    if plan.get("wt01_factorial_protocol") != expected_protocol():
        raise ValueError("WT-01 DEV-1 protocol changed")
    if tuple(plan.get("primary_metrics", ())) != PRIMARY_METRICS:
        raise ValueError("WT-01 DEV-1 metrics changed")
    if plan.get("parent_experiment_id") is not None:
        raise ValueError("WT-01 causal diagnostic is not a replication plan")


def registered_plans(base: Path) -> list[dict[str, Any]]:
    """Find and authenticate the at-most-one WT-01 DEV-1 registration."""
    records = {
        str(event.get("experiment_id")): str(event.get("plan_sha256"))
        for event in read_jsonl(research_dir(base) / "plan_registry.jsonl")
    }
    plans: list[dict[str, Any]] = []
    for path in sorted((research_dir(base) / "plans").glob("EXP-*.json")):
        plan = load_json(path)
        protocol = plan.get("wt01_factorial_protocol")
        if not isinstance(protocol, dict) or protocol.get("authority_sha256") != AUTHORITY_SHA256:
            continue
        if records.get(path.stem) != sha256_json(plan):
            raise ValueError("WT-01 DEV-1 plan is not immutably registered")
        validate_plan(plan)
        plans.append(plan)
    if len(plans) > 1:
        raise ValueError("WT-01 DEV-1 single registration cap exceeded")
    return plans


def status(base: Path) -> dict[str, Any] | None:
    policy = authority(base)
    if policy is None:
        return None
    plans = registered_plans(base)
    terminal_statuses = latest_plan_statuses(base)
    terminal = False
    result_complete = False
    if plans:
        experiment_id = str(plans[0]["experiment_id"])
        result_complete = (research_dir(base) / "results" / f"{experiment_id}.json").is_file()
        terminal = result_complete or experiment_id in terminal_statuses
        starts = [
            event for event in read_jsonl(base / "research/events.jsonl")
            if event.get("event") == "experiment_scoring_started"
            and event.get("experiment_id") == experiment_id
        ]
        if len(starts) > 1:
            raise ValueError("WT-01 DEV-1 scoring started more than once")
    return {
        **policy,
        "plans": plans,
        "registrations_used": len(plans),
        "registrations_cap": 1,
        "result_complete": result_complete,
        "terminal": terminal,
    }


def scope_problems(base: Path, *, experiment_id: str | None = None) -> list[str]:
    """Authorize one creation or the exact registered run, never a retry."""
    try:
        policy = status(base)
        if policy is None:
            return ["WT-01 DEV-1 scoring is not authorized"]
        if load_config(base).benchmark_version != BENCHMARK:
            return ["WT-01 DEV-1 cannot activate another benchmark"]
        plans = policy["plans"]
        if experiment_id is None:
            return [] if not plans else ["WT-01 DEV-1 single registration already consumed"]
        if len(plans) != 1 or plans[0]["experiment_id"] != experiment_id:
            return ["WT-01 DEV-1 does not cover this experiment"]
        if policy["terminal"]:
            return ["WT-01 DEV-1 is terminal; retry or replacement is forbidden"]
        return []
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"WT-01 DEV-1 activation: {exc}"]
