from dataclasses import asdict
from datetime import datetime, timezone
import json, math, os, subprocess, time, traceback
from pathlib import Path
from nextai_autoresearch.ledger import next_experiment_id, read_jsonl
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge, status, _execution_fit
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b=Path.cwd().resolve();assert b.name=="NEXTAI-VALIDATION-20261002"
assert not subprocess.check_output(["git","status","--porcelain"],cwd=b).strip()
for directory in (b,b.parent/"NEXTAI"):
 for name in ("STOP","PAUSE","research/run.lock"):assert not (directory/name).exists(),(directory,name)
study_path=b/"research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json"
study=json.loads(study_path.read_text());value=status(b)
assert value["ready"] and value["scoring_authorized"] and not value["study_terminal"] and not value["paid_run_pending"] and value["experiment_id"] is None
assert json.loads((b/"research/reviews/PVM01-ROBUSTNESS-prepaid-gates-V1.json").read_text())["can_create_plan"]
eid=next_experiment_id(b);plan_path=b/f"research/plans/{eid}.json"
assert not plan_path.exists() and not (b/f"research/results/{eid}.json").exists()
deadline=datetime.fromisoformat(study["study_deadline_at"].replace("Z","+00:00"))
assert (deadline-datetime.now(timezone.utc)).total_seconds()>1800
source=subprocess.check_output(["git","rev-parse","HEAD"],cwd=b).decode().strip()
cid="PVM01-ROBUSTNESS-audited-run-overhead-V1";cap=600
consumed=sum(e["seconds"] for e in read_jsonl(b/"research/events.jsonl") if e.get("event")=="research_program_aux_fit_charged" and str(e.get("charge_id","")).startswith("PVM01-ROBUSTNESS-"))
assert consumed+cap<=study["resources"]["auxiliary_test_seconds_cap"]
started=time.monotonic();auxiliary_reserve(b,cid,cap)
commands=[];error=None;worker_charge=0.;environment=os.environ.copy()
environment.update(CUBLAS_WORKSPACE_CONFIG=":4096:8",PYTHONHASHSEED="0",OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
try:
 write_report(b)
 for label,args in [("register",["program","register"]),("run",["run","--plan",plan_path.relative_to(b).as_posix()])]:
  remaining=(deadline-datetime.now(timezone.utc)).total_seconds()-900
  timeout=min(180,remaining) if label=="register" else min(study["resources"]["fit_seconds_study_cap"]+120,remaining)
  prefix=b/f"research/reviews/PVM01-ROBUSTNESS-{eid}-{label}-V1"
  print(f"{utc_now()} {label} {eid}; single invocation; timeout={timeout:.1f}",flush=True)
  result=run_bounded(["uv","run","--no-sync","nextai",*args],cwd=b,env=environment,stdout_path=prefix.with_suffix(".stdout.txt"),stderr_path=prefix.with_suffix(".stderr.txt"),timeout_seconds=timeout)
  commands.append({"label":label,"command":["uv","run","--no-sync","nextai",*args],"result":asdict(result),"raw_outputs":{p.name:sha256_file(p) for p in [prefix.with_suffix(".stdout.txt"),prefix.with_suffix(".stderr.txt")]}})
  assert result.returncode==0,(label,result.returncode,result.reason)
  if label=="register":
   assert plan_path.is_file() and status(b)["experiment_id"]==eid
except BaseException:
 error=traceback.format_exc()
finally:
 result_path=b/f"research/results/{eid}.json"
 if result_path.exists():worker_charge=_execution_fit(json.loads(result_path.read_text())["candidates"])
 else:worker_charge=_execution_fit(json.loads(p.read_text()) for p in sorted((b/f"research/tmp/{eid}").glob("*.supervisor.json")))
 wall=time.monotonic()-started;overhead=max(0.,wall-worker_charge);charge=math.ceil(overhead)+10
 auxiliary_charge(b,cid,min(charge,cap))
 if charge>cap:
  auxiliary_reserve(b,cid+"-overflow",charge-cap);auxiliary_charge(b,cid+"-overflow",charge-cap)
  error=(error or "")+"\nController overhead cap exceeded; full overflow preserved and charged; no further scope."
 receipt={"id":cid,"created_at":utc_now(),"experiment_id":eid,"study_sha256":sha256_file(study_path),"prepared_source_git_commit":source,"commands":commands,"wall_seconds":wall,"worker_full_wall_seconds_already_charged":worker_charge,"controller_overhead_seconds":overhead,"overhead_seconds_charged_conservatively":charge,"error":error,"no_retry":True}
 atomic_write_json(b/f"research/reviews/{cid}.json",receipt)
 print(json.dumps({k:receipt[k] for k in ["experiment_id","wall_seconds","worker_full_wall_seconds_already_charged","overhead_seconds_charged_conservatively","error"]}),flush=True)
 if error:raise SystemExit(1)

