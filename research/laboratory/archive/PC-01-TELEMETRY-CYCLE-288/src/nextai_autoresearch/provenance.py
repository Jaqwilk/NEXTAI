"""Resolve immutable candidate audit hashes without importing historical code."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from .utils import load_json, project_root, sha256_bytes


def _git(root: Path, *args: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, check=False, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def _safe_relative(value: str) -> str:
    path = PurePosixPath(value)
    if (path.is_absolute() or ".." in path.parts or ":" in value
            or "\\" in value or not value.startswith("src/nextai_autoresearch/")):
        raise ValueError(f"Invalid candidate audit path: {value!r}")
    return path.as_posix()


def resolve_audited_source(
    relative: str, expected: str, root: Path, *, revision: str | None = None,
) -> dict[str, Any]:
    relative = _safe_relative(relative)
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Expected a SHA-256 from an immutable result audit")
    base = root.resolve()
    path = (base / relative).resolve()
    if not path.is_relative_to(base):
        raise ValueError("Candidate audit path escapes the repository")
    record: dict[str, Any] = {"path": relative, "expected_sha256": expected, "resolved": False}
    if revision is None and path.is_file():
        raw = path.read_bytes()
        record["current_sha256"] = sha256_bytes(raw)
        if record["current_sha256"] == expected:
            return {**record, "resolved": True, "source": "working_tree", "bytes": len(raw)}
    if revision is not None:
        if not re.fullmatch(r"[0-9a-fA-F]{7,40}", revision):
            raise ValueError("--revision must be an explicit Git commit hash")
        commits = _git(base, "rev-parse", "--verify", f"{revision}^{{commit}}")
    else:
        commits = _git(base, "log", "--all", "-n", "256", "--format=%H", "--", relative)
    for commit in (commits or b"").decode("ascii").splitlines():
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            continue
        raw = _git(base, "show", f"{commit}:{relative}")
        if raw is None:
            continue
        # Historical Windows byte commitments can be reconstructed explicitly;
        # this is never silent hash normalization or execution of the source.
        variants = [("git_blob", raw)]
        if b"\r\n" not in raw:
            variants.append(("git_blob_with_crlf_checkout", raw.replace(b"\n", b"\r\n")))
        for source, data in variants:
            if sha256_bytes(data) == expected:
                return {**record, "resolved": True, "source": source,
                        "revision": commit, "bytes": len(data)}
    return {**record, "reason": "No exact audited bytes found; supply --revision or restore Git history"}


def candidate_provenance(
    experiment: str, candidate: str, root: Path | None = None, *, revision: str | None = None,
) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    if not re.fullmatch(r"EXP-[0-9]{8}-[0-9]{4}", experiment):
        raise ValueError("Invalid experiment ID")
    result = load_json(base / "research" / "results" / f"{experiment}.json")
    if result.get("kind") == "pc01_diagnostic_result":
        plan = load_json(base / result["plan_path"])
        if plan.get("candidate") != candidate:
            raise ValueError("Candidate differs from diagnostic plan")
        sources = result.get("execution", {}).get("source_audit", {}).get("files", {})
        resolved = [resolve_audited_source(path, digest, base, revision=revision)
                    for path, digest in sorted(sources.items())]
        return {"experiment_id": experiment, "candidate": candidate,
                "ok": bool(resolved) and all(item["resolved"] for item in resolved),
                "dependencies": resolved, "historical_code_executed": False,
                "evidence_scope": "local_single_corpus_diagnostic"}
    matches = [item for item in result.get("candidates", []) if item.get("candidate") == candidate]
    if len(matches) != 1:
        raise ValueError("Candidate must occur exactly once in the immutable result")
    audit = matches[0].get("audit") or {}
    sources: dict[str, str] = {}
    for dependency in [audit, *audit.get("dependencies", [])]:
        relative, digest = dependency.get("path"), dependency.get("sha256")
        if not relative or not digest:
            raise ValueError("Historical audit lacks source hashes; provenance is incomplete")
        if relative in sources and sources[relative] != digest:
            raise ValueError(f"Conflicting source hashes for {relative}")
        sources[relative] = digest
    resolved = [resolve_audited_source(path, digest, base, revision=revision)
                for path, digest in sorted(sources.items())]
    return {"experiment_id": experiment, "candidate": candidate,
            "ok": bool(resolved) and all(item["resolved"] for item in resolved),
            "dependencies": resolved, "historical_code_executed": False}
