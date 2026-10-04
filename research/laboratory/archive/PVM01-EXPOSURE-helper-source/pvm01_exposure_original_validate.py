"""Validate the clean original fast-forward with original source, charge in clone."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
original = b.parent / "NEXTAI"
snapshot = json.loads((b / "research/reviews/PVM01-EXPOSURE-startup-history-V1.json").read_text())
assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=original).strip()
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=original, text=True).strip() == commit
changed = set(subprocess.check_output(["git", "diff", "--name-only", snapshot["original_head"], commit], text=True).splitlines())
assert not [name for name, digest in snapshot["files"].items()
            if name not in changed and sha256_file(original / name) != digest]
for name, prefix in snapshot["append_only_prefixes"].items():
    raw = (original / name).read_bytes()
    assert hashlib.sha256(raw[:prefix["bytes"]]).hexdigest() == prefix["sha256"], name
    if name == "research/hypothesis_events.jsonl":
        assert len(raw) == prefix["bytes"]
assert sha256_file(original / "research/BELIEFS.json") == snapshot["files"]["research/BELIEFS.json"]
assert sha256_file(original / "research/results/EXP-20261004-0008.json") == json.loads((b / "research/reviews/PVM01-EXPOSURE-scientific-archive-V1.json").read_text())["result_sha256"]
env = os.environ.copy()
env.update(PYTHONPATH=str(original / "src"), NEXTAI_PROJECT_ROOT=str(original), PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
checks = []
for args in (("doctor",), ("lab", "status")):
    run = subprocess.run(["uv", "run", "--no-sync", "nextai", *args], cwd=original, env=env, capture_output=True)
    print(run.stdout.decode("utf8", errors="replace"), flush=True)
    print(run.stderr.decode("utf8", errors="replace"), flush=True)
    checks.append({"command": list(args), "returncode": run.returncode})
    assert run.returncode == 0
assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=original).strip()
atomic_write_json(b / "research/reviews/PVM01-EXPOSURE-original-source-validation-V1.json", {
    "created_at": utc_now(), "source_commit": commit, "commands": checks,
    "original_and_clone_have_same_head": True, "original_source_and_state_used": True,
    "original_unmodified_raw_scientific_files_preserved": True, "append_only_prefixes_preserved": True,
    "original_BELIEFS_raw_unchanged": True, "original_result_raw_sha256_valid": True,
    "original_git_clean": True, "charge_ledger_location": str(b), "no_model_fit_or_scoring": True})
print("Original clean fast-forward, original source doctor/lab and all historical raw bytes: PASS")
