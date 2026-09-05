from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import psutil

from .audit import audit_benchmark_boundary, audit_candidate
from .baseline_semantics import verify_preflight_certificate, verify_required_baselines
from .config import load_config
from .gates import lifecycle_problems, pending_plan_ids, stop_gate_problems
from .integrity import verify_manifest
from .laboratory import laboratory_contract, laboratory_problems, laboratory_progress
from .ledger import (
    ensure_layout,
    latest_hypotheses,
    read_jsonl,
    research_dir,
)
from .scientific_validity import invalid_experiment_ids, problems as validity_problems
from .schemas import check_all_schemas, validate_document
from .utils import load_json, project_root, sha256_json


@dataclass
class DoctorReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def run_doctor(root: Path | None = None) -> DoctorReport:
    base = (root or project_root()).resolve()
    report = DoctorReport()
    ensure_layout(base)
    try:
        config = load_config(base)
        report.facts.append(
            f"benchmark={config.benchmark_version} status={config.benchmark_status} protocol=v{config.protocol_version}"
        )
    except Exception as exc:
        report.errors.append(f"config: {exc}")
        return report

    if config.protocol_version >= 3:
        lab_errors = laboratory_problems(base)
        report.errors.extend(lab_errors)
        if not lab_errors:
            lab = laboratory_contract(base)
            progress = laboratory_progress(base)
            report.facts.append(f"laboratory={lab['status']} next={progress['next_action_id']} scoring={lab['scoring_authorized']}")
            if progress["user_decision_required"]:
                report.warnings.append("PC-01 bounded stage exhausted; user decision required, no automatic extra service or training")

    report.errors.extend(f"schema: {problem}" for problem in check_all_schemas(base))
    try:
        state = load_json(research_dir(base) / "state.json")
        validate_document("research_state", state, base)
        if int(state.get("protocol_version", 0)) != config.protocol_version:
            report.errors.append("state protocol_version differs from config")
        if int(state.get("generation", -1)) != int(config.raw["project"]["generation"]):
            report.errors.append("state generation differs from config")
        report.facts.append(
            f"cycle={state.get('cycle_number')} completed={state.get('completed_experiments')}"
        )
    except Exception as exc:
        report.errors.append(f"state: {exc}")

    try:
        hypotheses = latest_hypotheses(base)
        for value in hypotheses.values():
            validate_document("hypothesis", value, base)
        report.facts.append(f"hypotheses={len(hypotheses)}")
    except Exception as exc:
        report.errors.append(f"hypotheses: {exc}")

    try:
        source_ids: set[str] = set()
        for source in read_jsonl(research_dir(base) / "sources.jsonl"):
            validate_document("source", source, base)
            source_id = str(source["source_id"])
            if source_id in source_ids:
                report.errors.append(f"duplicate source ID: {source_id}")
            source_ids.add(source_id)
        report.facts.append(f"sources={len(source_ids)}")
    except Exception as exc:
        report.errors.append(f"sources: {exc}")

    registry: dict[str, str] = {}
    try:
        for event in read_jsonl(research_dir(base) / "plan_registry.jsonl"):
            registry[event["experiment_id"]] = event["plan_sha256"]
        for path in sorted((research_dir(base) / "plans").glob("EXP-*.json")):
            plan = load_json(path)
            validate_document("experiment_plan", plan, base)
            expected = registry.get(plan["experiment_id"])
            if expected is None:
                report.errors.append(f"unregistered plan: {path.name}")
            elif expected != sha256_json(plan):
                report.errors.append(f"changed preregistered plan: {path.name}")
    except Exception as exc:
        report.errors.append(f"plans: {exc}")

    try:
        for path in sorted((research_dir(base) / "results").glob("EXP-*.json")):
            validate_document("experiment_result", load_json(path), base)
        report.errors.extend(
            f"scientific validity: {problem}"
            for problem in validity_problems(base)
        )
        report.facts.append(
            f"scientifically_invalid_results={len(invalid_experiment_ids(base))}"
        )
    except Exception as exc:
        report.errors.append(f"results: {exc}")

    try:
        report.errors.extend(
            f"lifecycle: {problem}" for problem in lifecycle_problems(base)
        )
        report.facts.append(f"pending_plans={len(pending_plan_ids(base))}")
    except Exception as exc:
        report.errors.append(f"lifecycle: {exc}")

    benchmark_path = (
        base
        / "src"
        / "nextai_autoresearch"
        / "benchmarks"
        / f"{config.benchmark_version}.py"
    )
    if not benchmark_path.is_file():
        report.errors.append(
            f"active benchmark module is missing: {benchmark_path.relative_to(base).as_posix()}"
        )
    else:
        report.errors.extend(
            f"benchmark boundary: {problem}"
            for problem in audit_benchmark_boundary(config.benchmark_version, base)
        )

    integrity = verify_manifest(base)
    if integrity["ok"]:
        report.facts.append(f"integrity=ok files={integrity['checked_files']}")
    else:
        report.errors.extend(f"integrity: {problem}" for problem in integrity["problems"])
    if integrity["ok"] and config.benchmark_status == "active":
        try:
            certificate = verify_preflight_certificate(base)
            report.facts.append(f"preflight_certificate={certificate['certificate_sha256']}")
        except Exception as exc:
            report.errors.append(f"preflight certificate: {exc}")

    candidate_directory = base / "src" / "nextai_autoresearch" / "candidates"
    audited = 0
    for path in sorted(candidate_directory.glob("*.py")):
        if path.stem in {"__init__", "base"}:
            continue
        result = audit_candidate(path.stem, config, base)
        audited += 1
        if not result.ok:
            report.errors.extend(
                f"candidate {path.stem}: {problem}" for problem in result.problems
            )
    report.facts.append(f"audited_candidates={audited}")

    if config.benchmark_version == "pc01_byte_lm_learning_measurement_v1":
        try:
            from .pc01_execution import verify_certificate, attempt_history
            verify_certificate(base)
            report.facts.append(f"pc01_registered_attempts={len(attempt_history(base))} diagnostic_only=True")
        except Exception as exc:
            report.errors.append(f"PC-01 execution conformance: {exc}")

    if config.benchmark_version.startswith("heldout_mechanism_recombination_"):
        try:
            module = __import__(
                f"nextai_autoresearch.benchmarks.{config.benchmark_version}",
                fromlist=["static_control_gate"],
            )
            if hasattr(module, "static_control_gate"):
                static = module.static_control_gate()
                required_flags = (
                    "raw_reencoding_differs", "positive_canonical_match",
                    "pair_breaking_changes_operator",
                )
                if not all(static.get(name) for name in required_flags):
                    raise RuntimeError(f"operator experience static gate failed: {static}")
            required = list(config.raw["recombination"]["classical_baselines"])
            checked = verify_required_baselines(
                {
                    "candidates": required,
                    "mechanism_recombination_protocol": {"classical_baselines": required},
                },
                base,
                run_tests=False,
            )
            report.facts.append(f"semantic_baselines={len(checked['required'])}")
        except Exception as exc:
            report.errors.append(f"mechanism recombination maintenance: {exc}")
    elif config.benchmark_version.startswith("heldout_repository_sequence_"):
        try:
            module = __import__(
                f"nextai_autoresearch.benchmarks.{config.benchmark_version}",
                fromlist=["verify_static_contract"],
            )
            static = module.verify_static_contract(base)
            required = list(config.raw["compression"]["classical_baselines"])
            checked = verify_required_baselines(
                {
                    "candidates": required,
                    "compression_protocol": {"classical_baselines": required},
                },
                base,
                run_tests=False,
            )
            report.facts.append(f"repository_files={static['files']}")
            report.facts.append(f"semantic_baselines={len(checked['required'])}")
        except Exception as exc:
            report.errors.append(f"repository compression maintenance: {exc}")
    elif config.benchmark_version.startswith("heldout_parallel_masked_"):
        try:
            required = list(config.raw["masked_refinement"]["classical_baselines"])
            checked = verify_required_baselines(
                {
                    "candidates": required,
                    "masked_refinement_protocol": {"classical_baselines": required},
                },
                base,
                run_tests=False,
            )
            report.facts.append(f"semantic_baselines={len(checked['required'])}")
        except Exception as exc:
            report.errors.append(f"baseline semantics: {exc}")
    elif config.benchmark_version.startswith("cross_family_"):
        try:
            required = list(config.raw["transfer"]["specialist_baselines"])
            checked = verify_required_baselines(
                {
                    "candidates": required,
                    "transfer_protocol": {"specialist_baselines": required},
                },
                base,
                run_tests=False,
            )
            report.facts.append(f"semantic_baselines={len(checked['required'])}")
        except Exception as exc:
            report.errors.append(f"baseline semantics: {exc}")
    elif config.benchmark_version.startswith("heldout_dronepropa_"):
        try:
            module = __import__(
                f"nextai_autoresearch.benchmarks.{config.benchmark_version}",
                fromlist=["verify_static_contract"],
            )

            static = module.verify_static_contract(base)
            required = list(config.raw["dronepropa"]["classical_baselines"])
            checked = verify_required_baselines(
                {
                    "candidates": required,
                    "dronepropa_protocol": {"classical_baselines": required},
                },
                base,
                run_tests=False,
            )
            report.facts.append(f"dronepropa_files={static['files']}")
            report.facts.append(f"semantic_baselines={len(checked['required'])}")
        except Exception as exc:
            report.errors.append(f"dronepropa maintenance: {exc}")
    elif config.benchmark_version.startswith("heldout_wt_changepoints_"):
        try:
            module = __import__(
                f"nextai_autoresearch.benchmarks.{config.benchmark_version}",
                fromlist=["verify_static_contract"],
            )
            static = module.verify_static_contract(base)
            required = list(config.raw["wt_prequential"]["classical_baselines"])
            checked = verify_required_baselines(
                {
                    "candidates": required,
                    "wt_prequential_protocol": {"classical_baselines": required},
                },
                base,
                run_tests=False,
            )
            report.facts.append(f"wt_changepoints_files={static['files']}")
            report.facts.append(f"semantic_baselines={len(checked['required'])}")
        except Exception as exc:
            report.errors.append(f"WT changepoints maintenance: {exc}")
    elif config.benchmark_version.startswith("heldout_raw_sensor_active_"):
        try:
            module = __import__(
                f"nextai_autoresearch.benchmarks.{config.benchmark_version}",
                fromlist=["development_smoke"],
            )
            smoke = module.development_smoke()
            if smoke.get("decision") != "pass":
                raise RuntimeError(f"raw sensor development gate failed: {smoke.get('gates')}")
            required = list(config.raw["active_sensor"]["classical_baselines"])
            checked = verify_required_baselines(
                {
                    "candidates": required,
                    "active_sensor_protocol": {"classical_baselines": required},
                },
                base,
                run_tests=False,
            )
            report.facts.append(f"raw_sensor_baselines={len(checked['required'])}")
        except Exception as exc:
            report.errors.append(f"raw sensor maintenance: {exc}")
    elif config.benchmark_version == "heldout_suitesparse_cross_matrix_prolongation_v1":
        try:
            module = __import__(
                "nextai_autoresearch.benchmarks.heldout_suitesparse_cross_matrix_prolongation_v1",
                fromlist=["contract_audit"],
            )
            audit = module.contract_audit()
            if not audit.get("pass"):
                raise RuntimeError(f"contract audit failed: {audit.get('checks')}")
            required = list(config.raw["suitesparse_cross_matrix"]["classical_baselines"])
            checked = verify_required_baselines(
                {
                    "candidates": required,
                    "suitesparse_transfer_protocol": {"classical_baselines": required},
                },
                base,
                run_tests=False,
            )
            report.facts.append("suitesparse_split=12_train/3_heldout")
            report.facts.append(f"semantic_baselines={len(checked['required'])}")
        except Exception as exc:
            report.errors.append(f"SuiteSparse transfer maintenance: {exc}")
    elif config.benchmark_version == "orthogonal_double_matching_source_swap_v1":
        try:
            module = __import__(
                "nextai_autoresearch.benchmarks.orthogonal_double_matching_source_swap_v1",
                fromlist=["contract_audit"],
            )
            audit = module.contract_audit()
            if audit.get("decision") != "A_RID_EVALUATOR_CERTIFIED":
                raise RuntimeError(
                    f"RID-CONTRACT-001 falsification gate: {audit.get('decision')}"
                )
            if audit.get("scoring_performed") or audit.get(
                "runner_random_scoring_seed_realized"
            ):
                raise RuntimeError("service-only cycle realized forbidden scoring state")
            report.facts.append(f"rid_contract={audit['contract']}")
            report.facts.append(f"rid_decision={audit['decision']}")
        except Exception as exc:
            report.errors.append(f"relational identifiability maintenance: {exc}")

    pyproject = (base / "pyproject.toml").read_text(encoding="utf-8").lower()
    for dependency in ("openai", "anthropic", "google-generativeai"):
        if f'"{dependency}' in pyproject or f"'{dependency}" in pyproject:
            report.errors.append(f"external model/API dependency is forbidden: {dependency}")

    lock = research_dir(base) / "run.lock"
    if lock.exists():
        try:
            lock_data = load_json(lock)
            age = time.time() - float(lock_data.get("epoch", time.time()))
            stale = int(config.raw["execution"]["stale_lock_seconds"])
            if age <= stale:
                report.errors.append(f"active run lock: {lock_data}")
            else:
                report.warnings.append(f"stale run lock ({age:.0f}s old)")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            report.errors.append(f"invalid run lock: {exc}")
    report.errors.extend(f"gate: {problem}" for problem in stop_gate_problems(base))
    report.facts.append(
        f"hardware=cpu:{psutil.cpu_count(logical=True)} ram_gb:{psutil.virtual_memory().total / 2**30:.1f}"
    )
    return report
