"""Reserved whole-process-tree checks for the immutable cycle314 dense-noise contract."""
import argparse
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
from nextai_autoresearch.research_program import auxiliary_charge, auxiliary_reserve
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--cap", type=int, required=True)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / "research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json").read_text())
    assert args.id.startswith("PVM01-ROBUSTNESS-") and "/" not in args.id and "\\" not in args.id
    events = read_jsonl(root / "research/events.jsonl")
    consumed = sum(e["seconds"] for e in events if e.get("event") == "research_program_aux_fit_charged" and str(e.get("charge_id", "")).startswith("PVM01-ROBUSTNESS-"))
    assert consumed + args.cap <= plan["resources"]["auxiliary_test_seconds_cap"]
    assert args.timeout + 20 <= args.cap
    deadline = datetime.fromisoformat(plan["study_deadline_at"].replace("Z", "+00:00"))
    assert datetime.now(timezone.utc) < deadline
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    started = time.monotonic()
    auxiliary_reserve(root, args.id, args.cap)
    output = root / "research/reviews" / args.id
    result, error = None, None
    try:
        remaining = min(args.timeout, args.cap - (time.monotonic() - started) - 15,
                        (deadline - datetime.now(timezone.utc)).total_seconds() - 15)
        environment = os.environ.copy()
        environment.update(CUBLAS_WORKSPACE_CONFIG=":4096:8", PYTHONHASHSEED="0",
                           OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        result = run_bounded(command, cwd=root, env=environment,
                             stdout_path=output.with_suffix(".stdout.txt"),
                             stderr_path=output.with_suffix(".stderr.txt"), timeout_seconds=remaining)
    except BaseException:
        error = traceback.format_exc()
    wall = time.monotonic() - started
    charged = math.ceil(wall) + 5
    auxiliary_charge(root, args.id, min(charged, args.cap))
    if charged > args.cap:
        auxiliary_reserve(root, args.id + "-overflow", charged - args.cap)
        auxiliary_charge(root, args.id + "-overflow", charged - args.cap)
        error = (error or "") + "\nFull-wall overflow charged; stop this scope."
    receipt = {"id": args.id, "created_at": utc_now(), "command": command, "cap": args.cap,
               "wall_seconds": wall, "seconds_charged": charged, "result": asdict(result) if result else None,
               "error": error, "raw_outputs": {p.name: sha256_file(p) for p in
                   (output.with_suffix(".stdout.txt"), output.with_suffix(".stderr.txt")) if p.exists()}}
    atomic_write_json(output.with_suffix(".json"), receipt)
    print(json.dumps(receipt), flush=True)
    raise SystemExit(result.returncode if result is not None and not error else 1)


if __name__ == "__main__":
    main()
