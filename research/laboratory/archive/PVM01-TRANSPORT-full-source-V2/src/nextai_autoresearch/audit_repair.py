"""One new user decision; never replenishes the closed MUC v1 authority."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

from .ledger import latest_plan_statuses, read_jsonl
from .utils import load_json, sha256_file

AUTHORITY = "research/laboratory/AUDIT-REPAIR-20261002-V1.json"
PLAN = "research/plans/AUDIT-REPAIR-20261002-V1.json"
ROLES = ("dense_pair_transformer_v2", "bm25_pair_transformer_v2",
         "frozen_bm25_pair_transformer_v2", "symbolic_last_write_graph_v2")
COHORT = "mutable_contact_ledger_v2"


def status(base: Path) -> dict | None:
    path = base / AUTHORITY
    if not path.exists():
        return None
    events = read_jsonl(base / "research/events.jsonl")
    starts = [e for e in events if e.get("event") == "audit_repair_authorized"]
    if (len(starts) != 1 or starts[0].get("authorization_path") != AUTHORITY
            or starts[0].get("authorization_sha256") != sha256_file(path)):
        raise ValueError("Audit repair authority missing, changed or repeated")
    auth, plan = load_json(path), load_json(base / PLAN)
    if (auth.get("plan_path") != PLAN or auth.get("plan_sha256") != sha256_file(base / PLAN)
            or starts[0].get("plan_sha256") != auth["plan_sha256"]
            or plan.get("new_cohort") != COHORT or tuple(plan.get("candidates", ())) != ROLES
            or plan.get("experiment_registrations_cap") != 1 or plan.get("automatic_retry") is not False
            or plan.get("wt_files_8_9_access_authorized") is not False):
        raise ValueError("Audit repair prospective scope changed")
    registered = [load_json(p) for p in sorted((base / "research/plans").glob("EXP-*.json"))
                  if load_json(p).get("benchmark") == COHORT]
    if len(registered) > 1:
        raise ValueError("Audit repair one-registration cap exceeded")
    experiment_id = registered[0]["experiment_id"] if registered else None
    if registered and tuple(registered[0].get("candidates", ())) != ROLES:
        raise ValueError("Audit repair registered roles changed")
    terminal = bool(experiment_id and ((base / "research/results" / f"{experiment_id}.json").exists()
                                      or experiment_id in latest_plan_statuses(base)))
    ready = [e for e in events if e.get("event") == "audit_repair_harness_ready"]
    if len(ready) > 1:
        raise ValueError("Audit repair harness activation repeated")
    if ready and (ready[0].get("plan_sha256") != auth["plan_sha256"]
                  or sha256_file(base / ready[0]["receipt_path"]) != ready[0]["receipt_sha256"]):
        raise ValueError("Audit repair harness receipt changed")
    deadline = datetime.fromisoformat(auth["created_at"].replace("Z", "+00:00")) + timedelta(minutes=plan["maintenance_minutes_cap"])
    expired = datetime.now(timezone.utc) >= deadline
    return {"id": auth["id"], "ready": bool(ready), "terminal": terminal,
            "expired": expired, "deadline_at": deadline.isoformat(), "experiment_id": experiment_id,
            "registrations_used": len(registered), "registrations_cap": 1,
            "scoring_authorized": bool(ready) and not terminal and not expired}


def scope_problems(base: Path, experiment_id: str | None = None) -> list[str]:
    value = status(base)
    if value is None or not value["scoring_authorized"]:
        return ["Audit repair is preparation-only or terminal; no scoring/retry"]
    if experiment_id is None and value["registrations_used"]:
        return ["Audit repair one registration already consumed"]
    if experiment_id is not None and value["experiment_id"] != experiment_id:
        return ["Audit repair authority does not cover this experiment"]
    return []
