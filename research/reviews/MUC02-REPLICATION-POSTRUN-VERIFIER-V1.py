"""One read-only final verification; never trains or reruns an experiment."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import nextai_autoresearch
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.muc02_replication_stage import status
from nextai_autoresearch.research_program import status as program_status
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[2]
assert root.name == "NEXTAI-VALIDATION-20261002"
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
prefix = root / "research/reviews/MUC02-REPLICATION-CLONE-POSTRUN-V1"
assert not prefix.with_suffix(".json").exists()
assert verify_manifest(root)["ok"]
verify_preflight_certificate(root)
assert status(root) is None
completion = load_json(root / "research/laboratory/MUC02-REPLICATION-COMPLETION-V1.receipt.json")
identity = completion["experiment_id"]
assert sha256_file(root / f"research/results/{identity}.json") == completion["result_sha256"]
spec = importlib.util.spec_from_file_location("frozen_muc02_analysis", root / "scripts/analyze_muc02_hard_negatives.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.analyze(root, identity) == load_json(root / completion["analysis_path"])
parent = load_json(root / "research/laboratory/archive/MUC02-REPLICATION-parent-V1/parent-bindings.json")
wallet = program_status(root)
for key in ("fit_seconds_charged", "registration_attempts_used", "protected_future_registration_attempts", "protected_future_compute_seconds", "stage_b_compute_seconds_charged", "stage_b_registration_attempts_used"):
    assert wallet[key] == parent["B_wallet"][key], key
assert not wallet["scoring_authorized"] and not wallet["program_terminal"]
for name, binding in parent["ledger_prefixes"].items():
    assert hashlib.sha256((root / "research" / name).read_bytes()[:binding["bytes"]]).hexdigest() == binding["sha256"], name
controller = completion["controller"]
archive = root / controller["source_archive_path"]
assert sha256_file(archive) == controller["source_archive_sha256"]
with zipfile.ZipFile(archive) as z:
    old_manifest = json.loads(z.read("research/eval_manifest.json"))
    for name in z.namelist():
        if name in old_manifest["files"]:
            assert hashlib.sha256(z.read(name)).hexdigest() == old_manifest["files"][name], name
    old_result = load_json(root / f"research/results/{identity}.json")
    assert old_result["evaluator_sha256"] == old_manifest["evaluator_sha256"]

checks = []
commands = [
    ("lifecycle", [sys.executable, "-m", "pytest", "-q", "tests/test_protocol_v2.py::test_checked_in_research_lifecycle_is_consistent", "--basetemp", str(root / "research/tmp/MUC02-REPLICATION-POSTRUN-FIXTURES-V1"), "--junitxml", str(prefix.with_suffix(".xml"))], 180),
    ("doctor", [sys.executable, "-m", "nextai_autoresearch.cli", "doctor"], 400),
    ("lab", [sys.executable, "-m", "nextai_autoresearch.cli", "lab", "status"], 400),
]
for label, command, timeout in commands:
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
    checks.append({"name": label, "returncode": result.returncode, "timed_out": timed_out, "stdout_sha256": sha256_file(out), "stderr_sha256": sha256_file(err)})
    atomic_write_json(prefix.with_suffix(".json"), {"created_at": utc_now(), "checks": checks, "complete": len(checks) == 3 and all(c["returncode"] == 0 for c in checks), "analysis_reproduced": True, "B_wallet_preserved": True, "ledger_prefixes_preserved": True, "evaluated_archive_hashes_verified": True, "package_origin": str(nextai_autoresearch.__file__), "new_scoring_seed_draws": 0, "new_fit_seconds": 0})
    if result.returncode:
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(result.returncode)
lab = json.loads(prefix.with_name(prefix.name + ".lab.stdout.txt").read_text(encoding="utf-8"))
assert not lab["errors"] and not lab["warnings"] and not lab["scoring_authorized"]
print(json.dumps({"postrun_checks": checks, "analysis_reproduced": True, "B_wallet_preserved": True, "new_fit_seconds": 0}))
