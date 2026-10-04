"""Bounded auxiliary command with durable reservation, raw output and charge."""
import math
from pathlib import Path
import subprocess
import sys
import time

from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json

base = Path.cwd()
charge_id, cap = sys.argv[1], float(sys.argv[2])
command = sys.argv[3:]
assert charge_id.startswith("PVM01-EXPOSURE-") and "/" not in charge_id and "\\" not in charge_id
path = base / f"research/reviews/{charge_id}.json"
assert not path.exists()
events = read_jsonl(base / "research/events.jsonl")
paid = {e["charge_id"]: e["seconds"] for e in events if e.get("event") == "research_program_aux_fit_charged"}
used = sum(paid.get(e["charge_id"], e["seconds_cap"]) for e in events
           if e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id", "").startswith("PVM01-EXPOSURE-"))
assert used + cap <= 1800, "Study auxiliary reservation would exceed the frozen1800s cap"
auxiliary_reserve(base, charge_id, cap)
start = time.perf_counter()
write_report(base)
try:
    run = subprocess.run(command, capture_output=True, timeout=cap-15)
    code, stdout, stderr = run.returncode, run.stdout, run.stderr
except subprocess.TimeoutExpired as exc:
    code, stdout, stderr = 124, exc.stdout or b"", exc.stderr or b""
    stderr += b"\nAuxiliary deadline exceeded; failed check preserved.\n"
elapsed = time.perf_counter()-start
seconds = min(cap, math.ceil(elapsed)+5)
for suffix, payload in (("stdout", stdout), ("stderr", stderr)):
    (base / f"research/reviews/{charge_id}.{suffix}.txt").write_bytes(payload)
auxiliary_charge(base, charge_id, seconds)
atomic_write_json(path, {"command":command, "returncode":code, "wall_seconds":elapsed,
                       "seconds_charged":seconds, "cap":cap, "model_run_is_scored":False})
print(stdout.decode("utf-8", errors="replace")[-6500:])
print(stderr.decode("utf-8", errors="replace")[-2000:])
print(f"Auxiliary charge {charge_id}: {seconds}s, status={code}", flush=True)
raise SystemExit(code)
