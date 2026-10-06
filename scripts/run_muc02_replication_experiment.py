"""One registration and canonical clone execution, with complete failure preservation."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
import traceback
import zipfile
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.muc02_replication_stage import status, ID, PLAN, PLAN_SHA256, COHORT
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
assert root.name == "NEXTAI"
assert status(root)["scoring_authorized"] and status(clone)["scoring_authorized"]
assert status(clone)["registrations_used"] == 0
assert not any((p / gate).exists() for p in (root, clone) for gate in ("STOP", "PAUSE", "research/run.lock"))
prefix = root / "research/reviews/MUC02-REPLICATION-EXPERIMENT-CONTROLLER-V1"
assert not prefix.with_suffix(".started.json").exists() and not prefix.with_suffix(".json").exists()
atomic_write_json(prefix.with_suffix(".started.json"), {"created_at": utc_now(), "plan_sha256": PLAN_SHA256,
    "stage_id": ID, "attempt": 1, "clone": str(clone), "deadline_at": status(root)["deadline_at"]})
source_archive = root / "research/laboratory/archive/MUC02-REPLICATION-EVALUATED-SOURCE-V1.zip"
assert not source_archive.exists()
manifest = json.loads((clone / "research/eval_manifest.json").read_text())
source_files = [p for p in manifest["files"] if p.startswith(("src/", "tests/", "schemas/", "config/", "scripts/"))]
source_files += ["research/eval_manifest.json", "research/laboratory/preflight_certificate.json", PLAN,
                 f"research/laboratory/{ID}.json", "AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"]
source_archive.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(source_archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for relative in sorted(set(source_files)):
        archive.write(clone / relative, relative)
environment = os.environ.copy()
environment.update(PYTHONPATH=str(clone / "src"), NEXTAI_PROJECT_ROOT=str(clone), PYTHONDONTWRITEBYTECODE="1",
    PYTHONUTF8="1", PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
    CUBLAS_WORKSPACE_CONFIG=":4096:8", UV_CACHE_DIR=str(root / "research/tmp/muc02-replication-uv-cache"))
python = clone / ".venv/Scripts/python.exe"
started = time.monotonic()
registration = run = error = identity = None
try:
    registration = run_bounded([str(python), str(clone / "scripts/register_muc02_replication.py")], cwd=clone, env=environment,
        stdout_path=prefix.with_name(prefix.name + ".registration.stdout.txt"),
        stderr_path=prefix.with_name(prefix.name + ".registration.stderr.txt"), timeout_seconds=300)
    assert registration.returncode == 0, "Registration failed; single attempt consumed; no replacement"
    records = [e for e in read_jsonl(clone / "research/events.jsonl") if e.get("event") == "muc02_replication_registered"]
    assert len(records) == 1
    identity = records[0]["experiment_id"]
    assert not (clone / "research/tmp" / identity).exists()
    assert not (clone / "research/results" / f"{identity}.json").exists()
    deadline = datetime.fromisoformat(status(clone)["deadline_at"].replace("Z", "+00:00"))
    remaining = (deadline - datetime.now(timezone.utc)).total_seconds() - 600
    assert remaining > 0, "Stage deadline leaves no reporting reserve"
    run = run_bounded([str(python), "-m", "nextai_autoresearch.cli", "run", "--plan", records[0]["plan_path"]],
        cwd=clone, env=environment, stdout_path=prefix.with_suffix(".stdout.txt"),
        stderr_path=prefix.with_suffix(".stderr.txt"), timeout_seconds=remaining)
    assert run.returncode == 0, "Single canonical clone execution failed; no retry"
except BaseException:
    error = traceback.format_exc()
wall = time.monotonic() - started
outcomes = []
if identity:
    result_path = clone / "research/results" / f"{identity}.json"
    if result_path.is_file():
        outcomes = json.loads(result_path.read_text())["candidates"]
    else:
        outcomes = [json.loads(p.read_text()) for p in (clone / "research/tmp" / identity).glob("*.supervisor.json")]
fit = sum((o.get("execution") or {}).get("supervised_fit_seconds", 0) for o in outcomes)
workers = sum((o.get("execution") or {}).get("wall_seconds", 0) for o in outcomes)
receipt = {"created_at": utc_now(), "stage_id": ID, "plan_sha256": PLAN_SHA256, "experiment_id": identity,
    "parent_wall_seconds": wall, "worker_wall_seconds": workers, "parent_overhead_seconds": max(0, wall-workers),
    "supervised_fit_seconds": fit, "fit_total_cap": 3600, "registration": asdict(registration) if registration else None,
    "run": asdict(run) if run else None, "error": error, "paid_retry": False, "whole_process_trees_bounded": True,
    "source_archive_path": source_archive.relative_to(root).as_posix(), "source_archive_sha256": sha256_file(source_archive),
    "raw_outputs": {p.name: sha256_file(p) for p in prefix.parent.glob(prefix.name + "*.txt")}}
atomic_write_json(prefix.with_suffix(".json"), receipt)
if error:
    relative = prefix.with_suffix(".json").relative_to(root).as_posix()
    append_jsonl(root / "research/events.jsonl", {"event": "muc02_replication_preparation_failed", "created_at": utc_now(),
        "stage_id": ID, "plan_sha256": PLAN_SHA256, "receipt_path": relative, "receipt_sha256": sha256_file(root / relative)})
print(json.dumps(receipt), flush=True)
raise SystemExit(0 if run and run.returncode == 0 and not error else 1)
