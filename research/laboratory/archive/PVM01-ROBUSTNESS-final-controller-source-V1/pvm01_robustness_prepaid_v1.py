from pathlib import Path
import json,subprocess,xml.etree.ElementTree as ET
from nextai_autoresearch.baseline_semantics import write_preflight_certificate,verify_required_baselines
from nextai_autoresearch.config import load_config
from nextai_autoresearch.integrity import freeze_manifest,verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status,_study_scope
from nextai_autoresearch.gates import ensure_can_create_plan
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();relative='research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json';study=json.loads((b/relative).read_text())
for cid in ['PVM01-ROBUSTNESS-full-V2','PVM01-ROBUSTNESS-targeted-V3','PVM01-ROBUSTNESS-history-source-V1','PVM01-ROBUSTNESS-checkout-bytes-V2','PVM01-ROBUSTNESS-checkout-metadata-tests-V2','PVM01-ROBUSTNESS-history-source-V2']:
    receipt=json.loads((b/f'research/reviews/{cid}.json').read_text());assert receipt['result']['returncode']==0 and not receipt['error'],cid
xml=ET.parse(b/'research/checks/PVM01-ROBUSTNESS-full-V2.xml').getroot();suites=[xml] if xml.tag=='testsuite' else list(xml);counts={k:sum(int(x.get(k,0)) for x in suites) for k in ['tests','failures','errors','skipped']}
assert counts['tests']>=1198 and all(counts[k]==0 for k in ['failures','errors','skipped'])
assert verify_manifest(b)['ok'];source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=b).decode().strip()
p=b/'config/research.toml';raw=p.read_bytes();old=b'benchmark_status = "maintenance"';assert raw.count(old)==1;p.write_bytes(raw.replace(old,b'benchmark_status = "active"'))
manifest=freeze_manifest(b,overwrite=True);write_preflight_certificate(b)
receipt='research/laboratory/PVM01-DENSE-NOISE-ROBUSTNESS-V1-readiness.receipt.json';assert not (b/receipt).exists()
atomic_write_json(b/receipt,{'id':'PVM01-DENSE-NOISE-ROBUSTNESS-V1-readiness','created_at':utc_now(),'study_path':relative,'study_sha256':sha256_file(b/relative),'preregistration_git_commit':'e2342788c37e9bcb7d80db9331e9c2e825c695cf','validated_source_git_commit':source,'independent_clone_root':str(b),'original_root':str(b.parent/'NEXTAI'),'shared_runtime_not_source_or_state':True,'full_regression':counts,'classical_economic_contract_sha256':sha256_file(b/'research/plans/PVM01-ROBUSTNESS-CLASSICAL-ECONOMICS-V1.json'),'full_regression_receipt_sha256':sha256_file(b/'research/reviews/PVM01-ROBUSTNESS-full-V2.json'),'history_source_receipt_sha256':sha256_file(b/'research/reviews/PVM01-ROBUSTNESS-history-validated-V2.json'),'protected_files':len(manifest['files']),'evaluator_sha256':manifest['evaluator_sha256'],'new_private_seed_data_fit_EXP_before_readiness':False,'ready_for_exactly_one_audited_registration':True,'fresh_final_executed':False,'whole_program_complete':False})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_study_ready','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','study_path':relative,'study_sha256':sha256_file(b/relative),'receipt_path':receipt,'receipt_sha256':sha256_file(b/receipt)})
write_report(b)
commands=[]
for label,args in [('doctor',['doctor']),('lab',['lab','status'])]:
    with (b/f'research/reviews/PVM01-ROBUSTNESS-prepaid-{label}-V1.stdout.txt').open('xb') as out,(b/f'research/reviews/PVM01-ROBUSTNESS-prepaid-{label}-V1.stderr.txt').open('xb') as err:
        result=subprocess.run(['uv','run','--no-sync','nextai',*args],cwd=b,stdout=out,stderr=err)
    commands.append({'label':label,'returncode':result.returncode});assert result.returncode==0,label
ensure_can_create_plan(b)
plan=json.loads((b/'research/plans/EXP-20261005-0002.json').read_text());plan.update(candidates=study['candidates'],benchmark=study['cohort'],evaluator_sha256=manifest['evaluator_sha256'])
plan['research_program_protocol'].update(_study_scope(study),study_path=relative,study_sha256=sha256_file(b/relative));validate_document('experiment_plan',plan,b);verify_required_baselines(plan,b,run_tests=True)
v=status(b);assert v['ready'] and v['scoring_authorized'] and not v['paid_run_pending'] and v['experiment_id'] is None
reserve=study['programme_reserves'];assert v['unreserved_fit_seconds_remaining']-study['resources']['fit_seconds_study_cap']>=reserve['fresh_final_and_replication_min_seconds_unspent_after_worst_case_this_study']
assert v['continuation_registration_attempts_cap']-v['continuation_registration_attempts_used']-1>=reserve['remaining_registration_tickets_min_after_this_study']
atomic_write_json(b/'research/reviews/PVM01-ROBUSTNESS-prepaid-gates-V1.json',{'created_at':utc_now(),'commands':commands,'all85_semantic_source_records_and_schema':True,'checkout_byte_bridge_receipt_sha256':sha256_file(b/'research/reviews/PVM01-ROBUSTNESS-checkout-bytes-conformance-V2.json'),'can_create_plan':True,'readiness_integrity_preflight':True,'new_private_seed_data_fit_registration':False,'full_regression':counts,'minimum_future_reserves':reserve})
print('Ready,doctor,lab,all85 semantics/schema/scope/budget/reserves: PASS')

