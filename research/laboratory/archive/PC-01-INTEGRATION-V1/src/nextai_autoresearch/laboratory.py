"""Small preparation gate for the user-authorized laboratory restart."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from jsonschema.exceptions import ValidationError

from .config import load_config
from .schemas import validate_document
from .utils import load_json, project_root, sha256_file


CONTRACT_PATH = "research/laboratory/restart.json"


def laboratory_progress(root: Path | None = None) -> dict[str, Any]:
    """Resolve the bounded service queue from verified append-only completions.

    Progress cannot grant scoring authority or change the frozen restart limits.
    A preparation blocker is an operational state, not a doctor integrity error.
    """
    from .ledger import read_jsonl

    base = (root or project_root()).resolve()
    initial = laboratory_contract(base)
    milestones = {m["id"]: m for m in initial["milestones"]}
    events = [e for e in read_jsonl(base / "research/events.jsonl")
              if e.get("event") == "lab_milestone_progress"
              and e.get("restart_id") == initial["restart_id"] and e.get("milestone_id") == "PC-01"]
    default = {"next_action_id": initial["next_action_id"], "next_action": initial["next_action"],
               "service_cycles_used": 0, "service_cycles_cap": milestones["PC-01"]["max_service_cycles"],
               "service_budget_exhausted": False, "user_decision_required": False, "progress_source": CONTRACT_PATH}
    if not events:
        return default
    used, charged = 0, 0.0
    for event in events:
        attempt = event.get("attempt")
        if type(attempt) is not int or attempt != used+1 or attempt > default["service_cycles_cap"]:
            raise ValueError("PC-01 progress resets/skips/exceeds the service-cycle cap")
        if event.get("scoring_performed") is not False or event.get("training_performed") is not False:
            raise ValueError("PC-01 preparation event cannot certify training/scoring")
        budget = event.get("cumulative_budget", {})
        if budget.get("service_cycles_used") != attempt or budget.get("service_cycles_cap") != default["service_cycles_cap"]:
            raise ValueError("PC-01 progress budget differs from restart contract")
        minutes = budget.get("service_minutes_conservatively_charged")
        if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or not charged <= minutes <= 120:
            raise ValueError("PC-01 preparation minutes reset/exceed the total cap")
        if budget.get("total_fit_seconds_used") != 0 or budget.get("development_attempts_used") != 0:
            raise ValueError("PC-01 service progress cannot hide training attempts")
        charged = float(minutes)
        used = attempt
    latest = events[-1]
    expected_next = {"design_contract_completed": "PC-01-HARNESS",
                     "preparation_blocked": "PC-01-DECISION"}.get(latest.get("status"))
    if expected_next is None or latest.get("next_action_id") != expected_next:
        raise ValueError("Unrecognized PC-01 preparation transition; cannot unlock execution")
    artifacts = latest.get("artifact_sha256")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("PC-01 progress has no hash-linked artifacts")
    for relative, digest in artifacts.items():
        path = (base / relative).resolve()
        if not path.is_relative_to(base) or not path.is_file() or sha256_file(path) != digest:
            raise ValueError(f"PC-01 progress artifact missing or changed: {relative}")
    exhausted = used >= default["service_cycles_cap"]
    if exhausted and expected_next != "PC-01-DECISION":
        raise ValueError("PC-01 service cap exhausted without an explicit decision report")
    progress = {**default, "next_action_id": expected_next, "next_action": latest["next_action"],
            "service_minutes_accounted": charged, "remaining_service_minutes": max(0.0, 120-charged),
            "service_cycles_used": used, "service_budget_exhausted": exhausted,
            "user_decision_required": expected_next == "PC-01-DECISION",
            "progress_source": "research/events.jsonl", "completed_action_id": latest.get("action_id")}
    return _authorized_extension(base, progress)


def _authorized_extension(base: Path, progress: dict[str, Any]) -> dict[str, Any]:
    """One explicit user extension; never rewrite the original 2/2 accounting."""
    from datetime import datetime, timezone
    from .ledger import read_jsonl

    relative = "research/laboratory/PC-01-EXTENSION-20260905-V1.json"
    path = base / relative
    if not path.exists():
        return progress
    if sha256_file(path) != "863e659a69416c7efe96441f841e893e22fd436396822fcaa6679e4c6a237799":
        raise ValueError("PC-01 user extension changed")
    authorization = load_json(path)
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("action_id") == "PC-01-INTEGRATION"
              and e.get("event") == "laboratory_maintenance_started"]
    ends = [e for e in events if e.get("authorization_id") == authorization["id"]
            and e.get("event") == "lab_extension_completed"]
    if len(starts) != 1 or len(ends) > 1 or progress["service_cycles_used"] != 2:
        raise ValueError("PC-01 extension missing/repeated or original budget changed")
    if starts[0].get("authorization_sha256") != sha256_file(path):
        raise ValueError("PC-01 extension receipt does not match authorization")
    for event in ends:
        if event.get("training_performed") is not False or event.get("scoring_performed") is not False:
            raise ValueError("Service extension cannot certify training")
        if (type(event.get("service_cycles_used")) is not int or event["service_cycles_used"] != 1
                or type(event.get("minutes_charged")) not in (int, float)
                or not 0 <= event["minutes_charged"] <= 60):
            raise ValueError("Extension budget exceeded or reset")
        if not event.get("artifact_sha256"):
            raise ValueError("Extension completion requires immutable evidence")
        for rel, digest in event["artifact_sha256"].items():
            artifact = (base / rel).resolve()
            if not artifact.is_relative_to(base) or not artifact.is_file() or sha256_file(artifact) != digest:
                raise ValueError(f"Extension artifact changed: {rel}")
    expired = datetime.now(timezone.utc) >= datetime.fromisoformat(authorization["deadline_at"])
    active = not ends and not expired
    return {**progress, "extension_id": authorization["id"], "extension_cycles_used": 1,
            "extension_cycles_cap": 1, "extension_minutes_cap": 60,
            "extension_deadline": authorization["deadline_at"], "extension_complete": bool(ends),
            "next_action_id": "PC-01-INTEGRATION" if active else "PC-01-DECISION",
            "next_action": "Complete the single authorized no-training integration cycle before its deadline."
            if active else "Review integration receipt; further service or training needs a separate user decision.",
            "user_decision_required": not active}


def laboratory_contract(root: Path | None = None) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    config = load_config(base)
    setting = config.raw.get("laboratory", {})
    if setting.get("contract_path") != CONTRACT_PATH:
        raise ValueError("Laboratory contract_path must point to the protected restart contract")
    contract = load_json(base / CONTRACT_PATH)
    validate_document("laboratory_restart", contract, base)
    if contract["restart_id"] != setting.get("restart_id"):
        raise ValueError("Laboratory restart_id differs from config")
    if contract["protocol_version"] != config.protocol_version:
        raise ValueError("Laboratory protocol_version differs from config")
    for relative in contract["required_documents"]:
        path = (base / relative).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise ValueError(f"Missing or invalid laboratory document: {relative}")
    return contract


def laboratory_problems(root: Path | None = None, *, scoring: bool = False) -> list[str]:
    base = (root or project_root()).resolve()
    config = load_config(base)
    if config.protocol_version < 3:
        return []
    try:
        contract = laboratory_contract(base)
        laboratory_progress(base)
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        return [f"laboratory contract: {exc}"]
    problems = []
    if contract["status"] == "preparation_only" and config.benchmark_status != "maintenance":
        problems.append("laboratory preparation requires benchmark_status=maintenance")
    if scoring and not contract["scoring_authorized"]:
        problems.append(
            "laboratory scoring is not authorized: complete PC-01-CONTRACT and freeze a new claim-specific cohort"
        )
    return problems
