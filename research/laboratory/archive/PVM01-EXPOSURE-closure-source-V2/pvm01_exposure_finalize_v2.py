"""Seal one bounded cycle after clone/original checks; no new scored work."""
from datetime import datetime, timezone
import json
import math
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import auxiliary_charge, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
identity = "EXP-20261004-0008"
charge_id = "PVM01-EXPOSURE-final-accounting-allowance-V1"
events = read_jsonl(b/"research/events.jsonl")
assert any(e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id") == charge_id and e["seconds_cap"] == 120 for e in events)
# Append known actual overflow without lowering or replacing the original charge.
repair_path = b/"research/plans/PVM01-EXPOSURE-POSTRUN-ACCOUNTING-V1.json"
repair = json.loads(repair_path.read_text())
original_failed_path = b/"research/reviews/PVM01-EXPOSURE-original-validate-V1.json"
failed = json.loads(original_failed_path.read_text())
assert failed["returncode"] == 124 and math.ceil(failed["wall_seconds"])+5-failed["seconds_charged"] == 44
original_checkpoint_path = b/"research/reviews/PVM01-EXPOSURE-original-source-validation-V1.json"
original_checkpoint = json.loads(original_checkpoint_path.read_text())
assert original_checkpoint["original_git_clean"] and all(c["returncode"] == 0 for c in original_checkpoint["commands"])
from nextai_autoresearch.research_program import auxiliary_reserve
paid = {e["charge_id"]:e["seconds"] for e in events if e.get("event") == "research_program_aux_fit_charged"}
used = sum(paid.get(e["charge_id"],e["seconds_cap"]) for e in events if e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id", "").startswith("PVM01-EXPOSURE-"))
assert used+44 == 1795 and used+44 <= 1800
spill_id = "PVM01-EXPOSURE-original-validate-V1-wall-overflow"
assert not any(e.get("charge_id") == spill_id for e in events)
auxiliary_reserve(b,spill_id,44)
auxiliary_charge(b,spill_id,44)
atomic_write_json(b/f"research/reviews/{spill_id}.json",{
    "created_at":utc_now(),"failed_receipt_raw_sha256":sha256_file(original_failed_path),
    "wall_seconds":failed["wall_seconds"],"prior_seconds_charged":150,
    "additional_seconds_charged":44,"combined_charge_seconds":194,
    "charge_basis":"ceil(actual whole command wall)+5s, append-only overflow correction; no charge reduced",
    "reserved_after_execution_for_observed_deadline_overflow_accounting":True,
    "repair_contract_raw_sha256":sha256_file(repair_path),"new_research_fit_seed_or_retry":False})
# The prior V2 timeout formula did not bound the whole descendant process lifetime.
note = b/f"research/analyses/{identity}-ADDENDUM-V3.md"
assert not note.exists()
note.write_text("# EXP-20261004-0008 — final timeout accounting, ADDENDUM V3\n\n"
    "The original checkout's doctor and lab status both returned0, its raw history/prefixes/result were preserved, "
    "and it remained clean at source commit5e69c42f80f1e990dce25fb3048117547098f3d1. The outer V1 command nevertheless "
    "timed out: measured wall188.891736s versus150s reserved. Its timeout and150s charge remain; an additional44s "
    "now covers ceil(wall)+5, for194s combined. The V2 wrapper calculated a total deadline but failed to bound "
    "the full child process lifetime. Do not describe that supervisor as fixed or every outer check as passed.\n\n"
    "All scientific results, frozen INCONCLUSIVE decision, source/recipe/metrics/gates and prior addenda remain unchanged. "
    "Auxiliary charges including every failure and the retired120s final bookkeeping allowance total1795/1800s. "
    "Full workers cost1055.745196s, giving2850.745196s for cycle310. No further tests or paid retry in this cycle. "
    "The immutable cycle310 receipt holds exact global totals and checks. Before another research study, prospectively "
    "test Windows process-tree deadline enforcement and exact dense/cache decoder/loss determinism using fixed "
    "technical fixtures without research data/scoring/registration. This is remaining preparation work, not a repaired "
    "claim for EXP-0008. Independent/adverse/scaling/fresh-final scope remains unexecuted.\n",encoding="utf8",newline="\n")
append_jsonl(b/"research/events.jsonl",{"event":"research_validation_outer_timeout_final_accounting_addendum",
    "created_at":utc_now(),"experiment_id":identity,"repair_contract_sha256":sha256_file(repair_path),
    "failed_outer_receipt_sha256":sha256_file(original_failed_path),"original_validation_checkpoint_sha256":sha256_file(original_checkpoint_path),
    "extra_seconds_charged":44,"final_validation_addendum_path":note.relative_to(b).as_posix(),
    "final_validation_addendum_sha256":sha256_file(note),"no_additional_tests_or_paid_retry":True})
# Archive this new closure variant; keep the earlier unused finalizer exactly as archived.
closure_root = b/"research/laboratory/archive/PVM01-EXPOSURE-closure-source-V2"
assert not closure_root.exists()
closure_root.mkdir()
this_source = Path(__file__).resolve()
assert this_source.is_relative_to((b/"research/tmp").resolve())
raw = this_source.read_bytes()
free = shutil.disk_usage(b).free
assert free-len(raw) > 10*1024**3
copy = closure_root/this_source.name
copy.write_bytes(raw)
assert sha256_file(copy) == sha256_file(this_source)
atomic_write_json(closure_root/"receipt-V2.json",{"created_at":utc_now(),"source_raw_sha256":sha256_file(copy),
    "bytes":len(raw),"free_before_bytes":free,"free_after_bytes":shutil.disk_usage(b).free,
    "original_archived_helpers_unchanged":True,"no_scientific_result_or_source_changed":True})

auxiliary_charge(b,charge_id,120)
atomic_write_json(b/f"research/reviews/{charge_id}.json",{
    "created_at":utc_now(),"seconds_cap":120,"seconds_charged":120,
    "charge_basis":"Full allowance conservatively retired for final ledger/report/hash checks,helper/controller initialization and readonly progress/bookkeeping outside timed children. May overcount; no old charge reduced.",
    "new_research_seed_data_fit_or_registration":False})
original = json.loads((b/"research/reviews/PVM01-EXPOSURE-original-source-validation-V1.json").read_text())
guard_path = b/"research/reviews/PVM01-EXPOSURE-final-history-source-index-V1.json"
guard = json.loads(guard_path.read_text())
assert original["original_git_clean"] and all(c["returncode"] == 0 for c in original["commands"])
assert guard["all_indexed_raw_sha256_valid"] and guard["old_scientific_bytes_and_append_only_prefixes_preserved"]
for name in ("PVM01-EXPOSURE-postrun-targeted-V1","PVM01-EXPOSURE-postrun-check-V2"):
    assert json.loads((b/f"research/reviews/{name}.json").read_text())["returncode"] == 0
def suite_counts(relative):
    suites = list(ET.parse(b/relative).getroot().iter("testsuite"))
    return {key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ("tests","failures","errors","skipped")}
pre = suite_counts("research/reviews/PVM01-EXPOSURE-preseed-full-V2.xml")
post = suite_counts("research/reviews/PVM01-EXPOSURE-postrun-targeted-V1.xml")
assert pre["tests"] == 1114 and pre["failures"] == pre["errors"] == pre["skipped"] == 0
assert post["failures"] == post["errors"] == post["skipped"] == 0
a = json.loads((b/f"research/reviews/{identity}-PVM01-exposure-analysis.json").read_text())
d = json.loads((b/f"research/reviews/{identity}-PVM01-full-diagnostics-V2.json").read_text())
assert d["all80_workers_and720_trials_finished"] and not d["frozen_comparison_validity_passed"]
assert a["decision"] == "INCONCLUSIVE comparison"
assert a["identical_legal_data_across_arms"] and a["identical_training_sets"]
assert all(all(v for k,v in unit.items() if k != "dense_cache_identical_weights")
           and not unit["dense_cache_identical_weights"] for unit in a["source_fit_identity"].values())
archive = json.loads((b/"research/reviews/PVM01-EXPOSURE-scientific-archive-V1.json").read_text())
value = status(b)
events = read_jsonl(b/"research/events.jsonl")
charges = [e for e in events if e.get("event") == "research_program_aux_fit_charged" and e.get("charge_id","").startswith("PVM01-EXPOSURE-")]
reserves = [e for e in events if e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id","").startswith("PVM01-EXPOSURE-")]
assert {e["charge_id"] for e in reserves} == {e["charge_id"] for e in charges}
auxiliary = sum(e["seconds"] for e in charges)
assert auxiliary <= 1800
assert value["registration_attempts_used"] == 8 and value["continuation_registration_attempts_used"] == 5
assert value["study_terminal"] and not value["paid_run_pending"] and not value["program_terminal"]
assert not value["scoring_authorized"] and value["pending_fit_reservation_seconds"] == 0
integrity = verify_manifest(b)
assert integrity["ok"] and integrity["checked_files"] == 1166
now = datetime.now(timezone.utc)
start = datetime.fromisoformat("2026-10-04T20:50:36+00:00")
deadline = datetime.fromisoformat("2026-10-05T00:50:36+00:00")
assert now < deadline
path = b/"research/laboratory/PVM01-CYCLE-310-COMPLETION-V1.receipt.json"
assert not path.exists()
receipt = {"id":"PVM01-CYCLE-310-COMPLETION-V1","created_at":utc_now(),"cycle":310,
    "experiment_id":identity,"plan_path":f"research/plans/{identity}.json","plan_sha256":a["plan_sha256"],
    "study_path":"research/plans/PVM01-CAPACITY-EXPOSURE-V1.json","study_sha256":a["study_sha256"],
    "result_sha256":a["result_sha256"],"analysis_path":f"research/analyses/{identity}.md",
    "analysis_sha256":sha256_file(b/f"research/analyses/{identity}.md"),"decision":a["decision"],
    "complete_analysis_addendum_path":f"research/analyses/{identity}-ADDENDUM-V1.md",
    "complete_analysis_addendum_sha256":sha256_file(b/f"research/analyses/{identity}-ADDENDUM-V1.md"),
    "validation_addendum_path":f"research/analyses/{identity}-ADDENDUM-V2.md",
    "validation_addendum_sha256":sha256_file(b/f"research/analyses/{identity}-ADDENDUM-V2.md"),
    "final_validation_addendum_path":f"research/analyses/{identity}-ADDENDUM-V3.md",
    "final_validation_addendum_sha256":sha256_file(b/f"research/analyses/{identity}-ADDENDUM-V3.md"),
    "accounting_repair_contract_path":repair_path.relative_to(b).as_posix(),
    "accounting_repair_contract_sha256":sha256_file(repair_path),
    "whole_program_complete":False,"goal_turn_classification":"progress",
    "checks":{"preregistration_before_implementation_commit":"8fb10251a0c03356856469e1c37742c3956f15dc",
        "evaluated_source_commit":json.loads((b/f"research/plans/{identity}.json").read_text())["git_before"]["commit"],
        "validated_maintenance_source_commit":original["source_commit"],
        "preseed_full_regression":pre,"postrun_critical_integrity_lifecycle_memory_regression":post,
        "full_suite_not_repeated_after_unchanged_candidate_source":True,
        "preseed_full_V1_passed":1113,"preseed_full_V1_failed":1,
        "preseed_boundary_failure_preserved_and_source_corrected_before_paid_seed":True,
        "failed_readiness_ledger_report_clean_assertion_preserved_and_charged":True,
        "postrun_gate_V1_outer_timeout_preserved":True,
        "postrun_gate_V1_inner_doctor_lab_semantics_completed_and_V2_checkpoint_verified":True,
        "postrun_gate_V1_actual_wall_plus_margin_charged_seconds":133,
        "V2_auxiliary_wrapper_total_deadline_calculated_but_process_tree_lifetime_not_enforced":True,
        "original_outer_timeout_preserved_inner_doctor_lab_returncodes_zero":True,
        "original_whole_wall_plus_margin_charged_seconds":194,
        "post_original_no_additional_tests":True,
        "workers_and_trials_physically_complete":d["all80_workers_and720_trials_finished"],
        "frozen_whole_comparison_validity_passed":a["all_workers_and_trials_complete"],
        "fresh_paired_units":5,"all_feature_data_source_pairing_and_fit_identity_valid":True,
        "exact_dense_cache_decoder_identity_valid":False,"same_discrete_cache_predictions_count":28800,
        "initial_report_completion_conflation_corrected_append_only":True,
        "frozen_gates_analyzer_plan_result_and_decision_unchanged":True,
        "integrity_before_after_files":1166,"archived_raw_source_runtime_files":archive["source_count"]+archive["runtime_count"],
        "indexed_raw_archive_native_result_files":guard["indexed_raw_archive_native_result_preregistration_files"],
        "index_guard_receipt_sha256":sha256_file(guard_path),"doctor_and_lab_pass_clone_and_original":True,
        "original_old_raw_bytes_prefixes_and_BELIEFS_preserved":True,
        "completed_experiments_counter":115,"paid_model_retry":False,"WT8_9_access":False,
        "external_model_API":False,"schedule_changed":False},
    "budget":{"original_started_at":"2026-10-04T20:50:36Z","original_deadline_at":"2026-10-05T00:50:36Z",
        "elapsed_seconds_at_closure":(now-start).total_seconds(),"closed_before_deadline":True,
        "supervised_fit_phase_seconds":d["total_supervised_fit_phase_seconds"],
        "internal_algorithm_fit_seconds":d["total_internal_algorithm_fit_seconds"],
        "charged_full_worker_seconds":d["full_charged_worker_seconds"],"worker_compute_cap_seconds":16640,
        "stage_auxiliary_seconds_charged":auxiliary,"stage_auxiliary_seconds_cap":1800,
        "stage_total_compute_seconds":auxiliary+d["full_charged_worker_seconds"],
        "all_auxiliary_reservations_closed":True,"auxiliary_charges":charges,"budget_or_deadline_reset":False,
        "programme":value},
    "unexecuted_scope":["independent mechanism replication","adversarial paired-view variant",
        "frozen fresh final","economic non-domination against strongest classical controls"],
    "next_discriminating_question":"Preregister bounded preparation-only Windows process-tree deadline enforcement and decoder determinism/telemetry conformance in independent fixed-fixture children,no research data/scoring/registration/paid retry. Require exact encoder/decoder/loss identity across dense/cache before a distinct prospective alternative learned-transport/indexed-memory comparison on a justified adverse paired-view task,with unchanged strongest classical controls and full costs. Do not rescue or reinterpret EXP-0008. No second EXP in this completed cycle."}
atomic_write_json(path,receipt)
append_jsonl(b/"research/events.jsonl",{"event":"bounded_research_cycle_completed","created_at":utc_now(),
    "program_id":value["id"],"cycle":310,"experiment_id":identity,"completion_receipt_path":path.relative_to(b).as_posix(),
    "completion_receipt_sha256":sha256_file(path),"whole_program_complete":False,"next_scoring_requires_new_study_freeze":True})
write_report(b)
print(json.dumps({"receipt_sha256":sha256_file(path),"decision":a["decision"],"stage_auxiliary_seconds":auxiliary,
    "stage_total_seconds":auxiliary+d["full_charged_worker_seconds"],"programme_charged_seconds":value["fit_seconds_charged"],
    "remaining_seconds":value["fit_seconds_remaining"],"remaining_continuation_tickets":12}))
