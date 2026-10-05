from pathlib import Path
import json,os,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
b=Path.cwd();o=b.parent/'NEXTAI'
first=json.loads((b/'research/reviews/PVM01-REPLICATION-original-closure-V2.json').read_text())
assert first['result']['returncode']==1
assert 'Additional properties are not allowed' in (b/'research/reviews/PVM01-REPLICATION-original-doctor-V2.stdout.txt').read_text(encoding='utf8')
assert json.loads((o/'research/state.json').read_text())['last_literature_review_completed_experiments']==117
for identity in ['EXP-20261005-0001','EXP-20261005-0002']:
    pub=json.loads((o/f'research/laboratory/{identity}-publication-V2.json').read_text())
    assert sha256_file(o/pub['native_path'])==pub['native_sha256']
assert verify_manifest(o)['ok'];verify_preflight_certificate(o)
environment=os.environ.copy();environment['PYTHONPATH']=str(o/'src');environment['NEXTAI_PROJECT_ROOT']=str(o)
commands=[]
for label,args in [('doctor',['nextai','doctor']),('lab',['nextai','lab','status'])]:
    prefix=b/f'research/reviews/PVM01-REPLICATION-original-{label}-V3'
    with prefix.with_suffix('.stdout.txt').open('xb') as out,prefix.with_suffix('.stderr.txt').open('xb') as err:
        result=subprocess.run(['uv','run','--no-sync',*args],cwd=o,env=environment,stdout=out,stderr=err)
    commands.append({'label':label,'returncode':result.returncode,'raw_outputs':{p.name:sha256_file(p) for p in [prefix.with_suffix('.stdout.txt'),prefix.with_suffix('.stderr.txt')]}})
    assert result.returncode==0,label
atomic_write_json(b/'research/reviews/PVM01-REPLICATION-original-gates-V3.json',{'created_at':utc_now(),'original_root':str(o),'commands':commands,'both_native_hashes_verified':True,'history_integrity_preflight_doctor_lab':True,'history_receipt':'research/reviews/PVM01-REPLICATION-history-original-postrun-V1.json','failed_V1_check_preserved':'research/reviews/PVM01-REPLICATION-original-closure-V2.json','required_review':'research/reviews/PVM01-LITERATURE-CYCLE-313-V1.md','cadence_unchanged':True,'no_new_seed_data_model_fit_scoring':True,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=o,text=True).strip()})
print('Original exact hashes/integrity/preflight and repaired-cadence doctor/lab PASS',flush=True)

