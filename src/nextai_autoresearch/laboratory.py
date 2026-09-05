"""Small preparation gate for the user-authorized laboratory restart."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from jsonschema.exceptions import ValidationError

from .config import load_config
from .schemas import validate_document
from .utils import load_json, project_root, sha256_file


CONTRACT_PATH = "research/laboratory/restart.json"
ACTIVATION_PATH = "research/laboratory/PC-01-ACTIVATION-20260905-V1.json"
ACTIVATION_SHA256 = "9ea8810d50a4495770dba9f774ce6d006d62ba0632eb346b271c46b1ed1ca6ca"
REPAIR_PATH = "research/plans/PC-01-TELEMETRY-REPAIR-V1.json"
REPAIR_SHA256 = "9cee710f1d927153ae7aa72962f22e1721f47707da19392cf0a1343d784377f1"
DEV2_PATH = "research/laboratory/PC-01-DEV2-20260905-V1.json"
DEV2_SHA256 = "d595da85d8a16f70fde42375579f5e7012804ee61ddc225b5313b185f5664008"
GPU_METADATA_PATH = "research/plans/PC-01-GPU-METADATA-V1.json"
GPU_METADATA_SHA256 = "f0d14d68e266a9701ab6aaa66638e1375618eb59d2acae284c915830de69ed8e"


def final_preparation_status(base: Path) -> dict | None:
    """One bounded adapter preparation, without execution authority."""
    from datetime import datetime, timezone
    from .ledger import read_jsonl
    from .pc01_final_transition import PLAN_PATH, PLAN_SHA256
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("event") == "laboratory_maintenance_started"
              and e.get("action_id") == "PC-01-FINAL-PREP"]
    path = base / PLAN_PATH
    if not path.exists() and not starts:
        return None
    if (not path.is_file() or sha256_file(path) != PLAN_SHA256 or len(starts) != 1
            or starts[0].get("plan_path") != PLAN_PATH or starts[0].get("plan_sha256") != PLAN_SHA256):
        raise ValueError("Final preparation authorization missing, changed or repeated")
    plan = load_json(path)
    if sha256_file(base / plan["metadata_receipt"]) != plan["metadata_receipt_sha256"]:
        raise ValueError("Final preparation metadata receipt changed")
    ends = [e for e in events if e.get("event") == "pc01_final_preparation_completed"]
    if len(ends) > 1:
        raise ValueError("Final preparation completed more than once")
    if ends:
        event = ends[0]
        relative = "research/laboratory/PC-01-FINAL-PREP-V1.receipt.json"
        if (event.get("receipt_path") != relative or sha256_file(base / relative) != event.get("receipt_sha256")
                or event.get("training_performed") is not False or event.get("scoring_performed") is not False):
            raise ValueError("Final preparation completion changed or scope exceeded")
    return {"complete": bool(ends), "expired": datetime.now(timezone.utc) >= datetime.fromisoformat(plan["deadline_at"]),
            "deadline_at": plan["deadline_at"], "plan_path": PLAN_PATH}


def gpu_metadata_status(base: Path) -> dict | None:
    """A separate bounded repair, never authority for another training attempt."""
    from datetime import datetime, timezone
    from .ledger import read_jsonl
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("event") == "laboratory_maintenance_started"
              and e.get("action_id") == "PC-01-GPU-METADATA"]
    path = base / GPU_METADATA_PATH
    if not path.exists() and not starts:
        return None
    if (not path.is_file() or sha256_file(path) != GPU_METADATA_SHA256 or len(starts) != 1
            or starts[0].get("plan_path") != GPU_METADATA_PATH
            or starts[0].get("plan_sha256") != GPU_METADATA_SHA256):
        raise ValueError("GPU metadata repair authorization missing, changed or repeated")
    plan = load_json(path)
    if sha256_file(base / plan["prior_dev_receipt"]) != plan["prior_dev_receipt_sha256"]:
        raise ValueError("GPU metadata repair cannot replace the completed dev receipt")
    ends = [e for e in events if e.get("event") == "pc01_gpu_metadata_completed"]
    if len(ends) > 1:
        raise ValueError("GPU metadata repair completed more than once")
    if ends:
        event = ends[0]
        relative = "research/laboratory/PC-01-GPU-METADATA-V1.receipt.json"
        if (event.get("receipt_path") != relative or sha256_file(base / relative) != event.get("receipt_sha256")
                or event.get("training_performed") is not False or event.get("scoring_performed") is not False):
            raise ValueError("GPU metadata completion receipt changed or scope exceeded")
    return {"complete": bool(ends), "expired": datetime.now(timezone.utc) >= datetime.fromisoformat(plan["deadline_at"]),
            "deadline_at": plan["deadline_at"], "plan_path": GPU_METADATA_PATH}


def dev2_authority(base: Path) -> dict | None:
    """Prospective one-attempt overlay; never edits or replenishes old authority."""
    from .ledger import read_jsonl
    from .utils import sha256_json
    events = [e for e in read_jsonl(base / "research/events.jsonl")
              if e.get("event") == "pc01_dev2_authorized"]
    path = base / DEV2_PATH
    if not path.exists() and not events:
        return None
    if (not path.is_file() or sha256_file(path) != DEV2_SHA256 or len(events) != 1
            or events[0].get("authorization_path") != DEV2_PATH
            or events[0].get("authorization_sha256") != DEV2_SHA256):
        raise ValueError("PC-01 second dev authorization missing, changed or repeated")
    authority = load_json(path)
    repair = telemetry_repair_status(base)
    if activation_authority(base) is None or not repair or not repair["complete"]:
        raise ValueError("Second dev requires the preserved first authority and completed repair")
    for relative, digest in authority["historical_anchors"].items():
        artifact = base / relative
        actual = (sha256_json(load_json(artifact)) if relative == "research/plans/EXP-20260905-0001.json"
                  else sha256_file(artifact))
        if actual != digest:
            raise ValueError(f"Second dev historical anchor changed: {relative}")
    if load_json(base / "research/results/EXP-20260905-0001.json")["execution"]["fit_seconds_charged"] != 1200:
        raise ValueError("Second dev cannot reset the previous fit charge")
    candidate = base / "src/nextai_autoresearch/candidates/pc01_byte_gpt_v1.py"
    if sha256_file(candidate) != authority["candidate_sha256"]:
        raise ValueError("Second dev requires unchanged candidate source")
    if sha256_file(base / authority["design_path"]) != authority["design_sha256"]:
        raise ValueError("Second dev design changed")
    return authority


def _dev2_plans(base: Path, authority: dict) -> list[dict]:
    from .pc01_execution import registered_plans
    from .utils import sha256_json
    plans = registered_plans(base)
    if (not 1 <= len(plans) <= 2 or plans[0]["experiment_id"] != "EXP-20260905-0001"
            or sha256_json(plans[0]) != authority["historical_anchors"]["research/plans/EXP-20260905-0001.json"]):
        raise ValueError("Second dev cannot omit, replace or reset historical registrations")
    for plan in plans[1:]:
        if (plan["candidate"] != authority["candidate"] or plan["phase"] != "dev"
                or plan["attempt"] != 2 or plan["development_seed"] != 1103
                or plan["benchmark"] != authority["cohort"] or plan["series_sha256"] is not None
                or plan["recipe_sha256"] != authority["recipe_sha256"]):
            raise ValueError("Second dev registration exceeds the exact approved scope")
    return plans


def telemetry_repair_status(base: Path) -> dict | None:
    """One user-authorized maintenance deliverable; never grants a model retry."""
    from datetime import datetime, timezone, timedelta
    from .ledger import read_jsonl
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("event") == "laboratory_maintenance_started"
              and e.get("action_id") == "PC-01-TELEMETRY-REPAIR"]
    path = base / REPAIR_PATH
    if not path.exists() and not starts:
        return None
    if (not path.is_file() or sha256_file(path) != REPAIR_SHA256 or len(starts) != 1
            or starts[0].get("plan_path") != REPAIR_PATH or starts[0].get("plan_sha256") != REPAIR_SHA256):
        raise ValueError("Telemetry repair authorization missing, changed or repeated")
    ends = [e for e in events if e.get("event") == "pc01_telemetry_repair_completed"]
    if len(ends) > 1:
        raise ValueError("Telemetry repair completed more than once")
    if ends:
        event = ends[0]
        relative = "research/laboratory/PC-01-TELEMETRY-REPAIR-V1.receipt.json"
        if (event.get("receipt_path") != relative or sha256_file(base / relative) != event.get("receipt_sha256")
                or event.get("training_performed") is not False or event.get("scoring_performed") is not False):
            raise ValueError("Telemetry repair completion receipt changed or scope exceeded")
    deadline = datetime.fromisoformat(starts[0]["created_at"]) + timedelta(minutes=45)
    return {"complete": bool(ends), "expired": datetime.now(timezone.utc) >= deadline,
            "deadline_at": deadline.isoformat(), "plan_path": REPAIR_PATH}


def activation_authority(base: Path) -> dict | None:
    """A separately hash-bound user decision, not a rewrite of the restart."""
    from .ledger import read_jsonl
    events = [e for e in read_jsonl(base / "research/events.jsonl")
              if e.get("event") == "pc01_activation_authorized"]
    path = base / ACTIVATION_PATH
    if not path.exists() and not events:
        return None
    if (not path.is_file() or sha256_file(path) != ACTIVATION_SHA256 or len(events) != 1
            or events[0].get("authorization_path") != ACTIVATION_PATH
            or events[0].get("authorization_sha256") != ACTIVATION_SHA256):
        raise ValueError("PC-01 activation authorization missing, changed or repeated")
    return load_json(path)


def pc01_scope_problems(base: Path, *, candidate: str | None = None,
                        phase: str | None = None, experiment_id: str | None = None,
                        series_freeze: bool = False) -> list[str]:
    """One registered development attempt; invalidation does not replenish it."""
    try:
        from .pc01_final_authority import authority as final_authority, scope as final_scope
        final = final_authority(base)
        if final is not None:
            return final_scope(base, final, candidate=candidate, phase=phase,
                               experiment_id=experiment_id, series_freeze=series_freeze)
        if final_preparation_status(base) is not None:
            return ["Final preparation never authorizes training or final access"]
        if gpu_metadata_status(base) is not None:
            return ["GPU metadata maintenance never authorizes dev/final/legacy scoring"]
        second = dev2_authority(base)
        if second is not None:
            plans = _dev2_plans(base, second)
            if load_config(base).benchmark_version != second["cohort"]:
                return ["Second dev cannot activate another cohort"]
            if experiment_id is not None:
                if len(plans) != 2 or plans[1]["experiment_id"] != experiment_id:
                    return ["Second dev authorization does not cover this plan"]
                return []
            if len(plans) != 1:
                return ["Second dev single additional registration already consumed"]
            if candidate != second["candidate"] or phase != "dev":
                return ["Second dev forbids final/legacy/different candidate execution"]
            return []
        authority = activation_authority(base)
        if authority is None:
            return ["laboratory scoring is not authorized"]
        from .pc01_execution import registered_plans
        plans = registered_plans(base)
        if experiment_id is not None:
            if len(plans) != 1 or plans[0]["experiment_id"] != experiment_id:
                return ["PC-01 single-attempt authorization does not cover this plan"]
            plan = plans[0]
            candidate, phase = plan["candidate"], plan["phase"]
            if plan["attempt"] != 1 or plan["development_seed"] != 1103 or plan["series_sha256"] is not None:
                return ["PC-01 authorized dev contract differs"]
        elif plans:
            return ["PC-01 single registered development attempt already consumed"]
        if candidate != authority["candidate"] or phase != "dev":
            return ["PC-01 authorization covers only pc01_byte_gpt_v1 dev; final/legacy execution forbidden"]
        if load_config(base).benchmark_version != authority["cohort"]:
            return ["PC-01 authorization cannot activate another cohort"]
        return []
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        return [f"PC-01 activation: {exc}"]


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
    progress = _authorized_extension(base, progress)
    from .pc01_closure import closure as pc01_closure, migration_completed
    historical = pc01_closure(base)
    if historical is not None:
        completed = migration_completed(base)
        return {**progress, "activation_id": historical["id"],
                "development_registrations_used": 2, "development_registrations_cap": 2,
                "final_registrations_used": 3, "final_registrations_cap": 3,
                "final_completed": 3, "final_access_authorized": False,
                "scoring_authorized": False,
                "user_decision_required": completed is not None,
                "next_action_id": "WT-01-CONTRACT" if completed is not None
                    else "PC-01-TELEMETRY-LIFECYCLE-MIGRATION",
                "next_action": "Review the verified migration before a separate WT-01 no-scoring contract-preparation cycle."
                    if completed is not None else
                    "Complete the bounded no-training lifecycle migration; no PC-01 retry or WT-01 scoring.",
                "pc01_historical_decision": historical["terminal_decision"]["decision"],
                "lifecycle_migration_complete": completed is not None}
    from .pc01_final_authority import authority as final_authority
    final = final_authority(base)
    if final is not None:
        stopped = final["terminal"]
        return {**progress, "activation_id": final["id"], "development_registrations_used": 2,
                "development_registrations_cap": 2, "final_registrations_used": len(final["finals"]),
                "final_registrations_cap": 3, "final_completed": final["completed"],
                "final_access_authorized": not stopped, "user_decision_required": stopped,
                "next_action_id": "PC-01-DECISION" if stopped else
                    ("PC-01-FINAL-FREEZE" if not final["series_frozen"] else f"PC-01-FINAL-{final['completed']+1}"),
                "next_action": "Review all preserved final outcomes; no retry or promotion." if stopped else
                    "Execute at most one unchanged final replica this cycle, under the frozen three-replica authority."}
    authority = activation_authority(base)
    if authority is not None:
        from .pc01_execution import registered_plans
        plans = registered_plans(base)
        from .ledger import latest_plan_statuses
        terminal = bool(plans and ((base / "research/results" / f"{plans[0]['experiment_id']}.json").exists()
                                  or plans[0]["experiment_id"] in latest_plan_statuses(base)))
        # Historical 2/2 + 1/1 service accounting is retained in progress.
        progress.update(activation_id=authority["id"], development_registrations_used=len(plans),
                        development_registrations_cap=1, final_access_authorized=False,
                        user_decision_required=terminal,
                        next_action_id="PC-01-DECISION" if terminal else "PC-01-DEV-1",
                        next_action="Review the one preserved development outcome; no automatic retry."
                        if terminal else "Validate activation, register and execute only the authorized development attempt.")
    repair = telemetry_repair_status(base)
    if repair is not None:
        stopped = repair["complete"] or repair["expired"]
        progress.update(telemetry_repair=repair, user_decision_required=stopped,
                        next_action_id="PC-01-DECISION" if stopped else "PC-01-TELEMETRY-REPAIR",
                        next_action="Review the bounded no-training repair; another dev attempt requires separate authority."
                        if stopped else "Repair and validate synthetic telemetry only; no training or scoring.")
    second = dev2_authority(base)
    if second is not None:
        plans = _dev2_plans(base, second)
        from .ledger import latest_plan_statuses
        terminal = len(plans) == 2 and (
            (base / "research/results" / f"{plans[1]['experiment_id']}.json").exists()
            or plans[1]["experiment_id"] in latest_plan_statuses(base))
        progress.update(activation_id=second["id"], development_registrations_used=len(plans),
                        development_registrations_cap=2, final_access_authorized=False,
                        user_decision_required=terminal,
                        next_action_id="PC-01-DECISION" if terminal else "PC-01-DEV-2",
                        next_action="Review the preserved second dev outcome; no further attempt authorized."
                        if terminal else "Register and execute one fresh v2 dev, unchanged recipe, no final access.")
    metadata = gpu_metadata_status(base)
    if metadata is not None:
        stopped = metadata["complete"] or metadata["expired"]
        progress.update(gpu_metadata_repair=metadata, user_decision_required=stopped,
                        next_action_id="PC-01-DECISION" if stopped else "PC-01-GPU-METADATA",
                        next_action="Review the no-training metadata repair; no final or further dev authorized."
                        if stopped else "Validate scoped GPU metadata capture and completeness; no training or scoring.")
    preparation = final_preparation_status(base)
    if preparation is not None:
        stopped = preparation["complete"] or preparation["expired"]
        progress.update(final_preparation=preparation, user_decision_required=stopped,
                        next_action_id="PC-01-DECISION" if stopped else "PC-01-FINAL-PREP",
                        next_action="Review prepared final-series adapter; execution requires separate authorization."
                        if stopped else "Prepare and test the exact v2-to-v3 bridge; no training or final access.")
    return progress


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
    authority = activation_authority(base)
    second = dev2_authority(base)
    from .pc01_closure import closure as pc01_closure, migration_completed
    historical = pc01_closure(base)
    if historical is not None:
        completed = migration_completed(base)
        return {**contract, "status": "preparation_only", "scoring_authorized": False,
                "maintenance_plan": "research/plans/PC-01-TELEMETRY-LIFECYCLE-MIGRATION-V1.json",
                "activation_id": historical["id"], "original_status": contract["status"],
                "lifecycle_migration_complete": completed is not None}
    from .pc01_final_authority import authority as final_authority
    final = final_authority(base)
    if final is not None:
        return {**contract, "status": "final_authorized", "scoring_authorized": not final["terminal"],
                "activation_id": final["id"], "original_status": contract["status"]}
    if final_preparation_status(base) is not None:
        if second is not None:
            _dev2_plans(base, second)
        gpu_metadata_status(base)
        from .pc01_final_transition import PLAN_PATH
        return {**contract, "status": "preparation_only", "scoring_authorized": False,
                "maintenance_plan": PLAN_PATH}
    if gpu_metadata_status(base) is not None:
        if second is not None:
            _dev2_plans(base, second)
        return {**contract, "status": "preparation_only", "scoring_authorized": False,
                "maintenance_plan": GPU_METADATA_PATH}
    if second is not None:
        _dev2_plans(base, second)
        if config.benchmark_status == "active" and config.benchmark_version != second["cohort"]:
            raise ValueError("Second dev cannot activate another cohort")
        return {**contract, "status": "dev_authorized", "scoring_authorized": True,
                "activation_id": second["id"], "original_status": contract["status"]}
    if telemetry_repair_status(base) is not None:
        return {**contract, "status": "preparation_only", "scoring_authorized": False,
                "maintenance_plan": REPAIR_PATH}
    if authority is not None:
        if config.benchmark_status == "active" and config.benchmark_version != authority["cohort"]:
            raise ValueError("PC-01 authorization cannot activate another cohort")
        return {**contract, "status": "dev_authorized", "scoring_authorized": True,
                "activation_id": authority["id"], "original_status": contract["status"]}
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
    if contract["status"] == "dev_authorized":
        from .pc01_execution import registered_plans
        try:
            plans = registered_plans(base)
            if dev2_authority(base) is not None:
                _dev2_plans(base, dev2_authority(base))
            elif plans:
                problems.extend(pc01_scope_problems(base, experiment_id=plans[0]["experiment_id"]))
        except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
            problems.append(f"PC-01 activation registrations: {exc}")
    if contract["status"] == "preparation_only" and config.benchmark_status != "maintenance":
        problems.append("laboratory preparation requires benchmark_status=maintenance")
    if scoring and not contract["scoring_authorized"]:
        problems.append(
            "laboratory scoring is not authorized: complete PC-01-CONTRACT and freeze a new claim-specific cohort"
        )
    return problems
