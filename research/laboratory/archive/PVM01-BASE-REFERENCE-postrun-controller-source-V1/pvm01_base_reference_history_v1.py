from pathlib import Path
import argparse,hashlib,json,subprocess,xml.etree.ElementTree as ET
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
parser=argparse.ArgumentParser();parser.add_argument('--original',action='store_true');parser.add_argument('--postrun',action='store_true');args=parser.parse_args()
b=Path.cwd(); target=b.parent/'NEXTAI' if args.original else b
snapshot=json.loads((b/'research/checks/PVM01-BASE-REFERENCE-history-snapshot-V1.json').read_text(encoding='utf-8'))
mutable={'.gitattributes','.gitignore','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/research_program.py','src/nextai_autoresearch/integrity.py','src/nextai_autoresearch/worker_resources.py','schemas/experiment_plan.schema.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','research/REPORT.md','research/REPORT.provenance.json','research/state.json',*snapshot['prefixes']}
arc=b/'research/laboratory/archive/PVM01-BASE-REFERENCE-previous-source-V1'
assert (target/'.gitattributes').read_bytes().startswith((arc/'root.gitattributes.raw').read_bytes())
assert (target/'.gitignore').read_bytes().startswith((arc/'root.gitignore.raw').read_bytes())
eol={r['path']:r for r in json.loads((b/'research/laboratory/PVM01-TRANSPORT-original-checkout-EOL-V1.json').read_text(encoding='utf-8'))['differences']}
checked=0
for name,digest in snapshot['raw_files'].items():
    if name in mutable: continue
    if args.original and name in eol:
        assert sha256_file(target/name)==eol[name]['original_raw_sha256'],name
        assert subprocess.check_output(['git','rev-parse','HEAD:'+name],cwd=target,text=True).strip()==eol[name]['unchanged_git_blob'],name
    else: assert sha256_file(target/name)==digest,name
    checked+=1
for name,record in snapshot['prefixes'].items():
    raw=(target/name).read_bytes(); assert len(raw)>=record['length'] and hashlib.sha256(raw[:record['length']]).hexdigest()==record['sha256'],name
    if name.endswith('.jsonl'): read_jsonl(target/name)
for name in ('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md'):
    assert (target/name).read_bytes().endswith((arc/name).read_bytes()),name
assert (target/'config/baseline_semantics.json').read_bytes()==(arc/'config/baseline_semantics.json').read_bytes()
study=json.loads((target/'research/plans/PVM01-BASE-REFERENCE-CONFIRMATION-V1.json').read_text(encoding='utf-8'))
for name,digest in study['parent_evidence']['scientific_source_sha256_unchanged'].items(): assert sha256_file(target/name)==digest,name
assert verify_manifest(target)['ok']; verify_preflight_certificate(target)
for name in ('STOP','PAUSE','research/run.lock'): assert not (target/name).exists(),name
out={'created_at':utc_now(),'target':str(target),'old_nonmutable_raw_files':checked,'old_prefixes_preserved':True,'old_attributes_and_ignore_prefixes_preserved':True,'all107_scientific_source_bytes_preserved':True,'all_old_candidate_and_test_bytes_preserved':True,'old_baseline_registry_bytes_preserved':True,'protected_integrity_preflight':True,'no_stop_pause_lock':True,'five_historical_original_eol_proof_applied':args.original}
if not args.postrun:
    for cid in ('PVM01-BASE-REFERENCE-targeted-V1','PVM01-BASE-REFERENCE-full-V1'):
        receipt=json.loads((b/f'research/reviews/{cid}.json').read_text(encoding='utf-8')); assert receipt['result']['returncode']==0 and not receipt['error'],cid
    xml=ET.parse(b/'research/checks/PVM01-BASE-REFERENCE-full-V1.xml').getroot(); suites=[xml] if xml.tag=='testsuite' else list(xml)
    counts={k:sum(int(x.get(k,0)) for x in suites) for k in ('tests','failures','errors','skipped')}
    assert counts['tests']>=1272 and not any(counts[k] for k in ('failures','errors','skipped')),counts
    out['full_regression']=counts; out['new_scored_data_fit_EXP']=False
label='original' if args.original else 'clone'; phase='postrun' if args.postrun else 'validated'
atomic_write_json(b/f'research/reviews/PVM01-BASE-REFERENCE-history-{label}-{phase}-V1.json',out)
print(json.dumps(out),flush=True)
