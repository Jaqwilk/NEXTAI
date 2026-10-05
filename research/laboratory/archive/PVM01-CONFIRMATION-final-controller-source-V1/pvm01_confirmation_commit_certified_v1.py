from pathlib import Path
import json,subprocess
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.research_program import status
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import sha256_file
b=Path.cwd()
r=json.loads((b/'research/reviews/PVM01-CONFIRMATION-prepaid-V2.json').read_text(encoding='utf-8'))
assert r['result']['returncode']==0 and not r['error']
assert json.loads((b/'research/reviews/PVM01-CONFIRMATION-prepaid-gates-V1.json').read_text(encoding='utf-8'))['can_create_plan']
assert verify_manifest(b)['ok'];verify_preflight_certificate(b)
s=status(b);assert s['ready'] and s['scoring_authorized'] and s['experiment_id'] is None
study=json.loads((b/'research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json').read_text(encoding='utf-8'))
assert all(sha256_file(b/path)==value for path,value in study['parent_evidence']['scientific_source_sha256_unchanged'].items())
arc=b/'research/laboratory/archive/PVM01-CONFIRMATION-controller-source-V1'
for name in [p.name for p in sorted((b/'research/tmp').glob('pvm01_confirmation_*.py')) if 'startup' not in p.name]:
    source=b/'research/tmp'/name;target=arc/name
    assert source.is_file() and not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
write_report(b)
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('research/checks/PVM01-CONFIRMATION-','research/REPORT','research/events.jsonl','research/eval_manifest.json','research/plans/PVM01-CONFIRMATION-','research/laboratory/PVM01-','research/laboratory/archive/PVM01-CONFIRMATION-','research/laboratory/preflight_certificate','research/laboratory/certificates/','research/manifests/','research/reviews/PVM01-CONFIRMATION-')
for rel in paths:
    assert rel=='config/research.toml' or rel.startswith(allowed),rel
    assert (b/rel).stat().st_size<99_000_000,rel
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Certify one dense-noise intervention after checkout byte and clone conformance'],check=True)
assert not subprocess.check_output(['git','status','--porcelain']).strip()
print('Certified clean source',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),flush=True)
