from pathlib import Path
import hashlib,json,shutil,subprocess,time
from nextai_autoresearch.integrity import freeze_manifest,verify_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();eid='EXP-20261005-0002';result_path=b/f'research/results/{eid}.json';r=json.loads(result_path.read_text());assert r['integrity_before']['ok'] and r['integrity_after']['ok']
assert verify_manifest(b)['ok']
validated=json.loads((b/'research/checks/PVM01-REPLICATION-validation-source-V1.json').read_text())
for name in ['scripts/analyze_pvm01_replication.py','scripts/run_pvm01_replication_check.py']:
    assert sha256_file(b/name)==validated['files'][name],name
subprocess.run(['uv','run','--no-sync','python','scripts/analyze_pvm01_replication.py',eid],cwd=b,check=True)
analysis=json.loads((b/f'research/reviews/{eid}-PVM01-replication-analysis.json').read_text())
assert not any(e.get('event')=='research_program_outcome_preserved' and e.get('experiment_id')==eid for e in read_jsonl(b/'research/events.jsonl'))
append_jsonl(b/'research/events.jsonl',{'event':'research_program_outcome_preserved','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','experiment_id':eid,'result_sha256':sha256_file(result_path),'analysis_path':f'research/reviews/{eid}-PVM01-replication-analysis.json','decision':analysis['decision']})
manifest=json.loads((b/'research/eval_manifest.json').read_text());out=b/f'research/laboratory/archive/{eid}-evaluated-source';assert not out.exists()
for name,digest in manifest['files'].items():
 assert sha256_file(b/name)==digest,name
 target=out/('root.gitattributes.raw' if name=='.gitattributes' else name);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b/name,target);assert sha256_file(target)==digest
for name in ['scripts/analyze_pvm01_replication.py','scripts/run_pvm01_replication_check.py','research/checks/PVM01-REPLICATION-validation-source-V1.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','research/laboratory/PVM01-INDEPENDENT-REPLICATION-V1-readiness.receipt.json']:
 target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b/name,target)
runtime=b/f'research/tmp/{eid}';archive=b/f'research/laboratory/archive/{eid}-runtime/research/tmp/{eid}';assert not archive.exists();shutil.copytree(runtime,archive)
files={p.relative_to(archive).as_posix():sha256_file(p) for p in sorted(archive.rglob('*')) if p.is_file()}
atomic_write_json(b/f'research/laboratory/{eid}-runtime-archive.json',{'created_at':utc_now(),'experiment_id':eid,'original_runtime':runtime.relative_to(b).as_posix(),'archive':archive.relative_to(b).as_posix(),'files':files,'source_evaluator_sha256':manifest['evaluator_sha256'],'raw_result_sha256':sha256_file(result_path),'result_bytes':result_path.stat().st_size,'all_failed_partial_and_completed_outputs_preserved':True})
p=b/'config/research.toml';raw=p.read_bytes();assert raw.count(b'benchmark_status = "active"')==1;p.write_bytes(raw.replace(b'benchmark_status = "active"',b'benchmark_status = "maintenance"'))
freeze_manifest(b,overwrite=True);write_preflight_certificate(b)
append_jsonl(b/'research/events.jsonl',{'event':'research_program_analysis_preserved','program_id':'NEXTAI-CONTINUATION-20261004-V1','created_at':utc_now(),'experiment_id':eid,'analysis_path':f'research/reviews/{eid}-PVM01-replication-analysis.json','analysis_sha256':sha256_file(b/f'research/reviews/{eid}-PVM01-replication-analysis.json'),'evaluated_source_raw_archive':out.relative_to(b).as_posix(),'runtime_archive_manifest':f'research/laboratory/{eid}-runtime-archive.json','benchmark_maintenance':True,'fresh_final_executed':False,'whole_program_complete':False})
print('Native analysis, full source/runtime preservation, maintenance freeze: completed')


