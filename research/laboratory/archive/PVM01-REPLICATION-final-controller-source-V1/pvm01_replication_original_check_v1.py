from pathlib import Path
import json,os,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();o=b.parent/'NEXTAI'
environment=os.environ.copy();environment['PYTHONPATH']=str(o/'src');environment['NEXTAI_PROJECT_ROOT']=str(o)
commands=[]
for label,args,cwd in [
 ('restore-old',['python','scripts/restore_pvm01_transport_result.py'],o),
 ('restore-new',['python','scripts/restore_pvm01_replication_result.py'],o),
 ('history',['python',str(b/'research/tmp/pvm01_replication_history_postrun_v1.py'),'--original'],b),
 ('doctor',['nextai','doctor'],o),
 ('lab',['nextai','lab','status'],o)]:
    prefix=b/f'research/reviews/PVM01-REPLICATION-original-{label}-V1'
    with prefix.with_suffix('.stdout.txt').open('xb') as out,prefix.with_suffix('.stderr.txt').open('xb') as err:
        result=subprocess.run(['uv','run','--no-sync',*args],cwd=cwd,env=environment,stdout=out,stderr=err)
    commands.append({'label':label,'returncode':result.returncode,'raw_outputs':{p.name:sha256_file(p) for p in [prefix.with_suffix('.stdout.txt'),prefix.with_suffix('.stderr.txt')]}})
    assert result.returncode==0,label
atomic_write_json(b/'research/reviews/PVM01-REPLICATION-original-gates-V1.json',{'created_at':utc_now(),'original_root':str(o),'commands':commands,'both_native_hashes_verified':True,'history_integrity_preflight_doctor_lab':True,'no_new_seed_data_model_fit_scoring':True,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=o,text=True).strip()})
print('Original exact restoration/history/integrity/preflight/doctor/lab PASS',flush=True)
