from pathlib import Path
import json,subprocess
from nextai_autoresearch.utils import sha256_file,atomic_write_json,utc_now
b=Path.cwd();exception=['research/checks/PVM01-FRESH-FINAL-targeted-V2.xml','research/reviews/PVM01-FRESH-FINAL-targeted-V2.stdout.txt']
result=subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],capture_output=True)
assert result.returncode==2
errors=result.stdout.decode('utf-8');reported=[line.split(':',1)[0] for line in errors.splitlines() if 'trailing whitespace.' in line]
assert reported==exception,reported
rel='research/reviews/PVM01-FRESH-FINAL-native-trace-whitespace-V1.json';assert not (b/rel).exists()
atomic_write_json(b/rel,{'created_at':utc_now(),'observation':'The validation commit stopped because preserved failed pytest raw stdout/XML contain trailing space in the original traceback. Their bytes are scientific failure evidence and must not be rewritten. This is a formatting-only Git check,not a test or scientific gate failure.','git_check_returncode':result.returncode,'git_check_output':errors,'preserved_raw_trace_sha256':{p:sha256_file(b/p) for p in exception},'action':'Verify all other staged files with diff --check,exclude exactly these two byte-preserved raw artifacts and resume the interrupted commit. No data,model,metric,threshold,cap,deadline or paid registration change.','new_fit_arrays_scoring_registration':False,'charged_administrative_envelope':'PVM01-FRESH-FINAL-administration-prepaid-V1'})
subprocess.run(['git','add','--',rel],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check','--','.',*[f':(exclude){p}' for p in exception]],check=True)
assert all(sha256_file(b/p)==digest for p,digest in json.loads((b/rel).read_text())['preserved_raw_trace_sha256'].items())
subprocess.run(['git','commit','-q','-m','Validate frozen fresh final while preserving every failed raw trace byte'],check=True)
assert not subprocess.check_output(['git','status','--porcelain']).strip()
print('Validated clean source',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),flush=True)