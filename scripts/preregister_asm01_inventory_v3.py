"""Activate the separately frozen extension-only recipe before code or content."""
import json
from pathlib import Path
import shutil

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_charge, auxiliary_reserve, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
previous = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.json"
study = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.json"
proposal = "research/plans/ASM01-EXTENSION-CASE-REPAIR-PROSPECTIVE-V1.json"
completion = "research/laboratory/ASM01-CYCLE326-COMPLETION-V1.receipt.json"
assert root.name == "NEXTAI" and not (root / study).exists()
assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock",
    "src/nextai_autoresearch/asm01_inventory_v3.py", "src/nextai_autoresearch/asm01_inventory_members_v3.py",
    "tests/test_asm01_inventory_v3.py"))
assert sha256_file(root / proposal) == "6ec1001b6ea667dcc9e6b3582516cfb39483d71dff5cee48dc0f11373ee483f8"
for suffix in ("startup-doctor-local-cache", "startup-lab"):
    check = json.loads((root / f"research/reviews/NEXTAI-B-327-{suffix}.json").read_text())
    assert check["result"]["returncode"] == 0 and not check["error"]
    assert check["result"]["exit_job_active_process_count"] == 0
lab = json.loads((root / "research/reviews/NEXTAI-B-327-startup-lab.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
old = json.loads((root / completion).read_text())
assert old["native_scope_stopped"] and old["native_attempt_consumed"]
assert old["new_native_texts"] == 0 and not old["repair_implemented"]
assert verify_manifest(root)["ok"]
wallet = status(root)
assert wallet["study_terminal"] and not wallet["program_terminal"]
assert wallet["pending_fit_reservation_seconds"] == 0 and not wallet["paid_run_pending"]
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["fit_seconds_remaining"] - 47000 >= 1800
key = "NEXTAI-B-327-administration-prepaid"
auxiliary_reserve(root, key, 300)
auxiliary_charge(root, key, 300)
atomic_write_json(root / f"research/reviews/{key}.json", dict(id=key, created_at=utc_now(),
    seconds_charged=300, cap_seconds=300, conservative_prepaid=True,
    scope="Required reads and delegated read-only review, metadata/archive construction, syntax, report, settled mirrors and Git. Substantive tests, real metadata and native scan charged separately."))
wallet = status(root)
parents = ["AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md",
           "config/research.toml", "research/eval_manifest.json",
           "research/laboratory/preflight_certificate.json", "research/state.json"]
archive = root / "research/laboratory/archive/ASM01-cycle327-parent-V1"
assert not archive.exists()
for relative in parents:
    destination = archive / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / relative, destination)
plan = json.loads((root / previous).read_text())
references = list(plan["parent_reference_sha256"]) + [previous, proposal, completion,
    "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.receipt.json",
    "research/reviews/ASM01-INVENTORY-V2-EXTENSION-CASE-DIAGNOSIS-V1.json",
    "src/nextai_autoresearch/asm01_inventory_v2.py", "tests/test_asm01_inventory_v2.py"]
adapter_cases = ["accept-lower", "accept-mixed-actual-paths", "listing-missing", "listing-extra",
    "listing-duplicate", "listing-alias-collision", "listing-future", "listing-traversal",
    "listing-absolute", "listing-backslash", "listing-mixedcase", "listing-dircase", "listing-uid",
    "disk-missing", "disk-extra", "disk-alias-collision", "disk-rawcase-mismatch", "disk-foreign-dir",
    "root-symlink", "root-junction", "ancestor-link", "file-link", "directory-link", "resolved-escape",
    "per-file-cap", "aggregate-cap", "scanner-identity", "metadata-before-payload"]
plan.update(id="ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3", cycle=327, created_at=utc_now(),
    study_started_at="2026-10-06T01:21:00Z", study_deadline_at="2026-10-06T03:21:00Z",
    budget_at_freeze=wallet, previous_study_sha256=sha256_file(root / previous),
    parent_archive_path=archive.relative_to(root).as_posix(),
    parent_manifest_sha256=sha256_file(root / "research/eval_manifest.json"),
    parent_reference_sha256={p: sha256_file(root / p) for p in references},
    previous_goal_turn_classification="progress: terminal326 preserved failed intake before bytes and proved complete filename alias bijection; prospective concrete repair exists. No live handle or genuine impasse.",
    native_receipt_path="research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.receipt.json",
    conformance_path="research/reviews/ASM01-INVENTORY-V3-PRECONTENT-CONFORMANCE-V1.json",
    prospective_extension_recipe_path=proposal, prospective_extension_recipe_sha256=sha256_file(root / proposal),
    extension_recipe=json.loads((root / proposal).read_text())["recipe"],
    real_metadata_proof_path="research/reviews/ASM01-INVENTORY-V3-REAL-METADATA-V1.json",
    real_metadata_requirements={"files":1830, "uppercase_extensions":153, "uppercase_writer":5,
        "raw_name_set_sha256":"e96399e79a24b32109c3818eedd9b4f60a5143457d75df0eb75062928144597c",
        "raw_listing_equals_disk":True, "canonical_bijection":True, "links":0,
        "known_total_bytes":14394085, "known_max_bytes":25086},
    entrypoint_implementation_policy="Separate metadata-only adapter normalizes final literal .txt/.TXT in BOTH listing and disk raw strings. Guard ancestors and directories before descent; preserve actual Path and all fixed UIDs/order. Reuse inventory_bytes by identity with its exact original source hash. New V3 bindings/proofs guard before payload; add a separate payload_read_attempts count/current UID BEFORE opening, retaining successful-read counts. No parser/geometry/model change.",
    prospective_fixture_matrix={"unchanged_short_ID_scanner_cases":36,
        "new_binding_cases":["wrong checkout", "STOP", "PAUSE", "run.lock", "wrong study hash", "fixed V3 binding and unchanged scanner identity"],
        "adapter_cases":adapter_cases, "total_cases":70, "native_payloads":0, "research_fit":0,
        "aggregate_cap_fixture":"Production aggregate cap equals1830 times per-file cap and cannot independently overflow with every valid member. Assert exact unchanged production constants; only in this synthetic test monkeypatch the aggregate threshold smaller to exercise its rejection branch. No native threshold changes."},
    validation="Exactly one70-case synthetic run in independent clone; preserve36 scanner tests, six V3 guards and28 frozen adapter cases with short explicit IDs. Validate actual complete1830-name metadata/bounds before payload. Freeze proof/source/manifest before at most one complete lexical scan; then lifecycle and full Lab/Doctor. Failed synthetic/intake stops unstarted native scope without retry.",
    startup_failure_disclosure="First Doctor never started: default uv cache denied by managed filesystem;54s failure preserved. Prospective local UV_CACHE_DIR/offline/no-sync infrastructure overlay does not retry scientific or native scope.")
atomic_write_json(root / study, plan)
append_jsonl(root / "research/events.jsonl", dict(event="research_program_study_frozen", created_at=utc_now(),
    cycle=327, program_id=wallet["id"], study_path=study, study_sha256=sha256_file(root / study),
    new_adapter_implemented=False, new_native_texts_seen=0))
config = root / "config/research.toml"
needle = f'study_path = "{previous}"'.encode()
assert config.read_bytes().count(needle) == 1
config.write_bytes(config.read_bytes().replace(needle, f'study_path = "{study}"'.encode()))
header = ("# Current cycle327 — extension-only inventory V3 (2026-10-06)\n\n"
    "New separate preparation-only contract; deadline03:21Z,all auxiliary1800s including failures/admin.\n"
    "Accept only final .txt/.TXT aliases in listing AND disk; preserve all1830 UIDs/actual paths/order.\n"
    "70 synthetic cases and complete real metadata proof before one full lexical inventory.\n"
    "Unchanged scanner; no coordinates,numeric parser/geometry/model repair,fit,EXP or NPZ.\n"
    "Prior75 raw/74 numerical exposures disclosed; preserve all consumed V1/V2 failures.\n"
    "Any fixture/intake failure stops unstarted native scope; no retry or sample filtering.\n"
    "Maintenance/scoring=false; B/full goal active; protected7tickets/47000s unchanged.\n"
    "No future writers6-15/21-30,WT8-9,external model/API or schedule change.\n\n"
    "Earlier stage-specific sections below remain preserved history.\n\n").encode()
for relative in parents[:4]:
    (root / relative).write_bytes(header + (root / relative).read_bytes())
state = json.loads((root / "research/state.json").read_text())
assert state["cycle_number"] == 326 and state["active_experiment_id"] is None
state.update(cycle_number=327, updated_at=utc_now())
atomic_write_json(root / "research/state.json", state)
print(json.dumps(dict(study_path=study, study_sha256=sha256_file(root / study), new_code=False, new_native_texts=0)), flush=True)
