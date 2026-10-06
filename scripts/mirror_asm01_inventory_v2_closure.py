"""Mirror cycle326 closure and prove preserved source/accounting in both checkouts."""
import json
from pathlib import Path
import shutil
import subprocess
import time

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

started = time.monotonic()
root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
assert root.name == "NEXTAI" and (clone / ".git").is_dir() and root.resolve() != clone.resolve()
proof_path = "research/reviews/ASM01-INVENTORY-V2-FINAL-ADMIN-MIRROR-V1.json"
assert not any((d / proof_path).exists() for d in (root, clone))
completion_path = "research/laboratory/ASM01-CYCLE326-COMPLETION-V1.receipt.json"
completion = json.loads((root / completion_path).read_text())
assert completion["cycle"] == 326 and completion["native_scope_stopped"]
assert completion["native_attempt_consumed"] and not completion["native_inventory_complete"]
assert completion["synthetic_passed_cases"] == 42 and not completion["repair_implemented"]
assert completion["cycle_auxiliary_seconds_charged"] <= 1800
write_report(root)
mutable = {"research/events.jsonl", "research/state.json", "research/REPORT.md", "research/REPORT.provenance.json"}
fixed = {"scripts/inspect_asm01_inventory_case_metadata.py", "scripts/close_asm01_inventory_v2_failure.py",
         "scripts/mirror_asm01_inventory_v2_closure.py", "scripts/verify_asm01_inventory_v2_clone_maintenance.py",
         "research/plans/ASM01-EXTENSION-CASE-REPAIR-PROSPECTIVE-V1.json",
         "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.receipt.json"}
prefixes = ("research/reviews/NEXTAI-B-326-", "research/reviews/ASM01-INVENTORY-V2-",
            "research/laboratory/ASM01-CYCLE326-", "research/analyses/ASM01-CYCLE326-")
owned = set(mutable)
for row in subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=root).decode().split("\0"):
    if not row:
        continue
    assert row[:2] in (" M", "??"), row
    relative = row[3:]
    assert relative in mutable or relative in fixed or relative.startswith(prefixes), relative
    owned.add(relative)
assert (root / "research/events.jsonl").read_bytes().startswith((clone / "research/events.jsonl").read_bytes())
for relative in sorted(owned):
    source, destination = root / relative, clone / relative
    if destination.exists() and relative not in mutable:
        assert destination.read_bytes() == source.read_bytes(), relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
manifest = json.loads((root / "research/eval_manifest.json").read_text())
assert len(manifest["files"]) == 1450
digests = {}
for relative in sorted(set(manifest["files"]) | owned | {"research/experiments.tsv", "research/sources.jsonl"}):
    digest = sha256_file(root / relative)
    assert sha256_file(clone / relative) == digest, relative
    digests[relative] = digest
checks = {"original": verify_manifest(root), "clone": verify_manifest(clone)}
assert all(check["ok"] for check in checks.values())
wallets = {"original": status(root), "clone": status(clone)}
assert wallets["original"] == wallets["clone"]
wallet = wallets["original"]
assert wallet["study_terminal"] and not wallet["program_terminal"]
assert not wallet["scoring_authorized"] and not wallet["paid_run_pending"] and not wallet["ready"]
assert wallet["pending_fit_reservation_seconds"] == 0
assert wallet["protected_future_compute_seconds"] == 47000 and wallet["protected_future_registration_attempts"] == 7
for directory in (root, clone):
    assert sha256_file(directory / "research/results/EXP-20261005-0007.json") == "78380a19ffacf4a58af0bd8586425fbacee44b2e5a92c6e056f3699f769ed255"
    assert sha256_file(directory / "research/results/EXP-20261005-0006.fitted-state.zip") == "3576935b401f6c9324f2f4ed426de104b632a22ba74fb04da55757421f7632a8"
    assert not any((directory / p).exists() for p in ("STOP", "PAUSE", "research/run.lock",
        "research/reviews/ASM01-INVENTORY-PRECONTENT-CONFORMANCE-V1.json", "research/data/asm01_native_v1/screen-v3.npz"))
    failed = json.loads((directory / "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.receipt.json").read_text())
    assert not failed["complete"] and failed["attempted_files"] == failed["new_texts_opened"] == 0
    state = json.loads((directory / "research/state.json").read_text())
    assert state["cycle_number"] == 326 and state["completed_experiments"] == 122
    assert state["active_experiment_id"] is None and state["last_experiment_id"] == "EXP-20261005-0007"
    old = json.loads((directory / "research/data_manifests/ASM01-ACQUISITION-V3.json").read_text())
    assert (old["native_files_attempted"], old["native_files_converted"], old["D_samples_opened"]) == (75, 74, 0)
receipt = dict(created_at=utc_now(), cycle=326, original_root=str(root), clone_root=str(clone),
    files_compared=len(digests), file_sha256=digests, protected_files=1450,
    both_current_manifests_ok=True, manifest_verification=checks, both_program_status_identical=True,
    program=wallet, completion_receipt_sha256=sha256_file(root / completion_path),
    whole_wall_seconds=time.monotonic() - started, charged_by="NEXTAI-B-326-administration-prepaid", prepaid_seconds=300,
    new_EXPs=0, new_registrations=0, research_fit=0, scoring=False,
    native_attempt_consumed=True, native_inventory_complete=False, new_native_texts=0,
    native_data_decoded_in_mirror=False, repair_implemented=False, extended_goal_completed=False,
    disk_free_bytes=shutil.disk_usage(root).free)
atomic_write_json(root / proof_path, receipt)
(clone / proof_path).write_bytes((root / proof_path).read_bytes())
print(json.dumps({"mirror_ok": True, "files_compared": len(digests), "protected_files": 1450,
    "B_seconds": wallet["stage_b_compute_seconds_charged"], "whole_wall_seconds": receipt["whole_wall_seconds"],
    "study_terminal": True, "goal_complete": False}), flush=True)
