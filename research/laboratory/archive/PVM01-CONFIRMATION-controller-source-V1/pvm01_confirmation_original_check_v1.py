from pathlib import Path
import json,os,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();o=b.parent/'NEXTAI'
environment=os.environ.copy();environment['PYTHONPATH']=str(o/'src');environment['NEXTAI_PROJECT_ROOT']=str(o)
commands=[]
for label,args,cwd in [
 ('restore-old',['python','scripts/restore_pvm01_transport_result.py'],o),
 ('restore-new',['python','scripts/restore_pvm01_replication_result.py'],o),
 ('restore-dense-noise',['python','scripts/restore_pvm01_dense_noise_result.py'],o),
 ('restore-confirmation',['python','scripts/restore_pvm01_confirmation_result.py'],o),
 ('history',['python',str(b/'research/tmp/pvm01_confirmation_history_v1.py'),'--original','--postrun'],b),
 ('frozen-reanalysis',['python','scripts/analyze_pvm01_confirmation.py','EXP-20261005-0004'],o),
 ('doctor',['nextai','doctor'],o),
 ('lab',['nextai','lab','status'],o)]:
    prefix=b/f'research/reviews/PVM01-CONFIRMATION-original-{label}-V1'
    with prefix.with_suffix('.stdout.txt').open('xb') as out,prefix.with_suffix('.stderr.txt').open('xb') as err:
        result=subprocess.run(['uv','run','--no-sync',*args],cwd=cwd,env=environment,stdout=out,stderr=err)
    commands.append({'label':label,'returncode':result.returncode,'raw_outputs':{p.name:sha256_file(p) for p in [prefix.with_suffix('.stdout.txt'),prefix.with_suffix('.stderr.txt')]}})
    assert result.returncode==0,label
atomic_write_json(b/'research/reviews/PVM01-CONFIRMATION-original-gates-V1.json',{'created_at':utc_now(),'original_root':str(o),'commands':commands,'all_four_native_hashes_verified':True,'history_integrity_preflight_doctor_lab':True,'no_new_seed_data_model_fit_scoring':True,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=o,text=True).strip()})
print('Original exact restoration/history/integrity/preflight/doctor/lab PASS',flush=True)
