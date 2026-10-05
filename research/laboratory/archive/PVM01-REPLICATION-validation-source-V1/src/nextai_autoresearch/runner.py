from __future__ import annotations

import os
import math
import platform
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import psutil

from .audit import AuditResult, audit_candidate
from .baseline_semantics import verify_preflight_certificate, verify_required_baselines
from .config import ResearchConfig, load_config
from .integrity import manifest_path, verify_manifest
from .gates import ensure_can_run_plan
from .ledger import (
    RunLock,
    append_experiment_row,
    append_jsonl,
    append_plan_status,
    latest_plan_statuses,
    load_state,
    registered_plan_hash,
    research_dir,
    save_state,
)
from .metrics import aggregate_trials
from .pareto import is_privileged_candidate, pareto_front
from .comparison_contract import quality_contract, passes_quality
from .schemas import validate_document
from .utils import (
    atomic_write_json,
    load_json,
    project_root,
    relative_posix,
    sha256_file,
    sha256_json,
    utc_now,
)


def _stage_deadline_expired(plan):
    deadline = (plan.get("research_program_protocol") or plan.get("muc02_negatives_protocol", {})).get("deadline_at")
    return bool(deadline and datetime.now(timezone.utc) >= datetime.fromisoformat(deadline.replace("Z", "+00:00")))


def _stage_halt_reason(plan, outcome=None, fit_charged=0.):
    limits = plan.get("research_program_protocol") or plan.get("muc02_negatives_protocol")
    if not limits:
        return None
    if _stage_deadline_expired(plan):
        return "stage_deadline"
    if fit_charged >= limits["fit_seconds_total_cap"]:
        return "total_fit_budget"
    if outcome is not None and outcome.get("status") != "complete":
        return "previous_worker_failure"
    return None


def _git_value(root: Path, *arguments: str) -> str | None:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else None


def environment_fingerprint(root: Path) -> dict[str, Any]:
    memory = psutil.virtual_memory()
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": psutil.cpu_count(logical=True),
        "physical_cpus": psutil.cpu_count(logical=False),
        "ram_bytes": int(memory.total),
        "numpy": np.__version__,
        "git_commit": _git_value(root, "rev-parse", "HEAD"),
        "git_branch": _git_value(root, "branch", "--show-current"),
        "git_dirty": bool(_git_value(root, "status", "--porcelain")),
    }


def _sanitized_environment(root: Path) -> dict[str, str]:
    keep = {
        "COMSPEC",
        "PATH",
        "PATHEXT",
        "PYTHONHOME",
        "PYTHONPATH",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "VIRTUAL_ENV",
        "WINDIR",
    }
    environment = {key: value for key, value in os.environ.items() if key.upper() in keep}
    environment.update(
        {
            "NEXTAI_PROJECT_ROOT": str(root),
            "PYTHONHASHSEED": "0",
            "PYTHONIOENCODING": "utf-8",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        }
    )
    return environment


def _rss_tree(process: psutil.Process) -> int:
    total = 0
    try:
        items = [process, *process.children(recursive=True)]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0
    for item in items:
        try:
            total += int(item.memory_info().rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return total


def _terminate_tree(process: psutil.Process) -> None:
    try:
        children = process.children(recursive=True)
    except psutil.NoSuchProcess:
        return
    except psutil.AccessDenied:
        children = []
    for child in reversed(children):
        try:
            child.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    try:
        process.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    _, alive = psutil.wait_procs([*children, process], timeout=2.0)
    for item in alive:
        try:
            item.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def _apply_dronepropa_comparisons(
    candidate_results: list[dict[str, Any]], protocol: dict[str, Any]
) -> None:
    complete = {
        str(item["candidate"]): item
        for item in candidate_results
        if item.get("status") == "complete"
    }
    reference_names = [
        str(protocol["independent_ablation"]), str(protocol["no_sharing_ablation"])
    ]
    support_name = str(protocol.get(
        "privileged_support_control", "privileged_same_condition_oracle_arx_v2"
    ))
    if any(name not in complete for name in [*reference_names, support_name]):
        return

    def keyed(item: dict[str, Any]) -> dict[tuple[int, int, int], dict[str, Any]]:
        return {
            (int(row["seed"]), int(row["knowledge_size"]), int(row["reasoning_depth"])): row
            for row in item.get("trials", []) if row.get("status") == "complete"
        }

    references = [keyed(complete[name]) for name in reference_names]
    support = keyed(complete[support_name])
    for item in complete.values():
        for key, trial in keyed(item).items():
            if key not in support or any(key not in rows for rows in references):
                continue
            condition_gains: list[float] = []
            trajectory_gains: list[float] = []
            for rows in references:
                reference = rows[key]
                for group, target in (
                    ("condition_nrmse", condition_gains),
                    ("trajectory_nrmse", trajectory_gains),
                ):
                    candidate_values = trial.get(group, {})
                    reference_values = reference.get(group, {})
                    target.extend(
                        float(reference_values[name]) - float(candidate_values[name])
                        for name in candidate_values.keys() & reference_values.keys()
                    )
            trial["minimum_condition_transfer_gain"] = (
                min(condition_gains) if condition_gains else None
            )
            trial["minimum_trajectory_transfer_gain"] = (
                min(trajectory_gains) if trajectory_gains else None
            )
            independent = float(references[0][key]["normalized_rmse"])
            support_nrmse = float(support[key]["normalized_rmse"])
            if "privileged_support_control" in protocol:
                trial["privileged_support_gain"] = support_nrmse - float(trial["normalized_rmse"])
            else:
                denominator = independent - support_nrmse
                trial["oracle_gap_closed"] = (
                    (independent - float(trial["normalized_rmse"])) / denominator
                    if abs(denominator) > 1e-12 else None
                )
        item["summary"] = aggregate_trials(item.get("trials", []))


def _apply_continuous_transfer_comparisons(
    candidate_results: list[dict[str, Any]], protocol: dict[str, Any]
) -> None:
    complete = {str(row["candidate"]): row for row in candidate_results
                if row.get("status") == "complete"}
    names = [str(protocol[key]) for key in (
        "shared_candidate", "independent_ablation",
        "cross_family_only_ablation", "support_only_ablation",
    )]
    if any(name not in complete for name in names):
        return

    def keyed(item: dict[str, Any]) -> dict[tuple[str, int, int, int], dict[str, Any]]:
        return {(str(row["world_family"]), int(row["seed"]),
                 int(row["knowledge_size"]), int(row["reasoning_depth"])): row
                for row in item.get("trials", ()) if row.get("status") == "complete"}

    shared, independent, cross, support = (keyed(complete[name]) for name in names)
    if not (shared.keys() == independent.keys() == cross.keys() == support.keys()):
        return
    for key in shared:
        shared[key]["shared_vs_independent_gain"] = (
            float(independent[key]["normalized_rmse"]) - float(shared[key]["normalized_rmse"])
        )
        cross[key]["cross_family_transfer_gain"] = (
            float(support[key]["normalized_rmse"]) - float(cross[key]["normalized_rmse"])
        )
    for name in names:
        complete[name]["summary"] = aggregate_trials(complete[name].get("trials", []))


def _apply_suitesparse_transfer_comparisons(
    candidate_results: list[dict[str, Any]], protocol: dict[str, Any]
) -> None:
    complete = {str(row["candidate"]): row for row in candidate_results
                if row.get("status") == "complete"}
    names = [str(protocol[key]) for key in (
        "shared_candidate", "independent_ablation",
        "cross_family_only_ablation", "support_only_ablation",
    )]
    if any(name not in complete for name in names):
        return

    def keyed(item: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
        return {(str(row["world_family"]), int(row["seed"])): row
                for row in item.get("trials", ()) if row.get("status") == "complete"}

    shared, independent, cross, support = (keyed(complete[name]) for name in names)
    if not (shared.keys() == independent.keys() == cross.keys() == support.keys()):
        return
    for key in shared:
        shared[key]["shared_vs_independent_gain"] = (
            float(independent[key]["relative_residual"])
            - float(shared[key]["relative_residual"])
        )
        cross[key]["cross_family_transfer_gain"] = (
            float(support[key]["relative_residual"])
            - float(cross[key]["relative_residual"])
        )
    for name in names:
        complete[name]["summary"] = aggregate_trials(complete[name].get("trials", []))


def _run_candidate(
    candidate: str,
    plan_path: Path,
    plan: dict[str, Any],
    config: ResearchConfig,
    root: Path,
    audit: AuditResult | None = None,
) -> dict[str, Any]:
    audit = audit or audit_candidate(candidate, config, root)
    audit_payload = {
        "ok": audit.ok,
        "path": relative_posix(audit.path, root),
        "sha256": audit.sha256,
        "problems": list(audit.problems),
        "dependencies": [
            {"path": relative_posix(path, root), "sha256": digest}
            for path, digest in audit.dependencies
        ],
    }
    if not audit.ok:
        return {
            "candidate": candidate,
            "status": "audit_failed",
            "audit": audit_payload,
            "execution": None,
            "trials": [],
            "summary": {"status": "failed", "completed_trials": 0, "total_trials": 0},
        }

    budget = config.budget(plan["budget"])
    temporary = research_dir(root) / "tmp" / plan["experiment_id"]
    temporary.mkdir(parents=True, exist_ok=True)
    output_path = temporary / f"{candidate}.json"
    if output_path.exists():
        output_path.unlink()
    log_path = research_dir(root) / "logs" / f"{plan['experiment_id']}-{candidate}.log"
    command = [
        sys.executable,
        "-m",
        "nextai_autoresearch.worker",
        "--plan",
        str(plan_path),
        "--candidate",
        candidate,
        "--output",
        str(output_path),
    ]
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    started = time.monotonic()
    peak_rss = 0
    termination_reason: str | None = None
    from .worker import read_trial_journal
    from .worker_resources import resource_problem
    limits = plan.get("research_program_protocol") or plan.get("muc02_negatives_protocol") or plan.get("muc02_protocol", {})
    device_gap_started = started
    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        process = None
        monitored = None
        return_code = None
        try:
            if any((root / name).exists() for name in ("STOP", "PAUSE")) or _stage_deadline_expired(plan):
                termination_reason = "stopped"
            else:
                process = subprocess.Popen(
                    command, cwd=temporary, env=_sanitized_environment(root),
                    stdout=log, stderr=subprocess.STDOUT, creationflags=creation_flags,
                )
                try:
                    monitored = psutil.Process(process.pid)
                except psutil.NoSuchProcess:
                    # A short worker may finish before attachment; its output
                    # and exit code still determine the outcome.
                    process.wait(timeout=5)
                while process.poll() is None:
                    elapsed = time.monotonic() - started
                    peak_rss = max(peak_rss, _rss_tree(monitored))
                    if any((root / name).exists() for name in ("STOP", "PAUSE")) or _stage_deadline_expired(plan):
                        termination_reason = "stopped"
                    elif elapsed > min(budget.wall_seconds_per_candidate, limits.get("worker_seconds_cap", float("inf"))):
                        termination_reason = "timeout"
                    elif peak_rss > min(budget.max_rss_mb * 1024 * 1024, limits.get("max_rss_bytes", float("inf"))):
                        termination_reason = "memory_limit"
                    elif limits:
                        termination_reason, device_gap_started = resource_problem(output_path, limits, started, device_gap_started)
                    if termination_reason:
                        _terminate_tree(monitored)
                        break
                    time.sleep(float(config.raw["execution"]["poll_interval_seconds"]))
                return_code = process.wait(timeout=5)
        finally:
            if process is not None and process.poll() is None:
                if monitored is not None:
                    _terminate_tree(monitored)
                else:
                    process.terminate()
                process.wait(timeout=5)
    elapsed = time.monotonic() - started

    execution = {
        "return_code": return_code,
        "wall_seconds": elapsed,
        "peak_rss_bytes": peak_rss,
        "termination_reason": termination_reason,
        "log_path": relative_posix(log_path, root),
        "environment_sanitized": True,
        "network_policy": "forbidden_by_audit_and_rules_not_os_sandboxed",
    }
    if limits.get("compute_charge_basis") == "full_worker_wall_v1":
        execution["research_compute_seconds"] = elapsed
        execution["research_compute_charge_basis"] = "full_worker_wall_v1"
    if plan.get("research_program_protocol") or plan.get("muc02_negatives_protocol"):
        try:
            phase = load_json(output_path.with_suffix(".phase.json"))
            charged = (time.monotonic() - phase["fit_started"] if phase["phase"] == "fit"
                       else float(phase["fit_elapsed"]))
            if not math.isfinite(charged) or charged < 0:
                raise ValueError("Invalid final fit phase")
            execution["supervised_fit_seconds"] = charged
        except (OSError, ValueError, TypeError, KeyError):
            execution["supervised_fit_seconds"] = limits["fit_seconds_cap"]
            execution["fit_charge_conservative"] = True
    if termination_reason is not None:
        preserved = read_trial_journal(output_path)
        return {
            "candidate": candidate,
            "status": termination_reason,
            "audit": audit_payload,
            "execution": execution,
            "trials": preserved,
            "summary": {**aggregate_trials(preserved), "status": "partial" if preserved else "failed"},
        }
    if not output_path.is_file():
        return {
            "candidate": candidate,
            "status": "crash",
            "audit": audit_payload,
            "execution": execution,
            "trials": [],
            "summary": {"status": "failed", "completed_trials": 0, "total_trials": 0},
        }
    worker_output = load_json(output_path)
    if return_code != 0 and worker_output.get("status") == "complete":
        worker_output["status"] = "crash"
        worker_output["error"] = "Worker reported complete but exited unsuccessfully"
    if worker_output.get("candidate") != candidate:
        raise ValueError("Worker output candidate identity mismatch")
    return {
        "candidate": candidate,
        "status": worker_output.get("status", "crash"),
        "audit": audit_payload,
        "execution": execution,
        "trials": worker_output.get("trials", []),
        "summary": worker_output.get("summary", {}),
        "error_type": worker_output.get("error_type"),
        "error": worker_output.get("error"),
        "traceback": worker_output.get("traceback"),
    }


def _frontier(
    candidate_results: list[dict[str, Any]],
    plan: dict[str, Any],
    config: ResearchConfig,
) -> tuple[list[str], dict[str, list[str]]]:
    minimum_accuracy = float(config.raw["decision"]["minimum_screen_accuracy"])
    directions = plan.get("metric_directions", {})
    protocol = (
        plan.get("suitesparse_transfer_protocol", {})
        or plan.get("continuous_transfer_protocol", {})
        or plan.get("wt_prequential_protocol", {})
        or plan.get("mechanism_recombination_protocol", {})
        or plan.get("compression_protocol", {})
        or plan.get("continuous_local_protocol", {})
        or plan.get("active_sensor_protocol", {})
        or plan.get("whole_io_search_protocol", {})
    )
    primary_metrics = list(
        protocol.get("pareto_capability_metrics", plan.get("primary_metrics", ()))
    )
    if directions:
        maximize_requested = [
            metric for metric in primary_metrics if directions.get(metric) == "maximize"
        ]
        minimize_requested = [
            metric for metric in primary_metrics if directions.get(metric) == "minimize"
        ]
    else:
        maximize_requested = [
            metric
            for metric in config.raw["metrics"]["maximize"]
            if metric in primary_metrics
        ]
        minimize_requested = [
            metric
            for metric in config.raw["metrics"]["minimize"]
            if metric in primary_metrics
        ]
    maximize, minimize = maximize_requested, minimize_requested
    required = [*maximize, *minimize]
    rows: list[dict[str, Any]] = []
    for candidate in candidate_results:
        summary = candidate.get("summary", {})
        if candidate.get("status") != "complete" or summary.get("status") != "complete":
            continue
        missing = [metric for metric in required if summary.get(metric) is None]
        complete_trials = [
            trial for trial in candidate.get("trials", ())
            if trial.get("status") == "complete"
        ]
        aggregation_losses = [
            metric for metric in missing
            if complete_trials
            and all(trial.get(metric) is not None for trial in complete_trials)
        ]
        if aggregation_losses:
            raise RuntimeError(
                f"Complete summary for {candidate['candidate']} omitted declared "
                f"Pareto metrics present in every raw trial: {aggregation_losses}"
            )
        if missing or is_privileged_candidate(str(candidate["candidate"])):
            continue
        if not passes_quality(summary, quality_contract(plan, minimum_accuracy)):
            continue
        rows.append({"candidate": candidate["candidate"], **summary})
    front = (
        [
            str(row["candidate"])
            for row in pareto_front(rows, maximize, minimize)
        ]
        if maximize or minimize
        else []
    )
    return front, {"maximize": maximize, "minimize": minimize}


def _realize_evaluation_matrix(plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    matrix = dict(plan["matrix"])
    policy = matrix.pop("seed_policy", None)
    if policy is None:
        return matrix, None
    if policy.get("method") != "runner_random_v1":
        raise ValueError(f"Unsupported scoring seed policy: {policy!r}")
    minimum = int(policy["minimum"])
    maximum = int(policy["maximum"])
    count = int(policy["count"])
    if maximum < minimum or maximum - minimum + 1 < count:
        raise ValueError("Scoring seed policy range cannot supply unique seeds")
    matrix["seeds"] = secrets.SystemRandom().sample(
        range(minimum, maximum + 1), count
    )
    return matrix, dict(policy)


def _worker_artifacts(base: Path, experiment_id: str) -> list[dict[str, str]]:
    directory = research_dir(base) / "tmp" / experiment_id
    return [
        {"path": relative_posix(path, base), "sha256": sha256_file(path)}
        for path in sorted(directory.glob("*.json"))
        if path.name != "runtime-plan.json" and not path.name.endswith(".supervisor.json")
    ]


def _supervisor_artifacts(base: Path, experiment_id: str) -> list[dict[str, str]]:
    directory = research_dir(base) / "tmp" / experiment_id
    return [
        {"path": relative_posix(path, base), "sha256": sha256_file(path)}
        for path in sorted(directory.glob("*.supervisor.json"))
    ]


def _append_postseed_event(base: Path, event: dict[str, Any]) -> None:
    append_jsonl(research_dir(base) / "events.jsonl", event)


def run_experiment(plan_path: Path, root: Path | None = None) -> Path:
    base = (root or project_root()).resolve()
    plan_path = plan_path.resolve()
    config = load_config(base)
    plan = load_json(plan_path)
    if plan.get("kind") == "pc01_diagnostic_plan":
        from .pc01_execution import run_diagnostic
        return run_diagnostic(plan_path, base)
    validate_document("experiment_plan", plan, base)
    ensure_can_run_plan(str(plan["experiment_id"]), base)
    if plan["benchmark"] != config.benchmark_version:
        raise ValueError("Plan benchmark does not match the active benchmark cohort")
    plan_digest = sha256_json(plan)
    registered = registered_plan_hash(plan["experiment_id"], base)
    if registered is None:
        raise ValueError("Plan is not preregistered in research/plan_registry.jsonl")
    if registered != plan_digest:
        raise ValueError("Plan changed after preregistration")
    expected_evaluator = plan.get("evaluator_sha256")
    current_evaluator = load_json(manifest_path(base)).get("evaluator_sha256")
    if "seed_policy" in plan.get("matrix", {}) and not expected_evaluator:
        raise ValueError("Protocol-v2 plan has no evaluator digest commitment")
    if expected_evaluator is not None and expected_evaluator != current_evaluator:
        raise ValueError(
            "Evaluator changed after preregistration; invalidate this plan and create a new one"
        )
    result_path = research_dir(base) / "results" / f"{plan['experiment_id']}.json"
    if result_path.exists():
        raise FileExistsError(f"Result already exists: {result_path}")
    integrity_before = verify_manifest(base)
    if not integrity_before["ok"]:
        raise RuntimeError(f"Evaluation integrity check failed: {integrity_before['problems']}")

    # This gate executes registered semantic fixtures before any scoring seed exists.
    verify_required_baselines(plan, base, run_tests=True)
    verify_preflight_certificate(base)
    if (
        str(plan["benchmark"]).startswith("heldout_dronepropa_")
        and isinstance(plan.get("dronepropa_protocol"), dict)
    ):
        benchmark = __import__(
            f"nextai_autoresearch.benchmarks.{plan['benchmark']}",
            fromlist=["verify_corpus_hashes"],
        )
        benchmark.verify_corpus_hashes(base)

    stale_seconds = int(config.raw["execution"]["stale_lock_seconds"])
    started_at = utc_now()
    with RunLock(base, stale_seconds=stale_seconds):
        # Repeat terminality under the lock: another run can finish while we wait.
        ensure_can_run_plan(str(plan["experiment_id"]), base)
        if result_path.exists():
            raise FileExistsError(f"Result already exists: {result_path}")
        if registered_plan_hash(plan["experiment_id"], base) != plan_digest:
            raise ValueError("Plan registration changed before lock acquisition")
        state = load_state(base)
        if state.get("active_experiment_id") not in (None, plan["experiment_id"]):
            raise RuntimeError(
                f"State already has active experiment {state['active_experiment_id']}"
            )
        state["active_experiment_id"] = plan["experiment_id"]
        state["updated_at"] = utc_now()
        save_state(state, base)

        evaluation_matrix: dict[str, Any] | None = None
        scoring_seed_policy: dict[str, Any] | None = None
        runtime_plan_path = (
            research_dir(base) / "tmp" / plan["experiment_id"] / "runtime-plan.json"
        )
        candidate_results: list[dict[str, Any]] = []
        try:
            audits = {
                candidate: audit_candidate(candidate, config, base)
                for candidate in plan["candidates"]
            }
            evaluation_matrix, scoring_seed_policy = _realize_evaluation_matrix(plan)
            runtime_plan = {**plan, "matrix": evaluation_matrix}
            if plan["benchmark"] in ("paired_view_mutable_memory_v1", "paired_view_mutable_memory_v2", "paired_view_mutable_memory_v3", "paired_view_mutable_memory_v4", "paired_view_mutable_memory_v5", "paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7"):
                private_path = runtime_plan_path.parent / "pvm01-private-data.json"
                if private_path.exists():
                    raise FileExistsError("Private data realization already exists; no retry")
                unit_nonces = [secrets.token_hex(32) for _ in evaluation_matrix["seeds"]]
                if plan["benchmark"] in {"paired_view_mutable_memory_v3", "paired_view_mutable_memory_v4", "paired_view_mutable_memory_v5", "paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7"}:
                    from .research_program import verify_pvm01_fresh_realization
                    if plan["benchmark"] == "paired_view_mutable_memory_v7":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True, include_transport=True)
                    elif plan["benchmark"] == "paired_view_mutable_memory_v6":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True)
                    else:
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces)
                atomic_write_json(private_path, {"experiment_id": plan["experiment_id"],
                    "unit_nonces": unit_nonces,
                    "entropy_policy": "independent256bit_each_unit_separate_from_model_seed_v1"})
                runtime_plan.update(pvm01_private_data_path=str(private_path), pvm01_private_data_sha256=sha256_file(private_path))
            atomic_write_json(runtime_plan_path, runtime_plan)
            _append_postseed_event(
                base,
                {
                    "event": "experiment_scoring_started",
                    "experiment_id": plan["experiment_id"],
                    "hypothesis_id": plan["hypothesis_id"],
                    "created_at": utc_now(),
                    "plan_sha256": plan_digest,
                    "scoring_seed_policy": scoring_seed_policy,
                    "scoring_seeds": list(evaluation_matrix["seeds"]),
                    "runtime_plan_path": relative_posix(runtime_plan_path, base),
                    "runtime_plan_sha256": sha256_file(runtime_plan_path),
                    "scientific_evidence": False,
                },
            )
            fit_charged, halt_reason = 0., None
            for candidate in plan["candidates"]:
                halt_reason = halt_reason or _stage_halt_reason(plan, fit_charged=fit_charged)
                if halt_reason:
                    outcome = {"candidate": candidate, "status": "stopped", "audit": {"ok": audits[candidate].ok},
                               "execution": {"started": False, "wall_seconds": 0., "peak_rss_bytes": 0,
                                             "supervised_fit_seconds": 0., "termination_reason": halt_reason, "return_code": None},
                               "trials": [], "summary": {"status": "failed", "completed_trials": 0, "total_trials": 0},
                               "error": "Not started: finite stage stops at first failure/deadline/budget; no retry"}
                else:
                    outcome = _run_candidate(candidate, runtime_plan_path, runtime_plan, config, base, audits[candidate])
                    execution = outcome.get("execution") or {}
                    fit_charged += execution.get("research_compute_seconds", execution.get("supervised_fit_seconds", 0.))
                    halt_reason = _stage_halt_reason(plan, outcome, fit_charged)
                candidate_results.append(outcome)
                atomic_write_json(
                    runtime_plan_path.parent / f"{candidate}.supervisor.json", outcome
                )
            if (
                str(plan["benchmark"]).startswith("heldout_dronepropa_")
                and isinstance(plan.get("dronepropa_protocol"), dict)
            ):
                _apply_dronepropa_comparisons(
                    candidate_results, dict(plan["dronepropa_protocol"])
                )
            if isinstance(plan.get("continuous_transfer_protocol"), dict):
                _apply_continuous_transfer_comparisons(
                    candidate_results, dict(plan["continuous_transfer_protocol"])
                )
            if isinstance(plan.get("suitesparse_transfer_protocol"), dict):
                _apply_suitesparse_transfer_comparisons(
                    candidate_results, dict(plan["suitesparse_transfer_protocol"])
                )
            integrity_after = verify_manifest(base)
            if integrity_after["ok"]:
                frontier, pareto_metrics = _frontier(candidate_results, plan, config)
            else:
                frontier, pareto_metrics = [], {"maximize": [], "minimize": []}
            oracle_controls = [
                item["candidate"]
                for item in candidate_results
                if is_privileged_candidate(str(item["candidate"]))
                and item.get("status") == "complete"
            ]
            candidate_statuses = {item["status"] for item in candidate_results}
            if not integrity_after["ok"]:
                status = "invalid_integrity"
            elif candidate_statuses == {"complete"}:
                status = "complete"
            elif "complete" in candidate_statuses:
                status = "complete_with_failures"
            else:
                status = "failed"
            result = {
                "schema_version": 1,
                "experiment_id": plan["experiment_id"],
                "hypothesis_id": plan["hypothesis_id"],
                "plan_path": relative_posix(plan_path, base),
                "plan_sha256": plan_digest,
                "benchmark": plan["benchmark"],
                "evaluator_sha256": current_evaluator,
                "budget": plan["budget"],
                "started_at": started_at,
                "completed_at": utc_now(),
                "status": status,
                "integrity_before": integrity_before,
                "integrity_after": integrity_after,
                "environment": environment_fingerprint(base),
                "evaluation_matrix": evaluation_matrix,
                "scoring_seed_policy": scoring_seed_policy,
                "candidates": candidate_results,
                "pareto_front": frontier,
                "pareto_front_implementable": frontier,
                "oracle_controls": oracle_controls,
                "pareto_metrics": pareto_metrics,
                "interpretation_status": "pending_codex_analysis",
            }
            validate_document("experiment_result", result, base)
            atomic_write_json(result_path, result, compact=plan["benchmark"] in {"paired_view_mutable_memory_v3", "paired_view_mutable_memory_v4", "paired_view_mutable_memory_v5", "paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7"})
            for candidate in candidate_results:
                summary = candidate.get("summary", {})
                append_experiment_row(
                    {
                        "experiment_id": plan["experiment_id"],
                        "hypothesis_id": plan["hypothesis_id"],
                        "candidate": candidate["candidate"],
                        "budget": plan["budget"],
                        "status": candidate["status"],
                        "accuracy": summary.get("accuracy", ""),
                        "mean_query_ops": summary.get("mean_query_ops", ""),
                        "p95_latency_us": summary.get("p95_latency_us", ""),
                        "state_bytes": summary.get("state_bytes", ""),
                        "knowledge_compute_slope": summary.get(
                            "knowledge_compute_slope", ""
                        ),
                        "depth_compute_slope": summary.get("depth_compute_slope", ""),
                        "integrity_ok": integrity_after["ok"],
                        "plan_sha256": plan_digest,
                        "result_path": relative_posix(result_path, base),
                        "created_at": result["completed_at"],
                    },
                    base,
                )
            state["active_experiment_id"] = None
            state["last_experiment_id"] = plan["experiment_id"]
            state["cycle_number"] = int(state.get("cycle_number", 0)) + 1
            state["completed_experiments"] = int(
                state.get("completed_experiments", 0)
            ) + 1
            state["updated_at"] = utc_now()
            save_state(state, base)
            return result_path
        except BaseException as exc:
            recording_error: Exception | None = None
            try:
                if evaluation_matrix is not None and runtime_plan_path.is_file():
                    _append_postseed_event(
                        base,
                        {
                            "event": "experiment_runner_postseed_failure",
                            "experiment_id": plan["experiment_id"],
                            "hypothesis_id": plan["hypothesis_id"],
                            "created_at": utc_now(),
                            "plan_sha256": plan_digest,
                            "scoring_seeds": list(evaluation_matrix["seeds"]),
                            "runtime_plan_path": relative_posix(runtime_plan_path, base),
                            "runtime_plan_sha256": sha256_file(runtime_plan_path),
                            "worker_artifacts": _worker_artifacts(
                                base, str(plan["experiment_id"])
                            ),
                            "supervisor_artifacts": _supervisor_artifacts(
                                base, str(plan["experiment_id"])
                            ),
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                            "result_written": result_path.is_file(),
                            "scientific_evidence": False,
                        },
                    )
                    if (
                        not result_path.is_file()
                        and plan["experiment_id"] not in latest_plan_statuses(base)
                    ):
                        append_plan_status(
                            str(plan["experiment_id"]),
                            "invalidated",
                            "Automatic terminal invalidation after a post-seed runner "
                            f"failure ({type(exc).__name__}): {exc}",
                            base,
                        )
            except Exception as persistence_exc:
                recording_error = persistence_exc
            finally:
                state = load_state(base)
                state["active_experiment_id"] = None
                state["last_failure_at"] = utc_now()
                state["updated_at"] = utc_now()
                save_state(state, base)
            if recording_error is not None:
                raise RuntimeError(
                    f"Runner failed and failure recording also failed: {recording_error}"
                ) from exc
            raise
