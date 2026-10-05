from pathlib import Path
import subprocess,json
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
b=Path.cwd();o=b.parent/'NEXTAI'
assert verify_manifest(b)['ok'];verify_preflight_certificate(b)
generated=['research/REPORT.md','research/REPORT.provenance.json']
changed=subprocess.check_output(['git','diff','--name-only'],cwd=o,text=True).splitlines()
assert set(changed)<=set(generated),changed
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=o,text=True).strip()
arc=b/'research/laboratory/archive/PVM01-REPLICATION-original-pre-review-generated-V1';arc.mkdir()
for rel in generated:
    target=arc/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((o/rel).read_bytes())
    (o/rel).write_bytes(subprocess.check_output(['git','show','HEAD:'+rel],cwd=o))
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('research/REPORT','research/events.jsonl','research/state.json','research/sources.jsonl','research/reviews/PVM01-REPLICATION-original-','research/reviews/PVM01-REPLICATION-history-original-','research/reviews/PVM01-LITERATURE-CYCLE-313','research/laboratory/archive/PVM01-REPLICATION-original-pre-review-')
for rel in paths:assert rel.startswith(allowed),rel
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Complete required six-experiment literature review without changing gates'],check=True)
subprocess.run(['git','fetch','-q',str(b),'codex/muc03-autonomous-20261004'],cwd=o,check=True)
with (b/'research/tmp/PVM01-REPLICATION-original-review-FF-V1.log').open('xb') as out:
    subprocess.run(['git','merge','--ff-only','FETCH_HEAD'],cwd=o,check=True,stdout=out,stderr=out)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=o).strip()
print('Required review synchronized before new doctor/lab check',flush=True)
