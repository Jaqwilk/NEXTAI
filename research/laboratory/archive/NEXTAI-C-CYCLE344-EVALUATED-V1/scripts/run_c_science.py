"""The sole C scientific registration and execution, with immutable receipts."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
import traceback

import nextai_autoresearch
from nextai_autoresearch import research_program_c as c
from nextai_autoresearch.ledger import read_jsonl, append_plan_status, latest_plan_statuses
from nextai_autoresearch.research_program import create_plan
from nextai_autoresearch.runner import run_experiment
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now

STUDY = "research/plans/ASM01-C-STABILIZED-SCREEN-V1.json"
STUDY_SHA256 = "297357e54f271bebe8fdf8da0d6a31c6d2c7a3fea5251ad9f1008eb9b26b8c1d"


def _valid_seconds(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def worker_costs(root, identity):
    """Use completed supervisor receipts, including every partial worker."""
    rows = []
    try:
        if identity:
            result = root / "research/results" / f"{identity}.json"
            if result.is_file():
                rows = load_json(result)["candidates"]
            else:
                rows = [load_json(path) for path in sorted(
                    (root / "research/tmp" / identity).glob("*.supervisor.json"))]
        if not isinstance(rows, list):
            raise ValueError("Invalid C worker collection")
    except (OSError, ValueError, TypeError, KeyError):
        raise ValueError("C worker collection is missing or malformed") from None
    if identity and not rows:
        raise ValueError("Registered C execution has no worker receipts")
    worker, fit = 0., 0.
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("execution"), dict):
            raise ValueError("C worker receipt lacks its execution record")
        execution = row["execution"]
        if execution.get("started") is False:
            continue
        full = execution.get("research_compute_seconds", execution.get("wall_seconds"))
        supervised = execution.get("supervised_fit_seconds")
        if not _valid_seconds(full) or not _valid_seconds(supervised) or supervised > full:
            raise ValueError("C worker accounting has invalid or missing trusted telemetry")
        worker += full
        fit += supervised
    return worker, fit, len(rows)


def main():
    root = Path(__file__).resolve().parents[1]
    if root.name != "NEXTAI-VALIDATION-20261002" or not Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src"):
        raise ValueError("Science requires the independent clone and its actual imports")
    if sha256_file(root / STUDY) != STUDY_SHA256:
        raise ValueError("Frozen C scientific study changed")
    current = c.status(root)
    if (not current or current["study_path"] != STUDY or not current["scoring_authorized"]
            or current["registration_attempts_used"] or current["program_terminal"]):
        raise ValueError("Sole C attempt requires every release gate and unused scientific ticket")
    if (root / "STOP").exists() or (root / "PAUSE").exists():
        raise ValueError("C scientific execution is stopped")
    prefix = root / "research/reviews/NEXTAI-C-SCIENCE-V1"
    marker = Path(str(prefix) + ".started.json")
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump({"created_at": utc_now(), "pid": os.getpid(), "study_path": STUDY,
            "study_sha256": STUDY_SHA256, "paid_retry_authorized": False}, handle)
        handle.write("\n")
    started = time.monotonic()
    spans, identity, result_path, error = {}, None, None, None
    worker_started = None
    worker_interval = 0.
    try:
        phase_started = time.monotonic()
        print(json.dumps({"phase": "registration_started", "created_at": utc_now()}), flush=True)
        try:
            plan_path = create_plan(root)
            identity = plan_path.stem
        finally:
            spans["registration_seconds"] = time.monotonic() - phase_started
        print(json.dumps({"phase": "registered", "experiment_id": identity, "seconds": spans["registration_seconds"]}), flush=True)
        worker_started = time.monotonic()
        try:
            result_path = run_experiment(plan_path, root)
        finally:
            worker_interval = time.monotonic() - worker_started
            spans["runner_inclusive_seconds"] = worker_interval
        if load_json(result_path)["status"] != "complete":
            raise RuntimeError("Incomplete C scientific outcome; preserve partials and do not retry")
    except BaseException:
        error = traceback.format_exc()
    finally:
        try:
            events = read_jsonl(root / c.EVENTS)
            registered = [row for row in events if row["event"] == "registered"]
            if identity is None and len(registered) == 1:
                identity = registered[0]["experiment_id"]
        except BaseException:
            error = (error or "") + "\nRegistration discovery failure:\n" + traceback.format_exc()
    worker, fit, rows, recovery, telemetry_error = 0., 0., 0, 0., None
    cost_recorded, cost_digest = False, None
    if identity:
        try:
            if worker_started is not None:
                worker, fit, rows = worker_costs(root, identity)
        except BaseException:
            telemetry_error = traceback.format_exc()
            error = (error or "") + "\nWorker telemetry failure:\n" + telemetry_error
        missing_coverage = telemetry_error is not None or (error and worker_started is not None
            and (rows < 45
                 or not (root / "research/results" / f"{identity}.json").is_file()))
        recovery = max(0., worker_interval - worker) if missing_coverage else 0.
        # The uncovered failed interval is an upper bound, including possibly
        # pre-seed gates. It is never described as measured supervised fitting.
        worker += recovery
        fit += recovery
        try:
            cost_path = "research/reviews/NEXTAI-C-SCIENCE-V1.cost.json"
            if (root / cost_path).exists():
                raise FileExistsError("Earlier scientific cost receipt cannot be overwritten")
            atomic_write_json(root / cost_path, {**c._binding(), **c._study_binding(read_jsonl(root / c.EVENTS)),
                "experiment_id": identity, "full_worker_seconds": worker,
                "supervised_fit_seconds": fit, "supervisor_rows": rows,
                "conservative_uncovered_failed_runner_seconds": recovery,
                "recovery_is_upper_bound_not_measured_supervised_fit": bool(recovery),
                "telemetry_error": telemetry_error, "nested_in_C_outer_wall": True})
            c.record_scientific_cost(root, cost_path)
            cost_digest = sha256_file(root / cost_path)
            cost_recorded = True
        except BaseException:
            error = (error or "") + "\nScientific cost bookkeeping failure:\n" + traceback.format_exc()
        try:
            if error and not (root / "research/results" / f"{identity}.json").exists() and identity not in latest_plan_statuses(root):
                append_plan_status(identity, "invalidated", "C scientific execution failed before complete result; paid retry forbidden", root)
        except BaseException:
            error = (error or "") + "\nPlan terminalization failure:\n" + traceback.format_exc()
    receipt = {"created_at": utc_now(), "program_id": c.PROGRAM_ID,
        "contract_sha256": c.CONTRACT_SHA256, "study_path": STUDY, "study_sha256": STUDY_SHA256,
        "experiment_id": identity, "package_origin": nextai_autoresearch.__file__,
        "controller_wall_seconds": time.monotonic() - started, "spans": spans,
        "full_worker_seconds": worker, "supervised_fit_seconds": fit,
        "conservative_uncovered_failed_runner_seconds": recovery,
        "result_path": result_path.relative_to(root).as_posix() if result_path else None,
        "error": error, "paid_retry_authorized": False, "whole_goal_complete": False,
        "cost_recorded": cost_recorded,
        "cost_receipt_path": "research/reviews/NEXTAI-C-SCIENCE-V1.cost.json" if cost_recorded else None,
        "cost_receipt_sha256": cost_digest,
        "costs_are_nested_in_C_outer_wall": True}
    path = Path(str(prefix) + ".receipt.json")
    if path.exists():
        raise FileExistsError("Earlier scientific receipt cannot be overwritten")
    atomic_write_json(path, receipt)
    if identity and cost_recorded:
        try:
            c.mark_scientific_finished(root, path.relative_to(root).as_posix())
        except BaseException:
            terminal_error = traceback.format_exc()
            atomic_write_json(Path(str(prefix) + ".terminalization-error.json"), {
                "created_at": utc_now(), "receipt_sha256": sha256_file(path), "error": terminal_error,
                "paid_retry_authorized": False, "whole_goal_complete": False})
            error = (error or "") + terminal_error
    print(json.dumps(receipt), flush=True)
    return 0 if not error and result_path else 1


if __name__ == "__main__":
    raise SystemExit(main())
