"""Bound the previously reserved 300-second no-scoring closure/publication envelope."""
from pathlib import Path
from dataclasses import asdict
import json, os, subprocess, sys, time
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge
from nextai_autoresearch.utils import atomic_write_json, utc_now
b=Path.cwd();cid='PVM01-CONFIRMATION-final-administration-prepaid-V1'
if '--child' in sys.argv:
    for name in ('pvm01_confirmation_close_v1.py','pvm01_confirmation_final_sync_v1.py'):
        subprocess.run(['uv','run','--no-sync','python',str(b/'research/tmp'/name)],cwd=b,check=True)
    raise SystemExit(0)
check=json.loads((b/'research/reviews/PVM01-CONFIRMATION-original-closure-V1.json').read_text(encoding='utf-8'))
assert check['result']['returncode']==0 and not check['error']
events=read_jsonl(b/'research/events.jsonl')
charged=sum(e['seconds'] for e in events if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-CONFIRMATION-'))
assert charged+300<=3600 and not any(e.get('charge_id')==cid for e in events)
started=time.monotonic()
result=run_bounded(['uv','run','--no-sync','python',str(Path(__file__)),'--child'],cwd=b,env=os.environ.copy(),stdout_path=b/'research/tmp/c315-admin.stdout.txt',stderr_path=b/'research/tmp/c315-admin.stderr.txt',timeout_seconds=285)
events=read_jsonl(b/'research/events.jsonl')
if not any(e.get('event')=='research_program_aux_fit_charged' and e.get('charge_id')==cid for e in events):
    auxiliary_reserve(b,cid,300);auxiliary_charge(b,cid,300)
assert time.monotonic()-started<300
value={'created_at':utc_now(),'scope':'No-scoring final administration','result':asdict(result),'wall_seconds':time.monotonic()-started,'conservative_seconds_charged':300,'all_child_processes_bounded':True,'new_registration_data_fit_scoring':False}
atomic_write_json(b/'research/tmp/PVM01-CONFIRMATION-final-administration-observation-V1.json',value)
for name in ('c315-admin.stdout.txt','c315-admin.stderr.txt'):
    contents=(b/'research/tmp'/name).read_text(encoding='utf-8');print(contents,end='')
print(json.dumps(value),flush=True)
raise SystemExit(result.returncode)