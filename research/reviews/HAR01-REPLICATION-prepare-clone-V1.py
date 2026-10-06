"""One clone conformance/intake/readiness sequence under frozen preparation clock."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
import os,sys,shutil,traceback
import xml.etree.ElementTree as ET
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.research_program import auxiliary_charge
from nextai_autoresearch.utils import atomic_write_json,load_json,sha256_file,utc_now
ROOT=Path.cwd();CLONE=ROOT.parent/'NEXTAI-VALIDATION-20261002';STUDY='research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json';SHA='d5567973e85b444d95ac13a70db9fe24b87c0ab3b672932e8322862c336ad12a'
BINDING='research/reviews/HAR01-REPLICATION-SOURCE-BINDING-V1.json'
DEADLINE=datetime.fromisoformat('2026-10-06T15:16:00+00:00')
def main():
 prefix=ROOT/'research/reviews/HAR01-REPLICATION-preparation-V1';assert not prefix.with_suffix('.started.json').exists()
 assert sha256_file(ROOT/STUDY)==sha256_file(CLONE/STUDY)==SHA
 binding=load_json(ROOT/BINDING)
 for p,digest in binding['files'].items():assert sha256_file(ROOT/p)==sha256_file(CLONE/p)==digest,p
 atomic_write_json(prefix.with_suffix('.started.json'),{'created_at':utc_now(),'study_sha256':SHA,'attempt':1})
 env=os.environ.copy();env.update(PYTHONPATH=str(CLONE/'src'),NEXTAI_PROJECT_ROOT=str(CLONE),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUBLAS_WORKSPACE_CONFIG=':4096:8')
 jobs=[];error=None;count=0;ready=False
 def run(label,args,cap):
  remaining=(DEADLINE-datetime.now(timezone.utc)).total_seconds()-90
  if remaining<=0:raise TimeoutError('Frozen preparation closing reserve exhausted')
  out=ROOT/f'research/reviews/HAR01-REPLICATION-{label}-V1'
  result=run_bounded([str(CLONE/'.venv/Scripts/python.exe'),*args],cwd=CLONE,env=env,stdout_path=out.with_suffix('.stdout.txt'),stderr_path=out.with_suffix('.stderr.txt'),timeout_seconds=min(cap,remaining))
  record={'created_at':utc_now(),'study_sha256':SHA,'tested_source_files_sha256':binding['files'],'package_origin':str(CLONE/'src/nextai_autoresearch/__init__.py'),'result':asdict(result),'error':None,'command':args};atomic_write_json(out.with_suffix('.json'),record);shutil.copyfile(out.with_suffix('.json'),CLONE/'research/reviews'/out.with_suffix('.json').name)
  jobs.append({'label':label,**asdict(result)})
  if result.returncode!=0 or result.exit_live_descendant_pids:raise RuntimeError(f'{label} failed; no retry or native continuation')
  return out,result
 try:
  tests=['tests/test_har01_replication_budget.py','tests/test_har01_replication_intake.py','tests/test_har01_replication_analysis.py','tests/test_har01_replication_integration.py','tests/test_har01_intake.py','tests/test_har01_native_transfer.py','tests/test_har01_analysis_contract.py','tests/test_transfer_program_authority.py','tests/test_process_supervision.py']
  xml=CLONE/'research/reviews/HAR01-REPLICATION-conformance-V1.xml'
  out,result=run('conformance',['-m','pytest','-q','-x',*tests,f'--junitxml={xml}'],240)
  shutil.copyfile(xml,ROOT/'research/reviews'/xml.name);cases=ET.parse(xml).findall('.//testcase');count=len(cases)
  assert count>0 and not any(any(c.find(k) is not None for k in ('error','failure','skipped')) for c in cases)
  run('intake',['scripts/acquire_har01_replication.py'],120)
  run('readiness',['scripts/check_har01_replication_readiness.py','--ready','--expected-cases',str(count),'--required-node','tests.test_har01_replication_integration::test_independent_clone_package_provenance'],180)
  ready=True
 except BaseException:error=traceback.format_exc()
 finally:
  auxiliary_charge(ROOT,'HAR01-REPLICATION-preparation-V1',1200)
  receipt={'created_at':utc_now(),'study_sha256':SHA,'ready':ready,'error':error,'jobs':jobs,'conformance_cases':count,'charged_preparation_seconds':1200,'preparation_clock_start':'2026-10-06T14:56:00Z','preparation_deadline':'2026-10-06T15:16:00Z','fit':0,'EXP':0,'retry':False,'source_binding_sha256':sha256_file(ROOT/BINDING)}
  atomic_write_json(ROOT/'research/laboratory/HAR01-REPLICATION-PREPARATION-COMPLETION-V1.receipt.json',receipt)
  print(receipt,flush=True)
 return 0 if ready and not error else 1
if __name__=='__main__':raise SystemExit(main())
