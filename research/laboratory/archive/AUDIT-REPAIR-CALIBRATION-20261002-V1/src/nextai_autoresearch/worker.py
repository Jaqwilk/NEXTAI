from __future__ import annotations

import argparse
import importlib
import inspect
import json
import traceback
from pathlib import Path

from .metrics import aggregate_trials
from .utils import atomic_write_json, load_json, utc_now
from .ledger import append_jsonl
from .data_access import install_data_access_guard


def trial_journal_path(output_path: Path) -> Path:
    return output_path.with_suffix(".trials.jsonl")


def read_trial_journal(output_path: Path) -> list[dict]:
    path = trial_journal_path(output_path)
    if not path.exists():
        return []
    rows = []
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for index, line in enumerate(lines):
        try:
            value = json.loads(line)
        except ValueError:
            if index == len(lines) - 1 and not line.endswith("\n"):
                break  # Only a torn final append may be ignored.
            raise
        if not isinstance(value, dict):
            raise ValueError("Trial journal contains a non-object record")
        rows.append(value)
    return rows


def run_worker(plan_path: Path, candidate: str, output_path: Path) -> int:
    install_data_access_guard()
    trials = []
    resources = None
    try:
        plan = load_json(plan_path)
        benchmark_name = plan["benchmark"]
        benchmark = importlib.import_module(f".benchmarks.{benchmark_name}", __package__)
        if benchmark.BENCHMARK_VERSION != benchmark_name:
            raise ValueError("Benchmark module/version mismatch")
        options = {}
        parameters = inspect.signature(benchmark.run_suite).parameters
        if "trial_sink" in parameters:
            journal = trial_journal_path(output_path)
            if journal.exists():
                raise FileExistsError("Existing trial journal; worker retry is forbidden")
            options["trial_sink"] = lambda trial: append_jsonl(journal, trial)
        if plan.get("muc02_protocol"):
            from .worker_resources import WorkerResources
            resources = WorkerResources(output_path, plan["muc02_protocol"], plan_path)
            resources.start()
            options["phase_sink"] = resources.phase
        trials = benchmark.run_suite(candidate, plan, **options)
        if resources:
            resources.check()
        output = {
            "candidate": candidate,
            "status": "complete",
            "created_at": utc_now(),
            "trials": trials,
            "summary": aggregate_trials(trials),
        }
        atomic_write_json(output_path, output)
        return 0
    except Exception as exc:  # The parent records a structured crash outcome.
        preserved = read_trial_journal(output_path) or trials
        output = {
            "candidate": candidate,
            "status": "crash",
            "created_at": utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(limit=30),
            "trials": preserved,
            "summary": aggregate_trials(preserved),
        }
        output["summary"]["status"] = "partial" if output["trials"] else "failed"
        atomic_write_json(output_path, output)
        return 1
    finally:
        if resources:
            resources.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    return run_worker(args.plan.resolve(), args.candidate, args.output.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
