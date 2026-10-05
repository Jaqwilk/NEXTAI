from pathlib import Path
import json
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();r=json.loads((b/'research/reviews/PVM01-ROBUSTNESS-targeted-V3.json').read_text())
assert r['result']['returncode']==0 and not r['error']
assert b'benchmark_status = "maintenance"' in (b/'config/research.toml').read_bytes()
append_jsonl(b/'research/events.jsonl',{'event':'laboratory_preparation_decision_policy_conformance','created_at':utc_now(),'cycle':314,'study_path':'research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json','receipt':'research/reviews/PVM01-ROBUSTNESS-targeted-V3.json','cause':'Implemented the preregistered invalid-reference INCONCLUSIVE classification explicitly; no metric, gate, recipe, budget or completed outcome changed.','scored_experiment':False})
m=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
rels=[*m['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json']
arc=b/'research/laboratory/archive/PVM01-ROBUSTNESS-validation-source-V2'
for rel in dict.fromkeys(rels):
 target=arc/('root.gitattributes.raw' if rel=='.gitattributes' else rel);target.parent.mkdir(parents=True,exist_ok=True)
 assert not target.exists();target.write_bytes((b/rel).read_bytes())
atomic_write_json(b/'research/checks/PVM01-ROBUSTNESS-validation-source-V2.json',{'created_at':utc_now(),'preregistration_git_commit':'e2342788c37e9bcb7d80db9331e9c2e825c695cf','files':{rel:sha256_file(b/rel) for rel in dict.fromkeys(rels)},'new_scored_arrays_fit':False,'protected_files':len(m['files']),'first_validation_source_preserved':True})
print('Frozen final v8 maintenance',len(m['files']),flush=True)
