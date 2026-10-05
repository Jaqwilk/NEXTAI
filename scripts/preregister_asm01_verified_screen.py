"""Freeze the complete V3 study before cohort implementation or remaining native data."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_charge, auxiliary_reserve, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


root = Path(__file__).resolve().parents[1]
path = "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json"
task_path = "research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json"
parent_path = "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json"
completion_path = "research/laboratory/ASM01-CYCLE323-COMPLETION-V1.receipt.json"
assert root.name == "NEXTAI" and not (root / path).exists()
assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
startup = []
for suffix in ("startup-doctor", "startup-lab"):
    check = json.loads((root / f"research/reviews/NEXTAI-B-324-{suffix}.json").read_text())
    assert check["result"]["returncode"] == 0 and not check["error"]
    assert check["result"]["exit_job_active_process_count"] == 0
    startup.append(check["seconds_charged"])
lab = json.loads((root / "research/reviews/NEXTAI-B-324-startup-lab.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
wallet = status(root)
assert wallet["study_terminal"] and not wallet["program_terminal"]
assert wallet["pending_fit_reservation_seconds"] == 0 and not wallet["paid_run_pending"]
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000
assert wallet["unreserved_fit_seconds_remaining"] - 47000 >= 10800 - sum(startup)
assert verify_manifest(root)["ok"]
completion = json.loads((root / completion_path).read_text())
assert completion["passed_grammar_fixture_cases"] == 80 and completion["all3_descriptor_references_equal"]
assert completion["new_registrations"] == completion["new_research_fit_seconds"] == 0
task = json.loads((root / task_path).read_text())
assert task["cohort"] == "asm01_native_memory_v3" and task["execution_authority"] is False
assert sha256_file(root / task["serializer"]["source_path"]) == task["serializer"]["source_sha256"]

archive = root / "research/laboratory/archive/ASM01-cycle324-parent-V1"
assert not archive.exists()
parent_files = ["AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md",
                "config/research.toml", "config/baseline_semantics.json", "schemas/experiment_plan.schema.json",
                "src/nextai_autoresearch/research_program.py", "src/nextai_autoresearch/runner.py",
                "src/nextai_autoresearch/integrity.py", "research/eval_manifest.json",
                "research/laboratory/preflight_certificate.json", "research/state.json"]
for relative in parent_files:
    target = archive / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / relative, target)
identifier = "NEXTAI-B-324-administration-prepaid"
auxiliary_reserve(root, identifier, 300)
auxiliary_charge(root, identifier, 300)
atomic_write_json(root / f"research/reviews/{identifier}.json", {
    "id": identifier, "created_at": utc_now(), "seconds_charged": 300,
    "cap_seconds": 300, "conservative_prepaid": True,
    "scope": "Required reads and administrative scripts/syntax, preregistration, metadata archives/headers/config/state, byte mirrors and Git. Native intake, conformance fits/tests, freezes/preflight, readiness/registration, audited workers and result analysis separately bounded and charged.",
})
parent = json.loads((root / parent_path).read_text())
plan = deepcopy(parent)
plan.update(id="ASM01-FROZEN-SOURCE-SCREEN-V3", created_at=utc_now(), cycle=324,
            cohort=task["cohort"], task_contract_path=task_path,
            task_contract_sha256=sha256_file(root / task_path),
            study_started_at="2026-10-05T22:47:55Z", study_deadline_at="2026-10-06T02:47:55Z",
            parent_completion_receipt_path=completion_path,
            parent_completion_receipt_sha256=sha256_file(root / completion_path),
            invalid_parent_study_path=parent_path, invalid_parent_study_sha256=sha256_file(root / parent_path),
            metadata_only_intake_revision="A new bounded cohort uses the independently conformed V4 singleton-zero release/header adapter. Preserve both failed native intakes and all serializer failures. Already-exposed T1 is disclosed; remaining native data are still unseen. No model, geometry, observations, independent units, scientific metric or gate change; no paid retry.")
plan["resources"].update(work_minutes_cap=240, auxiliary_test_seconds_cap=2500,
                          fit_seconds_study_cap=8300,
                          startup_charge_included_seconds=sum(startup),
                          administration_prepaid_seconds_cap=300)
plan["data"]["acquisition"] = deepcopy(task["intake"])
plan["native_parser"]["grammar"] = task["serializer"]["grammar"]
plan["native_parser"]["adapter_provenance"] = deepcopy(task["serializer"])
plan["previous_goal_turn_classification"] = "progress: cycle323 completed exact serializer conformance, 80 fixtures/full doctor and clone lifecycle/lab, immutable analysis and accounting, byte mirror and non-force publication; the next native screen is now actionable"
plan["preexecution_implementation"] = {
    "parser": "Use unchanged SHA-bound asm01_task_v4. Preserve V1/V2/V3/V4 and every numeric/geometry rule.",
    "loader": "New asm01_task_v5 canonical loader changes only V3 task/study/acquisition paths from V2; all episode/pair/descriptor math delegates to unchanged existing functions.",
    "benchmark": "Thin asm01_native_memory_v3 wrapper runs unchanged V2 suite code with isolated globals bound to V3 identity/loader/manifest. No mutation of the historical module, math, measures, truth or source weights.",
    "intake": "Versioned acquire_asm01_verified_v3 uses the same canonical membership/extraction/complete loop, new artifact names and frozen V4 parser. One intake only, all1830 screen files; zero additional download. Preserve attempted/converted counts, current writer/sample position and every attempted text hash even on failure; no coordinates/names emitted. No schema rescue or sample dropping after native content.",
    "harness": "Append V3 exact schema clause and cohort registry entry; permit only V2/V3 in the existing native study guard; add V3 to private ASM nonce dispatch/compact-result lists and protected paths. All old schema clauses, semantic records and scientific source preserved.",
    "conformance": "Clone-only existing native/canonical/grammar/serializer/cohort tests plus V3 schema mutations, all45 audits, pre-fit serialized worker boundary and synthetic loader scope/hash/split/delegation tests. Tiny declared fixture fits only; no native research arrays or fitting before validation.",
    "readiness": "Successful complete native intake then freeze/preflight and clone gates/doctor before exactly one audited program registration/run. Missing native file, grammar, duplicate or geometry stops all unstarted scope with immutable receipt; no same-cycle repair.",
}
plan["prior_exposure"] = {
    "known_T1_sha256": "4c3e65ac49ff5ad55f521ab9f86b47dbaa55cfb5cd341d6d1d234ad1d4e9dfff",
    "known_T1_processed_previously": True, "fresh_native_screen_samples_remaining": 1829,
    "D_samples_previously_parsed": 0, "fresh_final_and_replication_native_samples_previously_parsed": 0,
    "native_samples_not_blinded": True, "known_T1_not_claimed_fresh": True,
    "intake_failures_preserved": ["research/data_manifests/ASM01-ACQUISITION-V1.json", "research/data_manifests/ASM01-ACQUISITION-V2.json"],
}
plan["budget_at_preregistration"] = {
    "stage_b_seconds_before_this_cycle": 14185.550240200071,
    "startup_seconds_charged": sum(startup), "administration_prepaid_seconds": 300,
    "cycle_full_worker_seconds_cap": 8300, "cycle_all_auxiliary_seconds_cap": 2500,
    "worker_cap_reason": "45 roles x unchanged184-second monitor-inclusive ceiling =8280 seconds, below8300. The remaining2500 covers full required conformance/intake/readiness/postrun checks. Combined10800 stays below unprotected wallet10814.44975979993; no individual fit/worker limit relaxed.",
    "protected_future_tickets": 7, "protected_future_compute_seconds": 47000,
    "stage_A_closed_no_credit": True, "stage_MUC_closed_no_reset": True,
}
plan["parent_metadata_archive_path"] = archive.relative_to(root).as_posix()
for key in ("candidates", "roles", "matrix", "recipe", "diagnostics", "diagnosis_gates", "reference_gates", "source_evidence", "cost_boundary", "decision_policy"):
    assert plan[key] == parent[key], key
for key in ("trajectory", "resampling", "filename_identity", "points_per_sample_cap", "sample_bytes_cap"):
    assert plan["native_parser"][key] == parent["native_parser"][key], key
atomic_write_json(root / path, plan)
append_jsonl(root / "research/events.jsonl", {
    "event": "research_program_study_frozen", "created_at": utc_now(), "cycle": 324,
    "program_id": wallet["id"], "study_path": path, "study_sha256": sha256_file(root / path),
    "before_V3_cohort_implementation": True, "before_remaining_native_content": True,
    "known_T1_exposure_disclosed": True,
})
old = b'study_path = "research/plans/ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1.json"'
config = root / "config/research.toml"
assert config.read_bytes().count(old) == 1
config.write_bytes(config.read_bytes().replace(old, f'study_path = "{path}"'.encode()))
header = ("# Prospective cycle324 — verified serializer native ASM01 screen (2026-10-05)\n\n"
          "ASM01-FROZEN-SOURCE-SCREEN-V3 freezes the unchanged nine-arm, five-pair screen.\n"
          "Actual source states,4096pairs,2048alignment/1024decoder,K16/32/64,updates0/1/4,\n"
          "nominal/adverse,all metrics/grids/competence/UNKNOWN/FA/economic gates unchanged.\n"
          "Only new cohort/intake binding to the independently conformed V4 serializer.\n"
          "Known T1 disclosed; all1830 screen samples required without dropping/replacement.\n"
          "Native intake failure stops unstarted scope; no same-cycle parser/geometry rescue.\n"
          "Deadline2026-10-06T02:47:55Z; fullworker8300s,auxiliary2500s includes startup,\n"
          "tests/failures/controller; protected7tickets/47000s untouched. Maintenance and\n"
          "scoring=false until independent clone/native feasibility/freeze/preflight/readiness.\n"
          "Exactly one audited EXP at most; no source refit,paid retry,WT8-9,external API\n"
          "or schedule change. B and the complete transfer/prototype goal remain active.\n\n"
          "Earlier stage-specific sections below remain preserved history.\n\n").encode()
for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"):
    (root / relative).write_bytes(header + (root / relative).read_bytes())
print(json.dumps({"study_path": path, "study_sha256": sha256_file(root / path),
                  "task_sha256": sha256_file(root / task_path), "all_scientific_recipes_gates_unchanged": True,
                  "remaining_native_content_seen": False, "roles": len(plan["roles"])}), flush=True)
