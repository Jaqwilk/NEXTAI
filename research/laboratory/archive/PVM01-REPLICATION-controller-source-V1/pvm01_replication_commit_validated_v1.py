from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.report import write_report
b=Path.cwd();s=json.loads((b/'research/checks/PVM01-REPLICATION-history-snapshot-V1.json').read_text())
mutable={'AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','config/baseline_semantics.json','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/research_program.py','schemas/experiment_plan.schema.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','research/REPORT.md','research/REPORT.provenance.json','research/state.json',*s['prefixes']}
checked=0
for name,digest in s['raw_files'].items():
    if name in mutable:continue
    assert sha256_file(b/name)==digest,name
    checked+=1
for name,record in s['prefixes'].items():
    raw=(b/name).read_bytes();assert len(raw)>=record['length'] and hashlib.sha256(raw[:record['length']]).hexdigest()==record['sha256'],name
    if name.endswith('.jsonl'):read_jsonl(b/name)
arc=b/'research/laboratory/archive/PVM01-REPLICATION-previous-source-V1'
for name in ['AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md']:
    assert (b/name).read_bytes().endswith((arc/name).read_bytes()),name
assert verify_manifest(b)['ok'];verify_preflight_certificate(b)
for name in ['STOP','PAUSE','research/run.lock']:assert not (b/name).exists(),name
for cid in ['PVM01-REPLICATION-targeted-V1','PVM01-REPLICATION-full-V1']:
    receipt=json.loads((b/f'research/reviews/{cid}.json').read_text())
    assert receipt['result']['returncode']==0 and not receipt['error'],cid
xml=ET.parse(b/'research/checks/PVM01-REPLICATION-full-V1.xml').getroot();suites=[xml] if xml.tag=='testsuite' else list(xml)
counts={k:sum(int(x.get(k,0)) for x in suites) for k in ['tests','failures','errors','skipped']}
assert counts['tests']>=1137+22 and all(counts[k]==0 for k in ['failures','errors','skipped']),counts
out={'created_at':utc_now(),'old_nonmutable_raw_files':checked,'old_prefixes_preserved':True,'all_old_candidate_and_test_bytes_preserved':True,'protected_integrity_preflight':True,'full_regression':counts,'no_stop_pause_lock':True,'new_scored_data_fit_EXP':False}
atomic_write_json(b/'research/reviews/PVM01-REPLICATION-history-validated-V1.json',out);write_report(b)
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('research/REPORT','research/events.jsonl','research/eval_manifest.json','research/checks/PVM01-REPLICATION-','research/reviews/PVM01-REPLICATION-','research/laboratory/PVM01-','research/laboratory/archive/PVM01-REPLICATION-','research/laboratory/preflight_certificate','research/laboratory/archive/preflight','research/laboratory/certificates/','research/manifests/')
exact={'config/research.toml','config/baseline_semantics.json','schemas/experiment_plan.schema.json','src/nextai_autoresearch/research_program.py','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v7.py','tests/test_pvm01_independent_replication.py','scripts/analyze_pvm01_replication.py','scripts/run_pvm01_replication_check.py'}
for rel in paths:
    assert rel in exact or rel.startswith(allowed),rel
    assert (b/rel).stat().st_size<99_000_000,rel
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Validate unchanged v7 replication and prospective classical cost decision'],check=True)
print(json.dumps({'validated_source':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'old_files_verified':checked,'full_regression':counts}),flush=True)

