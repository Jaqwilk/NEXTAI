"""Fail-closed Git-backed verification for the terminal PC-01 evidence bundle."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
import subprocess

from .ledger import read_jsonl
from .pc01 import require
from .utils import load_json, sha256_bytes, sha256_file, sha256_json


PATH = "research/laboratory/PC-01-HISTORICAL-CLOSURE-V1.json"
SHA256 = "7397274f6cdaeae78724c3ee3aaff5cf8186761e79cda7dbd88082a635735ab9"
AUTHORITY_PATH = "research/laboratory/PC-01-TELEMETRY-LIFECYCLE-MIGRATION-20260905-V1.json"
AUTHORITY_SHA256 = "fd1e3f265724334588abd330825d4ca9bc5168418b93c9e27cea56bbf7f4b7b3"
CORRECTION_PATH = "research/laboratory/PC-01-TELEMETRY-LIFECYCLE-MIGRATION-V1-ADDENDUM.json"
CORRECTION_SHA256 = "20ec81af2bc4d11adaff29498af584f130fd91b52b54dbad3c9a0d63cf18422d"


def _git(root: Path, *args: str) -> bytes:
    process = subprocess.run(
        ["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    require(process.returncode == 0, f"historical Git evidence unavailable: {' '.join(args)}")
    return process.stdout


def git_bytes(root: Path, commit: str, relative: str) -> bytes:
    require(relative and "\\" not in relative and not relative.startswith(('/', '.git/')),
            "invalid historical evidence path")
    require(".." not in Path(relative).parts and ":" not in relative,
            "invalid historical evidence path")
    return _git(root, "show", f"{commit}:{relative}")


@lru_cache(maxsize=4)
def _verify_git_bundle(root_text: str) -> None:
    """Git objects are immutable; avoid dozens of repeated subprocess reads."""
    root = Path(root_text)
    value = load_json(root / PATH)
    commit = value["git_commit"]
    _git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    _git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    historical = value["historical_files"]
    for relative, digest in historical.items():
        require(sha256_bytes(git_bytes(root, commit, relative)) == digest,
                f"historical Git evidence changed: {relative}")
    certificate = json.loads(git_bytes(
        root, commit, "research/laboratory/PC-01-EXECUTION-CERTIFICATE-V7.json"
    ))
    require(certificate.get("all_required_checks_passed") is True
            and certificate.get("evaluator_sha256") == value.get("evaluator_sha256"),
            "historical PC-01 certificate is not valid")
    require(certificate.get("test_report_sha256") == historical[
        "research/laboratory/PC-01-FINAL-ACTIVATION-CONFORMANCE-V7-C.xml"
    ], "historical PC-01 conformance report mismatch")
    for relative, digest in certificate.get("files", {}).items():
        require(sha256_bytes(git_bytes(root, commit, relative)) == digest,
                f"certificate Git evidence changed: {relative}")
    series = json.loads(git_bytes(
        root, commit, "research/laboratory/PC-01-FINAL-SERIES-V1.json"
    ))
    require(sha256_json(series) == value.get("series_canonical_sha256"),
            "historical final-series canonical hash changed")
    require(series.get("benchmark") == value.get("benchmark_version")
            and series.get("evaluator_sha256") == value.get("evaluator_sha256"),
            "historical final-series identity changed")
    for index in range(1, 6):
        relative = f"research/results/EXP-20260905-{index:04d}.json"
        result = json.loads(git_bytes(root, commit, relative))
        expected_status = "inconclusive" if index == 1 else "complete"
        require(result.get("experiment_id") == f"EXP-20260905-{index:04d}"
                and result.get("status") == expected_status
                and result.get("integrity_after", {}).get("ok") is True
                and (index != 1 or result.get("error") == "worker_crash"),
                f"historical PC-01 result outcome changed: {relative}")


def closure(root: Path) -> dict | None:
    """Return a verified closure, or None before the migration artifact exists."""
    path = root / PATH
    if not path.exists():
        return None
    require(path.is_file() and sha256_file(path) == SHA256,
            "PC-01 historical closure missing or changed")
    require(sha256_file(root / AUTHORITY_PATH) == AUTHORITY_SHA256,
            "PC-01 lifecycle authority missing or changed")
    require(sha256_file(root / CORRECTION_PATH) == CORRECTION_SHA256,
            "PC-01 lifecycle correction missing or changed")
    events = [event for event in read_jsonl(root / "research/events.jsonl")
              if event.get("event") == "pc01_telemetry_lifecycle_migration_authorized"]
    require(len(events) == 1
            and events[0].get("authorization_path") == AUTHORITY_PATH
            and events[0].get("authorization_sha256") == AUTHORITY_SHA256,
            "PC-01 lifecycle authority event missing, changed or repeated")
    corrections = [event for event in read_jsonl(root / "research/events.jsonl")
                   if event.get("event") == "pc01_telemetry_lifecycle_preregistration_corrected"]
    require(len(corrections) == 1
            and corrections[0].get("addendum_path") == CORRECTION_PATH
            and corrections[0].get("addendum_sha256") == CORRECTION_SHA256,
            "PC-01 lifecycle correction event missing, changed or repeated")

    value = load_json(path)
    require(value.get("kind") == "git_backed_terminal_pc01_evidence_closure",
            "wrong PC-01 closure kind")
    require(value.get("authority_path") == AUTHORITY_PATH
            and value.get("authority_sha256") == AUTHORITY_SHA256,
            "PC-01 closure authority mismatch")
    require(value.get("correction_path") == CORRECTION_PATH
            and value.get("correction_sha256") == CORRECTION_SHA256,
            "PC-01 closure correction mismatch")
    commit = value.get("git_commit")
    require(isinstance(commit, str) and len(commit) == 40,
            "invalid PC-01 closure Git commit")

    historical = value.get("historical_files")
    require(isinstance(historical, dict) and len(historical) >= 20,
            "PC-01 closure omits historical evidence")
    for digest in historical.values():
        require(isinstance(digest, str) and len(digest) == 64,
                "invalid PC-01 historical digest")

    live = value.get("current_immutable_evidence")
    require(isinstance(live, list) and len(live) == len(set(live)) and live,
            "invalid current immutable evidence list")
    for relative in live:
        require(relative in historical and sha256_file(root / relative) == historical[relative],
                f"current immutable PC-01 evidence changed: {relative}")

    _verify_git_bundle(str(root.resolve()))
    decision = value.get("terminal_decision", {})
    require(decision.get("decision") == "positive_control_pass"
            and decision.get("architecture_promoted") is False
            and decision.get("economic_advantage_established") is False
            and decision.get("transfer_established") is False,
            "historical PC-01 claim boundary changed")
    return value


def migration_completed(root: Path) -> dict | None:
    """Verify the single append-only completion receipt when it exists."""
    verified = closure(root)
    if verified is None:
        return None
    events = [event for event in read_jsonl(root / "research/events.jsonl")
              if event.get("event") == "pc01_telemetry_lifecycle_migration_completed"]
    require(len(events) <= 1, "PC-01 lifecycle migration completion repeated")
    if not events:
        return None
    event = events[0]
    relative = "research/laboratory/PC-01-TELEMETRY-LIFECYCLE-MIGRATION-V1.receipt.json"
    require(event.get("receipt_path") == relative
            and sha256_file(root / relative) == event.get("receipt_sha256")
            and event.get("training_performed") is False
            and event.get("scoring_performed") is False,
            "PC-01 lifecycle migration completion changed or exceeded scope")
    receipt = load_json(root / relative)
    regression = receipt.get("full_regression_v2", {})
    require(receipt.get("status") == "complete"
            and regression.get("passed") is True
            and regression.get("failures") == 0
            and regression.get("errors") == 0
            and regression.get("skipped") == 0,
            "PC-01 lifecycle migration receipt is not complete")
    return receipt
