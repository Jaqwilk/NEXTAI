"""One-use full-process-tree stage checks; a failure forbids unstarted science."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import traceback
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("--postrun", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tag = "MUC02-NEGATIVES-REPLICATION-20261006-V1"
    plan_path = f"research/plans/{tag}.json"
    plan = json.loads((root / plan_path).read_text(encoding="utf-8"))
    assert args.id.startswith("MUC02-REPL-") and "/" not in args.id and "\\" not in args.id
    prefix = root / "research/reviews" / args.id
    claim = prefix.with_suffix(".started.json")
    assert not claim.exists() and not prefix.with_suffix(".json").exists()
    prior = [json.loads(p.read_text(encoding="utf-8")) for p in (root / "research/reviews").glob("MUC02-REPL-*.json") if not p.name.endswith(".started.json")]
    spent = sum(r.get("wall_seconds", 0) for r in prior)
    assert spent + args.timeout <= plan["resources"]["auxiliary_test_seconds_cap"]
    if not args.postrun:
        assert all(r.get("result", {}).get("returncode") == 0 and not r.get("error") for r in prior)
    deadline = datetime.fromisoformat(plan["deadline_at"].replace("Z", "+00:00"))
    assert datetime.now(timezone.utc) < deadline
    assert not any((root / p).exists() for p in ("STOP", "PAUSE"))
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    atomic_write_json(claim, {"id": args.id, "created_at": utc_now(), "command": command, "plan_sha256": sha256_file(root / plan_path)})
    started = time.monotonic()
    result = error = None
    try:
        environment = os.environ.copy()
        environment.update(UV_CACHE_DIR=str(root / "research/tmp/muc02-replication-uv-cache"), PYTHONDONTWRITEBYTECODE="1",
            PYTHONUTF8="1", PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", CUBLAS_WORKSPACE_CONFIG=":4096:8")
        timeout = min(args.timeout, (deadline - datetime.now(timezone.utc)).total_seconds() - 10)
        result = run_bounded(command, cwd=root, env=environment, stdout_path=prefix.with_suffix(".stdout.txt"),
                             stderr_path=prefix.with_suffix(".stderr.txt"), timeout_seconds=timeout)
    except BaseException:
        error = traceback.format_exc()
    receipt = {"id": args.id, "created_at": utc_now(), "wall_seconds": time.monotonic() - started,
               "result": asdict(result) if result else None, "error": error,
               "plan_sha256": sha256_file(root / plan_path), "fit_seconds": 0, "whole_tree_bounded": True,
               "raw_outputs": {p.name: sha256_file(p) for p in (prefix.with_suffix(".stdout.txt"), prefix.with_suffix(".stderr.txt")) if p.exists()}}
    atomic_write_json(prefix.with_suffix(".json"), receipt)
    if not args.postrun and (error or not result or result.returncode):
        relative = prefix.with_suffix(".json").relative_to(root).as_posix()
        append_jsonl(root / "research/events.jsonl", {"event": "muc02_replication_preparation_failed", "created_at": utc_now(),
            "stage_id": tag, "plan_sha256": sha256_file(root / plan_path), "receipt_path": relative, "receipt_sha256": sha256_file(root / relative)})
    print(json.dumps(receipt), flush=True)
    raise SystemExit(result.returncode if result and not error else 1)

if __name__ == "__main__":
    main()
