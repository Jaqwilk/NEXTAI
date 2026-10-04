"""Preserve outer timeout, account all wall time and validate its saved checkpoint."""
import json
import math
from pathlib import Path

from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
failed_path = b/"research/reviews/PVM01-EXPOSURE-postrun-gates-V1.json"
failed = json.loads(failed_path.read_text())
assert failed["returncode"] == 124
extra = math.ceil(failed["wall_seconds"])+5-failed["seconds_charged"]
assert extra == 13
events = read_jsonl(b/"research/events.jsonl")
paid = {e["charge_id"]:e["seconds"] for e in events if e.get("event") == "research_program_aux_fit_charged"}
used = sum(paid.get(e["charge_id"],e["seconds_cap"]) for e in events
           if e.get("event") == "research_program_aux_fit_reserved"
           and e.get("charge_id", "").startswith("PVM01-EXPOSURE-"))
assert used+extra <= 1800
charge_id = "PVM01-EXPOSURE-postrun-gates-V1-wall-overflow"
assert not any(e.get("charge_id") == charge_id for e in events)
auxiliary_reserve(b,charge_id,extra)
auxiliary_charge(b,charge_id,extra)
checkpoint_path = b/"research/reviews/PVM01-EXPOSURE-postrun-state-integrity-V1.json"
saved = json.loads(checkpoint_path.read_text())
raw = (b/"research/reviews/PVM01-EXPOSURE-postrun-gates-V1.stdout.txt").read_text(encoding="utf8")
assert saved["doctor_and_lab_status_pass"] and saved["all80_semantic_records_valid"]
assert "Doctor: PASS" in raw and "Terminal maintenance, no pending paid run, active continuation, old budgets and all80 semantics: PASS" in raw
assert saved["integrity"]["ok"] and saved["integrity"]["checked_files"] == 1166
assert not any((b/name).exists() for name in ("STOP","PAUSE","research/run.lock"))
current = verify_manifest(b)
assert current["ok"] and current["checked_files"] == 1166
assert current["candidate_bundle_sha256"] == saved["integrity"]["candidate_bundle_sha256"]
assert current["evaluator_sha256"] == saved["integrity"]["evaluator_sha256"]
verify_preflight_certificate(b)
value = status(b)
assert value["study_terminal"] and not value["paid_run_pending"] and not value["program_terminal"]
assert not value["scoring_authorized"] and value["registration_attempts_used"] == 8
assert value["continuation_registration_attempts_used"] == 5 and value["pending_fit_reservation_seconds"] == 0
target = b/"research/reviews/PVM01-EXPOSURE-postrun-checkpoint-V2.json"
assert not target.exists()
atomic_write_json(target,{"created_at":utc_now(),"failed_outer_check_preserved":True,
    "failed_receipt_sha256":sha256_file(failed_path),"original_outer_returncode":124,
    "saved_checkpoint_sha256":sha256_file(checkpoint_path),
    "doctor_lab_and_semantics_completed_inside_V1_before_timeout":True,
    "doctor_lab_not_repeated_in_this_checkpoint_check":True,
    "current_source_manifest_preflight_and_terminal_budget_checked":True,
    "wall_overflow_additional_seconds":extra,"V1_combined_charge_seconds":failed["seconds_charged"]+extra,
    "integrity":current,"programme":value,"new_paid_retry_fit_seed_or_scoring":False})
note = b/"research/analyses/EXP-20261004-0008-ADDENDUM-V2.md"
assert not note.exists()
note.write_text("# EXP-20261004-0008 — validation bookkeeping, ADDENDUM V2\n\n"
    "The scientific result, frozen INCONCLUSIVE decision and complete ADDENDUM V1 are unchanged. "
    "Postrun gates V1 completed doctor, lab status, source integrity, preflight and all 80 semantic checks, "
    "then the outer command timed out. Its return code124, raw outputs and120s charge remain. "
    "Measured wall127.3117658s is now conservatively covered by an additional13s, for133s combined.\n\n"
    "Postrun checkpoint V2 separately verifies the saved completion receipt and unchanged current source/manifest, "
    "preflight and terminal budget; it does not rerun doctor/lab or any model. The auxiliary wrapper V2 uses "
    "a total deadline including report creation. Original source validation and final exact accounting appear "
    "in the immutable cycle310 completion receipt. All failures and costs remain; no paid-plan retry, "
    "new research data, seed, fit or gate relaxation occurred.\n",encoding="utf8",newline="\n")
append_jsonl(b/"research/events.jsonl",{"event":"research_validation_timeout_accounting_addendum",
    "created_at":utc_now(),"experiment_id":"EXP-20261004-0008",
    "failed_outer_check_sha256":sha256_file(failed_path),"checkpoint_V2_sha256":sha256_file(target),
    "validation_addendum_path":note.relative_to(b).as_posix(),"validation_addendum_sha256":sha256_file(note),
    "extra_seconds_charged":extra,"frozen_decision_unchanged":"INCONCLUSIVE comparison"})
print("Saved doctor/lab completion, exact current source and terminal budget: PASS; timeout retained, total V1 charge133s")
