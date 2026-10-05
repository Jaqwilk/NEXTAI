"""Mirror only settled cycle322 records; verify exact bytes under prepaid administration."""
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
proof_path = "research/reviews/ASM01-GRAMMAR-FINAL-ADMIN-MIRROR-V1.json"
assert not (root / proof_path).exists()
assert (root / "research/laboratory/ASM01-CYCLE322-COMPLETION-V1.receipt.json").is_file()
write_report(root)
ledger = "research/events.jsonl"
assert (root / ledger).read_bytes().startswith((clone / ledger).read_bytes())
mutable = {ledger, "research/state.json", "research/REPORT.md", "research/REPORT.provenance.json",
           "research/eval_manifest.json", "research/laboratory/preflight_certificate.json"}
owned = set(mutable)
for item in subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=root).decode().split("\0"):
    if not item:
        continue
    relative = item[3:]
    assert relative in mutable or relative.startswith((
        "research/reviews/NEXTAI-B-322-", "research/reviews/ASM01-GRAMMAR-",
        "research/reviews/ASM01-EXPOSED-T1-GRAMMAR-", "research/laboratory/certificates/",
        "research/manifests/asm01_native_memory_v2-", "research/analyses/ASM01-CYCLE322-",
        "research/laboratory/ASM01-CYCLE322-", "scripts/seal_asm01_grammar_preparation.py",
        "scripts/verify_asm01_grammar_clone_maintenance.py", "scripts/close_asm01_grammar_conformance.py",
        "scripts/mirror_asm01_grammar_closure.py")), relative
    owned.add(relative)
for relative in sorted(owned):
    target = clone / relative
    source = (root / relative).read_bytes()
    if target.exists() and relative not in mutable:
        assert target.read_bytes() == source, relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source)
manifest = json.loads((root / "research/eval_manifest.json").read_text(encoding="utf-8"))
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
assert not wallet["scoring_authorized"] and not wallet["paid_run_pending"]
assert wallet["pending_fit_reservation_seconds"] == 0
for directory in (root, clone):
    assert sha256_file(directory / "research/results/EXP-20261005-0007.json") == "78380a19ffacf4a58af0bd8586425fbacee44b2e5a92c6e056f3699f769ed255"
    assert sha256_file(directory / "research/results/EXP-20261005-0006.fitted-state.zip") == "3576935b401f6c9324f2f4ed426de104b632a22ba74fb04da55757421f7632a8"
    assert not (directory / "STOP").exists() and not (directory / "PAUSE").exists()
    state = json.loads((directory / "research/state.json").read_text())
    assert state["cycle_number"] == 322 and state["completed_experiments"] == 122
    assert state["last_experiment_id"] == "EXP-20261005-0007" and state["active_experiment_id"] is None
receipt = {
    "created_at": utc_now(), "cycle": 322, "original_root": str(root), "clone_root": str(clone),
    "files_compared": len(digests), "file_sha256": digests, "protected_files": len(manifest["files"]),
    "both_current_manifests_ok": True, "manifest_verification": checks,
    "both_program_status_identical": True, "program": wallet,
    "whole_wall_seconds": time.monotonic() - started,
    "charged_by": "NEXTAI-B-322-administration-prepaid", "prepaid_seconds": 300,
    "new_EXPs": 0, "fit": 0, "scoring": False, "native_data_decoded": False,
    "extended_goal_completed": False, "disk_free_bytes": shutil.disk_usage(root).free,
}
atomic_write_json(root / proof_path, receipt)
(clone / proof_path).write_bytes((root / proof_path).read_bytes())
assert sha256_file(root / proof_path) == sha256_file(clone / proof_path)
print(json.dumps({"mirror_ok": True, "files_compared": len(digests),
                  "protected_files": len(manifest["files"]), "both_manifests_ok": True,
                  "both_program_status_identical": True, "whole_wall_seconds": receipt["whole_wall_seconds"],
                  "B_seconds": wallet["stage_b_compute_seconds_charged"],
                  "pending_reservations": 0, "study_terminal": True, "goal_complete": False}), flush=True)
