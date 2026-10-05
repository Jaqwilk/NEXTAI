"""Metadata-only clone conformance; no target content, fit or network access."""
import importlib.util
import json
from email.message import Message
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


root = Path(__file__).resolve().parents[1]
assert Path(importlib.import_module("nextai_autoresearch").__file__).resolve().is_relative_to(root / "src")
parent = root / "research/laboratory/archive/FAMILY2-cycle320-parent-V1"
archive = json.loads((parent / "archive.json").read_text())
for relative, digest in archive["sha256"].items():
    physical = ".gitattributes.raw" if relative == ".gitattributes" else relative
    assert sha256_file(parent / physical) == digest, relative
for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"):
    assert (root / relative).read_bytes().endswith((parent / relative).read_bytes()), relative

permitted = {".gitattributes", "config/research.toml", "AGENTS.md", "program.md",
             "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"}
old_manifest = json.loads((parent / "research/eval_manifest.json").read_text())
for relative, digest in old_manifest["files"].items():
    if relative not in permitted:
        assert sha256_file(root / relative) == digest, relative
assert verify_manifest(root)["ok"]
verify_preflight_certificate(root)
for relative in ("research/events.jsonl", "research/sources.jsonl", "research/experiments.tsv"):
    original = subprocess.check_output(["git", "show", f"{archive['parent_commit']}:{relative}"], cwd=root)
    current = (root / relative).read_bytes()
    assert current.startswith(original), relative
    if relative.endswith("experiments.tsv"):
        assert current == original

plan_path = root / "research/plans/NEXTAI-FAMILY2-INTAKE-PREPARATION-V1.json"
task_path = root / "research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json"
plan = json.loads(plan_path.read_text())
task = json.loads(task_path.read_text())
assert sha256_file(plan_path) == "dc8d6b48cad1872fb9047b99d05f573c32a348003a9139855599c6119579cfa5"
assert sha256_file(task_path) == "218d7a5d7fd0efb748341f76a4d83fb2e62ab793136382888ef241d877872360"
assert task["preparation_parent_sha256"] == sha256_file(plan_path)
assert not task["execution_authority"] and not task["source"]["arrays_seen"]
assert task["program_contract_sha256"] == sha256_file(root / task["program_contract_path"])
units = task["independent_units"]
pools = [units[f"{stage}_{split}"] for stage in ("screen", "replication", "fresh_final")
         for split in ("train", "dev")]
assert all(len(pool) == 5 and len(set(pool)) == 5 for pool in pools)
assert len(set(sum(pools, []))) == 30
assert sorted(sum(pools, []) + units["unused_writers"]) == list(range(1, 46))
assert sum(task["training"][field] for field in
           ("distinct_fit_instances_per_train_writer", "validation_instances", "calibration_instances")) == 183
assert task["training"]["calibration_instances"] >= max(task["comparison"]["scales"]) + 31
for field in ("reference_mean_accuracy_min", "reference_each_seed_accuracy_min",
              "unknown_rejection_min", "known_false_abstention_max",
              "full_workload_latency_ratio_simultaneous_upper_max", "p95_ratio_upper_max"):
    assert task["metrics"]["economic_gates"][field] == plan["unchanged_gates"][field]
assert task["metrics"]["economic_gates"]["candidate_quality_difference_simultaneous_lower_min"] == plan["unchanged_gates"]["quality_difference_simultaneous_lower_min"]

recovery = json.loads((root / "research/laboratory/FAMILY2-CYCLE320-METADATA-RECOVERY-V1.json").read_text())
assert recovery["metadata_only"] and recovery["numeric_samples_read"] == 0
assert recovery["assamese_archive_bytes"] is None and not recovery["nist_complete_index_read"]
metadata_root = root / recovery["raw_metadata_path"]
for name, digest in recovery["metadata_hashes"].items():
    assert sha256_file(metadata_root / name) == digest
assert sum((metadata_root / name).stat().st_size for name in recovery["metadata_hashes"]) == recovery["bytes_saved"]
assert recovery["bytes_saved"] <= plan["resources"]["metadata_download_bytes_cap"]

# Exercise the fixed missing-HEAD-length serializer on synthetic public metadata.
# Requests are replaced entirely; this neither contacts a publisher nor opens data.
spec = importlib.util.spec_from_file_location("metadata_intake", root / "scripts/intake_family2_metadata.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
serializer_cases = []
for length in (None, "1234"):
    with tempfile.TemporaryDirectory(prefix="NEXTAI-metadata-fixture-") as temporary:
        module.ROOT = Path(temporary)
        (module.ROOT / "research/laboratory").mkdir(parents=True)
        headers = Message()
        if length is not None:
            headers["Content-Length"] = length
        nist_headers = Message()
        nist_headers["Content-Length"] = "65536"
        eocd = struct.pack("<4s4H2IH", b"PK\x05\x06", 0, 0, 0, 0, 24, 0, 0)
        def synthetic_request(url, *, method="GET", byte_range=None, cap=32768):
            if method == "HEAD":
                return b"", headers if url.endswith(".rar") else nist_headers
            if byte_range:
                return (eocd if byte_range[0] else b"synthetic directory"), Message()
            return b"Synthetic metadata fixture; no numeric target samples.", Message()
        module.request = synthetic_request
        module.main()
        generated = json.loads((module.ROOT / "research/laboratory/FAMILY2-CYCLE320-METADATA-V1.json").read_text())
        assert generated["assamese_archive_bytes"] == (int(length) if length else None)
        assert generated["numeric_samples_read"] == 0
        serializer_cases.append({"supplied_length": length, "recorded_length": generated["assamese_archive_bytes"]})

wallet = status(root)
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000
assert wallet["protected_future_registration_attempts"] == 7
assert not wallet["scoring_authorized"] and not wallet["paid_run_pending"]
code = subprocess.call([sys.executable, "-m", "pytest", "-q",
                       "tests/test_transfer_program_authority.py", "tests/test_source_metadata.py",
                       "tests/test_integrity_and_schemas.py", "-k", "not all_shipped_candidates_pass_source_audit",
                       "--junitxml=research/reviews/NEXTAI-B-320-clone-conformance.xml"], cwd=root)
assert code == 0, f"pytest returned {code}"
atomic_write_json(root / "research/reviews/FAMILY2-CLONE-CONFORMANCE-V1.json", {
    "created_at": utc_now(), "clone_root": str(root), "python_source_root_confirmed": True,
    "parent_commit": archive["parent_commit"], "old_protected_files": len(old_manifest["files"]),
    "old_scientific_bytes_unchanged": True, "historical_ledger_prefixes_preserved": True,
    "previous_document_bytes_retained_verbatim": True, "current_integrity_preflight_ok": True,
    "writer_pool_and_resource_contract_ok": True, "metadata_hashes_verified": recovery["metadata_hashes"],
    "nullable_HEAD_length_synthetic_cases": serializer_cases, "network_requests": 0,
    "target_numeric_samples_read": 0, "research_fit_seconds": 0, "new_EXP": 0,
    "pytest_exit_code": code, "junit_sha256": sha256_file(root / "research/reviews/NEXTAI-B-320-clone-conformance.xml"),
    "study_sha256": sha256_file(plan_path), "task_sha256": sha256_file(task_path),
    "protected_future_compute_seconds": 47000, "protected_future_registration_attempts": 7,
    "note": "Source audits are covered by the separate full CLI lab status; no duplicate candidate audit here."
})
print("Metadata-only clone conformance PASS", flush=True)
