"""Mirror settled cycle325 records under prepaid administration, without native reads."""
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
assert root.name == "NEXTAI" and (clone / ".git").is_dir()
assert root.resolve() != clone.resolve()
proof_path = "research/reviews/ASM01-INVENTORY-FINAL-ADMIN-MIRROR-V1.json"
assert not any((directory / proof_path).exists() for directory in (root, clone))
completion_path = "research/laboratory/ASM01-CYCLE325-COMPLETION-V1.receipt.json"
completion = json.loads((root / completion_path).read_text(encoding="utf-8"))
assert completion["cycle"] == 325 and completion["native_scope_stopped"]
assert not completion["native_inventory_executed"]
assert completion["cycle_auxiliary_seconds_charged"] == 1364
assert completion["corrected_passed_cases"] == 36
assert completion["full_clone_Lab_including_Doctor_pass"]
write_report(root)

mutable = {"research/events.jsonl", "research/state.json", "research/REPORT.md",
           "research/REPORT.provenance.json"}
owned = set(mutable)
prefixes = ("research/reviews/NEXTAI-B-325-", "research/reviews/ASM01-INVENTORY-",
            "research/laboratory/ASM01-CYCLE325-", "research/analyses/ASM01-CYCLE325-")
helpers = {"scripts/verify_asm01_inventory_clone_maintenance.py",
           "scripts/close_asm01_inventory_precontent_failure.py",
           "scripts/mirror_asm01_inventory_closure.py"}
for item in subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root).decode().split("\0"):
    if not item:
        continue
    relative = item[3:]
    assert relative in mutable or relative in helpers or relative.startswith(prefixes), relative
    owned.add(relative)
assert (root / "research/events.jsonl").read_bytes().startswith(
    (clone / "research/events.jsonl").read_bytes())
for relative in sorted(owned):
    source, destination = root / relative, clone / relative
    if destination.exists() and relative not in mutable:
        assert destination.read_bytes() == source.read_bytes(), relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())

manifest = json.loads((root / "research/eval_manifest.json").read_text(encoding="utf-8"))
assert len(manifest["files"]) == 1448
paths = set(manifest["files"]) | owned | {"research/experiments.tsv", "research/sources.jsonl"}
digests = {}
for relative in sorted(paths):
    digest = sha256_file(root / relative)
    assert sha256_file(clone / relative) == digest, relative
    digests[relative] = digest
checks = {"original": verify_manifest(root), "clone": verify_manifest(clone)}
assert all(item["ok"] for item in checks.values()), checks
wallets = {"original": status(root), "clone": status(clone)}
assert wallets["original"] == wallets["clone"]
wallet = wallets["original"]
assert wallet["study_terminal"] and not wallet["program_terminal"]
assert not wallet["scoring_authorized"] and not wallet["paid_run_pending"] and not wallet["ready"]
assert wallet["pending_fit_reservation_seconds"] == 0
assert wallet["protected_future_compute_seconds"] == 47000
assert wallet["protected_future_registration_attempts"] == 7
for directory in (root, clone):
    assert sha256_file(directory / "research/results/EXP-20261005-0007.json") == "78380a19ffacf4a58af0bd8586425fbacee44b2e5a92c6e056f3699f769ed255"
    assert sha256_file(directory / "research/results/EXP-20261005-0006.fitted-state.zip") == "3576935b401f6c9324f2f4ed426de104b632a22ba74fb04da55757421f7632a8"
    forbidden = ("STOP", "PAUSE", "research/run.lock",
                 "research/reviews/ASM01-INVENTORY-PRECONTENT-CONFORMANCE-V1.json",
                 "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.receipt.json",
                 "research/data/asm01_native_v1/screen-v3.npz")
    assert not any((directory / name).exists() for name in forbidden)
    state = json.loads((directory / "research/state.json").read_text(encoding="utf-8"))
    assert state["cycle_number"] == 325 and state["completed_experiments"] == 122
    assert state["active_experiment_id"] is None and state["last_experiment_id"] == "EXP-20261005-0007"
    previous = json.loads((directory / "research/data_manifests/ASM01-ACQUISITION-V3.json").read_text(encoding="utf-8"))
    assert (previous["native_files_attempted"], previous["native_files_converted"], previous["D_samples_opened"]) == (75, 74, 0)

receipt = dict(created_at=utc_now(), cycle=325, original_root=str(root), clone_root=str(clone),
               files_compared=len(digests), file_sha256=digests, protected_files=len(manifest["files"]),
               both_current_manifests_ok=True, manifest_verification=checks,
               both_program_status_identical=True, program=wallet,
               completion_receipt_sha256=sha256_file(root / completion_path),
               whole_wall_seconds=time.monotonic() - started,
               charged_by="NEXTAI-B-325-administration-prepaid", prepaid_seconds=300,
               new_EXPs=0, new_registrations=0, research_fit=0, scoring=False,
               native_data_decoded_in_mirror=False, native_inventory_executed=False,
               extended_goal_completed=False, disk_free_bytes=shutil.disk_usage(root).free)
atomic_write_json(root / proof_path, receipt)
(clone / proof_path).write_bytes((root / proof_path).read_bytes())
print(json.dumps({"mirror_ok": True, "files_compared": len(digests),
                  "protected_files": len(manifest["files"]), "both_manifests_ok": True,
                  "B_seconds": wallet["stage_b_compute_seconds_charged"],
                  "whole_wall_seconds": receipt["whole_wall_seconds"], "study_terminal": True,
                  "goal_complete": False}), flush=True)
