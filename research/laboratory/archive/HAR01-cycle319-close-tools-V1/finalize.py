"""Append the completed bounded cycle's final accounting; no research execution."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[3]
original = Path("C:/Users/NATAN/Documents/ChatGPT/NEXTAI").resolve()
assert root.name == "NEXTAI-VALIDATION-20261002"
identity = "EXP-20261005-0007"
receipt_path = root / "research/laboratory/HAR01-CYCLE319-COMPLETION-V1.receipt.json"
assert not receipt_path.exists()
events = read_jsonl(root / "research/events.jsonl")
charged = [e for e in events if e.get("event") == "research_program_aux_fit_charged"
           and str(e.get("charge_id", "")).startswith("NEXTAI-B-319-")]
reserved = [e for e in events if e.get("event") == "research_program_aux_fit_reserved"
            and str(e.get("charge_id", "")).startswith("NEXTAI-B-319-")]
charges = {e["charge_id"]: e["seconds"] for e in charged}
assert len(charges) == len(charged) and set(charges) == {e["charge_id"] for e in reserved}
assert sum(charges.values()) == 3445 <= 3500
analysis_path = root / f"research/analyses/{identity}-har01.json"
analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
assert analysis["valid"] and not analysis["problems"]
assert all(analysis["trusted_resource_journal_checks"].values())
wallet = status(root)
assert wallet["scoring_authorized"] is False and wallet["study_terminal"] and not wallet["program_terminal"]
assert wallet["stage_b_registration_attempts_used"] == 1 and wallet["stage_b_registration_attempts_cap"] == 12
assert wallet["pending_fit_reservation_seconds"] == 0 and not wallet["paid_run_pending"]
assert wallet["protected_future_compute_seconds"] == 47000 and wallet["protected_future_registration_attempts"] == 7
assert math.isclose(wallet["stage_b_compute_seconds_charged"], 6201.550240200071, abs_tol=1e-8)
assert math.isclose(wallet["stage_a_accounting"]["fit_seconds_charged"], 35649.98936010008, abs_tol=1e-8)
now = datetime.now(timezone.utc)
assert now < datetime.fromisoformat("2026-10-05T17:08:19+00:00")
reviews = {}
failed = []
for path in sorted((root / "research/reviews").glob("NEXTAI-B-319-*.json")):
    record = json.loads(path.read_text(encoding="utf-8"))
    reviews[path.relative_to(root).as_posix()] = sha256_file(path)
    result = record.get("result") or {}
    if result.get("returncode", 0) != 0 or record.get("error") or record.get("status") == "failed":
        failed.append(path.relative_to(root).as_posix())
full = ET.parse(root / "research/reviews/NEXTAI-B-319-full-regression-V1.xml").findall(".//testcase")
affected = ET.parse(root / "research/reviews/NEXTAI-B-319-affected-conformance-V1.xml").findall(".//testcase")
assert len(full) == 1361 and sum(any(c.find(k) is not None for k in ("failure", "error")) for c in full) == 1
assert len(affected) == 38 and not any(any(c.find(k) is not None for k in ("failure", "error", "skipped")) for c in affected)
proof_path = root / "research/checks/HAR01-clone-original-preservation-V2.json"
proof = json.loads(proof_path.read_text(encoding="utf-8"))
assert proof["protected_files_verified_each_root"] == 1370 and proof["fresh_empty_destination_restoration_verified"]
tools_directory = root / "research/laboratory/archive/HAR01-cycle319-close-tools-V1"
tools_directory.mkdir(parents=True, exist_ok=False)
tool_hashes = {}
for name in ("mirror_validate.py", "mirror_validate_v2.py", "finalize.py"):
    path = Path(__file__).parent / name
    shutil.copy2(path, tools_directory / name)
    tool_hashes[name] = sha256_file(path)
next_question = ("Separate bounded preparation:finish the full original CLI lab status check before new data;"
                 "preregister optical-digit native views,intake/writer independence and sufficient disjoint units before fit."
                 "If writer provenance is unavailable,preserve the limitation and choose another justified native family."
                 "Then separately freeze a five-pair,three-scale source-trained/untrained/shuffled versus competent dense/strong-classical screen;"
                 "keep all UNKNOWN,competence,economic gates and reserved replication/fresh-final/prototype budgets;no HAR D-guided rescue.")
payload = {
    "schema_version": 1, "id": "HAR01-CYCLE319-COMPLETION-V1", "cycle": 319, "created_at": utc_now(),
    "cycle_started_at": "2026-10-05T13:08:19Z", "cycle_deadline_at": "2026-10-05T17:08:19Z",
    "experiment_id": identity, "new_registration_attempts": 1, "paid_retry": False,
    "plan_path": f"research/plans/{identity}.json", "plan_sha256": sha256_file(root / f"research/plans/{identity}.json"),
    "study_sha256": sha256_file(root / "research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json"),
    "task_sha256": sha256_file(root / "research/plans/HAR01-NATIVE-TASK-CONTRACT-V1.json"),
    "native_result_sha256": sha256_file(root / f"research/results/{identity}.json"),
    "analysis_path": analysis_path.relative_to(root).as_posix(), "analysis_sha256": sha256_file(analysis_path),
    "source_information_decision": analysis["source_information_transfer"], "economic_decision": analysis["economic_decision"],
    "workers_complete": 45, "trials_complete": 810, "independent_paired_units": 5,
    "supervised_fit_seconds": analysis["supervised_fit_seconds"], "full_workers_charged_seconds": analysis["full_worker_seconds"],
    "full_worker_cap_seconds": 9000, "cycle_auxiliary_charges": charges,
    "cycle_auxiliary_seconds_charged": sum(charges.values()), "cycle_auxiliary_cap_seconds": 3500,
    "cycle_total_compute_seconds_charged": sum(charges.values()) + analysis["full_worker_seconds"],
    "all_auxiliary_reservations_resolved": True, "program_budget": wallet,
    "prior_MUC03_registration_attempts": 3, "prior_MUC03_compute_seconds": 2655.336484700005,
    "prior_A_registration_attempts": 11, "prior_A_compute_seconds": 35649.98936010008,
    "extended_goal_completed": False, "scoring_authorized": False, "benchmark_status": "maintenance",
    "checks_and_failures_receipt_sha256": reviews, "failed_check_receipts": failed,
    "full_regression": {"cases": 1361, "passed": 1360, "failed": 1, "cause": "stale aggregate REPORT;fixed before paid execution"},
    "passing_affected_conformance_cases": 38, "clone_terminal_doctor_pass": True,
    "preservation_proof_sha256": sha256_file(proof_path), "preserved_evaluated_source_and_runtime_before_maintenance": True,
    "separate_failed_original_CLI_lab_status_preserved": True,
    "unfinished_technical_scope": ["Full original CLI lab status did not complete within its140-second test cap;clone full doctor passed and original laboratory progress plus1370 protected files,seven native records/bundles,317 runtime/archive files and fresh restoration passed separately;finish full CLI next preparation cycle."],
    "reflection_range": [111, 122], "reflection_review_path": "research/reviews/NEXTAI-PORTFOLIO-CYCLE319-V1.md",
    "reflection_review_sha256": sha256_file(root / "research/reviews/NEXTAI-PORTFOLIO-CYCLE319-V1.md"),
    "future_HAR_numeric_subjects_unopened": "6-15/21-30;screen onlyT1-5/D16-20",
    "remaining_goal_scope": ["second independently sourced native family", "independent native replications", "frozen fresh native finals", "evidence-selected local fact/source/update/UNKNOWN prototype"],
    "exact_next_discriminating_experiment": next_question, "close_tool_sha256": tool_hashes,
    "manual_bookkeeping_covered_by_prepaid_administration_seconds": 350,
}
atomic_write_json(receipt_path, payload)
append_jsonl(root / "research/events.jsonl", {"event": "research_program_cycle_completed", "created_at": utc_now(),
    "program_id": wallet["id"], "cycle": 319, "experiment_id": identity,
    "receipt_path": receipt_path.relative_to(root).as_posix(), "receipt_sha256": sha256_file(receipt_path),
    "decision": "DISCARD exact HAR source-transfer recipe;economic comparison INCONCLUSIVE;whole goal ACTIVE",
    "scoring_authorized": False, "extended_goal_completed": False})
paths = set(reviews) | {"research/events.jsonl", receipt_path.relative_to(root).as_posix()} | {
    p.relative_to(root).as_posix() for p in tools_directory.iterdir()}
for relative in sorted(paths):
    source, target = root / relative, original / relative
    if relative == "research/events.jsonl":
        assert source.read_bytes().startswith(target.read_bytes())
    elif target.exists():
        assert sha256_file(target) == sha256_file(source), relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert sha256_file(target) == sha256_file(source)
print(json.dumps({"cycle_total_seconds": payload["cycle_total_compute_seconds_charged"],
                  "B_used_seconds": wallet["stage_b_compute_seconds_charged"], "B_remaining_seconds": wallet["fit_seconds_remaining"],
                  "auxiliary_seconds": sum(charges.values()), "all_reserves_settled": True, "failed_receipts": failed,
                  "broader_goal_completed": False}), flush=True)
