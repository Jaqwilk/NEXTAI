from pathlib import Path
import json
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd()
r=json.loads((b/'research/reviews/PVM01-BASE-REFERENCE-targeted-V1.json').read_text(encoding='utf-8'))
assert r['result']['returncode']==0 and not r['error']
p=b/'config/research.toml'; raw=p.read_bytes(); old=b'benchmark_version = "paired_view_mutable_memory_v9"'; assert raw.count(old)==1; p.write_bytes(raw.replace(old,b'benchmark_version = "paired_view_mutable_memory_v10"'))
manifest=freeze_manifest(b,overwrite=True); write_preflight_certificate(b); write_report(b)
rels=[*manifest['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json']
arc=b/'research/laboratory/archive/PVM01-BASE-REFERENCE-validation-source-V1'
for rel in dict.fromkeys(rels):
    target=arc/('root.gitattributes.raw' if rel=='.gitattributes' else rel); target.parent.mkdir(parents=True,exist_ok=True)
    assert not target.exists(); target.write_bytes((b/rel).read_bytes())
prereg=json.loads((b/'research/tmp/PVM01-BASE-REFERENCE-preregistration-V1.json').read_text(encoding='utf-8'))
atomic_write_json(b/'research/checks/PVM01-BASE-REFERENCE-validation-source-V1.json',{'created_at':utc_now(),'preregistration_git_commit':prereg['preregistration_git_commit'],'files':{rel:sha256_file(b/rel) for rel in dict.fromkeys(rels)},'new_scored_arrays_fit':False,'protected_files':len(manifest['files'])})
print('Frozen v9 maintenance',len(manifest['files']),flush=True)
