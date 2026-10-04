"""Reserved, file-backed technical checks under PVM01-REPRO-PREPARATION-V1."""
import argparse
from dataclasses import asdict
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
    plan = json.loads((root / "research/plans/PVM01-REPRO-PREPARATION-V1.json").read_text())
    assert args.id.startswith("PVM01-REPRO-") and "/" not in args.id and "\\" not in args.id
    assert utc_now() < plan["deadline_at"]
    events = read_jsonl(root / "research/events.jsonl")
    consumed = sum(e["seconds"] for e in events if e.get("event") == "research_program_aux_fit_charged" and str(e.get("charge_id", "")).startswith("PVM01-REPRO-"))
    assert consumed + args.cap <= plan["auxiliary_compute_seconds_cap"]
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    assert command and args.timeout + 20 <= args.cap
    started = time.monotonic()
    auxiliary_reserve(root, args.id, args.cap)
    result, error = None, None
    output = root / "research/reviews" / args.id
    try:
        remaining = min(args.timeout, args.cap - (time.monotonic() - started) - 15)
        result = run_bounded(command, cwd=root, env=os.environ.copy(),
                             stdout_path=output.with_suffix(".stdout.txt"),
                             stderr_path=output.with_suffix(".stderr.txt"), timeout_seconds=remaining)
    except BaseException:
        error = traceback.format_exc()
    wall = time.monotonic() - started
    charged = math.ceil(wall) + 5
    # Never conceal a whole-wall overflow by clipping the measured charge.
    primary = min(charged, args.cap)
    auxiliary_charge(root, args.id, primary)
    if charged > args.cap:
        auxiliary_reserve(root, args.id + "-wall-overflow", charged - args.cap)
        auxiliary_charge(root, args.id + "-wall-overflow", charged - args.cap)
        error = (error or "") + "\nReservation overflow: full wall charged, preparation must stop."
    receipt = {"id": args.id, "created_at": utc_now(), "command": command, "cap": args.cap,
               "wall_seconds": wall, "seconds_charged": charged, "result": asdict(result) if result else None,
               "error": error, "scoring_or_research_data": False,
               "raw_outputs": {p.name: sha256_file(p) for p in (output.with_suffix(".stdout.txt"), output.with_suffix(".stderr.txt")) if p.exists()}}
    atomic_write_json(output.with_suffix(".json"), receipt)
    print(json.dumps(receipt, ensure_ascii=False))
    return result.returncode if result and not error else 1


if __name__ == "__main__":
    raise SystemExit(main())
