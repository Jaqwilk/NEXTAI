from pathlib import Path
import json,subprocess
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import sha256_file,utc_now
from nextai_autoresearch.report import write_report
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
b=Path.cwd();o=b.parent/'NEXTAI';cid='PVM01-REPLICATION-source-scope-tests-V1'
r=json.loads((b/f'research/reviews/{cid}.json').read_text());assert r['result']['returncode']==0 and not r['error']
assert verify_manifest(b)['ok'];verify_preflight_certificate(b)
s=json.loads((b/'research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json').read_text())
assert all(sha256_file(b/name)==value for name,value in s['independent_replication']['scientific_source_sha256_unchanged'].items())
append_jsonl(b/'research/events.jsonl',{'event':'maintenance_repair_validated','created_at':utc_now(),'plan_path':'research/plans/PVM01-SOURCE-SCOPE-METADATA-REPAIR-V1.json','schema_after_sha256':sha256_file(b/'schemas/source.schema.json'),'test_receipt':f'research/reviews/{cid}.json','tests_passed':16,'old_sources_preserved':True,'scientific_recipes_metrics_thresholds_unchanged':True,'scoring':False})
write_report(b)
generated=['research/REPORT.md','research/REPORT.provenance.json']
changed=subprocess.check_output(['git','diff','--name-only'],cwd=o,text=True).splitlines();assert set(changed)<=set(generated)
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=o).strip()
arc=b/'research/laboratory/archive/PVM01-REPLICATION-original-pre-scope-generated-V1';arc.mkdir()
for rel in generated:
    target=arc/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((o/rel).read_bytes())
    (o/rel).write_bytes(subprocess.check_output(['git','show','HEAD:'+rel],cwd=o))
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('research/REPORT','research/events.jsonl','research/eval_manifest.json','research/checks/PVM01-REPLICATION-source-scope-','research/plans/PVM01-SOURCE-SCOPE-','research/laboratory/archive/PVM01-SOURCE-SCOPE-','research/laboratory/archive/PVM01-REPLICATION-original-pre-scope-','research/laboratory/preflight_certificate','research/laboratory/certificates/','research/manifests/','research/reviews/PVM01-REPLICATION-original-','research/reviews/PVM01-REPLICATION-source-scope-')
for rel in paths:assert rel in {'schemas/source.schema.json','tests/test_source_review_scope.py'} or rel.startswith(allowed),rel
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Validate explicit review-scope metadata while retaining strict source schema'],check=True)
subprocess.run(['git','fetch','-q',str(b),'codex/muc03-autonomous-20261004'],cwd=o,check=True)
with (b/'research/tmp/PVM01-REPLICATION-original-scope-FF-V1.log').open('xb') as out:subprocess.run(['git','merge','--ff-only','FETCH_HEAD'],cwd=o,check=True,stdout=out,stderr=out)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=o).strip()
print('Typed metadata conformance synchronized; scientific source hashes unchanged',flush=True)
