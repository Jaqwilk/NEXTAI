from pathlib import Path
from dataclasses import asdict
import json,math,os,time,traceback,subprocess
from nextai_autoresearch.research_program import auxiliary_reserve,auxiliary_charge,status
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import utc_now,atomic_write_json,sha256_file
b=Path.cwd();cid='PVM01-CONFIRMATION-startup-V1';started=time.monotonic()
for rel in ['STOP','PAUSE','research/run.lock']:assert not (b/rel).exists(),rel
assert not subprocess.check_output(['git','status','--porcelain'],text=True).strip()
auxiliary_reserve(b,cid,600)
write_report(b)
out=b/'research/reviews'/cid
result,error=None,None
try:
 env=os.environ.copy()
 env.update(CUBLAS_WORKSPACE_CONFIG=':4096:8',PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 result=run_bounded(['uv','run','--no-sync','python','research/tmp/pvm01_confirmation_startup_child_v1.py'],cwd=b,env=env,stdout_path=out.with_suffix('.stdout.txt'),stderr_path=out.with_suffix('.stderr.txt'),timeout_seconds=max(1,560-(time.monotonic()-started)))
except BaseException:error=traceback.format_exc()
wall=time.monotonic()-started;charged=math.ceil(wall)+5
auxiliary_charge(b,cid,min(charged,600))
if charged>600:
 auxiliary_reserve(b,cid+'-overflow',charged-600);auxiliary_charge(b,cid+'-overflow',charged-600)
 error=(error or '')+'\nStartup overflow; stop unstarted scope.'
arc=b/'research/laboratory/archive/PVM01-CONFIRMATION-startup-V1';arc.mkdir()
for name in ['pvm01_confirmation_startup_child_v1.py','pvm01_confirmation_startup_controller_v1.py']:
 (arc/name).write_bytes((b/'research/tmp'/name).read_bytes())
receipt={'id':cid,'created_at':utc_now(),'base_commit':'ecbbb2b3cfebb331944350766e49b3f5f62d23f0','proposed_cycle':315,
 'purpose':'Unchanged-source startup for prospective independent fixed-recipe confirmation; no model/data/EXP or scored retry.',
 'seconds_cap':600,'wall_seconds':wall,'seconds_charged':charged,'result':asdict(result) if result else None,'error':error,
 'old_study_costs_and_outcomes_unchanged':True,'budget_source':'standing continuation A; anticipated confirmation auxiliary cost',
 'raw_outputs':{p.name:sha256_file(p) for p in [out.with_suffix('.stdout.txt'),out.with_suffix('.stderr.txt')] if p.exists()}}
atomic_write_json(out.with_suffix('.json'),receipt);write_report(b)
print(json.dumps(receipt),flush=True)
raise SystemExit(result.returncode if result and not error else 1)
