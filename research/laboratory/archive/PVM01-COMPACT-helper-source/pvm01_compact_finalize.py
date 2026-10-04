"""Seal immutable cycle accounting after successful original validation."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import auxiliary_charge, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
charge_id = "PVM01-COMPACT-final-accounting-allowance-V1"
assert any(e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id") == charge_id
           and e.get("seconds_cap") == 120 for e in read_jsonl(b / "research/events.jsonl"))
auxiliary_charge(b, charge_id, 120)
started = time.perf_counter()
atomic_write_json(b / f"research/reviews/{charge_id}.json", {
    "created_at": utc_now(), "seconds_cap": 120, "seconds_charged": 120,
    "charge_basis": "Full allowance retired conservatively for final ledger/report/hash verification and wrapper initialization or read-only bookkeeping outside timed child checks. May overcount; not measured research fit. No previous charge reduced.",
    "new_research_seed_data_fit_or_registration": False})
original = json.loads((b / "research/reviews/PVM01-COMPACT-original-source-validation-V1.json").read_text())
assert original["original_git_clean"] and all(c["returncode"] == 0 for c in original["commands"])
guard_path = b / "research/reviews/PVM01-COMPACT-final-history-source-index-V1.json"
guard = json.loads(guard_path.read_text())
assert guard["all_indexed_raw_sha256_valid"] and guard["old_scientific_bytes_and_append_only_prefixes_preserved"]
for name in ("PVM01-COMPACT-postanalysis-lifecycle-V2", "PVM01-COMPACT-postrun-gates-V2"):
    assert json.loads((b / f"research/reviews/{name}.json").read_text())["returncode"] == 0
repair_suites = list(ET.parse(b / "research/reviews/PVM01-COMPACT-postanalysis-lifecycle-V2.xml").getroot().iter("testsuite"))
assert all(sum(int(s.attrib.get(k,0)) for k in ("failures","errors","skipped")) == 0 for s in repair_suites)
identity = "EXP-20261004-0007"
diag = json.loads((b / f"research/reviews/{identity}-PVM01-full-diagnostics-V2.json").read_text())
value = status(b)
events = read_jsonl(b / "research/events.jsonl")
charges = [e for e in events if e.get("event") == "research_program_aux_fit_charged" and e.get("charge_id", "").startswith("PVM01-COMPACT-")]
reservations = [e for e in events if e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id", "").startswith("PVM01-COMPACT-")]
assert {e["charge_id"] for e in reservations} == {e["charge_id"] for e in charges}
auxiliary = sum(e["seconds"] for e in charges)
assert auxiliary <= 1800
assert value["registration_attempts_used"] == 7 and value["continuation_registration_attempts_used"] == 4
assert value["study_terminal"] and not value["paid_run_pending"] and not value["program_terminal"]
assert not value["scoring_authorized"] and value["pending_fit_reservation_seconds"] == 0
integrity = verify_manifest(b)
assert integrity["ok"] and integrity["checked_files"] == 1136
now = datetime.now(timezone.utc)
cycle_start = datetime.fromisoformat("2026-10-04T19:32:56+00:00")
deadline = datetime.fromisoformat("2026-10-04T23:32:56+00:00")
assert now < deadline
receipt_path = b / "research/laboratory/PVM01-CYCLE-309-COMPLETION-V1.receipt.json"
assert not receipt_path.exists()
receipt = {"id": "PVM01-CYCLE-309-COMPLETION-V1", "created_at": utc_now(), "cycle": 309,
    "experiment_id": identity, "plan_path": f"research/plans/{identity}.json", "plan_sha256": diag["plan_sha256"],
    "study_path": "research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json", "study_sha256": diag["study_sha256"],
    "result_sha256": diag["result_sha256"], "analysis_path": f"research/analyses/{identity}.md",
    "analysis_sha256": sha256_file(b / f"research/analyses/{identity}.md"),
    "decision": "DISCARD exact RFF512/512-step learned feature recipe", "whole_program_complete": False,
    "checks": {"preregistration_before_implementation_commit": "2ba76b6c9b2d4de1d76dcbcca7b3e4de5663c48a",
        "evaluated_source_commit": subprocess.check_output(["git", "rev-parse", "3338c78"], text=True).strip(),
        "validated_maintenance_source_commit": original["source_commit"],
        "preseed_full_suite_tests_passed": 1108, "postrun_full_suite_tests": 1108,
        "postrun_full_suite_initial_passed": 1107, "postrun_full_suite_initial_failed": 1,
        "initial_failure": "Lifecycle expected completed analysis before the report had been written; first doctor found the same missing file.",
        "postanalysis_targeted_lifecycle_and_report_tests_passed": sum(int(s.attrib["tests"]) for s in repair_suites),
        "repaired_lifecycle_report_and_doctor_pass": True, "unique1108_regression_cases_validated": True,
        "failures_errors_skips_final_targeted": 0,
        "workers_complete": 75, "trials_complete": 675, "fresh_paired_units": 5,
        "data_source_pairing_and_fit_identity_valid": True, "integrity_before_after_files": 1136,
        "archived_raw_source_runtime_files": 1749,
        "indexed_raw_archive_native_result_files": guard["indexed_raw_archive_native_result_preregistration_files"],
        "index_guard_receipt_sha256": sha256_file(guard_path), "doctor_and_lab_status_pass_clone_and_original": True,
        "current_integrity": integrity, "original_old_raw_bytes_and_prefixes_preserved": True,
        "original_BELIEFS_raw_unchanged": True, "completed_experiments_counter": 114,
        "failed_helpers_and_diagnostics_preserved_and_charged": True, "model_retry": False,
        "WT8_9_access": False, "external_model_api": False, "schedule_changed": False},
    "budget": {"original_started_at": "2026-10-04T19:32:56Z", "original_deadline_at": "2026-10-04T23:32:56Z",
        "elapsed_seconds_at_closure": (now-cycle_start).total_seconds(), "closed_before_deadline": True,
        "supervised_fit_phase_seconds": diag["total_supervised_fit_phase_seconds"],
        "internal_algorithm_fit_seconds": diag["total_internal_algorithm_fit_seconds"],
        "charged_full_worker_seconds": diag["full_charged_worker_seconds"], "worker_compute_cap_seconds": 15600,
        "stage_auxiliary_seconds_charged": auxiliary, "stage_auxiliary_seconds_cap": 1800,
        "stage_total_compute_seconds": auxiliary + diag["full_charged_worker_seconds"],
        "all_auxiliary_reservations_closed": True, "auxiliary_charges": charges,
        "budget_or_deadline_reset": False, "programme": value},
    "unexecuted_scope": ["matched memory-training support exposure alternative", "independent mechanism replication",
        "adversarial task variant", "frozen fresh final and strong classical non-domination"],
    "next_discriminating_question": "Preregister K32/128 versus including K512 feature-fit support exposure with fixed512 features/512 steps, source-identical correct transport and frozen/shuffled controls, optimized dense and strong classical/retrieval, five fresh paired units. Freeze before implementation/data; no current D rescue or second EXP in this cycle."}
atomic_write_json(receipt_path, receipt)
append_jsonl(b / "research/events.jsonl", {"event": "bounded_research_cycle_completed", "created_at": utc_now(),
    "program_id": value["id"], "cycle": 309, "experiment_id": identity,
    "completion_receipt_path": receipt_path.relative_to(b).as_posix(), "completion_receipt_sha256": sha256_file(receipt_path),
    "whole_program_complete": False, "next_scoring_requires_new_study_freeze": True})
write_report(b)
print(json.dumps({"receipt_sha256": sha256_file(receipt_path), "stage_auxiliary_seconds": auxiliary,
    "stage_total_seconds": auxiliary + diag["full_charged_worker_seconds"], "programme_charged_seconds": value["fit_seconds_charged"],
    "remaining_seconds": value["fit_seconds_remaining"], "remaining_continuation_tickets": 13,
    "closure_bookkeeping_seconds": time.perf_counter()-started}))
