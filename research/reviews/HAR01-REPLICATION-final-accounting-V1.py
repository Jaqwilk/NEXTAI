"""Separately frozen bookkeeping; never starts experimental work."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import psutil
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path.cwd().resolve()
clone = root.parent / "NEXTAI-VALIDATION-20261002"
plan_rel = "research/plans/HAR01-REPLICATION-FINAL-ACCOUNTING-V1.json"
plan = json.loads((root / plan_rel).read_text(encoding="utf-8"))
complete = root / plan["previous_completion_path"]
assert sha256_file(complete) == plan["previous_completion_sha256"]
assert sha256_file(root / plan["human_authority_path"]) == plan["human_authority_sha256"]
assert not (clone / plan_rel).exists()
shutil.copyfile(root / plan_rel, clone / plan_rel)
binding = {"accounting_plan_path": plan_rel, "accounting_plan_sha256": sha256_file(root / plan_rel),
           "prior_receipt_sha256": sha256_file(complete), "additional_charge_id": plan["additional_charge_id"]}
append_jsonl(clone / "research/events.jsonl", {"event": "research_program_final_accounting_bound",
    "created_at": utc_now(), "program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", **binding})
auxiliary_reserve(clone, plan["additional_charge_id"], 450)
auxiliary_charge(clone, plan["additional_charge_id"], 450)
wallet = status(clone)
assert wallet["stage_b_registration_attempts_used"] == 2
assert abs(wallet["stage_b_compute_seconds_charged"] - 30919.55024020007) < 1e-7
assert wallet["fit_seconds_remaining"] >= 41000 and wallet["study_terminal"]
assert not wallet["paid_run_pending"] and not wallet["scoring_authorized"]
old = (root / "research/events.jsonl").read_bytes()
incoming = (clone / "research/events.jsonl").read_bytes()
assert incoming.startswith(old)
(root / "research/events.jsonl").write_bytes(incoming)
pid_proof = {str(pid): psutil.pid_exists(pid) for pid in (35856, 34780, 23712)}
now = datetime.now(timezone.utc)
earliest = datetime.fromisoformat("2026-10-07T00:50:21+00:00")
marker = datetime.fromisoformat("2026-10-07T00:50:48+00:00")
receipt = {"id": "HAR01-REPLICATION-FINAL-ACCOUNTING-COMPLETION-V1", "created_at": utc_now(), **binding,
    "previous_stage_charge_seconds": 5500, "additional_conservative_seconds": 450,
    "whole_stage_charged_seconds": 5950, "whole_stage_cap_seconds": 6000,
    "unused50_not_released": True, "registration_attempts_added": 0, "EXP": None,
    "scientific_workers": 0, "scientific_fit_seconds": 0,
    "B_registrations_used": 2, "B_seconds_charged": wallet["stage_b_compute_seconds_charged"],
    "B_seconds_remaining": wallet["fit_seconds_remaining"], "protected_other_seconds": 41000,
    "protected_other_registrations": 6, "original_controller250_subcap_overrun": True,
    "elapsed_from_marker_seconds_at_receipt": (now-marker).total_seconds(),
    "conservative_elapsed_from_earliest_launch_seconds_at_receipt": (now-earliest).total_seconds(),
    "original250_overrun_lower_bound_seconds_at_receipt": max(0, (now-marker).total_seconds()-250),
    "final_publication_included_in_prepaid700_envelope_until": plan["final_work_deadline_at"],
    "remaining_admin_envelope_seconds_at_receipt": max(0, 700-(now-earliest).total_seconds()),
    "postreturn_pid_exists": pid_proof, "pid_reuse_caveat": True,
    "study_terminal": True, "scoring": False, "whole_goal_complete": False,
    "wallet": wallet}
rel = "research/laboratory/HAR01-REPLICATION-FINAL-ACCOUNTING-COMPLETION-V1.json"
atomic_write_json(root / rel, receipt)
shutil.copyfile(root / rel, clone / rel)
print(json.dumps({"stage": 5950, "B": wallet["stage_b_compute_seconds_charged"],
                  "remaining": wallet["fit_seconds_remaining"], "drain_pid_exists": pid_proof}), flush=True)
