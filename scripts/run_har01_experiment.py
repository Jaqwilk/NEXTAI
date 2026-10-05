"""Exactly one paid native registration/run; preserve failure and charge parent overhead."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
import traceback

from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge, status, _execution_fit
from nextai_autoresearch.utils import atomic_write_json, utc_now, sha256_file


def main():
    root = Path(__file__).resolve().parents[1]
    study_path = "research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json"
    study = json.loads((root / study_path).read_text(encoding="utf-8"))
    deadline = datetime.fromisoformat(study["study_deadline_at"].replace("Z", "+00:00"))
    current = status(root)
    assert current["study_path"] == study_path and current["ready"] and current["scoring_authorized"]
    assert not current["paid_run_pending"] and not current["study_terminal"]
    assert not (root / "STOP").exists() and not (root / "PAUSE").exists()
    assert not any(e.get("event") == "research_program_registration_started" and e.get("study_path") == study_path
                   for e in read_jsonl(root / "research/events.jsonl"))
    charge_id, cap = "NEXTAI-B-319-experiment-controller-V1", 900
    consumed = sum(e["seconds"] for e in read_jsonl(root / "research/events.jsonl")
                   if e.get("event") == "research_program_aux_fit_charged" and str(e.get("charge_id", "")).startswith("NEXTAI-B-319-"))
    assert consumed + cap <= study["resources"]["auxiliary_test_seconds_cap"]
    started = time.monotonic()
    auxiliary_reserve(root, charge_id, cap)
    environment = os.environ.copy()
    environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1",
                       OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", CUBLAS_WORKSPACE_CONFIG=":4096:8")
    prefix = root / "research/reviews" / charge_id
    result = registered = error = None
    identity = None
    try:
        registered = run_bounded(["uv", "run", "--no-sync", "nextai", "program", "register"], cwd=root,
            env=environment, stdout_path=prefix.with_suffix(".registration.stdout.txt"),
            stderr_path=prefix.with_suffix(".registration.stderr.txt"), timeout_seconds=160)
        assert registered.returncode == 0, "Paid registration failed; no replacement allowed"
        records = [e for e in read_jsonl(root / "research/events.jsonl")
                   if e.get("event") == "research_program_registered" and e.get("study_path") == study_path]
        assert len(records) == 1
        identity = records[0]["experiment_id"]
        remaining = min(study["resources"]["fit_seconds_study_cap"] + cap - (time.monotonic() - started) - 35,
                        (deadline - datetime.now(timezone.utc)).total_seconds() - 600)
        assert remaining > 0, "Deadline exhausted after registration; paid ticket preserved"
        result = run_bounded(["uv", "run", "--no-sync", "nextai", "run", "--plan", records[0]["plan_path"]],
            cwd=root, env=environment, stdout_path=prefix.with_suffix(".stdout.txt"),
            stderr_path=prefix.with_suffix(".stderr.txt"), timeout_seconds=remaining)
    except BaseException:
        error = traceback.format_exc()
    parent = time.monotonic() - started
    workers = 0.
    if identity:
        saved = root / f"research/results/{identity}.json"
        if saved.exists():
            workers = _execution_fit(json.loads(saved.read_text(encoding="utf-8"))["candidates"])
        else:
            workers = _execution_fit(json.loads(p.read_text(encoding="utf-8")) for p in
                                     (root / "research/tmp" / identity).glob("*.supervisor.json"))
    charge = math.ceil(max(0., parent - workers)) + 20
    auxiliary_charge(root, charge_id, min(cap, charge))
    if charge > cap:
        auxiliary_reserve(root, charge_id + "-overflow", charge - cap)
        auxiliary_charge(root, charge_id + "-overflow", charge - cap)
        error = (error or "") + "\nParent overhead overflow charged; stop unstarted scope."
    receipt = {"created_at": utc_now(), "experiment_id": identity, "study_path": study_path,
        "study_sha256": sha256_file(root / study_path), "parent_wall_seconds": parent,
        "full_workers_charged_separately_seconds": workers, "auxiliary_parent_overhead_seconds_charged": charge,
        "registration": asdict(registered) if registered else None, "run": asdict(result) if result else None,
        "error": error, "whole_process_trees_bounded": True, "paid_retry": False}
    atomic_write_json(prefix.with_suffix(".json"), receipt)
    print(json.dumps(receipt), flush=True)
    raise SystemExit(0 if result and result.returncode == 0 and not error else 1)


if __name__ == "__main__":
    main()
