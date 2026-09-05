"""Registered PC-01 diagnostic lifecycle. Preparation does not authorize execution.

Every public execution path retains the normal maintenance/STOP/integrity gates.
Subprocess supervision is sampled enforcement, not an OS security sandbox.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

import psutil

from .audit import audit_candidate
from .config import load_config
from .gates import ensure_can_create_plan, ensure_can_run_plan, stop_gate_problems
from .integrity import manifest_path, verify_manifest
from .ledger import (RunLock, append_jsonl, load_state, next_experiment_id, read_jsonl,
                     register_plan, registered_plan_hash, save_state, latest_plan_statuses)
from .pc01 import (COHORTS, CONTRACT_SHA256, DATA_SHA256, GIB, contract, require,
                   series_decision)
from .schemas import validate_document
from .utils import atomic_write_json, load_json, sha256_file, sha256_json, utc_now
from .pc01_telemetry import read_device_sample
from .pc01_final_transition import selected_transition


ATTEMPTS = "research/laboratory/pc01_attempts.jsonl"
SERIES = "research/laboratory/PC-01-FINAL-SERIES-V1.json"
CERTIFICATE = "research/laboratory/PC-01-EXECUTION-CERTIFICATE-V1.json"
CERTIFICATE_FILES = (
    "src/nextai_autoresearch/pc01.py", "src/nextai_autoresearch/pc01_execution.py",
    "src/nextai_autoresearch/pc01_worker.py", "src/nextai_autoresearch/runner.py",
    "src/nextai_autoresearch/cli.py", "src/nextai_autoresearch/gates.py",
    "src/nextai_autoresearch/schemas.py", "src/nextai_autoresearch/audit.py",
    "src/nextai_autoresearch/report.py", "schemas/pc01_plan.schema.json",
    "schemas/pc01_result.schema.json", "schemas/pc01_replica.schema.json",
    "tests/test_pc01_execution.py", "tests/test_pc01_harness.py", "tests/fixtures/pc01_process_fixture.py",
    "src/nextai_autoresearch/laboratory.py", "tests/test_pc01_activation.py",
    "research/laboratory/PC-01-ACTIVATION-20260905-V1.json",
    "src/nextai_autoresearch/pc01_telemetry.py", "tests/test_pc01_telemetry.py",
    "tests/fixtures/pc01_telemetry_fixture.py",
    "research/laboratory/PC-01-DEV2-20260905-V1.json", "tests/test_pc01_dev2.py",
    "src/nextai_autoresearch/pc01_gpu_metadata.py", "tests/test_pc01_gpu_metadata.py",
    "research/plans/PC-01-GPU-METADATA-V1.json",
    "src/nextai_autoresearch/pc01_final_transition.py", "tests/test_pc01_final_transition.py",
    "research/plans/PC-01-FINAL-PREP-V1.json",
    "src/nextai_autoresearch/pc01_final_authority.py", "tests/test_pc01_final_authority.py",
    "research/laboratory/PC-01-FINAL-ACTIVATION-20260905-V1.json",
)
CERTIFICATE_TESTS = (
    "test_complete_authenticated_series_uses_three_distinct_runner_seeds",
    "test_registered_diagnostic_completes_without_architecture_rows",
    "test_unresolved_parent_interrupt_blocks_retry",
    "test_model_layout_is_checked_without_instantiating_storage_or_training",
    "test_real_maintenance_blocks_new_diagnostic_and_series_without_mutation",
    "test_numerical_controls_and_train_only_classical_baselines",
    "test_cuda_fixture_checks_sync_and_causality_without_training",
    "test_authorization_allows_only_one_scoped_development_registration",
    "test_real_authorization_denies_final_and_legacy_without_mutation",
    "test_transient_reader_lock_recovers_without_partial_json",
    "test_persistent_read_contention_fails_without_blocking_parent",
    "test_second_dev_is_single_use_and_cannot_reset_history",
    "test_v2_diagnostic_retains_identity_and_prior_fit_charge",
    "test_real_sanitized_probe_pair_without_training",
    "test_v3_parent_rejects_missing_metadata_but_preserves_v2",
    "test_failed_prefit_probe_preserves_error_without_model_or_training",
    "test_v3_authenticated_series_preserves_metadata",
    "test_exact_real_transition_is_read_only",
    "test_v3_series_rejects_missing_metadata",
    "test_final_scope_is_exact_and_single_use",
    "test_real_final_authority_keeps_dev_and_replay_closed",
)


def new_json(path: Path, value: dict) -> None:
    require(not path.exists(), f"Immutable artifact already exists: {path}")
    atomic_write_json(path, value)


def recipe_digest(root: Path) -> str:
    design = contract(root)
    return sha256_json({key: design[key] for key in ("model", "recipe", "controls", "evaluation", "measurement")})


def audit_bundle(candidate: str, root: Path) -> dict:
    audit = audit_candidate(candidate, load_config(root), root)
    require(audit.ok, f"PC-01 candidate audit failed: {audit.problems}")
    files = {p.relative_to(root).as_posix(): digest for p, digest in audit.dependencies}
    files[audit.path.relative_to(root).as_posix()] = audit.sha256
    return {"files": files, "sha256": sha256_json(files)}


def registered_plans(root: Path) -> list[dict]:
    rows = []
    registry = read_jsonl(root / "research/plan_registry.jsonl")
    require(len({r["experiment_id"] for r in registry}) == len(registry), "duplicate plan registration")
    for path in sorted((root / "research/plans").glob("EXP-*.json")):
        plan = load_json(path)
        if plan.get("kind") != "pc01_diagnostic_plan":
            continue
        validate_document("pc01_plan", plan, root)
        require(registered_plan_hash(plan["experiment_id"], root) == sha256_json(plan), "unregistered/changed PC-01 plan")
        require(path.stem == plan["experiment_id"], "plan filename mismatch")
        rows.append(plan)
    for phase in ("dev", "final"):
        attempts = [p["attempt"] for p in rows if p["phase"] == phase]
        require(sorted(attempts) == list(range(1, len(attempts)+1)) and len(attempts) <= 3,
                "PC-01 phase attempts reset/duplicated/exceeded")
    return rows


def attempt_history(root: Path) -> list[dict]:
    """Starts count even if the parent dies. No retry of an already started ID."""
    plans = {p["experiment_id"]: p for p in registered_plans(root)}
    starts, finishes = {}, {}
    for event in read_jsonl(root / ATTEMPTS):
        identifier = event["experiment_id"]
        require(identifier in plans, "attempt has no registered plan")
        if event["event"] == "started":
            require(identifier not in starts and identifier not in finishes, "attempt replay")
            require(event["plan_sha256"] == sha256_json(plans[identifier]), "attempt plan changed")
            runtime_path = (root / event["runtime_path"]).resolve()
            require(runtime_path == (root / "research/tmp" / identifier / "pc01-runtime.json").resolve(), "noncanonical runtime receipt")
            runtime = load_json(runtime_path)
            require(sha256_json(runtime) == event["runtime_sha256"], "runtime receipt changed")
            require(runtime["plan"] == plans[identifier], "runtime plan substitution")
            require(runtime["seed"] == event["seed"], "runtime seed substitution")
            if plans[identifier]["phase"] == "dev":
                require(event["seed"] == 1103, "wrong development seed")
            else:
                require(type(event["seed"]) is int and 10000 <= event["seed"] <= 2147483647, "wrong final seed")
            starts[identifier] = event
        elif event["event"] == "finished":
            require(identifier in starts and identifier not in finishes, "orphan/duplicate completion")
            path = root / "research/results" / f"{identifier}.json"
            require(path.is_file() and sha256_file(path) == event["result_sha256"], "completion result missing/changed")
            result = load_json(path)
            require(result["execution"]["fit_seconds_charged"] == event["fit_seconds_charged"], "fit charge differs from supervisor")
            require(result["runtime_sha256"] == starts[identifier]["runtime_sha256"], "result runtime differs")
            require(result["plan_sha256"] == starts[identifier]["plan_sha256"], "result plan differs")
            if result["status"] == "complete":
                runtime = load_json(root / starts[identifier]["runtime_path"])
                validate_measurement(result["measurement"], runtime, root)
            artifacts = result["execution"].get("worker_artifacts", {})
            require(artifacts, "result missing worker artifact commitments")
            directory = root / "research/tmp" / identifier
            for name, digest in artifacts.items():
                artifact = (directory / name).resolve()
                require(artifact.parent == directory.resolve() and artifact.is_file() and sha256_file(artifact) == digest,
                        "worker artifact missing/changed")
            finishes[identifier] = event
        else:
            raise ValueError("unknown attempt event")
    rows = []
    for identifier, start in starts.items():
        end = finishes.get(identifier)
        # A lost supervisor reserves the full fit allowance and blocks continuation.
        charged = 1200.0 if end is None else end["fit_seconds_charged"]
        require(type(charged) in (int, float) and math.isfinite(charged) and charged >= 0,
                "invalid fit accounting")
        rows.append({**start, "complete": end is not None, "fit_seconds_charged": charged,
                     "phase": plans[identifier]["phase"]})
    require(sum(r["fit_seconds_charged"] for r in rows) <= 7200, "cumulative fit budget exceeded")
    finals = [r["seed"] for r in rows if r["phase"] == "final"]
    require(len(set(finals)) == len(finals), "reused final seed")
    for identifier in plans:
        if (root / "research/results" / f"{identifier}.json").exists():
            require(identifier in finishes, "diagnostic result has no completed attempt receipt")
    return rows


def verify_certificate(root: Path) -> dict:
    import re
    import xml.etree.ElementTree as ET
    evaluator = load_json(manifest_path(root))["evaluator_sha256"]
    events = [e for e in read_jsonl(root / "research/events.jsonl") if e.get("event") == "pc01_execution_certificate_created"]
    paths = set()
    for event in events:
        relative = event.get("certificate_path", "")
        require(re.fullmatch(r"research/laboratory/PC-01-EXECUTION-CERTIFICATE-V[1-9][0-9]*\.json", relative) is not None,
                "invalid certificate path")
        require(relative not in paths, "certificate path reused")
        paths.add(relative)
        require(sha256_file(root / relative) == event["certificate_sha256"], "registered certificate replaced")
    matching = [e for e in events if e.get("evaluator_sha256") == evaluator]
    require(len(matching) == 1, "execution certificate unregistered or ambiguous for current evaluator")
    certificate = load_json(root / matching[0]["certificate_path"])
    require(certificate.get("kind") == "pc01_execution_conformance", "wrong execution certificate")
    require(certificate.get("all_required_checks_passed") is True, "PC-01 conformance incomplete")
    require(certificate.get("contract_sha256") == CONTRACT_SHA256, "wrong certificate contract")
    require(certificate.get("evaluator_sha256") == load_json(manifest_path(root))["evaluator_sha256"],
            "execution certificate evaluator changed")
    require(set(certificate["files"]) == set(CERTIFICATE_FILES), "execution certificate missing required source/test commitment")
    for rel, digest in certificate["files"].items():
        path = (root / rel).resolve()
        require(path.is_relative_to(root) and sha256_file(path) == digest, "certificate source/test changed")
    report = (root / certificate["test_report"]).resolve()
    require(report.is_relative_to(root) and sha256_file(report) == certificate["test_report_sha256"], "conformance report changed")
    xml = ET.parse(report).getroot()
    suites = list(xml.iter("testsuite"))
    require(suites and all(int(s.get(key, "0")) == 0 for s in suites for key in ("failures", "errors", "skipped")),
            "conformance report contains failed or unverified checks")
    names = {case.get("name") for case in xml.iter("testcase")}
    require(not any(list(xml.iter(tag)) for tag in ("failure", "error", "skipped")), "conformance case failed/skipped")
    require(set(CERTIFICATE_TESTS).issubset(names), "conformance report omits required checks")
    return certificate


def validate_plan(plan: dict, root: Path) -> None:
    validate_document("pc01_plan", plan, root)
    require(plan["contract_sha256"] == CONTRACT_SHA256 and plan["data_sha256"] == DATA_SHA256,
            "PC-01 contract/data substitution")
    require(plan["recipe_sha256"] == recipe_digest(root), "PC-01 recipe substitution")
    require(plan["evaluator_sha256"] == load_json(manifest_path(root))["evaluator_sha256"], "evaluator changed")


def create_plan(root: Path, *, candidate: str, phase: str, question: str,
                series_path: Path | None = None) -> Path:
    root = root.resolve()
    ensure_can_create_plan(root, pc01_candidate=candidate, pc01_phase=phase)  # No maintenance exception.
    cohort = load_config(root).benchmark_version
    require(cohort in COHORTS, "activate the separately frozen PC-01 cohort first")
    verify_certificate(root)
    with RunLock(root, stale_seconds=2400):
        ensure_can_create_plan(root, pc01_candidate=candidate, pc01_phase=phase)
        history = attempt_history(root)
        require(all(r["complete"] for r in history), "unresolved interrupted attempt")
        plans = registered_plans(root)
        require(phase in ("dev", "final"), "invalid phase")
        attempt = 1 + sum(p["phase"] == phase for p in plans)  # Invalidated plans also consume a development attempt.
        require(attempt <= 3, "phase registration cap exhausted")
        series_digest = None
        if phase == "dev":
            require(not (root / SERIES).exists() and series_path is None, "development closed by final-series freeze")
        else:
            require(series_path is not None and series_path.resolve() == (root / SERIES).resolve(), "canonical final series required")
            series = verify_series(root)
            require(candidate == series["candidate"], "final candidate changed")
            series_digest = sha256_json(series)
        plan = {"schema_version": 1, "kind": "pc01_diagnostic_plan", "experiment_id": next_experiment_id(root),
                "created_at": utc_now(), "status": "planned", "benchmark": cohort, "phase": phase,
                "candidate": candidate, "contract_sha256": CONTRACT_SHA256, "data_sha256": DATA_SHA256,
                "evaluator_sha256": load_json(manifest_path(root))["evaluator_sha256"],
                "recipe_sha256": recipe_digest(root), "series_sha256": series_digest, "development_seed": 1103,
                "final_seed_policy": {"method": "runner_random_v1", "minimum": 10000, "maximum": 2147483647, "count": 1},
                "architecture_promoted": False, "budget": "pc01_fixed_v1", "question": question, "attempt": attempt}
        validate_plan(plan, root)
        path = root / "research/plans" / f"{plan['experiment_id']}.json"
        new_json(path, plan)
        register_plan(plan, path, root)
        return path


def freeze_series(root: Path, selected_dev_id: str) -> Path:
    """Must be explicitly invoked before first final access; no implicit selection."""
    ensure_can_create_plan(root, pc01_series_freeze=True)
    verify_certificate(root)
    with RunLock(root, stale_seconds=2400):
        ensure_can_create_plan(root, pc01_series_freeze=True)
        history = attempt_history(root)
        require(history and all(r["complete"] for r in history), "unfinished development")
        require(all(r["phase"] == "dev" for r in history), "final access already started")
        plans = registered_plans(root)
        require(all(p["phase"] == "dev" for p in plans), "final already registered")
        selected = next((p for p in plans if p["experiment_id"] == selected_dev_id), None)
        require(selected is not None, "selected development plan does not exist")
        result = load_json(root / "research/results" / f"{selected_dev_id}.json")
        require(result["status"] == "complete", "selection needs complete valid development")
        bundle = audit_bundle(selected["candidate"], root)
        runtime = load_json(root / "research/tmp" / selected_dev_id / "pc01-runtime.json")
        require(bundle == runtime["audit"], "selected source differs from executed development")
        require(7200 - sum(r["fit_seconds_charged"] for r in history) >= 3600, "insufficient final fit reservation")
        series = {"kind": "pc01_final_series", "created_at": utc_now(), "candidate": selected["candidate"],
                  "selected_dev_id": selected_dev_id, "audit": bundle, "contract_sha256": CONTRACT_SHA256,
                  "recipe_sha256": recipe_digest(root), "evaluator_sha256": selected["evaluator_sha256"],
                  "data_sha256": DATA_SHA256, "replicates": 3, "max_fit_seconds": 7200,
                  "development_plans": {p["experiment_id"]: sha256_json(p) for p in plans},
                  "development_attempts_sha256": sha256_json(history)}
        if load_config(root).benchmark_version == "pc01_byte_lm_learning_measurement_v3":
            transition = selected_transition(root, selected_dev_id)
            series.update(benchmark=transition["target_cohort"], transition=transition,
                          evaluator_sha256=transition["target_evaluator_sha256"])
        new_json(root / SERIES, series)
        append_jsonl(root / "research/events.jsonl", {"event": "pc01_final_series_frozen", "created_at": utc_now(),
                                                      "series_sha256": sha256_json(series)})
        return root / SERIES


def verify_series(root: Path) -> dict:
    series = load_json(root / SERIES)
    require(series.get("kind") == "pc01_final_series" and series.get("replicates") == 3
            and series.get("max_fit_seconds") == 7200 and series.get("data_sha256") == DATA_SHA256, "final series contract changed")
    events = [e for e in read_jsonl(root / "research/events.jsonl") if e.get("event") == "pc01_final_series_frozen"]
    require(len(events) == 1 and events[0]["series_sha256"] == sha256_json(series), "final series missing/changed/replaced")
    require(series["audit"] == audit_bundle(series["candidate"], root), "source changed after final freeze")
    require(series["recipe_sha256"] == recipe_digest(root) and series["contract_sha256"] == CONTRACT_SHA256,
            "final recipe changed")
    require(series["evaluator_sha256"] == load_json(manifest_path(root))["evaluator_sha256"], "final evaluator changed")
    cohort = load_config(root).benchmark_version
    require(cohort in COHORTS, "unknown final cohort")
    if cohort == "pc01_byte_lm_learning_measurement_v3":
        require(series.get("benchmark") == cohort, "v3 series requires an explicit cohort")
        require(series.get("transition") == selected_transition(root, series["selected_dev_id"]), "final transition changed/missing")
    else:
        require("transition" not in series and series.get("benchmark", cohort) == cohort, "legacy transition mismatch")
    dev = {p["experiment_id"]: sha256_json(p) for p in registered_plans(root) if p["phase"] == "dev"}
    require(dev == series["development_plans"], "development added/omitted after freeze")
    history = [r for r in attempt_history(root) if r["phase"] == "dev"]
    require(sha256_json(history) == series["development_attempts_sha256"], "development history changed")
    return series


@dataclass(frozen=True)
class Limits:
    fit_seconds: float = 1200
    worker_seconds: float = 1800
    rss_bytes: int = 10*GIB
    cuda_bytes: int = 10*GIB
    payload_bytes: int = 2*GIB
    disk_reserve_bytes: int = 10*GIB


def payload_bytes(root: Path) -> int:
    total = 0
    for relative in ("research/data/pc01_tinyshakespeare_v1", "research/pc01_payload"):
        folder = root / relative
        for path in folder.rglob("*") if folder.exists() else ():
            if path.is_file():
                require(not path.is_symlink(), "PC-01 payload cannot link outside accounting")
                total += path.stat().st_size
    return total


def supervise(command: list[str], root: Path, work: Path, *, limits: Limits = Limits()) -> dict:
    """Trusted worker asks for fit; parent starts its clock BEFORE granting fit.

    Limits can be reduced by isolated tests, never supplied in a registered plan.
    CUDA allocator peaks come from the trusted worker; PyTorch also caps its allocator.
    RSS/storage are sampled at 50 ms and are not kernel-enforced hard quotas.
    """
    from .runner import _rss_tree, _terminate_tree, _sanitized_environment
    work.mkdir(parents=True, exist_ok=True)
    require(not (work / "supervisor.json").exists(), "supervisor replay")
    started, fit_start, fit_end = time.monotonic(), None, None
    peak_rss = allocated = reserved = 0
    telemetry_unavailable_since = None
    telemetry_read_conflicts, telemetry_max_read_gap_seconds = 0, 0.0
    reason, process, return_code = None, None, None
    try:
        require(shutil.disk_usage(root).free >= limits.disk_reserve_bytes, "disk reserve")
        require(payload_bytes(root) <= limits.payload_bytes, "payload cap")
        with (work / "worker.log").open("xb") as log:
            process = subprocess.Popen(command, cwd=root, env=_sanitized_environment(root), stdout=log, stderr=log)
            handle = psutil.Process(process.pid)
            while True:
                now = time.monotonic()
                peak_rss = max(peak_rss, _rss_tree(handle))
                if (work / "fit-request.json").exists() and fit_start is None:
                    fit_start = now
                    new_json(work / "fit-granted.json", {"parent_started": True})
                if (work / "fit-finished.json").exists():
                    require(fit_start is not None, "fit ended without parent grant")
                    if fit_end is None:
                        fit_end = now
                telemetry = work / "device.json"
                if telemetry.exists():
                    sample = read_device_sample(telemetry)
                    if sample is None:
                        telemetry_read_conflicts += 1
                        if telemetry_unavailable_since is None:
                            telemetry_unavailable_since = now
                    else:
                        allocated = max(allocated, int(sample["allocated"]))
                        reserved = max(reserved, int(sample["reserved"]))
                        if telemetry_unavailable_since is not None:
                            telemetry_max_read_gap_seconds = max(telemetry_max_read_gap_seconds, now - telemetry_unavailable_since)
                        telemetry_unavailable_since = None
                if telemetry_unavailable_since is not None:
                    telemetry_max_read_gap_seconds = max(telemetry_max_read_gap_seconds, now - telemetry_unavailable_since)
                if stop_gate_problems(root):
                    reason = "stop_gate"
                elif now-started > limits.worker_seconds:
                    reason = "worker_timeout"
                elif fit_start is not None and (fit_end or now)-fit_start > limits.fit_seconds:
                    reason = "fit_timeout"
                elif telemetry_unavailable_since is not None and now - telemetry_unavailable_since >= 1.0:
                    reason = "telemetry_read_timeout"
                elif peak_rss > limits.rss_bytes:
                    reason = "rss_limit"
                elif allocated > limits.cuda_bytes or reserved > limits.cuda_bytes:
                    reason = "cuda_limit"
                elif payload_bytes(root) > limits.payload_bytes:
                    reason = "payload_limit"
                elif shutil.disk_usage(root).free < limits.disk_reserve_bytes:
                    reason = "disk_reserve"
                if reason:
                    if process.poll() is None:
                        _terminate_tree(handle)
                    break
                if process.poll() is not None and telemetry_unavailable_since is None:
                    break
                time.sleep(0.05)
            return_code = process.wait(timeout=5)
    except BaseException as exc:
        reason = f"supervisor_error:{type(exc).__name__}:{exc}"
        if process is not None and process.poll() is None:
            _terminate_tree(psutil.Process(process.pid))
            return_code = process.wait(timeout=5)
    ended = time.monotonic()
    fit_seconds = 0.0 if fit_start is None else (fit_end or ended)-fit_start
    record = {"return_code": return_code, "termination_reason": reason, "worker_seconds": ended-started,
              "fit_seconds": fit_seconds, "fit_seconds_charged": fit_seconds
              if fit_end is not None and reason is None else max(limits.fit_seconds, fit_seconds),
              "rss_bytes": peak_rss, "cuda_allocated_bytes": allocated, "cuda_reserved_bytes": reserved,
              "persisted_bytes": payload_bytes(root), "disk_free_bytes": shutil.disk_usage(root).free,
              "limits": asdict(limits), "sampling_interval_seconds": 0.05,
              "telemetry_read_conflicts": telemetry_read_conflicts,
              "telemetry_max_read_gap_seconds": telemetry_max_read_gap_seconds,
              "network_policy": "forbidden_by_audit_not_os_sandboxed"}
    new_json(work / "supervisor.json", record)
    return record


def run_diagnostic(plan_path: Path, root: Path) -> Path:
    root = root.resolve()
    plan = load_json(plan_path)
    validate_plan(plan, root)
    ensure_can_run_plan(plan["experiment_id"], root)
    verify_certificate(root)
    identifier = plan["experiment_id"]
    require(plan_path.resolve() == (root / "research/plans" / f"{identifier}.json").resolve(), "canonical plan required")
    require(registered_plan_hash(identifier, root) == sha256_json(plan), "plan unregistered/changed")
    with RunLock(root, stale_seconds=2400):
        ensure_can_run_plan(identifier, root)
        before = verify_manifest(root)
        require(before["ok"], "integrity before execution")
        history = attempt_history(root)
        require(all(r["complete"] for r in history), "unresolved previous attempt; no silent retry")
        require(identifier not in {r["experiment_id"] for r in history}, "attempt already started")
        require(sum(r["fit_seconds_charged"] for r in history)+1200 <= 7200, "aggregate fit reservation exhausted")
        bundle = audit_bundle(plan["candidate"], root)  # Audit BEFORE any random final seed.
        seed = 1103
        if plan["phase"] == "final":
            series = verify_series(root)
            require(plan["series_sha256"] == sha256_json(series), "plan series differs")
            used = {r["seed"] for r in history if r["phase"] == "final"}
            require(len(used) < 3, "three final attempts consumed")
            while seed == 1103 or seed in used:
                seed = 10000 + secrets.randbelow(2147483647-10000+1)
        else:
            require(not (root / SERIES).exists(), "no dev runs after final freeze")
        work = root / "research/tmp" / identifier
        runtime = {"plan": plan, "seed": seed, "audit": bundle, "created_at": utc_now()}
        runtime_path = work / "pc01-runtime.json"
        new_json(runtime_path, runtime)
        append_jsonl(root / ATTEMPTS, {"event": "started", "experiment_id": identifier,
            "created_at": utc_now(), "plan_sha256": sha256_json(plan), "seed": seed,
            "runtime_path": runtime_path.relative_to(root).as_posix(), "runtime_sha256": sha256_json(runtime)})
        state = load_state(root)
        state["active_experiment_id"] = identifier
        save_state(state, root)
        result_path = root / "research/results" / f"{identifier}.json"
        try:
            execution = supervise([sys.executable, "-m", "nextai_autoresearch.pc01_worker", "--runtime", str(runtime_path)], root, work)
            error, measurement = None, None
            output = work / "measurement.json"
            if execution["return_code"] != 0 or execution["termination_reason"]:
                error = execution["termination_reason"] or "worker_crash"
            elif not output.exists():
                error = "worker_missing_output"
            else:
                try:
                    require((work / "fit-granted.json").exists() and (work / "fit-finished.json").exists(),
                            "worker skipped supervised fit")
                    require((work / "device.json").exists(), "missing device measurements")
                    measurement = load_json(output)
                    measurement["resources"] = {k: execution[k] for k in (
                        "fit_seconds", "worker_seconds", "rss_bytes", "cuda_allocated_bytes", "cuda_reserved_bytes",
                        "persisted_bytes", "disk_free_bytes")}
                    validate_measurement(measurement, runtime, root)
                except (ValueError, KeyError, TypeError) as exc:
                    error = f"invalid_worker_output:{exc}"
                    measurement = None  # Keep malformed raw output by hash, not as a valid metric object.
            after = verify_manifest(root)
            try:
                if audit_bundle(plan["candidate"], root) != bundle:
                    error = "source_changed_during_execution"
            except (OSError, ValueError) as exc:
                error = f"source_invalid_after_execution:{exc}"
            if not after["ok"]:
                error = "integrity_after"
            execution["source_audit"] = bundle
            execution["runtime_path"] = runtime_path.relative_to(root).as_posix()
            execution["worker_artifacts"] = {p.name: sha256_file(p) for p in work.iterdir() if p.is_file()}
            result = {"schema_version": 1, "kind": "pc01_diagnostic_result", "experiment_id": identifier,
                      "benchmark": plan["benchmark"], "plan_path": plan_path.relative_to(root).as_posix(), "plan_sha256": sha256_json(plan),
                      "phase": plan["phase"], "started_at": runtime["created_at"], "completed_at": utc_now(),
                      "status": "complete" if error is None else "inconclusive", "runtime_sha256": sha256_json(runtime),
                      "execution": execution, "measurement": measurement, "integrity_before": before,
                      "integrity_after": after, "error": error, "architecture_promoted": False,
                      "pareto_front": [], "candidates": [], "evidence_scope": "local_single_corpus_diagnostic"}
            validate_document("pc01_result", result, root)
            new_json(result_path, result)
            append_jsonl(root / ATTEMPTS, {"event": "finished", "experiment_id": identifier, "created_at": utc_now(),
                "result_sha256": sha256_file(result_path), "fit_seconds_charged": execution["fit_seconds_charged"]})
            state["active_experiment_id"] = None
            state["last_experiment_id"] = identifier
            state["completed_experiments"] += 1
            state["cycle_number"] += 1
            state["updated_at"] = utc_now()
            save_state(state, root)
            return result_path
        except BaseException as exc:
            # Keep start/runtime/supervisor bytes. Unresolved starts block subsequent work.
            append_jsonl(root / "research/events.jsonl", {"event": "pc01_parent_interrupted", "experiment_id": identifier,
                "created_at": utc_now(), "error": f"{type(exc).__name__}: {exc}", "fit_reservation_seconds": 1200})
            raise


def validate_measurement(record: dict, runtime: dict, root: Path) -> None:
    """Dev uses the same strict measurement schema, with only phase-specific fields changed."""
    from copy import deepcopy
    from jsonschema import Draft202012Validator
    from .schemas import load_schema
    from .pc01 import check_resources, choose_checkpoint, precision_gate, validate_timing, CONTROL_NAMES

    plan = runtime["plan"]
    schema = deepcopy(load_schema("pc01_replica", root))
    if plan["benchmark"] == "pc01_byte_lm_learning_measurement_v3":
        schema["properties"]["gpu_metadata"] = {"type": "object"}
        schema["required"].append("gpu_metadata")
    if plan["phase"] == "dev":
        schema["properties"]["phase"] = {"const": "dev"}
        schema["properties"]["seed"] = {"const": 1103}
        schema["properties"]["series_sha256"] = {"type": "null"}
        schema["properties"]["target_count"] = {"const": 55769}
    errors = list(Draft202012Validator(schema).iter_errors(record))
    require(not errors, f"measurement schema: {[e.message for e in errors[:3]]}")
    for key in ("contract_sha256", "data_sha256", "evaluator_sha256", "recipe_sha256", "series_sha256", "phase", "experiment_id"):
        require(record[key] == plan[key], f"measurement plan mismatch: {key}")
    require(record["seed"] == runtime["seed"], "measurement seed mismatch")
    require(record["candidate_sha256"] == runtime["audit"]["sha256"], "measurement source mismatch")
    require(record["status"] == "complete" and record["updates"] == 5000, "unfinished recipe")
    require(record["initial_weights_sha256"] == record["frozen_weights_sha256"] != record["trained_weights_sha256"], "learning/frozen state mismatch")
    require(choose_checkpoint(record["dev_curve"], split="dev")["checkpoint_sha256"] == record["trained_weights_sha256"], "selection mismatch")
    require(set(record["controls"]) == set(CONTROL_NAMES) and all(v is True for v in record["controls"].values()), "control failed")
    for key in ("trained_bpb", "frozen_bpb", "unigram_bpb", "bigram_bpb"):
        require(math.isfinite(record[key]) and record[key] >= 0, "nonfinite/negative measurement")
    check_resources(record["resources"])
    validate_timing(record["timing"])
    precision_gate(record["fp32_dev_bpb"], record["bf16_dev_bpb"])
    if plan["benchmark"] == "pc01_byte_lm_learning_measurement_v3":
        from .pc01_gpu_metadata import validate_pair
        validate_pair(record["gpu_metadata"])
        for stage, snapshot in record["gpu_metadata"].items():
            path = root / "research/tmp" / plan["experiment_id"] / f"gpu-{stage}.json"
            try:
                artifact = load_json(path)
            except OSError as exc:
                raise ValueError("Missing GPU metadata worker artifact") from exc
            require(artifact == snapshot, "GPU metadata differs from its immutable worker artifact")


def authenticated_series_decision(root: Path) -> dict:
    series = verify_series(root)
    history = attempt_history(root)
    final_plans = [p for p in registered_plans(root) if p["phase"] == "final"]
    require(len(final_plans) == 3, "all three registered final attempts required")
    ids = {p["experiment_id"] for p in final_plans}
    final = [r for r in history if r["phase"] == "final"]
    require(len(final) == 3 and {r["experiment_id"] for r in final} == ids and all(r["complete"] for r in final),
            "omitted/unfinished final attempt")
    records = []
    for attempt in final:
        result = load_json(root / "research/results" / f"{attempt['experiment_id']}.json")
        require(result["status"] == "complete" and result["integrity_after"]["ok"], "invalid/crashed final attempt")
        record = result["measurement"]
        require(record["seed"] == attempt["seed"] and record["series_sha256"] == sha256_json(series), "final runtime mismatch")
        runtime = load_json(root / attempt["runtime_path"])
        require(runtime["audit"] == series["audit"], "final source bundle differs from series")
        validate_measurement(record, runtime, root)
        record = {**record, "resources": {k: result["execution"][k] for k in (
            "fit_seconds", "worker_seconds", "rss_bytes", "cuda_allocated_bytes", "cuda_reserved_bytes", "persisted_bytes", "disk_free_bytes")}}
        records.append(record)
    decision = series_decision(records, root=root, cohort=series.get("benchmark", COHORTS[0]))
    return {**decision, "runner_authenticity_checked": True, "scientific_result_created": False}
