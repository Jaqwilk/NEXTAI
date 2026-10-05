from pathlib import Path
import json,subprocess
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd()
r=json.loads((b/'research/reviews/PVM01-ROBUSTNESS-targeted-V2.json').read_text());assert r['result']['returncode']==0 and not r['error']
append_jsonl(b/'research/events.jsonl',{'event':'laboratory_preparation_fixture_corrected','created_at':utc_now(),'cycle':314,'study_path':'research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json','failed_receipt':'research/reviews/PVM01-ROBUSTNESS-targeted-V1.json','corrected_receipt':'research/reviews/PVM01-ROBUSTNESS-targeted-V2.json','cause':'Test invoked established audit_candidate API incorrectly; fixed fixture signature only, no training/metrics/threshold changes.','scored_experiment':False})
p=b/'config/research.toml';raw=p.read_bytes();old=b'benchmark_version = "paired_view_mutable_memory_v7"';assert raw.count(old)==1;p.write_bytes(raw.replace(old,b'benchmark_version = "paired_view_mutable_memory_v8"'))
m=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
rels=[*m['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json']
arc=b/'research/laboratory/archive/PVM01-ROBUSTNESS-validation-source-V1'
for rel in dict.fromkeys(rels):
 target=arc/('root.gitattributes.raw' if rel=='.gitattributes' else rel);target.parent.mkdir(parents=True,exist_ok=True)
 assert not target.exists();target.write_bytes((b/rel).read_bytes())
atomic_write_json(b/'research/checks/PVM01-ROBUSTNESS-validation-source-V1.json',{'created_at':utc_now(),'preregistration_git_commit':'e2342788c37e9bcb7d80db9331e9c2e825c695cf','files':{rel:sha256_file(b/rel) for rel in dict.fromkeys(rels)},'new_scored_arrays_fit':False,'protected_files':len(m['files'])})
print('Frozen v8 maintenance',len(m['files']),flush=True)
