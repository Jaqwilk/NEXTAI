"""Mirror only settled cycle327 administration; never open native payloads."""
import json
from pathlib import Path
import shutil
import time

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


started = time.monotonic()
root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
assert root.name == "NEXTAI" and (clone / ".git").is_dir() and root.resolve() != clone.resolve()
proof_path = "research/reviews/ASM01-INVENTORY-V3-FINAL-ADMIN-MIRROR-V1.json"
assert not any((directory / proof_path).exists() for directory in (root, clone))
completion_path = "research/laboratory/ASM01-CYCLE327-COMPLETION-V1.receipt.json"
completion = json.loads((root / completion_path).read_text())
assert completion["cycle"] == 327 and completion["native_inventory_complete"]
assert completion["synthetic_passed_cases"] == 70 and completion["lifecycle_passed_cases"] == 1
assert completion["cycle_auxiliary_seconds_charged"] <= 1800 and not completion["repair_implemented"]
assert completion["negative_Y_numeric_values_known"] is False
write_report(root)
mutable = {"research/events.jsonl", "research/state.json", "research/REPORT.md", "research/REPORT.provenance.json"}
owned = mutable | {completion_path, completion["analysis_path"], completion["prospective_recipe_path"],
    "scripts/close_asm01_inventory_v3.py", "scripts/mirror_asm01_inventory_v3_closure.py",
    "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.receipt.json"}
owned |= {path.relative_to(root).as_posix() for path in (root / "research/reviews").glob("NEXTAI-B-327-*") if path.is_file()}
owned |= {path.relative_to(root).as_posix() for path in (root / "research/reviews").glob("ASM01-INVENTORY-V3-*") if path.is_file()}
assert (root / "research/events.jsonl").read_bytes().startswith((clone / "research/events.jsonl").read_bytes())
for relative in sorted(owned):
    source, destination = root / relative, clone / relative
    if destination.exists() and relative not in mutable:
        assert sha256_file(destination) == sha256_file(source), relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
manifest = json.loads((root / "research/eval_manifest.json").read_text())
assert len(manifest["files"]) == 1453
digests = {}
for relative in sorted(set(manifest["files"]) | owned | {"research/experiments.tsv", "research/sources.jsonl"}):
    digest = sha256_file(root / relative)
    assert sha256_file(clone / relative) == digest, relative
    digests[relative] = digest
excluded = sorted(path.relative_to(root).as_posix()
                  for parent in (root / "src", root / "tests")
                  for path in parent.rglob("*.py")
                  if path.relative_to(root).as_posix() not in manifest["files"])
checks = {"original": {"ok": True, "files_checked": 1453,
    "scope": "Exact frozen1453 checksums; separately authorized new MUC source excluded",
    "strict_current_discovery_asserted": False, "unfrozen_source_files_excluded": excluded},
    "clone": verify_manifest(clone)}
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
        "research/data/asm01_native_v1/screen-v3.npz"))
    native = json.loads((directory / "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.receipt.json").read_text())
    assert native["complete"] and native["inventoried_files"] == 1830
    state = json.loads((directory / "research/state.json").read_text())
    assert state["cycle_number"] == 327 and state["completed_experiments"] == 122
    assert state["active_experiment_id"] is None and state["last_experiment_id"] == "EXP-20261005-0007"
    old = json.loads((directory / "research/data_manifests/ASM01-ACQUISITION-V3.json").read_text())
    assert (old["native_files_attempted"], old["native_files_converted"], old["D_samples_opened"]) == (75, 74, 0)
receipt = dict(created_at=utc_now(), cycle=327, original_root=str(root), clone_root=str(clone),
    files_compared=len(digests), file_sha256=digests, protected_files=1453,
    both_frozen_file_sets_match=True, clone_current_manifest_ok=True,
    original_strict_current_discovery_asserted=False, manifest_verification=checks,
    both_program_status_identical=True,
    program=wallet, completion_receipt_sha256=sha256_file(root / completion_path),
    whole_wall_seconds=time.monotonic() - started, charged_by="NEXTAI-B-327-administration-prepaid", prepaid_seconds=300,
    new_EXPs=0, new_registrations=0, research_fit=0, scoring=False,
    native_attempt_consumed=True, native_inventory_complete=True, native_data_decoded_in_mirror=False,
    repair_implemented=False, negative_Y_numeric_values_known=False, extended_goal_completed=False,
    disk_free_bytes=shutil.disk_usage(root).free)
atomic_write_json(root / proof_path, receipt)
(clone / proof_path).write_bytes((root / proof_path).read_bytes())
print(json.dumps({"mirror_ok": True, "files_compared": len(digests), "protected_files": 1453,
    "B_seconds": wallet["stage_b_compute_seconds_charged"], "whole_wall_seconds": receipt["whole_wall_seconds"],
    "study_terminal": True, "goal_complete": False}), flush=True)
