"""Bounded, read-only C engineering probes; never register or realize seeds."""
import argparse
import cProfile
from dataclasses import asdict
import importlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback

import psutil

PROBES = ("cli-import", "wallet", "lifecycle", "laboratory", "integrity", "report-inputs", "baseline-hashes", "preflight", "git-metadata")
SOURCE_FILES = ("research_program.py", "gates.py", "laboratory.py", "report.py", "integrity.py", "baseline_semantics.py", "cli.py", "schemas.py", "runner.py", "ledger.py", "utils.py")


def _probe(name, root):
    if name == "cli-import":
        return {"module": importlib.import_module("nextai_autoresearch.cli").__file__}
    if name == "wallet":
        from nextai_autoresearch.research_program import status
        return status(root)
    if name == "lifecycle":
        from nextai_autoresearch.gates import lifecycle_problems
        return lifecycle_problems(root)
    if name == "laboratory":
        from nextai_autoresearch.laboratory import laboratory_problems
        return laboratory_problems(root, scoring=False)
    if name == "integrity":
        from nextai_autoresearch.integrity import verify_manifest
        return verify_manifest(root)
    if name == "report-inputs":
        from nextai_autoresearch.report import report_inputs
        return report_inputs(root)
    if name == "baseline-hashes":
        from nextai_autoresearch.research_program import status, _study_scope
        from nextai_autoresearch.baseline_semantics import verify_required_baselines
        from nextai_autoresearch.utils import load_json
        study = load_json(root / status(root)["study_path"])
        return verify_required_baselines({"candidates": study["candidates"], "research_program_protocol": _study_scope(study)}, root, run_tests=False)
    if name == "preflight":
        from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
        return verify_preflight_certificate(root)
    if name == "git-metadata":
        from nextai_autoresearch.runner import _git_value
        return {"commit": _git_value(root, "rev-parse", "HEAD"), "branch": _git_value(root, "branch", "--show-current"), "dirty": _git_value(root, "status", "--porcelain")}
    raise ValueError(name)


def child(args):
    root = Path(os.environ["NEXTAI_PROJECT_ROOT"]).resolve()
    assert root.name == "NEXTAI-VALIDATION-20261002", "Independent clone required"
    process = psutil.Process()
    observed, peak_rss = {}, [0]
    stop = threading.Event()
    def sample():
        while not stop.is_set():
            try:
                tree = (process, *process.children(recursive=True))
            except psutil.Error:
                tree = (process,)
            rss = 0
            for item in tree:
                try:
                    stamp = item.create_time()
                    cpu = item.cpu_times()
                    entry = observed.setdefault((item.pid, stamp), {"pid": item.pid, "created_at_epoch": stamp, "cmdline": item.cmdline(), "cpu_user_seconds_observed": 0., "cpu_system_seconds_observed": 0.})
                    entry["cpu_user_seconds_observed"] = max(entry["cpu_user_seconds_observed"], cpu.user)
                    entry["cpu_system_seconds_observed"] = max(entry["cpu_system_seconds_observed"], cpu.system)
                    rss += item.memory_info().rss
                except psutil.Error:
                    pass
            peak_rss[0] = max(peak_rss[0], rss)
            stop.wait(.05)
    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    profiler = cProfile.Profile()
    started = time.monotonic()
    print(json.dumps({"event": "probe_started", "probe": args.probe, "pid": os.getpid(), "root": str(root)}), flush=True)
    result, error = None, None
    try:
        result = profiler.runcall(_probe, args.probe, root)
    except BaseException:
        error = traceback.format_exc()
    finally:
        elapsed = time.monotonic() - started
        stop.set()
        thread.join(timeout=2)
        profiler.dump_stats(str(args.prefix) + ".pstats")
        from nextai_autoresearch.utils import sha256_file
        source_hashes = {name: sha256_file(root / "src/nextai_autoresearch" / name) for name in SOURCE_FILES}
        metadata = {"probe": args.probe, "span_wall_seconds": elapsed, "sampled_peak_tree_rss_bytes": peak_rss[0], "observed_processes": list(observed.values()), "cpu_observation_is_lower_bound_for_short_lived_children": True, "source_sha256": source_hashes, "package_root": str(root / "src"), "result": result, "error": error, "no_ticket_or_seed_or_native_intake": True}
        path = Path(str(args.prefix) + ".span.json")
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(metadata, handle, sort_keys=True)
            handle.write("\n")
        print(json.dumps({"event": "probe_completed", "probe": args.probe, "elapsed": elapsed, "error": error}), flush=True)
    return 1 if error else 0


def parent(args):
    from nextai_autoresearch.process_supervision import run_bounded
    from nextai_autoresearch.utils import sha256_file
    root = Path(os.environ["NEXTAI_PROJECT_ROOT"]).resolve()
    assert root.name == "NEXTAI-VALIDATION-20261002"
    prefix = root / "research/reviews" / f"NEXTAI-C-PROFILE-{args.label}-{args.probe}"
    assert not any(prefix.parent.glob(prefix.name + ".*")), "Preserve each profile iteration"
    environment = os.environ.copy()
    environment.update(PYTHONPATH=str(root / "src"), NEXTAI_PROJECT_ROOT=str(root), PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    command = [sys.executable, str(Path(__file__).resolve()), "--child", "--probe", args.probe, "--prefix", str(prefix)]
    started = time.monotonic()
    job, error = None, None
    try:
        job = run_bounded(command, cwd=root, env=environment, stdout_path=Path(str(prefix) + ".stdout.txt"), stderr_path=Path(str(prefix) + ".stderr.txt"), timeout_seconds=args.timeout)
    except BaseException:
        error = traceback.format_exc()
    finally:
        record = {"command": command, "inclusive_parent_wall_seconds": time.monotonic() - started, "job": asdict(job) if job else None, "error": error, "profiler_sha256": sha256_file(Path(__file__)), "timeout_seconds": args.timeout, "no_scientific_registration": True}
        with Path(str(prefix) + ".job.json").open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(record, handle, sort_keys=True)
            handle.write("\n")
        print(json.dumps(record), flush=True)
    return 0 if job and job.returncode == 0 and error is None else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", choices=PROBES, required=True)
    parser.add_argument("--label", default="baseline1")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--prefix", type=Path)
    arguments = parser.parse_args()
    assert 0 < arguments.timeout <= 600
    raise SystemExit(child(arguments) if arguments.child else parent(arguments))
