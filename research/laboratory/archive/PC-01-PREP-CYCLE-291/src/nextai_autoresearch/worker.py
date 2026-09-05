from __future__ import annotations

import argparse
import importlib
import json
import traceback
from pathlib import Path

from .metrics import aggregate_trials
from .utils import atomic_write_json, load_json, utc_now


def run_worker(plan_path: Path, candidate: str, output_path: Path) -> int:
    try:
        plan = load_json(plan_path)
        benchmark_name = plan["benchmark"]
        benchmark = importlib.import_module(f".benchmarks.{benchmark_name}", __package__)
        if benchmark.BENCHMARK_VERSION != benchmark_name:
            raise ValueError("Benchmark module/version mismatch")
        trials = benchmark.run_suite(candidate, plan)
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
        output = {
            "candidate": candidate,
            "status": "crash",
            "created_at": utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(limit=30),
            "trials": [],
            "summary": {"status": "failed", "completed_trials": 0, "total_trials": 0},
        }
        atomic_write_json(output_path, output)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    return run_worker(args.plan.resolve(), args.candidate, args.output.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
