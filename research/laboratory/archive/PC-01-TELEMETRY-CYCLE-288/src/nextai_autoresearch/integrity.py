from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import (
    atomic_write_json,
    load_json,
    project_root,
    sha256_file,
    sha256_json,
    utc_now,
)


FIXED_PROTECTED_FILES = (
    ".gitattributes",
    ".cursor/environment.json",
    ".cursor/install.sh",
    "scripts/bootstrap_environment.py",
    "config/bootstrap_sizes.json",
    "README.md",
    ".gitignore",
    "AGENTS.md",
    "program.md",
    "pyproject.toml",
    "uv.lock",
    "config/research.toml",
    "config/baseline_semantics.json",
    "docs/SCIENTIFIC_PROTOCOL.md",
    "docs/ROADMAP.md",
    "docs/METRICS.md",
    "docs/AUTOMATION_PROMPT.md",
    "docs/CODEX_SETUP.md",
    "docs/archive/SCIENTIFIC_PROTOCOL_V2_2026-09-04.md",
    "research/LAB_PLAN.md",
    "research/laboratory/restart.json",
    "research/laboratory/BELIEFS_POLICY.md",
    "schemas/laboratory_restart.schema.json",
    "schemas/pc01_replica.schema.json",
    "schemas/pc01_plan.schema.json",
    "schemas/pc01_result.schema.json",
    "research/laboratory/PC-01-EXTENSION-20260905-V1.json",
    "research/laboratory/PC-01-INTEGRATION-V1.json",
    "research/laboratory/PC-01-ACTIVATION-20260905-V1.json",
    "scripts/validate_pc01_activation.py",
    "scripts/validate_pc01_telemetry_repair.py",
    "research/plans/PC-01-TELEMETRY-REPAIR-V1.json",
    "research/plans/PC-01-TELEMETRY-REPAIR-V1-READ-ADDENDUM.json",
    "scripts/validate_pc01_integration.py",
    "research/plans/PC-01-CONTRACT-V1.json",
    "research/laboratory/PC-01-CONTRACT-V1.md",
    "research/laboratory/PC-01-CONTRACT-V1.receipt.json",
    "research/laboratory/PC-01-HARNESS-V1.json",
    "scripts/validate_pc01_harness.py",
    "research/data/pc01_tinyshakespeare_v1/acquisition.json",
    "research/data/pc01_tinyshakespeare_v1/LICENSE-NOTICE.md",
    "schemas/experiment_plan.schema.json",
    "schemas/experiment_result.schema.json",
    "schemas/hypothesis.schema.json",
    "schemas/research_state.schema.json",
    "schemas/source.schema.json",
    "research/data/dronepropa_v1/acquisition.json",
    "research/data/dronepropa_v1/files.jsonl",
    "research/checks/dronepropa_anonymous_split_v1.jsonl",
    "research/checks/dronepropa_anonymous_split_v2.jsonl",
    "research/corpora/heldout_parallel_masked_infilling_v12.json",
    "research/data/suitesparse_real_pde_v1/LICENSE-NOTICE.md",
    "research/data/suitesparse_real_pde_v1/acquisition_manifest.json",
    "research/data/suitesparse_real_pde_v1/audit.json",
    "research/data/suitesparse_real_pde_v1/recycling_sequence_manifest.json",
    "research/data/suitesparse_real_pde_v1/recycling_audit.json",
    "research/data/suitesparse_real_pde_v1/recycling_sequence_receipt.json",
)


def protected_files(root: Path | None = None) -> tuple[str, ...]:
    base = (root or project_root()).resolve()
    discovered: set[str] = set(FIXED_PROTECTED_FILES)
    for pattern in ("src/nextai_autoresearch/**/*.py", "tests/**/*.py"):
        for path in base.glob(pattern):
            if path.is_file() and "__pycache__" not in path.parts:
                discovered.add(path.relative_to(base).as_posix())
    return tuple(sorted(discovered))


# Compatibility snapshot for callers that need to copy the current harness fixture.
PROTECTED_FILES = protected_files()


def _candidate_bundle_files(root: Path) -> set[str]:
    paths = {"config/baseline_semantics.json"}
    registry_path = root / "config" / "baseline_semantics.json"
    if registry_path.is_file():
        registry = load_json(registry_path)
        for record in registry.get("baselines", {}).values():
            paths.update(str(path) for path in record.get("implementation_files", {}))
            paths.update(
                str(test.get("path", ""))
                for test in record.get("conformance_tests", ())
            )
    return paths


def _is_candidate_implementation(relative: str, bundle_files: set[str]) -> bool:
    if relative in bundle_files:
        return True
    prefix = "src/nextai_autoresearch/candidates/"
    if not relative.startswith(prefix):
        return False
    return Path(relative).name not in {"__init__.py", "base.py"}


def _role_digest(files: dict[str, str], root: Path, *, candidates: bool) -> str:
    bundle_files = _candidate_bundle_files(root)
    selected = {
        relative: digest
        for relative, digest in files.items()
        if _is_candidate_implementation(relative, bundle_files) is candidates
    }
    return sha256_json(selected)


def manifest_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "research" / "eval_manifest.json"


def _config_identity(root: Path) -> tuple[str, int]:
    from .config import load_config

    config = load_config(root)
    return config.benchmark_version, config.protocol_version


def _archive_manifest(root: Path, manifest: dict[str, Any]) -> Path:
    benchmark = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(manifest.get("benchmark_version", "unknown")))
    protocol = int(manifest.get("protocol_version", 1))
    digest = sha256_json(manifest)[:12]
    archive = (
        root
        / "research"
        / "manifests"
        / f"{benchmark}-protocol-v{protocol}-{digest}.json"
    )
    if archive.exists():
        if load_json(archive) != manifest:
            raise FileExistsError(f"Manifest archive collision: {archive}")
        return archive
    atomic_write_json(archive, manifest)
    return archive


def freeze_manifest(root: Path | None = None, *, overwrite: bool = False) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    path = manifest_path(base)
    if path.exists() and not overwrite:
        raise FileExistsError(
            "Evaluation manifest already exists. A new harness requires a new benchmark/protocol cohort."
        )
    previous_manifest = load_json(path) if path.exists() else None
    required = protected_files(base)
    missing = [relative for relative in required if not (base / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"Cannot freeze; protected files are missing: {missing}")
    benchmark_version, protocol_version = _config_identity(base)
    files = {relative: sha256_file(base / relative) for relative in required}
    evaluator_sha256 = _role_digest(files, base, candidates=False)
    if path.exists():
        from .ledger import latest_plan_statuses, research_dir

        statuses = latest_plan_statuses(base)
        for plan_path in sorted((research_dir(base) / "plans").glob("EXP-*.json")):
            experiment_id = plan_path.stem
            if experiment_id in statuses or (
                research_dir(base) / "results" / f"{experiment_id}.json"
            ).exists():
                continue
            plan = load_json(plan_path)
            commitment = plan.get("evaluator_sha256")
            if commitment is not None and commitment != evaluator_sha256:
                raise RuntimeError(
                    f"Evaluator changed after preregistration of {experiment_id}; invalidate the plan before freezing"
                )
    if previous_manifest is not None:
        _archive_manifest(base, previous_manifest)
    manifest = {
        "schema_version": 2,
        "protocol_version": protocol_version,
        "benchmark_version": benchmark_version,
        "created_at": utc_now(),
        "evaluator_sha256": evaluator_sha256,
        "candidate_bundle_sha256": _role_digest(files, base, candidates=True),
        "files": files,
    }
    atomic_write_json(path, manifest)
    return manifest


def load_json_or_config_version(root: Path) -> str:
    return _config_identity(root)[0]


def verify_manifest(root: Path | None = None) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    path = manifest_path(base)
    if not path.exists():
        return {"ok": False, "problems": ["research/eval_manifest.json is missing"]}
    manifest = load_json(path)
    problems: list[str] = []
    benchmark_version, protocol_version = _config_identity(base)
    if manifest.get("benchmark_version") != benchmark_version:
        problems.append("benchmark version differs from config")
    if int(manifest.get("protocol_version", 1)) != protocol_version:
        problems.append("protocol version differs from config")
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        return {"ok": False, "problems": ["manifest files field is not an object"]}
    for relative, expected in files.items():
        candidate = base / relative
        if not candidate.is_file():
            problems.append(f"missing protected file: {relative}")
        elif sha256_file(candidate) != expected:
            problems.append(f"changed protected file: {relative}")
    for required in protected_files(base):
        if required not in files:
            problems.append(f"protected file absent from manifest: {required}")
    expected_evaluator = _role_digest(files, base, candidates=False)
    expected_candidates = _role_digest(files, base, candidates=True)
    if manifest.get("evaluator_sha256") != expected_evaluator:
        problems.append("manifest evaluator digest is missing or inconsistent")
    if manifest.get("candidate_bundle_sha256") != expected_candidates:
        problems.append("manifest candidate-bundle digest is missing or inconsistent")
    return {
        "ok": not problems,
        "benchmark_version": manifest.get("benchmark_version"),
        "protocol_version": manifest.get("protocol_version", 1),
        "evaluator_sha256": manifest.get("evaluator_sha256"),
        "candidate_bundle_sha256": manifest.get("candidate_bundle_sha256"),
        "problems": problems,
        "checked_files": len(files),
    }
