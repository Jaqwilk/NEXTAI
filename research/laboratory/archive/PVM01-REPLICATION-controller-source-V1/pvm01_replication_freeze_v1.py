from pathlib import Path
import json,subprocess
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd()
p=b/'config/research.toml';raw=p.read_bytes();old=b'benchmark_version = "paired_view_mutable_memory_v6"';assert raw.count(old)==1;p.write_bytes(raw.replace(old,b'benchmark_version = "paired_view_mutable_memory_v7"'))
m=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
rels=[*m['files'],'scripts/analyze_pvm01_replication.py','scripts/run_pvm01_replication_check.py','research/eval_manifest.json','research/laboratory/preflight_certificate.json']
arc=b/'research/laboratory/archive/PVM01-REPLICATION-validation-source-V1'
for rel in dict.fromkeys(rels):
    target=arc/('root.gitattributes.raw' if rel=='.gitattributes' else rel)
    target.parent.mkdir(parents=True,exist_ok=True)
    assert not target.exists()
    target.write_bytes((b/rel).read_bytes())
atomic_write_json(b/'research/checks/PVM01-REPLICATION-validation-source-V1.json',{'created_at':utc_now(),'preregistration_git_commit':'430e4e45a249ce0ec69e335bb04adda7f81ff913','files':{rel:sha256_file(b/rel) for rel in dict.fromkeys(rels)},'new_scored_arrays_fit':False,'protected_files':len(m['files'])})
print('Frozen v7 maintenance',len(m['files']))
