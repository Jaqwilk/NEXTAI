"""Freeze structural diagnosis before implementing it or reopening known T1."""
from pathlib import Path
import json
import shutil

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_charge, auxiliary_reserve, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
plan_path = "research/plans/ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1.json"
assert root.name == "NEXTAI" and not (root / plan_path).exists()
assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
for suffix in ("startup-doctor", "startup-lab"):
    check = json.loads((root / f"research/reviews/NEXTAI-B-323-{suffix}.json").read_text())
    assert check["result"]["returncode"] == 0 and not check["error"]
lab = json.loads((root / "research/reviews/NEXTAI-B-323-startup-lab.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
wallet = status(root)
assert wallet["study_terminal"] and not wallet["program_terminal"]
assert wallet["pending_fit_reservation_seconds"] == 0 and not wallet["paid_run_pending"]
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000
assert verify_manifest(root)["ok"]
identifier = "NEXTAI-B-323-administration-prepaid"
auxiliary_reserve(root, identifier, 300)
auxiliary_charge(root, identifier, 300)
atomic_write_json(root / f"research/reviews/{identifier}.json", {
    "id": identifier, "created_at": utc_now(), "seconds_charged": 300, "cap_seconds": 300,
    "conservative_prepaid": True,
    "scope": "Required prereads, administrative scripts/syntax, prospective diagnosis and separate repair contracts, archives/header/config/state, settled byte mirrors, final derived report and Git; no native diagnosis, parse, fixture or scoring. Substantive checks separately charged.",
})
parent_paths = ["AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md",
                "config/research.toml", "research/eval_manifest.json",
                "research/laboratory/preflight_certificate.json", "research/state.json"]
archive = root / "research/laboratory/archive/ASM01-serializer-cycle323-parent-V1"
assert not archive.exists()
for relative in parent_paths:
    destination = archive / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / relative, destination)
parent_manifest = json.loads((root / "research/eval_manifest.json").read_text())
parent_refs = ["research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json",
               "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json",
               "research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json",
               "research/plans/ASM01-NATIVE-GRAMMAR-CONFORMANCE-V1.json",
               "research/laboratory/ASM01-CYCLE322-COMPLETION-V1.receipt.json",
               "research/reviews/ASM01-EXPOSED-T1-GRAMMAR-CONFORMANCE-V1.json"]
plan = {
    "schema_version": 1, "id": "ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1",
    "created_at": utc_now(), "cycle": 323, "stage": "task_design", "study_kind": "preparation_only",
    "cohort": "asm01_native_memory_v2", "program_id": wallet["id"],
    "program_contract_path": wallet["contract_path"],
    "program_contract_sha256": sha256_file(root / wallet["contract_path"]),
    "study_started_at": "2026-10-05T21:38:34Z", "study_deadline_at": "2026-10-05T23:38:34Z",
    "registration_attempts_for_this_study_cap": 0,
    "question": "Which complete serializer row forms explain the exposed T1 failure, and can a separately prospectively frozen metadata-only normalization preserve all numeric geometry and scientific rules?",
    "previous_goal_turn_classification": "progress: cycle322 implemented and validated header handling, preserved failures and exact budgets, and identified PEN_UP as the next concrete serializer error; no genuine impasse",
    "resources": {"work_minutes_cap": 120, "auxiliary_test_seconds_cap": 2200,
                  "fit_seconds_study_cap": 0, "fit_seconds_per_role_cap": 0,
                  "administration_prepaid_seconds": 300, "native_samples_cap": 1,
                  "native_sample_bytes_cap": 262144, "new_download_bytes_cap": 0},
    "parent_reference_sha256": {p: sha256_file(root / p) for p in parent_refs},
    "parent_manifest_sha256": sha256_file(root / "research/eval_manifest.json"),
    "parent_archive_path": archive.relative_to(root).as_posix(),
    "native_validation": json.loads((root / parent_refs[3]).read_text())["native_validation"],
    "diagnosis_recipe": {
        "scope": "Only exact SHA-bound already-exposed W1/1.1 in the independent clone; no other native file, extraction or NPZ.",
        "enumeration": "Every nonempty row: declared header/end category, complete recognized column-header positions, PEN_DOWN/PEN_UP token counts and per-field lexical kinds, point-row token counts/kinds and categorical state/stroke counts, pen alternation/serial pattern and declared stroke count.",
        "redaction": "Never emit character names, X/Y coordinate values or unknown raw tokens. Coordinate fields get lexical-kind histograms only, no int/float conversion. Emit only trailing categorical marker state/stroke fields when positions are unambiguous and only point state/stroke fields; any other fields redacted by type.",
        "models_and_geometry": "No original parser/model call, point array, descriptor, fitting, threshold/metric selection or scientific inference during diagnosis.",
        "bound": "One sample at most262144 bytes; record whole-sample SHA and complete row-count coverage; report unknown forms rather than guessing.",
    },
    "conditional_repair": {
        "must_freeze_before_implementation": "A NEW immutable ASM01-SERIALIZER-METADATA-REPAIR-V1.json, hash-bound to the completed structural diagnosis, specifying every accepted/rejected change and fixture before parser implementation or renewed numeric T1 conversion.",
        "allowed_scope": "New minimal versioned adapter only. Metadata row normalization with exact public header/pen token grammar; original V1/V2/V3, candidates, models, generators, numeric bounds/state/stroke/point caps, geometry/views and scientific contracts remain byte-identical.",
        "not_authorized": "No post-parse native failure rescue in this cycle. If geometry/numeric law would need changing, close inconclusive and choose a separate prospective task decision.",
        "validation": "Synthetic valid/invalid header/marker/lifecycle/numeric/type/byte cases and exact old-parser/descriptor equivalence; then one bounded parse of exact known T1, counts/shapes/hashes only. New sample/D/future access0, fit0, scoringfalse.",
    },
    "unchanged_gates": json.loads((root / parent_refs[3]).read_text())["unchanged_gates"],
    "decision_rule": "KEEP only technical serializer conformance if complete diagnosis, separately preregistered repair fixtures, exact single T1 parse/views and clone integrity/lifecycle pass; otherwise INCONCLUSIVE and stop unstarted scope. No learning/transfer/economic claim or scoring readiness.",
    "forbidden": ["EXP/registration", "research fit", "new native samples/extraction/NPZ", "D/future coordinates", "source refit", "model/descriptor/gate changes", "completed artifact edits", "paid retry", "WT8-9", "external model/API", "schedule changes"],
    "next_discriminating_experiment": "After technical success freeze a NEW native scientific intake/cohort with exact models,source states,4096pairs,steps,metrics,grids/gates and five predefined writer pairs; independent clone/native feasibility/preflight/readiness before exactly one audited three-scale nominal/adverse EXP. Disclose already-exposed T1 and preserve failed V1/V2/grammarV3.",
}
atomic_write_json(root / plan_path, plan)
atomic_write_json(root / "research/reviews/ASM01-STRUCTURE-PARENT-BYTES-V1.json", {
    "created_at": utc_now(), "archive_path": archive.relative_to(root).as_posix(),
    "files": {p: sha256_file(root / p) for p in parent_paths},
    "all_current_protected_files": len(parent_manifest["files"]),
})
append_jsonl(root / "research/events.jsonl", {
    "event": "research_program_study_frozen", "created_at": utc_now(), "cycle": 323,
    "program_id": wallet["id"], "study_path": plan_path, "study_sha256": sha256_file(root / plan_path),
    "no_diagnosis_implementation_or_native_reopen_yet": True,
})
config = root / "config/research.toml"
old = b'study_path = "research/plans/ASM01-NATIVE-GRAMMAR-CONFORMANCE-V1.json"'
assert config.read_bytes().count(old) == 1
config.write_bytes(config.read_bytes().replace(old, f'study_path = "{plan_path}"'.encode()))
header = ("# Current cycle323 — complete native serializer conformance (2026-10-05)\n\n"
          "ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1 is preparation only.\n"
          "Deadline2026-10-05T23:38:34Z; auxiliary2200s includes startup/failures/admin.\n"
          "Zero EXP,registration,research fit,new native sample/extraction/NPZ or scoring.\n"
          "Diagnose every row form in only exact already-exposed T1,redacting coordinates/names.\n"
          "Freeze a separate hash-bound concrete metadata repair BEFORE implementing it,\n"
          "then validate synthetic fixtures and one T1 parse in the independent clone.\n"
          "Preserve V1/V2/V3,all geometry/models/numeric rules/metrics/grids/gates/history.\n"
          "Native failure stops unstarted scope; no same-cycle schema rescue.\n"
          "Technical success needs a NEW separately frozen scientific cohort/intake;\n"
          "it is not learning,transfer,economics or scoring readiness. B remains active,\n"
          "protected7tickets/47000s unchanged; no paid retry,WT8-9,external model/API or schedule change.\n\n"
          "Earlier stage-specific sections below remain preserved history.\n\n").encode()
for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"):
    (root / relative).write_bytes(header + (root / relative).read_bytes())
state_path = root / "research/state.json"
state = json.loads(state_path.read_text())
assert state["cycle_number"] == 322 and state["completed_experiments"] == 122 and state["active_experiment_id"] is None
state.update(cycle_number=323, updated_at=utc_now())
atomic_write_json(state_path, state)
print(json.dumps({"plan_path": plan_path, "plan_sha256": sha256_file(root / plan_path),
                  "native_reopen": False, "maintenance": True, "scoring": False}), flush=True)
