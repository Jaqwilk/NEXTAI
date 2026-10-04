"""Exactly one CLI registration and audited run; never invokes a candidate directly."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import time

from nextai_autoresearch.ledger import next_experiment_id
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge, _execution_fit
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b=Path.cwd()
assert not subprocess.check_output(["git","status","--porcelain"],cwd=b).strip()
assert json.loads((b/"research/reviews/PVM01-COMPACT-prepaid-gates-V1.json").read_text())["can_create_plan"]
identity=next_experiment_id(b)
assert identity=="EXP-20261004-0007"
study=json.loads((b/"research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json").read_text())
assert datetime.now(timezone.utc)<datetime.fromisoformat(study["study_deadline_at"].replace("Z","+00:00"))
cid="PVM01-COMPACT-controller-overhead-V1"
auxiliary_reserve(b,cid,240)
write_report(b)
start=time.perf_counter(); checks=[]
for label,command in (("register",["uv","run","--no-sync","nextai","program","register"]),
                      ("run",["uv","run","--no-sync","nextai","run","--plan",f"research/plans/{identity}.json"])):
    tick=time.perf_counter()
    result=subprocess.run(command,capture_output=True)
    elapsed=time.perf_counter()-tick
    for suffix,payload in (("stdout",result.stdout),("stderr",result.stderr)):
        (b/f"research/reviews/PVM01-COMPACT-{label}-V1.{suffix}.txt").write_bytes(payload)
    checks.append({"command":command,"returncode":result.returncode,"wall_seconds":elapsed})
    print(label, result.returncode, result.stdout.decode("utf-8",errors="replace")[-2500:],
          result.stderr.decode("utf-8",errors="replace")[-2500:],flush=True)
    if result.returncode:
        break
path=b/f"research/results/{identity}.json"
workers=_execution_fit(json.loads(path.read_text())["candidates"]) if path.exists() else 0.
wall=time.perf_counter()-start
overhead=max(0.,wall-workers)
seconds=math.ceil(overhead)+5
assert seconds<=240, "Controller cap exceeded; preserve receipt and do not hide overage"
auxiliary_charge(b,cid,seconds)
atomic_write_json(b/"research/reviews/PVM01-COMPACT-audited-controller-V1.json",{
    "created_at":utc_now(),"experiment_id":identity,"commands":checks,"total_wall_seconds":wall,
    "charged_worker_seconds":workers,"controller_overhead_seconds":overhead,"auxiliary_seconds_charged":seconds,
    "result_present":path.exists(),"result_sha256":sha256_file(path) if path.exists() else None,
    "direct_model_execution":False,"same_plan_retries":0})
assert all(row["returncode"]==0 for row in checks) and len(checks)==2
print("Audited result",identity,"full workers",workers,"controller charged",seconds,flush=True)
