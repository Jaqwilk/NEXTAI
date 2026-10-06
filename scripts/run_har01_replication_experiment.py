"""One clone registration and hard-bounded replication; never restart a failure."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

import nextai_autoresearch
from nextai_autoresearch.ledger import read_jsonl, append_jsonl
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge, status, _execution_fit
from nextai_autoresearch.utils import atomic_write_json, utc_now, sha256_file

STUDY_PATH = "research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json"
STUDY_SHA = "d5567973e85b444d95ac13a70db9fe24b87c0ab3b672932e8322862c336ad12a"


def main():
    root = Path(__file__).resolve().parents[1]
    assert root.name == "NEXTAI-VALIDATION-20261002", "Independent clone required"
    assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
    assert sha256_file(root / STUDY_PATH) == STUDY_SHA
    study = json.loads((root / STUDY_PATH).read_text(encoding="utf-8"))
    deadline = datetime.fromisoformat(study["study_deadline_at"].replace("Z", "+00:00"))
    current = status(root)
    assert current["study_path"] == STUDY_PATH and current["ready"] and current["scoring_authorized"]
    assert not current["paid_run_pending"] and not current["study_terminal"]
    assert not (root / "STOP").exists() and not (root / "PAUSE").exists()
    events = read_jsonl(root / "research/events.jsonl")
    assert not any(e.get("event") == "research_program_registration_started" and e.get("study_path") == STUDY_PATH for e in events)
    charge_id, cap = "HAR01-REPLICATION-controller-V1", 1200
    prefix = root / "research/reviews" / charge_id
    marker = prefix.with_suffix(".started.json")
    assert not marker.exists(), "Controller has already started; no retry"
    atomic_write_json(marker, {"created_at": utc_now(), "study_path": STUDY_PATH, "study_sha256": STUDY_SHA,
        "controller_pid": os.getpid(), "paid_retry": False})
    started = time.monotonic()
    auxiliary_reserve(root, charge_id, cap)
    environment = os.environ.copy()
    environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(root / "src"), NEXTAI_PROJECT_ROOT=str(root), OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", CUBLAS_WORKSPACE_CONFIG=":4096:8")
    registered = result = error = None
    identity = None
    worker_started = None
    worker_elapsed = 0.
    try:
        registered = run_bounded([sys.executable, "-m", "nextai_autoresearch.cli", "program", "register"], cwd=root,
            env=environment, stdout_path=prefix.with_suffix(".registration.stdout.txt"),
            stderr_path=prefix.with_suffix(".registration.stderr.txt"), timeout_seconds=160)
        assert registered.returncode == 0 and not registered.exit_live_descendant_pids
        records = [e for e in read_jsonl(root / "research/events.jsonl")
                   if e.get("event") == "research_program_registered" and e.get("study_path") == STUDY_PATH]
        assert len(records) == 1, "Exactly one registration required"
        identity = records[0]["experiment_id"]
        remaining = min(3500., (deadline - datetime.now(timezone.utc)).total_seconds() - 600.)
        assert remaining > 0, "Deadline exhausted after registration; ticket preserved"
        worker_started = time.monotonic()
        try:
            result = run_bounded([sys.executable, "-m", "nextai_autoresearch.cli", "run", "--plan", records[0]["plan_path"]],
                cwd=root, env=environment, stdout_path=prefix.with_suffix(".stdout.txt"),
                stderr_path=prefix.with_suffix(".stderr.txt"), timeout_seconds=remaining)
        finally:
            worker_elapsed = time.monotonic() - worker_started
        assert result.elapsed_seconds <= 3600., "Enclosing worker Job ceiling exceeded"
        assert result.returncode == 0 and not result.exit_live_descendant_pids, "Worker stage failed; no retry"
    except BaseException:
        error = traceback.format_exc()
    finally:
        if identity is None:
            records = [e for e in read_jsonl(root / "research/events.jsonl")
                       if e.get("event") == "research_program_registered" and e.get("study_path") == STUDY_PATH]
            if len(records) == 1:
                identity = records[0]["experiment_id"]
    parent = time.monotonic() - started
    workers = 0.
    if identity:
        saved = root / f"research/results/{identity}.json"
        if saved.exists():
            workers = _execution_fit(json.loads(saved.read_text(encoding="utf-8"))["candidates"])
        else:
            workers = _execution_fit(json.loads(p.read_text(encoding="utf-8")) for p in
                                     (root / "research/tmp" / identity).glob("*.supervisor.json"))
    recovered = max(0., worker_elapsed - workers) if error and worker_started is not None else 0.
    if recovered and identity:
        recovery_path = prefix.with_suffix(".worker-recovery.json")
        recovery = {
            "created_at": utc_now(), "program_id": current["id"], "study_path": STUDY_PATH,
            "study_sha256": STUDY_SHA, "experiment_id": identity, "worker_charge_total": workers + recovered,
            "observed_worker_seconds": workers, "bounded_job_wall_seconds": worker_elapsed,
            "job": asdict(result) if result else None, "supervision_exception": error,
            "drain_verified": result is not None and not result.exit_live_descendant_pids,
            "charge_basis": "conservative_uncovered_failed_enclosing_job_wall_v1"}
        atomic_write_json(recovery_path, recovery)
        append_jsonl(root / "research/events.jsonl", {"event": "research_program_worker_charge_recovery",
            **{key: recovery[key] for key in ("created_at", "program_id", "study_path", "study_sha256", "experiment_id", "worker_charge_total")},
            "receipt_path": str(recovery_path.relative_to(root)).replace("\\", "/"),
            "receipt_sha256": sha256_file(recovery_path)})
    charge = math.ceil(max(0., parent - workers - recovered)) + 20
    # Full preallocated auxiliary envelope covers this parent plus the later
    # analysis, immutable archive and maintenance closure; never settle twice.
    auxiliary_charge(root, charge_id, cap)
    if charge > cap:
        error = (error or "") + f"\nAuxiliary physical overrun: required {charge}s exceeds {cap}s; exact excess {charge-cap}s retained."
    receipt = {"created_at": utc_now(), "experiment_id": identity, "study_path": STUDY_PATH,
        "study_sha256": STUDY_SHA, "parent_wall_seconds": parent, "package_origin": nextai_autoresearch.__file__,
        "full_workers_charged_separately_seconds": workers, "conservative_missing_worker_seconds": recovered,
        "auxiliary_parent_overhead_and_closure_seconds_charged": cap,
        "observed_parent_overhead_seconds": max(0., parent - workers - recovered),
        "minimum_auxiliary_charge_with_bookkeeping_margin": charge,
        "physical_auxiliary_overrun_seconds": max(0, charge - cap),
        "worker_interval_observed_seconds": worker_elapsed,
        "physical_worker_envelope_overrun_seconds": max(0., worker_elapsed - 3600.),
        "registration": asdict(registered) if registered else None, "run": asdict(result) if result else None,
        "error": error, "whole_process_trees_bounded": True, "enclosing_job_cap_seconds": 3600,
        "enclosing_job_timeout_seconds_maximum": 3500, "shutdown_margin_seconds": 100,
        "paid_retry": False, "auxiliary_charge_basis": "full_reserved_controller_and_closure_envelope_v1",
        "missing_worker_charge_is_conservative_not_supervised_fit": True,
        "remaining_auxiliary_seconds_for_analysis_archive_and_closure": max(0, cap - charge)}
    atomic_write_json(prefix.with_suffix(".json"), receipt)
    print(json.dumps(receipt), flush=True)
    raise SystemExit(0 if result and result.returncode == 0 and not error else 1)


if __name__ == "__main__":
    main()
