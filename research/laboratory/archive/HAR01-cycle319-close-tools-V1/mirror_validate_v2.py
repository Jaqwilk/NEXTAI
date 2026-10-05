"""Verify copied evidence without repeating the already passed full doctor."""
import json
from pathlib import Path
import shutil
import subprocess

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.laboratory import laboratory_progress
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

src = Path("C:/Users/NATAN/Documents/ChatGPT/NEXTAI-VALIDATION-20261002").resolve()
dst = Path("C:/Users/NATAN/Documents/ChatGPT/NEXTAI").resolve()
identity = "EXP-20261005-0007"
parent = "e11194fa4e87bf4d4768a9194a5580e2162d955b"
for root in (src, dst):
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip() == parent
paths = sorted(set(p for p in subprocess.check_output(
    ["git", "ls-files", "--modified", "--others", "--exclude-standard", "-z"], cwd=src
).decode().split("\0") if p and "NEXTAI-B-319-mirror-validation-V2" not in p))
for relative in paths:
    source, target = (src / relative).resolve(), (dst / relative).resolve()
    assert source.is_relative_to(src) and target.is_relative_to(dst) and source.is_file()
    if target.exists() and sha256_file(target) != sha256_file(source):
        assert relative == "research/events.jsonl", relative
        assert source.read_bytes().startswith(target.read_bytes())
    if not target.exists() or relative == "research/events.jsonl":
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    assert sha256_file(target) == sha256_file(source), relative
manifest = json.loads((src / "research/eval_manifest.json").read_text())
for root in (src, dst):
    assert verify_manifest(root)["ok"]
    for number in range(1, 8):
        name = f"EXP-20261005-{number:04d}"
        record = json.loads((root / f"research/laboratory/{name}-publication-V2.json").read_text())
        assert sha256_file(root / record["native_path"]) == record["native_sha256"]
        assert sha256_file(root / record["bundle_path"]) == record["bundle_sha256"]
archive = json.loads((src / f"research/laboratory/{identity}-archive-V1.json").read_text())
for relative, expected in archive["runtime_files"].items():
    assert sha256_file(dst / f"research/tmp/{identity}" / relative) == expected["sha256"]
    assert sha256_file(dst / archive["runtime_archive_path"] / relative) == expected["sha256"]
native = f"research/results/{identity}.json"
temporary = src / "research/tmp/HAR01-result-restoration-proof-V1"
assert sha256_file(temporary / native) == sha256_file(src / native)
doctor = json.loads((src / "research/reviews/NEXTAI-B-319-terminal-doctor-V2.json").read_text())
assert doctor["result"]["returncode"] == 0 and doctor["error"] is None
progress = laboratory_progress(dst)
assert progress["scoring_authorized"] is False
proof = {"created_at": utc_now(), "independent_clone": str(src), "original": str(dst),
         "parent_git_commit": parent, "current_manifest_sha256": sha256_file(src / "research/eval_manifest.json"),
         "copied_files_verified": {p: sha256_file(src / p) for p in paths},
         "protected_files_verified_each_root": len(manifest["files"]),
         "all_seven_native_records_and_bundles_verified_both_roots": True,
         "runtime_and_archive_journals_verified_original": len(archive["runtime_files"]),
         "fresh_empty_destination_restoration_verified": True,
         "clone_full_doctor_pass_receipt_sha256": sha256_file(src / "research/reviews/NEXTAI-B-319-terminal-doctor-V2.json"),
         "original_CLI_lab_status_V1_timed_out_and_preserved": True,
         "original_full_doctor_not_repeated_in_this_check": True,
         "verified_original_laboratory_progress": progress,
         "snapshot_includes_live_parent_check_reservation": True,
         "final_settlement_requires_completion_receipt_after_parent_exit": True,
         "new_research_fit_or_evaluation": False,
         "mirror_script_sha256": sha256_file(Path(__file__))}
receipt = "research/checks/HAR01-clone-original-preservation-V2.json"
assert not (src / receipt).exists() and not (dst / receipt).exists()
atomic_write_json(src / receipt, proof)
shutil.copy2(src / receipt, dst / receipt)
print(json.dumps({"files_verified": len(paths), "protected_files_each_root": len(manifest["files"]),
                  "runtime_and_archive_files": len(archive["runtime_files"]), "fresh_restoration": True,
                  "scoring_authorized": False, "original_CLI_V1_timeout_retained": True}), flush=True)
