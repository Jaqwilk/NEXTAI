from pathlib import Path
import json,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();o=Path('C:/Users/NATAN/Documents/ChatGPT/NEXTAI')
s=json.loads((b/'research/checks/PVM01-TRANSPORT-history-snapshot-V1.json').read_text())
mutable={'.gitignore','.gitattributes','README.md','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','config/baseline_semantics.json','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/research_program.py','src/nextai_autoresearch/integrity.py','schemas/experiment_plan.schema.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','research/REPORT.md','research/REPORT.provenance.json','research/state.json',*s['prefixes']}
def tree(root,rev):
 raw=subprocess.check_output(['git','ls-tree','-r','-z',rev],cwd=root).decode()
 return {x.split('\t',1)[1]:x.split('\t',1)[0].split()[2] for x in raw.split('\0') if x}
base='905ed709ad18d3fdc2dac863deb121cefbf1b874'
t0,tb,to=tree(b,base),tree(b,'HEAD'),tree(o,'HEAD')
m=[]
for rel,digest in s['raw_files'].items():
 if rel in mutable:continue
 assert sha256_file(b/rel)==digest,rel
 if sha256_file(o/rel)==digest:continue
 x,y=(b/rel).read_bytes(),(o/rel).read_bytes()
 assert x.replace(b'\r\n',b'\n')==y.replace(b'\r\n',b'\n'),rel
 assert t0[rel]==tb[rel]==to[rel],rel
 m.append({'path':rel,'clone_raw_sha256':digest,'original_raw_sha256':sha256_file(o/rel),'unchanged_git_blob':t0[rel],'difference':'CRLF/LF only'})
p=b/'research/laboratory/PVM01-TRANSPORT-original-checkout-EOL-V1.json'
atomic_write_json(p,{'created_at':utc_now(),'differences':m,'original_files_not_modified':True,'all_old_nonmutable_clone_raw_preserved':True,'base_revision':base,'correction':'Clone-local raw snapshot is not a raw snapshot of the distinct original checkout; prove CRLF/LF equivalence and unchanged immutable Git blobs for only these files.'})
print('All differences:',len(m));print([x['path'] for x in m][:8])
