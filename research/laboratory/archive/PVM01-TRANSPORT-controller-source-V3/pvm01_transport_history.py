from pathlib import Path
import argparse,hashlib,json
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);args=parser.parse_args()
b=Path.cwd();s=json.loads((b/'research/checks/PVM01-TRANSPORT-history-snapshot-V1.json').read_text())
mutable={'.gitattributes','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','config/baseline_semantics.json','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/research_program.py','src/nextai_autoresearch/integrity.py','schemas/experiment_plan.schema.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','research/REPORT.md','research/REPORT.provenance.json','research/state.json',*s['prefixes']}
checked=0
for name,digest in s['raw_files'].items():
 if name in mutable:continue
 assert sha256_file(b/name)==digest,name
 checked+=1
for name,record in s['prefixes'].items():
 raw=(b/name).read_bytes();assert len(raw)>=record['length'] and hashlib.sha256(raw[:record['length']]).hexdigest()==record['sha256'],name
 if name.endswith('.jsonl'):read_jsonl(b/name)
archive=b/'research/laboratory/archive/PVM01-TRANSPORT-previous-source-V1'
for name in ['AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md']:
 assert (b/name).read_bytes().endswith((archive/name).read_bytes()),name
assert verify_manifest(b)['ok'];verify_preflight_certificate(b)
for name in ['STOP','PAUSE','research/run.lock']:assert not (b/name).exists(),name
out={'created_at':utc_now(),'label':args.label,'old_nonmutable_raw_files':checked,'old_prefixes_preserved':True,'all_old_candidate_and_test_bytes_preserved':True,'protected_integrity_preflight':True,'no_stop_pause_lock':True}
atomic_write_json(b/f'research/reviews/PVM01-TRANSPORT-history-{args.label}.json',out);print(json.dumps(out))
