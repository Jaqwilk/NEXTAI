"""Exact cycle319 evidence copy; do not overwrite unrelated or immutable changes."""
import json
import os
from pathlib import Path
import shutil
import subprocess

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

src = Path("C:/Users/NATAN/Documents/ChatGPT/NEXTAI-VALIDATION-20261002").resolve()
dst = Path("C:/Users/NATAN/Documents/ChatGPT/NEXTAI").resolve()
identity = "EXP-20261005-0007"
parent = "e11194fa4e87bf4d4768a9194a5580e2162d955b"
for root in (src, dst):
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip() == parent
assert not subprocess.check_output(["git", "status", "--porcelain", "-z"], cwd=dst)
assert shutil.disk_usage(dst).free - 1024**3 >= 10 * 1024**3
mutable = {".gitignore", "AGENTS.md", "config/research.toml", "docs/CURRENT_STATUS.md", "program.md",
           "research/LAB_PLAN.md", "research/REPORT.md", "research/REPORT.provenance.json",
           "research/eval_manifest.json", "research/events.jsonl", "research/experiments.tsv",
           "research/laboratory/preflight_certificate.json", "research/plan_registry.jsonl", "research/state.json"}
append_only = {"research/events.jsonl", "research/experiments.tsv", "research/plan_registry.jsonl"}
paths = sorted(set(p for p in subprocess.check_output(
    ["git", "ls-files", "--modified", "--others", "--exclude-standard", "-z"], cwd=src
).decode().split("\0") if p and "NEXTAI-B-319-mirror-validation-V1" not in p))
for relative in paths:
    source, target = (src / relative).resolve(), (dst / relative).resolve()
    assert source.is_relative_to(src) and target.is_relative_to(dst) and source.is_file()
    if target.exists():
        if relative in append_only:
            assert source.read_bytes().startswith(target.read_bytes()), relative
        elif relative not in mutable:
            assert sha256_file(source) == sha256_file(target), relative
copied = {}
for relative in paths:
    source, target = src / relative, dst / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    expected = sha256_file(source)
    assert sha256_file(target) == expected, relative
    copied[relative] = expected
native = f"research/results/{identity}.json"
assert not (dst / native).exists()
shutil.copy2(src / native, dst / native)
assert sha256_file(dst / native) == sha256_file(src / native)
runtime = f"research/tmp/{identity}"
assert not (dst / runtime).exists()
shutil.copytree(src / runtime, dst / runtime)
archive = json.loads((src / f"research/laboratory/{identity}-archive-V1.json").read_text())
for relative, expected in archive["runtime_files"].items():
    assert sha256_file(dst / runtime / relative) == expected["sha256"], relative
for root in (src, dst):
    assert verify_manifest(root)["ok"]
    for number in range(1, 8):
        name = f"EXP-20261005-{number:04d}"
        record = json.loads((root / f"research/laboratory/{name}-publication-V2.json").read_text())
        assert sha256_file(root / record["native_path"]) == record["native_sha256"]
        assert sha256_file(root / record["bundle_path"]) == record["bundle_sha256"]
    assert sha256_file(root / "research/data/har01_native_v1/screen.npz") == "d8c0084c16f490e79654910b8dd28834dedbfd97204003bb689507a96ac37dfd"

temporary = src / "research/tmp/HAR01-result-restoration-proof-V1"
assert not temporary.exists()
for relative in (f"research/laboratory/{identity}-publication-V2.json", native + ".gz"):
    target = temporary / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / relative, target)
subprocess.run(["uv", "run", "--no-sync", "python", "scripts/restore_har01_result.py",
                identity, str(temporary)], cwd=src, check=True)
assert sha256_file(temporary / native) == sha256_file(src / native)

environment = os.environ.copy()
environment.update(PYTHONPATH=str(dst / "src"), NEXTAI_PROJECT_ROOT=str(dst),
                   PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
subprocess.run(["uv", "run", "--no-sync", "nextai", "lab", "status"], cwd=dst, env=environment, check=True)
proof = {"created_at": utc_now(), "independent_clone": str(src), "original": str(dst),
         "parent_git_commit": parent, "copied_files": copied,
         "append_only_prefixes_preserved": sorted(append_only),
         "current_manifest_sha256": sha256_file(src / "research/eval_manifest.json"),
         "protected_files_verified_both_roots": len(json.loads((src / "research/eval_manifest.json").read_text())["files"]),
         "native_result_sha256": sha256_file(src / native),
         "all_seven_native_records_and_bundles_verified_both_roots": True,
         "runtime_journals_verified_original": len(archive["runtime_files"]),
         "fresh_empty_destination_restoration_verified": True,
         "new_research_fit_or_evaluation": False,
         "snapshot_includes_live_parent_check_reservation": True,
         "final_settlement_requires_completion_receipt_after_parent_exit": True,
         "mirror_script_sha256": sha256_file(Path(__file__))}
receipt = "research/checks/HAR01-clone-original-preservation-V1.json"
assert not (src / receipt).exists() and not (dst / receipt).exists()
atomic_write_json(src / receipt, proof)
shutil.copy2(src / receipt, dst / receipt)
print(json.dumps({"mirrored_files": len(copied), "protected_files_each_root": proof["protected_files_verified_both_roots"],
                  "runtime_files": len(archive["runtime_files"]), "fresh_restoration": True}), flush=True)
