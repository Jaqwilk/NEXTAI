"""Bound and charge one cycle326 check, including intake, failure and bookkeeping."""
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
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--cap", type=int, required=True)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.json").read_text(encoding="utf-8"))
    assert args.id.startswith("NEXTAI-B-326-") and "/" not in args.id and "\\" not in args.id
    events = read_jsonl(root / "research/events.jsonl")
    charges = sum(e["seconds"] for e in events if e.get("event") == "research_program_aux_fit_charged"
                  and str(e.get("charge_id", "")).startswith("NEXTAI-B-326-"))
    assert charges + args.cap <= plan["resources"]["auxiliary_test_seconds_cap"]
    assert args.timeout + 70 <= args.cap
    deadline = datetime.fromisoformat(plan["study_deadline_at"].replace("Z", "+00:00"))
    assert datetime.now(timezone.utc) < deadline
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    started = time.monotonic()
    auxiliary_reserve(root, args.id, args.cap)
    prefix = root / "research/reviews" / args.id
    result = error = None
    try:
        remaining = min(args.timeout, args.cap - (time.monotonic() - started) - 65,
                        (deadline - datetime.now(timezone.utc)).total_seconds() - 65)
        environment = os.environ.copy()
        environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1",
                           OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", CUBLAS_WORKSPACE_CONFIG=":4096:8")
        result = run_bounded(command, cwd=root, env=environment,
                             stdout_path=prefix.with_suffix(".stdout.txt"),
                             stderr_path=prefix.with_suffix(".stderr.txt"), timeout_seconds=remaining)
    except BaseException:
        error = traceback.format_exc()
    wall = time.monotonic() - started
    charge = math.ceil(wall) + 40
    auxiliary_charge(root, args.id, min(charge, args.cap))
    if charge > args.cap:
        auxiliary_reserve(root, args.id + "-overflow", charge - args.cap)
        auxiliary_charge(root, args.id + "-overflow", charge - args.cap)
        error = (error or "") + "\nFull-wall overflow charged; stop unstarted scope."
    receipt = {"created_at": utc_now(), "id": args.id, "command": command, "cap_seconds": args.cap,
               "wall_seconds": wall, "seconds_charged": charge,
               "conservative_accounting_allowance_seconds": 40,
               "result": asdict(result) if result else None, "error": error,
               "whole_process_tree_bounded": True,
               "raw_outputs": {p.name: sha256_file(p) for p in
                               (prefix.with_suffix(".stdout.txt"), prefix.with_suffix(".stderr.txt")) if p.exists()}}
    atomic_write_json(prefix.with_suffix(".json"), receipt)
    print(json.dumps(receipt), flush=True)
    raise SystemExit(result.returncode if result is not None and not error else 1)


if __name__ == "__main__":
    main()
