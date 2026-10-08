"""Preserve one C command and its whole Windows process tree in the clone."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import traceback

from nextai_autoresearch import process_supervision
from nextai_autoresearch.utils import sha256_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--seconds", required=True, type=float)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = Path(os.environ["NEXTAI_PROJECT_ROOT"]).resolve()
    if root.name != "NEXTAI-VALIDATION-20261002":
        raise ValueError("Independent validation clone is required")
    origin = Path(process_supervision.__file__).resolve()
    if not origin.is_relative_to(root / "src"):
        raise ValueError("Imported supervisor is outside the validation clone")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,90}", args.label):
        raise ValueError("Use a new bounded C evidence label")
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 18000:
        raise ValueError("Command cap must be finite and at most five hours")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("An explicit Python command is required")
    # Python executable is inherited, never an arbitrary shell command.
    command = [sys.executable, *command]
    prefix = root / "research/reviews" / f"NEXTAI-C-{args.label}"
    prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = [Path(str(prefix) + suffix) for suffix in (".stdout.txt", ".stderr.txt", ".job.json")]
    if any(path.exists() for path in paths):
        raise FileExistsError("Earlier C evidence must not be overwritten")
    env = os.environ.copy()
    env.update(PYTHONPATH=str(root / "src"), NEXTAI_PROJECT_ROOT=str(root),
               PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    job, error = None, None
    try:
        job = process_supervision.run_bounded(command, cwd=root, env=env,
            stdout_path=paths[0], stderr_path=paths[1], timeout_seconds=args.seconds)
    except BaseException:
        error = traceback.format_exc()
    receipt = {"started_at": started_at, "completed_at": datetime.now(timezone.utc).isoformat(),
        "inclusive_controller_wall_seconds": time.monotonic() - started,
        "command": command, "timeout_seconds": args.seconds, "root": str(root),
        "supervisor_origin": str(origin), "supervisor_sha256": sha256_file(origin),
        "driver_sha256": sha256_file(Path(__file__)), "job": asdict(job) if job else None,
        "error": error, "component_nested_in_C_outer_wall": True,
        "stdout_sha256": sha256_file(paths[0]) if paths[0].is_file() else None,
        "stderr_sha256": sha256_file(paths[1]) if paths[1].is_file() else None}
    with paths[2].open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(receipt), flush=True)
    return 0 if job and job.returncode == 0 and error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
