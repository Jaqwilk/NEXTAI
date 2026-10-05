"""Bounded startup doctor/lab checks, without research data/model execution."""
from dataclasses import asdict
from pathlib import Path
import json, math, os, subprocess, sys, time, traceback
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b=Path.cwd(); o=b.parent/'NEXTAI'; parent='28cff0932543303de1c065ba01205c3096125757'
cid='PVM01-FRESH-FINAL-startup-V1'; observation=b/'research/reviews/PVM01-FRESH-FINAL-startup-observation-V1.json'
if '--child' in sys.argv:
    env=os.environ.copy(); env.update(PYTHONPATH=str(o/'src'),NEXTAI_PROJECT_ROOT=str(o))
    rows=[]
    for label,args in [('doctor',['doctor']),('lab',['lab','status'])]:
        prefix=b/f'research/reviews/PVM01-FRESH-FINAL-startup-{label}-V1'
        with prefix.with_suffix('.stdout.txt').open('xb') as out,prefix.with_suffix('.stderr.txt').open('xb') as err:
            result=subprocess.run(['uv','run','--no-sync','nextai',*args],cwd=o,env=env,stdout=out,stderr=err)
        rows.append({'label':label,'returncode':result.returncode,'outputs':{p.name:sha256_file(p) for p in [prefix.with_suffix('.stdout.txt'),prefix.with_suffix('.stderr.txt')]}})
        atomic_write_json(b/'research/tmp/c317-startup-commands.json',{'commands':rows})
        if result.returncode:raise SystemExit(result.returncode)
    raise SystemExit(0)
for root in (b,o):
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
    for rel in ('STOP','PAUSE','research/run.lock'):assert not (root/rel).exists(),(root,rel)
assert not observation.exists()
auxiliary_reserve(b,cid,500)
started=time.monotonic(); error=None; result=None
try:
    result=run_bounded(['uv','run','--no-sync','python',str(Path(__file__)),'--child'],cwd=b,env=os.environ.copy(),stdout_path=b/'research/tmp/c317-startup.stdout.txt',stderr_path=b/'research/tmp/c317-startup.stderr.txt',timeout_seconds=450)
    assert result.returncode==0,asdict(result)
except BaseException:error=traceback.format_exc()
wall=time.monotonic()-started; seconds=math.ceil(wall)+5
assert seconds<=500
auxiliary_charge(b,cid,seconds)
rows=json.loads((b/'research/tmp/c317-startup-commands.json').read_text(encoding='utf-8'))['commands'] if (b/'research/tmp/c317-startup-commands.json').exists() else []
values={x['label']:x['returncode'] for x in rows}
atomic_write_json(observation,{'created_at':utc_now(),'source_revision':parent,'stage_started_at':'2026-10-05T08:58:30Z','stage_deadline_at':'2026-10-05T12:58:30Z','doctor_returncode':values.get('doctor'),'lab_returncode':values.get('lab'),'commands':rows,'result':asdict(result) if result else None,'error':error,'wall_seconds':wall,'conservative_seconds_to_charge':seconds,'reserved_before_testing':True,'charge_id':cid,'charge_completed':True,'new_research_arrays_fit_registration_scoring':False})
print(json.dumps({'startup':values,'wall_seconds':wall,'charged':seconds,'error':error}),flush=True)
if error:raise SystemExit(1)
