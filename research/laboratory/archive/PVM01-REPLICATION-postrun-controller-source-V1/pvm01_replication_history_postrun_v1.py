from pathlib import Path
import argparse,hashlib,json,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
parser=argparse.ArgumentParser();parser.add_argument('--original',action='store_true');args=parser.parse_args()
b=Path.cwd();o=Path('C:/Users/NATAN/Documents/ChatGPT/NEXTAI');target=o if args.original else b
snapshot=json.loads((b/'research/checks/PVM01-REPLICATION-history-snapshot-V1.json').read_text())
mutable={'.gitignore','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','config/baseline_semantics.json','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/research_program.py','schemas/experiment_plan.schema.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','research/REPORT.md','research/REPORT.provenance.json','research/state.json',*snapshot['prefixes']}
eol={r['path']:r for r in json.loads((b/'research/laboratory/PVM01-TRANSPORT-original-checkout-EOL-V1.json').read_text())['differences']}
checked=0
for name,digest in snapshot['raw_files'].items():
    if name in mutable:continue
    if args.original and name in eol:
        assert sha256_file(target/name)==eol[name]['original_raw_sha256'],name
        blob=subprocess.check_output(['git','rev-parse','HEAD:'+name],cwd=target,text=True).strip()
        assert blob==eol[name]['unchanged_git_blob'],name
    else:assert sha256_file(target/name)==digest,name
    checked+=1
for name,record in snapshot['prefixes'].items():
    raw=(target/name).read_bytes();assert len(raw)>=record['length'] and hashlib.sha256(raw[:record['length']]).hexdigest()==record['sha256'],name
    if name.endswith('.jsonl'):read_jsonl(target/name)
arc=b/'research/laboratory/archive/PVM01-REPLICATION-previous-source-V1'
for name in ['AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md']:
    assert (target/name).read_bytes().endswith((arc/name).read_bytes()),name
old_ignore=(b/'research/laboratory/archive/EXP-20261005-0002-publication-source/root.gitignore.before.raw').read_bytes()
assert (target/'.gitignore').read_bytes().startswith(old_ignore)
study=json.loads((target/'research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json').read_text())
for name,digest in study['independent_replication']['scientific_source_sha256_unchanged'].items():assert sha256_file(target/name)==digest,name
assert verify_manifest(target)['ok'];verify_preflight_certificate(target)
for name in ['STOP','PAUSE','research/run.lock']:assert not (target/name).exists(),name
label='original' if args.original else 'clone'
out={'created_at':utc_now(),'target':str(target),'old_nonmutable_raw_files':checked,'old_prefixes_preserved':True,'all80_scientific_source_bytes_preserved':True,'all_old_candidate_and_test_bytes_preserved':True,'protected_integrity_preflight':True,'no_stop_pause_lock':True,'five_historical_original_eol_proof_applied':args.original}
atomic_write_json(b/f'research/reviews/PVM01-REPLICATION-history-{label}-postrun-V1.json',out)
print(json.dumps(out),flush=True)
