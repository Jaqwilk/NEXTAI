from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .utils import atomic_write_json, load_json, project_root, sha256_file, sha256_json, utc_now


REGISTRY_PATH = Path("config/baseline_semantics.json")
PREFLIGHT_CERTIFICATE_PATH = Path("research/checks/preflight_certificate.json")


def _certificate_path(base: Path) -> Path:
    from .integrity import manifest_path

    protocol = int(load_json(manifest_path(base)).get("protocol_version", 1))
    if protocol >= 3:
        return base / "research/laboratory/preflight_certificate.json"
    return base / PREFLIGHT_CERTIFICATE_PATH


def required_baseline_names(plan: dict[str, Any]) -> list[str]:
    for protocol_name, key in (
        ("entity_addressing_protocol", "classical_baselines"),
        ("masked_refinement_protocol", "classical_baselines"),
        ("compression_protocol", "classical_baselines"),
        ("transfer_protocol", "specialist_baselines"),
        ("mechanism_recombination_protocol", "classical_baselines"),
        ("dronepropa_protocol", "classical_baselines"),
        ("continuous_transfer_protocol", "classical_baselines"),
        ("wt_prequential_protocol", "classical_baselines"),
        ("continuous_local_protocol", "classical_baselines"),
        ("active_sensor_protocol", "classical_baselines"),
        ("whole_io_search_protocol", "classical_baselines"),
        ("suitesparse_transfer_protocol", "classical_baselines"),
    ):
        protocol = plan.get(protocol_name)
        if isinstance(protocol, dict):
            return [str(value) for value in protocol.get(key, ())]
    return []


def verify_required_baselines(
    plan: dict[str, Any], root: Path | None = None, *, run_tests: bool = True
) -> dict[str, Any]:
    required = required_baseline_names(plan)
    if not required:
        return {"required": [], "tests": []}
    base = (root or project_root()).resolve()
    registry = load_json(base / REGISTRY_PATH)
    records = registry.get("baselines", {})
    plan_candidates = {str(value) for value in plan.get("candidates", ())}
    problems: list[str] = []
    nodes: list[str] = []
    for candidate in required:
        record = records.get(candidate)
        if not isinstance(record, dict):
            problems.append(f"missing semantic baseline record: {candidate}")
            continue
        if candidate not in plan_candidates:
            problems.append(f"required semantic baseline absent from plan: {candidate}")
        for relative, expected in record.get("implementation_files", {}).items():
            path = base / relative
            if not path.is_file() or sha256_file(path) != expected:
                problems.append(f"semantic implementation hash mismatch: {candidate}: {relative}")
        tests = record.get("conformance_tests", [])
        if not tests:
            problems.append(f"semantic baseline has no conformance test: {candidate}")
        for test in tests:
            relative = str(test.get("path", ""))
            node_id = str(test.get("node_id", ""))
            expected = str(test.get("sha256", ""))
            path = base / relative
            if not path.is_file() or sha256_file(path) != expected:
                problems.append(f"semantic test hash mismatch: {candidate}: {relative}")
            if not node_id.startswith(relative + "::"):
                problems.append(f"invalid semantic test node: {candidate}: {node_id}")
            else:
                nodes.append(node_id)
    if problems:
        raise RuntimeError("Baseline semantic gate failed: " + "; ".join(problems))
    unique_nodes = list(dict.fromkeys(nodes))
    if run_tests and unique_nodes:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *unique_nodes],
            cwd=base,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                "Baseline semantic conformance failed before scoring seed:\n"
                + completed.stdout[-4000:]
            )
    return {"required": required, "tests": unique_nodes}


def _preflight_payload(base: Path) -> dict[str, Any]:
    from .integrity import manifest_path
    from .schemas import SCHEMA_FILES

    manifest = load_json(manifest_path(base))
    files = {
        "runner": sha256_file(base / "src/nextai_autoresearch/runner.py"),
        "baseline_registry": sha256_file(base / REGISTRY_PATH),
        "manifest": sha256_file(manifest_path(base)),
        **{
            f"schema:{name}": sha256_file(base / "schemas" / filename)
            for name, filename in sorted(SCHEMA_FILES.items())
        },
    }
    return {
        "schema_version": 1,
        "benchmark_version": manifest.get("benchmark_version"),
        "evaluator_sha256": manifest.get("evaluator_sha256"),
        "files": files,
    }


def write_preflight_certificate(root: Path | None = None) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    payload = _preflight_payload(base)
    certificate = {**payload, "created_at": utc_now(), "certificate_sha256": sha256_json(payload)}
    path = _certificate_path(base)
    if path.is_file() and path != base / PREFLIGHT_CERTIFICATE_PATH:
        previous = load_json(path)
        archive = base / "research/laboratory/certificates" / f"{sha256_json(previous)}.json"
        if not archive.exists():
            atomic_write_json(archive, previous)
        elif load_json(archive) != previous:
            raise RuntimeError("Preflight certificate archive collision")
    atomic_write_json(path, certificate)
    return certificate


def verify_preflight_certificate(root: Path | None = None) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    path = _certificate_path(base)
    if not path.is_file():
        raise RuntimeError("Preflight certificate is missing")
    certificate = load_json(path)
    expected = _preflight_payload(base)
    if certificate.get("certificate_sha256") != sha256_json(expected):
        raise RuntimeError("Preflight certificate does not match evaluator/runner/schemas/registry/manifest")
    for key, value in expected.items():
        if certificate.get(key) != value:
            raise RuntimeError(f"Preflight certificate field mismatch: {key}")
    return certificate
