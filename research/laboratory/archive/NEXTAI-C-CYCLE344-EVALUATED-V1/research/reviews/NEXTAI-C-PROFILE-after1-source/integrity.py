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
    "research/plans/HAR01-INDEPENDENT-REPLICATION-V3.json",
    "research/plans/HAR01-REPLICATION-TASK-V3.json",
    "research/laboratory/HAR01-REPLICATION-CONTINUATION-AUTHORITY-V3.json",
    "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V3.json",
    "scripts/acquire_har01_replication_v3.py",
    "scripts/check_har01_replication_readiness_v3.py",
    "scripts/run_har01_replication_experiment_v3.py",
    "scripts/analyze_har01_replication_v3.py",
    "research/plans/HAR01-INDEPENDENT-REPLICATION-V2.json",
    "research/plans/HAR01-REPLICATION-TASK-V2.json",
    "research/plans/HAR01-REPLICATION-CONTINUATION-CLOCK-V2.json",
    "research/laboratory/HAR01-REPLICATION-CONTINUATION-AUTHORITY-V2.json",
    "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V2.json",
    "scripts/acquire_har01_replication_v2.py",
    "scripts/check_har01_replication_readiness_v2.py",
    "scripts/run_har01_replication_experiment_v2.py",
    "scripts/analyze_har01_replication_v2.py",
    "research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json",
    "research/plans/HAR01-REPLICATION-TASK-V1.json",
    "research/laboratory/HAR01-REPLICATION-PREPARATION-AUTHORITY-V1.json",
    "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V1.json",
    "scripts/acquire_har01_replication.py",
    "scripts/check_har01_replication_readiness.py",
    "scripts/run_har01_replication_experiment.py",
    "scripts/analyze_har01_replication.py",
    "research/plans/MUC02-NEGATIVES-REPLICATION-20261006-V1.json",
    "research/laboratory/MUC02-NEGATIVES-REPLICATION-20261006-V1.json",
    "scripts/preregister_muc02_negatives_replication.py",
    "scripts/prepare_muc02_replication.py",
    "scripts/seal_muc02_replication.py",
    "scripts/verify_muc02_replication_preseed.py",
    "scripts/run_muc02_replication_check.py",
    "scripts/ready_muc02_replication.py",
    "scripts/register_muc02_replication.py",
    "scripts/run_muc02_replication_experiment.py",
    "scripts/close_muc02_replication.py",
    "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json",
    "research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json",
    "research/data_manifests/ASM01-ACQUISITION-V3.json",
    "scripts/preregister_asm01_verified_screen.py",
    "scripts/run_asm01_verified_check.py",
    "scripts/acquire_asm01_verified_v3.py",
    "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json",
    "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json",
    "research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json",
    "research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json",
    "research/data_manifests/ASM01-ACQUISITION-V1.json",
    "research/data_manifests/ASM01-ACQUISITION-V2.json",
    "scripts/run_asm01_check.py",
    "scripts/acquire_asm01.py",
    "scripts/acquire_asm01_canonical_v2.py",
    "research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json",
    "research/plans/HAR01-NATIVE-TASK-CONTRACT-V1.json",
    "research/plans/HAR01-PRESEED-CONFORMANCE-V1.json",
    "research/plans/HAR01-PRESEED-CAP-CONFORMANCE-V1.json",
    "research/plans/HAR01-ANALYSIS-CONFORMANCE-V1.json",
    "research/plans/HAR01-REPORT-CONFORMANCE-V1.json",
    "research/plans/HAR01-OFFLINE-COST-CONFORMANCE-V1.json",
    "research/data_manifests/HAR01-ACQUISITION-V1.json",
    "research/data_manifests/HAR01-LICENSE-CONFORMANCE-V1.json",
    "scripts/run_har01_check.py",
    "scripts/acquire_har01.py",
    "scripts/analyze_har01.py",
    "scripts/run_har01_experiment.py",
    "scripts/check_har01_readiness.py",
    "scripts/restore_har01_result.py",
    "research/plans/NEXTAI-A-CLOSURE-B-PREPARATION-V1.json",
    "research/plans/NEXTAI-B-METADATA-CONFORMANCE-ADDENDUM-V1.json",
    "research/plans/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-V1.json",
    "research/plans/NEXTAI-TRANSFER-PREPARATION-V1.json",
    "research/laboratory/NEXTAI-TRANSFER-PROTOTYPE-20261005-V1.json",
    "research/laboratory/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1.json",
    "research/laboratory/NEXTAI-A-CONTINUATION-PROGRAM-COMPLETION-V1.receipt.json",
    "research/analyses/NEXTAI-A-CONTINUATION-PROGRAM-RESOLUTION-V1.md",
    "research/analyses/NEXTAI-B-TASK-FEASIBILITY-V1.md",
    "scripts/prepare_transfer_program.py",
    "scripts/run_transfer_preparation_check.py",
    "scripts/check_transfer_preparation.py",
    "scripts/analyze_pvm01_fresh_final.py",
    "scripts/run_pvm01_fresh_final_check.py",
    "scripts/analyze_pvm01_base_reference.py",
    "scripts/run_pvm01_base_reference_check.py",
    "scripts/analyze_pvm01_confirmation.py",
    "scripts/run_pvm01_confirmation_check.py",
    "scripts/analyze_pvm01_replication.py",
    "scripts/run_pvm01_replication_check.py",
    "scripts/analyze_pvm01_dense_noise.py",
    "scripts/run_pvm01_dense_noise_check.py",
    "research/plans/PVM01-TRANSPORT-CLASSICAL-ECONOMICS-V1.json",
    "research/plans/PVM01-TRANSPORT-COMPRESSION-ADVERSE-V1.json",
    "research/plans/PVM01-TRANSPORT-COMPRESSION-ADVERSE-V2.json",
    "scripts/analyze_pvm01_transport.py",
    "scripts/run_pvm01_transport_check.py",
    "research/plans/PVM01-CAPACITY-EXPOSURE-V1.json",
    "scripts/analyze_pvm01_capacity_exposure.py",
    "research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json",
    "scripts/analyze_pvm01_compact_features.py",
    "research/plans/PVM01-DELTA-MEMORY-SCREEN-V1.json",
    "scripts/analyze_pvm01_delta_memory.py",
    "research/plans/PVM01-ANALYSIS-SERIALIZATION-REPAIR-V1.json",
    "scripts/analyze_pvm01_reference_v2.py",
    "research/plans/PVM01-REFERENCE-V2.json",
    "research/plans/PVM01-PATH-BINDING-REPAIR-V1.json",
    "research/plans/PVM01-PATH-BINDING-REPAIR-DISPATCH-ADDENDUM-V1.json",
    "research/plans/PVM01-ARCHIVE-RAW-BYTES-ADDENDUM-V1.json",
    "research/plans/PVM01-REFERENCE-V1.json",
    "research/plans/PVM01-QUERY-BATCH-CONFORMANCE-V1.json",
    "scripts/analyze_pvm01_reference.py",
    "research/plans/NEXTAI-CONTINUATION-PROGRAM-V1.json",
    "research/plans/NEXTAI-CONTINUATION-PREPARATION-V1.json",
    "research/plans/PVM01-TASK-CONTRACT-V1.json",
    "research/plans/NEXTAI-RAW-TEST-EVIDENCE-PRESERVATION-V1.json",
    "research/laboratory/NEXTAI-CONTINUATION-20261004-V1.json",
    "scripts/analyze_muc_ranking_absence.py",
    "research/plans/MUC03-REFERENCE-CALIBRATION-V1.json",
    "research/plans/MUC03-DIAG-UNDERTRAINING-V2.json",
    "research/laboratory/MUC03-AUTONOMOUS-20261004-V1.json",
    "research/plans/MUC03-AUTONOMOUS-PROGRAM-V1.json",
    "research/plans/MUC03-DIAG-UNDERTRAINING-V1.json",
    "research/plans/MUC02-HARD-NEGATIVES-PRESEED-CONFORMANCE-V1.json",
    "research/plans/MUC02-HARD-NEGATIVES-DATA-CONFORMANCE-V1.json",
    "research/plans/MUC02-HARD-NEGATIVES-20261003-V1.json",
    "research/laboratory/MUC02-HARD-NEGATIVES-20261003-V1.json",
    "research/plans/AUDIT-REPAIR-20261002-V1.json",
    "research/laboratory/AUDIT-REPAIR-20261002-V1.json",
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
    "research/laboratory/PC-01-DEV2-20260905-V1.json",
    "research/laboratory/WT-01-DEV1-20260905-V1.json",
    "research/plans/WT-01-DEV1-ACTIVATION-V1.json",
    "research/laboratory/WT-01-LIFECYCLE-REPLACEMENT-20260906-V1.json",
    "research/plans/WT-01-LIFECYCLE-REPLACEMENT-V1.json",
    "research/laboratory/REVIEW-01-20260906-V1.json",
    "research/plans/REVIEW-01-V1.json",
    "research/plans/MUC-01-PROPOSED-CONTRACT-V1.json",
    "scripts/validate_pc01_dev2.py",
    "research/plans/PC-01-GPU-METADATA-V1.json",
    "scripts/validate_pc01_gpu_metadata.py",
    "research/plans/PC-01-FINAL-PREP-V1.json",
    "scripts/validate_pc01_final_preparation.py",
    "research/laboratory/PC-01-FINAL-ACTIVATION-20260905-V1.json",
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


_HAR_UNSTARTED_STUDY = "research/plans/HAR01-INDEPENDENT-REPLICATION-V3.json"
_HAR_UNSTARTED_STUDY_SHA = "9cf2153945a322e9c0e47c6d20287a9286e544a62ca0f711b64c797bcb493400"
_HAR_UNSTARTED_MANIFESTS = {
    "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V1.json": {
        "receipt_path": "research/laboratory/HAR01-REPLICATION-PREPARATION-COMPLETION-V1.receipt.json",
        "receipt_sha256": "fbca149a18f1010c9355f3ae95ee1eaa18dc72f8183d5d311708ebdc5d0a5b4f",
        "scope": "onlyabsentunstarted; presentfile alwaysprotected",
    },
    "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V2.json": {
        "receipt_path": "research/laboratory/HAR01-REPLICATION-COMPLETION-V2.receipt.json",
        "receipt_sha256": "132a331f4d6125d7ccbb3d3684b6ef3dfc52c6fa688c0a32bf25a91b88455567",
        "scope": "onlyabsentunstarted; presentfile alwaysprotected",
    },
}


def _exclude_proven_unstarted_har_intakes(base: Path, discovered: set[str]) -> None:
    study_path = base / _HAR_UNSTARTED_STUDY
    if not study_path.exists():
        return
    if not study_path.is_file() or sha256_file(study_path) != _HAR_UNSTARTED_STUDY_SHA:
        raise ValueError("Historical HAR intake exemption study binding changed")
    study = load_json(study_path)
    if study.get("historical_unstarted_intake_manifest_exemptions") != _HAR_UNSTARTED_MANIFESTS:
        raise ValueError("Historical HAR intake exemption scope changed")
    receipts = []
    for binding in _HAR_UNSTARTED_MANIFESTS.values():
        path = base / binding["receipt_path"]
        if not path.is_file() or sha256_file(path) != binding["receipt_sha256"]:
            raise ValueError("Historical HAR unstarted intake receipt binding changed")
        receipts.append(load_json(path))
    first, second = receipts
    if (first.get("ready") is not False or first.get("EXP") != 0 or first.get("fit") != 0
            or second.get("experiment_id", "missing") is not None
            or second.get("workers_present") != 0 or second.get("trials_present") != 0
            or second.get("observed_full_workers_seconds") != 0
            or second.get("full_worker_charge_including_conservative_recovery") != 0
            or second.get("native_raw_publisher_or_NPZ_published") is not False):
        raise ValueError("Historical HAR intake was not proven unstarted")
    for relative in _HAR_UNSTARTED_MANIFESTS:
        path = base / relative
        if not path.exists() and not path.is_symlink():
            discovered.discard(relative)


def protected_files(root: Path | None = None) -> tuple[str, ...]:
    base = (root or project_root()).resolve()
    discovered: set[str] = set(FIXED_PROTECTED_FILES)
    _exclude_proven_unstarted_har_intakes(base, discovered)
    # C adds prospective documents and native payloads only to its new cohort.
    # Their absence before intake cannot masquerade as a scoring-ready freeze.
    from .config import load_config
    if (base / "config/research.toml").is_file() and load_config(base).benchmark_version == "asm01_native_memory_v4":
        discovered.update((
            "research/laboratory/NEXTAI-C-HUMAN-AUTHORITY-20261008.md",
            "research/plans/NEXTAI-C-STABILIZATION-ASM-SCREEN-V1.json",
            "research/plans/NEXTAI-C-ENGINEERING-PREREGISTRATION-V1.json",
            "research/plans/ASM01-C-SIGNED-SERIAL-TASK-V1.json",
            "research/plans/ASM01-C-STABILIZED-SCREEN-V1.json",
            "research/reviews/ASM01-C-source-binding-V1.json",
            "research/data_manifests/ASM01-C-ACQUISITION-V1.json",
            "research/data/asm01_c_v1/screen.npz",
            "scripts/acquire_asm01_c_v1.py",
            "scripts/run_c_bounded.py",
            "scripts/run_c_science.py",
        ))
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
