"""Hash-bound scope gate for the single MUC-01 baseline calibration."""
from __future__ import annotations

from pathlib import Path

from .ledger import latest_plan_statuses, read_jsonl
from .utils import load_json, sha256_file


AUTHORITY_PATH = "research/laboratory/MUC-01-CALIBRATION-20260906-V1.json"
ACTIVATION_PATH = "research/plans/MUC-01-CALIBRATION-ACTIVATION-V1.json"
EXPECTED_CANDIDATES = ("dense_transformer_v1", "bm25_iterative_reader_v1", "symbolic_last_write_graph_v1")


def authority(base: Path):
    path = base / AUTHORITY_PATH
    if not path.is_file():
        return None
    value = load_json(path)
    if value.get("id") != "MUC-01-CALIBRATION-20260906-V1" or tuple(value.get("candidates", ())) != EXPECTED_CANDIDATES:
        raise ValueError("MUC-01 calibration authority changed")
    if value.get("experiment_registrations_cap") != 1 or value.get("runner_random_seeds") != 1 or value.get("automatic_retry") is not False:
        raise ValueError("MUC-01 calibration count or retry scope changed")
    if value.get("candidate_mechanism_implementation_authorized") is not False or value.get("wt_files_8_9_access_authorized") is not False:
        raise ValueError("MUC-01 calibration widened into forbidden work")
    review = load_json(base / value["review_receipt"])
    if review.get("status") != "complete":
        raise ValueError("REVIEW-01 is not complete")
    if not (base / ACTIVATION_PATH).is_file():
        raise ValueError("MUC-01 activation plan is missing")
    return value


def registered(base: Path):
    return [load_json(path) for path in sorted((base / "research/plans").glob("EXP-*.json")) if load_json(path).get("benchmark") == "mutable_contact_ledger_v1"]


def scope_problems(base: Path, experiment_id: str | None = None):
    try:
        value = authority(base)
        if value is None:
            return ["MUC-01 calibration authority is absent"]
        plans = registered(base)
        if len(plans) > 1:
            return ["MUC-01 calibration single registration cap exceeded"]
        if experiment_id is None:
            return [] if not plans else ["MUC-01 calibration registration already consumed"]
        if len(plans) != 1 or plans[0].get("experiment_id") != experiment_id:
            return ["MUC-01 calibration authority does not cover this plan"]
        plan = plans[0]
        if tuple(plan.get("candidates", ())) != EXPECTED_CANDIDATES or plan.get("benchmark") != value["benchmark"]:
            return ["MUC-01 plan roles or cohort differ from authority"]
        terminal = (base / "research/results" / f"{experiment_id}.json").exists() or experiment_id in latest_plan_statuses(base)
        if terminal:
            return ["MUC-01 calibration is terminal; no retry"]
        return []
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"MUC-01 calibration: {exc}"]


def status(base: Path):
    value = authority(base)
    if value is None:
        return None
    plans = registered(base)
    experiment_id = plans[0]["experiment_id"] if plans else None
    terminal = bool(experiment_id and ((base / "research/results" / f"{experiment_id}.json").exists() or experiment_id in latest_plan_statuses(base)))
    return {"id": value["id"], "registrations_used": len(plans), "registrations_cap": 1, "experiment_id": experiment_id, "terminal": terminal, "scoring_authorized": not terminal}
