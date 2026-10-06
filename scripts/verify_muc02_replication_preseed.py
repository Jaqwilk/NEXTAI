"""One clone conformance pass, with no scientific data or optimizer fitting."""
import json
from pathlib import Path
import subprocess
import sys
import nextai_autoresearch
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.muc02_replication_stage import status, protocol
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
assert verify_manifest(root)["ok"]
verify_preflight_certificate(root)
assert not status(root)["scoring_authorized"] and status(root)["registrations_used"] == 0
assert protocol(root)["data_tag"] == "MUC02-NEGATIVES-REPLICATION-20261006-V1"
prefix = root / "research/reviews/MUC02-REPLICATION-CLONE-PRESEED-V1"
assert not prefix.with_suffix(".json").exists()
command = [sys.executable, "-m", "pytest", "-q",
    "tests/test_muc02_replication.py", "tests/test_muc02_replication_stage.py",
    "tests/test_muc02_negatives_candidates.py", "tests/test_muc02_negatives_harness.py", "tests/test_muc02_baselines.py",
    "tests/test_protocol_v2.py::test_checked_in_research_lifecycle_is_consistent",
    "--basetemp", str(root / "research/tmp/MUC02-REPLICATION-PRESEED-FIXTURES-V1"),
    "--junitxml", str(prefix.with_suffix(".xml"))]
checks = []
for label, command, timeout in [("targeted_conformance", command, 180),
    ("doctor", [sys.executable, "-m", "nextai_autoresearch.cli", "doctor"], 400),
    ("lab", [sys.executable, "-m", "nextai_autoresearch.cli", "lab", "status"], 400)]:
    timed_out = False
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        result = subprocess.CompletedProcess(command, 124, exc.stdout or b"", exc.stderr or b"")
    out = prefix.with_name(prefix.name + "." + label + ".stdout.txt")
    err = prefix.with_name(prefix.name + "." + label + ".stderr.txt")
    out.write_bytes(result.stdout)
    err.write_bytes(result.stderr)
    checks.append({"name": label, "returncode": result.returncode, "timed_out": timed_out,
                   "stdout_sha256": sha256_file(out), "stderr_sha256": sha256_file(err)})
    atomic_write_json(prefix.with_suffix(".json"), {"created_at": utc_now(), "checks": checks,
        "package_origin": str(nextai_autoresearch.__file__), "clone_package_origin_verified": True,
        "fit_seconds": 0, "scoring_seed_draws": 0, "complete": len(checks) == 3 and all(c["returncode"] == 0 for c in checks)})
    if result.returncode:
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(result.returncode)
print(json.dumps({"checks": checks, "source_integrity": True, "fit": 0, "scoring_seed_draws": 0}))
