from pathlib import Path
from dataclasses import asdict
import json,os,subprocess,time,traceback
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();outer='PVM01-FRESH-FINAL-postrun-V1';commands=[]
for label,name,extra in (
 ('native-analysis-preservation','post',[]),
 ('publication','publish',[]),
 ('report-metadata','report_metadata',[]),
 ('history-postrun','history',['--postrun'])):
    stem=b/f'research/reviews/PVM01-FRESH-FINAL-{label}-V1'
    command=['uv','run','--no-sync','python',str(b/f'research/tmp/pvm01_fresh_final_{name}_v1.py'),*extra]
    started=time.monotonic();error=None;result=None
    try:
        with stem.with_suffix('.stdout.txt').open('xb') as out,stem.with_suffix('.stderr.txt').open('xb') as err:
            result=subprocess.run(command,cwd=b,env=os.environ.copy(),stdout=out,stderr=err)
    except BaseException:error=traceback.format_exc()
    receipt={'id':stem.name,'created_at':utc_now(),'command':command,'wall_seconds':time.monotonic()-started,'result':{'returncode':result.returncode} if result else None,'error':error,'whole_process_tree_bound_and_charge':'research/reviews/'+outer+'.json','charge_is_outer_batch_once_not_per_child':True,'raw_outputs':{p.name:sha256_file(p) for p in (stem.with_suffix('.stdout.txt'),stem.with_suffix('.stderr.txt')) if p.exists()}}
    atomic_write_json(stem.with_suffix('.json'),receipt);commands.append(receipt)
    print(json.dumps({'phase':label,'returncode':result.returncode if result else None,'wall_seconds':receipt['wall_seconds'],'error':error}),flush=True)
    if error or result is None or result.returncode!=0:raise SystemExit(1)
print('All postrun phases completed once under a single reserved whole-tree envelope',flush=True)