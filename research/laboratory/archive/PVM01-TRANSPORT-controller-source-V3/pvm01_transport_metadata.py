from pathlib import Path
import json,re
from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.utils import sha256_file
b=Path.cwd(); study=json.loads((b/'research/plans/PVM01-TRANSPORT-COMPRESSION-ADVERSE-V2.json').read_text()); test='tests/test_pvm01_transport_compression.py'
nodes=re.findall(r'^def (test_\w+)\(', (b/test).read_text(),re.M)
p=b/'config/baseline_semantics.json'; raw=p.read_text(); registry=json.loads(raw); entries=[]
for name,role in study['roles'].items():
 assert name not in registry['baselines']; audit=audit_candidate(name,load_config(b),b); assert audit.ok,audit.problems
 files={audit.path.relative_to(b).as_posix():audit.sha256,**{path.relative_to(b).as_posix():digest for path,digest in audit.dependencies}}
 tests=[{'path':test,'node_id':test+'::'+node,'sha256':sha256_file(b/test)} for node in nodes]
 if role['arm'].startswith('dense'):
  old='pvm01_'+role['arm']+'_s0'; tests+=registry['baselines'][old]['conformance_tests']
 record={'baseline_id':name,'version':1,'implementation_files':files,'conformance_tests':tests,'specification':{'arm':role['arm'],'cohort':study['cohort'],'prospective_study_sha256':sha256_file(b/'research/plans/PVM01-TRANSPORT-COMPRESSION-ADVERSE-V2.json'),'no_privileged_generator_inputs':True,'all_costs_included':True,'no_architecture_novelty_claim':True}}
 entries.append('    '+json.dumps(name)+': '+json.dumps(record,ensure_ascii=False,separators=(',',':')))
ending='\n  }\n}\n'; assert raw.endswith(ending); raw=raw[:-len(ending)]+',\n'+',\n'.join(entries)+ending
start=raw.index('[',raw.index('"cohorts"')); end=raw.index(']',start); previous=raw[start:end].rstrip(); raw=raw[:start]+previous+', "paired_view_mutable_memory_v6"'+raw[end:]
assert len(json.loads(raw)['baselines'])==len(registry['baselines'])+70
p.write_text(raw,encoding='utf-8',newline='\n')
p=b/'config/research.toml';raw=p.read_bytes();old=b'benchmark_version = "paired_view_mutable_memory_v5"'; assert raw.count(old)==1;p.write_bytes(raw.replace(old,b'benchmark_version = "paired_view_mutable_memory_v6"'))
print('70 audited semantic records and v6 maintenance cohort prepared')

from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
m=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);print("Frozen maintenance source",len(m["files"]))
