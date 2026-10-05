"""Freeze a separate preparation-only grammar repair before code or numeric T1."""
import json
from pathlib import Path
import shutil

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
plan_path = "research/plans/ASM01-NATIVE-GRAMMAR-CONFORMANCE-V1.json"
assert not (root / plan_path).exists()
assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
for name in ("startup-doctor", "startup-lab"):
    check = json.loads((root / f"research/reviews/NEXTAI-B-322-{name}.json").read_text())
    assert check["result"]["returncode"] == 0 and not check["error"]
lab = json.loads((root / "research/reviews/NEXTAI-B-322-startup-lab.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
admin_id = "NEXTAI-B-322-administration-prepaid"
auxiliary_reserve(root, admin_id, 300)
auxiliary_charge(root, admin_id, 300)
atomic_write_json(root / f"research/reviews/{admin_id}.json", {
    "created_at": utc_now(), "id": admin_id, "seconds_charged": 300,
    "cap_seconds": 300, "conservative_prepaid": True,
    "scope": "Prereads, failed manual blank-line JSON read, preregistration, archive/header/config administration, closed-file byte mirrors, final derived-report refresh, Git checks/commits/sync; no fit or scoring. All substantive checks charged separately.",
})
assert verify_manifest(root)["ok"]
wallet = status(root)
assert wallet["study_terminal"] and not wallet["program_terminal"]
assert wallet["stage_b_registration_attempts_used"] == 1 and wallet["protected_future_compute_seconds"] == 47000
refs = ["research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json",
        "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json",
        "research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json",
        "research/laboratory/ASM01-CYCLE321-COMPLETION-V1.receipt.json",
        "research/reviews/ASM01-NATIVE-GRAMMAR-DIAGNOSIS-V1.json",
        "research/data_manifests/ASM01-ACQUISITION-V1.json",
        "research/data_manifests/ASM01-ACQUISITION-V2.json"]
plan = {
    "schema_version": 1, "id": "ASM01-NATIVE-GRAMMAR-CONFORMANCE-V1", "created_at": utc_now(),
    "cycle": 322, "study_kind": "preparation_only", "stage": "task_design", "cohort": "asm01_native_memory_v2",
    "program_id": wallet["id"], "program_contract_path": wallet["contract_path"],
    "program_contract_sha256": sha256_file(root / wallet["contract_path"]),
    "study_started_at": "2026-10-05T20:38:28Z", "study_deadline_at": "2026-10-05T22:08:28Z",
    "registration_attempts_for_this_study_cap": 0,
    "resources": {"work_minutes_cap": 90, "auxiliary_test_seconds_cap": 1800,
                  "fit_seconds_per_role_cap": 0, "fit_seconds_study_cap": 0,
                  "administration_prepaid_seconds": 300, "native_samples_cap": 1,
                  "native_sample_bytes_cap": 262144, "new_download_bytes_cap": 0},
    "question": "Does a minimal versioned grammar adapter remove the specific public column-header failure while preserving every numeric, stroke, geometry, model and scientific rule?",
    "previous_goal_turn_classification": "progress: cycle321 preserved failed intake, code conformance, exact histories and charged results; identified the public-header failure and changed the next safe action",
    "immutable_parent_reference_sha256": {p: sha256_file(root / p) for p in refs},
    "parent_manifest_sha256": sha256_file(root / "research/eval_manifest.json"),
    "recipe": {
        "new_module": "src/nextai_autoresearch/asm01_task_v3.py",
        "implementation": "New parse_native_sample adapter only; original asm01_task.py/v2 and all source/candidate/benchmark/model/analysis/scientific-plan bytes stay unchanged. Delegate numeric/stroke/geometry handling to the exact V1 parser.",
        "column_tokens": ["X", "Y", "STYLUS_STATE", "STROKE"],
        "accepted_location": "Only index2 of the stripped nonempty lines, immediately after CHARACTER_NAME and STROKE_COUNT; zero or one exact whitespace-separated header. No other line removed.",
        "duplicate_or_misplaced_header": "Reject before numeric conversion",
        "absent_header": "Delegate original bytes unchanged; preserve V1 success/failure and outputs",
        "malformed_header": "Reject via unchanged strict V1 grammar, never infer or reorder fields",
        "original_byte_and_point_caps": "Apply the original bytes type/262144-byte cap before removal; retain32768point cap and all original numeric/state/stroke/bounds/view validation",
        "descriptor_and_model_change": False,
    },
    "tests": [
        "Space/tab-separated valid public header, legacy no-header exact output equivalence and equal write/nominal/adverse descriptors",
        "Duplicate header, header before stroke count or after PEN_DOWN/points, reordered/missing/extra/renamed/case-changed columns must reject",
        "Point bounds, point state, stroke serial, pen lifecycle, degenerate view, input type and pre-removal byte cap remain strict",
        "Original V1 parser still fails on the valid header fixture and unchanged already-exposed T1 payload",
        "Single native T1 parse and all3 descriptors finite/nondegenerate; return only count/shape/hashes, never coordinate/class values; no fitting or performance inference",
        "Clone source identity, protected science byte preservation, manifest/preflight/doctor/lab lifecycle and prefix accounting",
    ],
    "native_validation": {
        "root": "Independent NEXTAI-VALIDATION-20261002 checkout only",
        "relative_path": "research/data/asm01_native_v1/screen-text-v2/Online Handwritten Assamese Characters Dataset/W1/1.1.TXT",
        "expected_bytes": 10644,
        "expected_sha256": "4c3e65ac49ff5ad55f521ab9f86b47dbaa55cfb5cd341d6d1d234ad1d4e9dfff",
        "already_exposed_training_sample": True,
        "numerical_conversion_authorized_for_this_sample_only": True,
        "new_sample_access": False, "new_extraction": False, "class_names_or_coordinate_values_in_outputs": False,
    },
    "decision_rule": "KEEP technical adapter only if every declared fixture, old-source preservation, single authorized native conformance and clone integrity check passes. Native failure stops all unstarted scientific scope and is INCONCLUSIVE, with no same-cycle schema rescue. No learning/transfer/economic claim or scoring readiness from technical success.",
    "unchanged_gates": json.loads((root / "research/plans/NEXTAI-FAMILY2-INTAKE-PREPARATION-V1.json").read_text())["unchanged_gates"],
    "forbidden": ["new EXP/registration", "research fit", "scoring", "new native sample/NPZ/generator data", "model or descriptor changes", "source replay", "D sample numerical access", "future replication/final files", "WT8-9", "external model/API", "schedule changes", "paid retry", "completed plan/result edits", "weakened gates"],
    "next_discriminating_experiment": "After technical success, separately freeze a NEW ASM scientific cohort and intake with the same source states,models,4096pairs,steps,metrics,calibration/classical grids,gates,costs and five predefined disjoint writer pairs; verify native feasibility,independent clone/preflight/readiness before exactly one audited EXP. Preserve the exposed-T1 limitation and failed V1/V2; no same-plan retry.",
}
atomic_write_json(root / plan_path, plan)
archive = root / "research/laboratory/archive/ASM01-grammar-cycle322-parent-V1"
assert not archive.exists()
parents = ["AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md",
           "config/research.toml", "research/eval_manifest.json", "research/laboratory/preflight_certificate.json",
           "research/state.json", "src/nextai_autoresearch/asm01_task.py", "src/nextai_autoresearch/asm01_task_v2.py"]
for relative in parents:
    dest = archive / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / relative, dest)
atomic_write_json(root / "research/reviews/ASM01-GRAMMAR-PARENT-BYTES-V1.json", {
    "created_at": utc_now(), "archive_path": archive.relative_to(root).as_posix(),
    "files": {p: sha256_file(root / p) for p in parents}, "all_current_protected_files": 1432,
})
append_jsonl(root / "research/events.jsonl", {
    "event": "research_program_study_frozen", "created_at": utc_now(), "cycle": 322,
    "program_id": wallet["id"], "study_path": plan_path, "study_sha256": sha256_file(root / plan_path),
    "no_implementation_or_new_native_numeric_access_yet": True,
})
config = root / "config/research.toml"
before = config.read_bytes()
old = b'study_path = "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json"'
assert before.count(old) == 1
config.write_bytes(before.replace(old, f'study_path = "{plan_path}"'.encode()))
header = ("# Current cycle322 — prospective native grammar conformance (2026-10-05)\n\n"
          "ASM01-NATIVE-GRAMMAR-CONFORMANCE-V1 is a separate preparation-only contract.\n"
          "Deadline2026-10-05T22:08:28Z; auxiliary1800s including startup/failures/admin;\n"
          "zero research fit,EXP or registration. Keep maintenance/scoring=false.\n"
          "A versioned parser adapter accepts only the public four-column header after\n"
          "stroke count. Preserve exact V1/V2 source,all models/descriptors/gates.\n"
          "Test public positive/negative fixtures and only the already-exposed W1/1.1\n"
          "training sample in the independent clone; no new sample,extraction,D,future\n"
          "replication/final data or native NPZ. Native failure stops unstarted scope.\n"
          "Technical success does not establish transfer or scoring readiness; a new\n"
          "separately frozen scientific cohort/intake is required for one audited EXP.\n"
          "B remains active; protected7tickets/47000s and old budgets/history unchanged.\n"
          "No paid retry,WT8-9,external model/API or schedule change.\n\n"
          "All earlier stage-specific text below is preserved history.\n\n").encode("utf-8")
for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"):
    (root / relative).write_bytes(header + (root / relative).read_bytes())
state_path = root / "research/state.json"
state = json.loads(state_path.read_text())
assert state["cycle_number"] == 321 and state["completed_experiments"] == 122 and state["active_experiment_id"] is None
state.update(cycle_number=322, updated_at=utc_now())
atomic_write_json(state_path, state)
print(json.dumps({"plan_path": plan_path, "plan_sha256": sha256_file(root / plan_path),
                  "maintenance": True, "new_EXP": 0, "native_numeric_reads": 0}))
