from pathlib import Path
import hashlib,json,os,subprocess,sys
b=Path(__file__).resolve().parents[2]
o=Path('C:/Users/NATAN/Documents/ChatGPT/NEXTAI')
os.environ.update(PYTHONPATH=str(o/'src'),NEXTAI_PROJECT_ROOT=str(o),PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,str(o/'src'))
import nextai_autoresearch
from nextai_autoresearch.report import write_report
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import read_jsonl
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(o/'src')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=b,text=True).strip()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=o,text=True).strip()==head
pub=json.loads((b/'research/laboratory/EXP-20261005-0001-publication-V2.json').read_text())
subprocess.run([sys.executable,str(o/'scripts/restore_pvm01_transport_result.py')],cwd=o,env=os.environ.copy(),check=True)
assert sha256_file(o/pub['native_path'])==pub['native_sha256']
assert sha256_file(b/pub['native_path'])==pub['native_sha256']
assert verify_manifest(o)['ok'];verify_preflight_certificate(o)
snap=json.loads((o/'research/checks/PVM01-TRANSPORT-history-snapshot-V1.json').read_text())
mutable={'.gitignore','.gitattributes','README.md','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','config/baseline_semantics.json','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/research_program.py','src/nextai_autoresearch/integrity.py','schemas/experiment_plan.schema.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','research/REPORT.md','research/REPORT.provenance.json','research/state.json',*snap['prefixes']}
old_ignore=o/'research/laboratory/archive/EXP-20261005-0001-publication-source/root.gitignore.before.raw'
assert sha256_file(old_ignore)==snap['raw_files']['.gitignore']
assert (o/'.gitignore').read_bytes().startswith(old_ignore.read_bytes())
assert sha256_file(o/'research/laboratory/archive/README-PRESENTATION-20261005-V1/README.md.raw')==snap['raw_files']['README.md']
assert sha256_file(o/'README.md')=='39db095f752b0a31bf86cc7ad270af413986e1c0dbf68ec526ae36faf3d34671'
checked=0
for rel,digest in snap['raw_files'].items():
 if rel in mutable:continue
 assert sha256_file(o/rel)==digest,rel
 checked+=1
for rel,record in snap['prefixes'].items():
 raw=(o/rel).read_bytes()
 assert hashlib.sha256(raw[:record['length']]).hexdigest()==record['sha256'],rel
 if rel.endswith('.jsonl'):read_jsonl(o/rel)
archive=o/'research/laboratory/archive/PVM01-TRANSPORT-previous-source-V1'
for rel in ['AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md']:
 assert (o/rel).read_bytes().endswith((archive/rel).read_bytes()),rel
for root in (o,b):
 for rel in ['STOP','PAUSE','research/run.lock']:assert not (root/rel).exists(),str(root/rel)
write_report(o)
records={}
for label,args in [('doctor',['doctor']),('lab',['lab','status'])]:
 stem=b/'research/reviews'/f'PVM01-TRANSPORT-original-{label}-V1'
 with stem.with_suffix('.stdout.txt').open('xb') as out,stem.with_suffix('.stderr.txt').open('xb') as err:
  r=subprocess.run(['uv','run','--no-sync','nextai',*args],cwd=o,env=os.environ.copy(),stdout=out,stderr=err)
 assert r.returncode==0,(label,r.returncode)
 text=stem.with_suffix('.stdout.txt').read_text(encoding='utf-8')
 if label=='doctor':assert 'Doctor: PASS' in text and '[ERROR]' not in text
 else:
  lab=json.loads(text);assert lab['errors']==[] and lab['scoring_ready'] is False and lab['scoring_authorized'] is False
 records[label]={'returncode':r.returncode,'stdout_sha256':sha256_file(stem.with_suffix('.stdout.txt')),'stderr_sha256':sha256_file(stem.with_suffix('.stderr.txt'))}
 print('Original',label,'PASS',flush=True)
for rel in ['research/REPORT.md','research/REPORT.provenance.json']:
 p=b/'research/laboratory/archive/PVM01-TRANSPORT-original-validation-V1'/rel
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((o/rel).read_bytes())
accounting=status(o)
assert accounting['program_closed'] is False and accounting['study_terminal'] is True and accounting['scoring_authorized'] is False
receipt={'created_at':utc_now(),'validated_head':head,'original_root':str(o),'original_import_path':str(nextai_autoresearch.__file__),
 'native_result_sha256':pub['native_sha256'],'old_nonmutable_raw_files_checked':checked,'old_prefixes_preserved':True,
 'original_user_readme_preserved':True,'integrity':verify_manifest(o),'preflight':True,'cli':records,
 'program_status_before_validation_job_charge':accounting,'one_research_run_no_retry':True}
atomic_write_json(b/'research/reviews/PVM01-TRANSPORT-original-validation-V1.json',receipt)
print(json.dumps({'original_validation':'PASS','old_raw_files_checked':checked,'scoring':False,'head':head}),flush=True)
