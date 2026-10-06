"""Freeze a new inventory binding before implementation and new native text."""
from pathlib import Path
import json
import shutil

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_charge, auxiliary_reserve, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
previous_plan = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.json"
plan_path = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.json"
assert root.name == "NEXTAI" and not (root / plan_path).exists()
assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock",
    "src/nextai_autoresearch/asm01_inventory_v2.py", "tests/test_asm01_inventory_v2.py"))
for suffix in ("startup-doctor", "startup-lab"):
    check = json.loads((root / f"research/reviews/NEXTAI-B-326-{suffix}.json").read_text())
    assert check["result"]["returncode"] == 0 and not check["error"]
    assert not check["result"]["exit_job_active_process_count"]
lab = json.loads((root / "research/reviews/NEXTAI-B-326-startup-lab.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
completed = "research/laboratory/ASM01-CYCLE325-COMPLETION-V1.receipt.json"
closure = json.loads((root / completed).read_text())
assert closure["native_scope_stopped"] and not closure["native_inventory_executed"]
assert closure["new_native_texts"] == 0 and closure["corrected_passed_cases"] == 36
assert verify_manifest(root)["ok"]
wallet = status(root)
assert wallet["study_terminal"] and not wallet["program_terminal"]
assert not wallet["paid_run_pending"] and wallet["pending_fit_reservation_seconds"] == 0
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000
identifier = "NEXTAI-B-326-administration-prepaid"
auxiliary_reserve(root, identifier, 300)
auxiliary_charge(root, identifier, 300)
atomic_write_json(root / f"research/reviews/{identifier}.json", {
    "id": identifier, "created_at": utc_now(), "seconds_charged": 300,
    "cap_seconds": 300, "conservative_prepaid": True,
    "scope": "Required reads, metadata construction, syntax, archived parent bytes, report, settled mirrors and Git. No native scan, numerical parser/model call or substantive test; these are charged separately.",
})
wallet = status(root)
parent_paths = ["AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md",
                "config/research.toml", "research/eval_manifest.json",
                "research/laboratory/preflight_certificate.json", "research/state.json"]
archive = root / "research/laboratory/archive/ASM01-cycle326-parent-V1"
assert not archive.exists()
for relative in parent_paths:
    destination = archive / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / relative, destination)
plan = json.loads((root / previous_plan).read_text())
references = list(plan["parent_reference_sha256"]) + [previous_plan, completed,
    "research/plans/ASM01-INVENTORY-FIXTURE-ID-CONFORMANCE-V1.json",
    "research/reviews/ASM01-INVENTORY-FIXTURE-ID-CONFORMANCE-V1.receipt.json",
    "src/nextai_autoresearch/asm01_grammar_inventory.py",
    "tests/test_asm01_grammar_inventory.py"]
plan.update(id="ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2", cycle=326, created_at=utc_now(),
    study_started_at="2026-10-06T00:28:24Z", study_deadline_at="2026-10-06T02:28:24Z",
    budget_at_freeze=wallet,
    budget_snapshot_stage="After settled startup charges and administration prepayment; before selecting the new study in config. Ledger is authoritative.",
    parent_reference_sha256={p: sha256_file(root / p) for p in references},
    parent_archive_path=archive.relative_to(root).as_posix(),
    parent_manifest_sha256=sha256_file(root / "research/eval_manifest.json"),
    previous_goal_turn_classification="progress: cycle325 preserved the failed Windows fixture, preregistered and passed 36 short-ID cases, closed lifecycle/Lab and sealed identical clean checkouts. Native scope remained unexecuted; no scientific result or genuine impasse.",
    previous_study_sha256=sha256_file(root / previous_plan),
    native_execution_count_cap=1,
    native_receipt_path="research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.receipt.json",
    conformance_path="research/reviews/ASM01-INVENTORY-V2-PRECONTENT-CONFORMANCE-V1.json",
    entrypoint_implementation_policy="Reuse inventory_bytes and screen_members from the byte-identical conformed scanner. The new fixed entrypoint copies the V1 main body with only cycle/study/proof/output bindings and scanner versus entrypoint hash metadata changed. No native parsing algorithm or numerical geometry changes.",
    prospective_fixture_matrix={"unchanged_short_ID_scanner_cases": 36,
        "new_binding_cases": ["wrong checkout rejects before payload", "STOP rejects before payload",
            "PAUSE rejects before payload", "run.lock rejects before payload",
            "wrong study hash rejects before payload", "main AST unchanged except declared bindings/hash metadata"],
        "total_cases": 42, "native_payloads": 0, "research_fit": 0},
    validation="Exactly one 42-case synthetic run in the independent clone, retaining the unchanged 36 scanner fixtures and six binding guards; precontent source/manifest/hash proof before exactly one complete 1830-file inventory. Then lifecycle and full Lab/Doctor plus matching protected source in both checkouts. No failed fixture or native retry.")
assert sha256_file(clone / plan["scope"]["listing_relative_path"]) == plan["scope"]["listing_sha256"]
atomic_write_json(root / plan_path, plan)
atomic_write_json(root / "research/reviews/ASM01-INVENTORY-V2-PARENT-BYTES-V1.json", {
    "created_at": utc_now(), "archive_path": archive.relative_to(root).as_posix(),
    "files": {p: sha256_file(root / p) for p in parent_paths}, "protected_files": 1448})
append_jsonl(root / "research/events.jsonl", {"event": "research_program_study_frozen",
    "created_at": utc_now(), "cycle": 326, "program_id": wallet["id"],
    "study_path": plan_path, "study_sha256": sha256_file(root / plan_path),
    "new_entrypoint_implemented": False, "new_native_texts_seen": 0})
config = root / "config/research.toml"
old = f'study_path = "{previous_plan}"'.encode()
assert config.read_bytes().count(old) == 1
config.write_bytes(config.read_bytes().replace(old, f'study_path = "{plan_path}"'.encode()))
header = ("# Current cycle326 — ASM01 inventory V2 (2026-10-06)\n\n"
    "Preparation only; deadline2026-10-06T02:28:24Z, auxiliary cap1800s including all failures/admin.\n"
    "One complete inventory of the fixed1830 T1-5/D16-20 texts;75 prior raw exposures/74 conversions disclosed.\n"
    "Unchanged scanner and36 short-ID fixtures; new fixed bindings validated before new bytes.\n"
    "Only redacted lexical/categorical structure; no coordinates, parser/geometry repair, model, fit, EXP or NPZ.\n"
    "Any fixture or intake failure stops unstarted scope; no retry or sample filtering.\n"
    "Maintenance/scoring=false; B/full goal active; future7tickets/47000s protected.\n"
    "No future writers6-15/21-30,WT8-9,external model/API or schedule change.\n\n"
    "Earlier stage-specific sections below remain preserved history.\n\n").encode()
for relative in parent_paths[:4]:
    (root / relative).write_bytes(header + (root / relative).read_bytes())
state = json.loads((root / "research/state.json").read_text())
assert state["cycle_number"] == 325 and state["completed_experiments"] == 122
assert state["active_experiment_id"] is None
state.update(cycle_number=326, updated_at=utc_now())
atomic_write_json(root / "research/state.json", state)
print(json.dumps({"study_path": plan_path, "study_sha256": sha256_file(root / plan_path),
    "scanner_unchanged": True, "new_entrypoint_implemented": False, "new_native_texts_seen": 0}), flush=True)
