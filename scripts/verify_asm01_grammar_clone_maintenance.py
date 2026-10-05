"""Verify derived report, lifecycle and read-only lab in the independent clone."""
from pathlib import Path
import subprocess
import sys

import nextai_autoresearch
from nextai_autoresearch.report import write_report

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
write_report(root)
prefix = root / "research/reviews/NEXTAI-B-322-clone-lifecycle-V1"
command = [sys.executable, "-m", "pytest",
           str(root / "tests/test_protocol_v2.py") + "::test_checked_in_research_lifecycle_is_consistent",
           "-q", "--basetemp", str(root / "research/tmp/ASM01-grammar-lifecycle-fixture-V1"),
           "--junitxml", str(prefix.with_suffix(".xml"))]
result = subprocess.run(command, cwd=root, capture_output=True, timeout=100)
prefix.with_suffix(".stdout.txt").write_bytes(result.stdout)
prefix.with_suffix(".stderr.txt").write_bytes(result.stderr)
if result.returncode:
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    raise SystemExit(result.returncode)
result = subprocess.run(["uv", "run", "--no-sync", "nextai", "lab", "status"],
                        cwd=root, capture_output=True, timeout=270)
sys.stdout.buffer.write(result.stdout)
sys.stderr.buffer.write(result.stderr)
raise SystemExit(result.returncode)
