from pathlib import Path
import json,subprocess,xml.etree.ElementTree as ET
from nextai_autoresearch.baseline_semantics import write_preflight_certificate,verify_required_baselines
from nextai_autoresearch.integrity import freeze_manifest,verify_manifest
from nextai_autoresearch.ledger import append_jsonl,read_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status,_study_scope
from nextai_autoresearch.gates import ensure_can_create_plan
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd(); relative='research/plans/PVM01-FRESH-FINAL-V1.json'; study=json.loads((b/relative).read_text(encoding='utf-8'))
for cid in ('PVM01-FRESH-FINAL-full-V1','PVM01-FRESH-FINAL-targeted-V4','PVM01-FRESH-FINAL-history-source-V1'):
    r=json.loads((b/f'research/reviews/{cid}.json').read_text(encoding='utf-8')); assert r['result']['returncode']==0 and not r['error'],cid
history=json.loads((b/'research/reviews/PVM01-FRESH-FINAL-history-clone-validated-V1.json').read_text(encoding='utf-8'))
counts=history['full_regression']; assert counts['tests']>=1310 and not any(counts[k] for k in ('failures','errors','skipped'))
assert verify_manifest(b)['ok']; source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
p=b/'config/research.toml'; raw=p.read_bytes(); old=b'benchmark_status = "maintenance"'; assert raw.count(old)==1; p.write_bytes(raw.replace(old,b'benchmark_status = "active"'))
manifest=freeze_manifest(b,overwrite=True); write_preflight_certificate(b)
receipt='research/laboratory/PVM01-FRESH-FINAL-V1-readiness.receipt.json'; assert not (b/receipt).exists()
prereg=json.loads((b/'research/tmp/PVM01-FRESH-FINAL-preregistration-V1.json').read_text(encoding='utf-8'))
atomic_write_json(b/receipt,{'id':'PVM01-FRESH-FINAL-V1-readiness','created_at':utc_now(),'study_path':relative,'study_sha256':sha256_file(b/relative),'preregistration_git_commit':prereg['preregistration_git_commit'],'validated_source_git_commit':source,'independent_clone_root':str(b),'original_root':str(b.parent/'NEXTAI'),'shared_runtime_not_source_or_state':True,'full_regression':counts,'classical_economic_contract_sha256':sha256_file(b/'research/plans/PVM01-FRESH-FINAL-CLASSICAL-ECONOMICS-V1.json'),'full_regression_receipt_sha256':sha256_file(b/'research/reviews/PVM01-FRESH-FINAL-full-V1.json'),'history_source_receipt_sha256':sha256_file(b/'research/reviews/PVM01-FRESH-FINAL-history-clone-validated-V1.json'),'protected_files':len(manifest['files']),'evaluator_sha256':manifest['evaluator_sha256'],'scientific_sources_unchanged':112,'trusted_resource_phase_snapshots_validated':True,'new_private_seed_data_fit_EXP_before_readiness':False,'ready_for_exactly_one_audited_registration':True,'fresh_final_executed':False,'whole_program_complete':False})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_study_ready','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','study_path':relative,'study_sha256':sha256_file(b/relative),'receipt_path':receipt,'receipt_sha256':sha256_file(b/receipt)})
write_report(b); commands=[]
for label,args in (('doctor',['doctor']),('lab',['lab','status'])):
    stem=b/f'research/reviews/PVM01-FRESH-FINAL-prepaid-{label}-V1'
    with stem.with_suffix('.stdout.txt').open('xb') as out,stem.with_suffix('.stderr.txt').open('xb') as err:
        result=subprocess.run(['uv','run','--no-sync','nextai',*args],cwd=b,stdout=out,stderr=err)
    commands.append({'label':label,'returncode':result.returncode}); assert result.returncode==0,label
ensure_can_create_plan(b)
plan=json.loads((b/'research/plans/EXP-20261005-0003.json').read_text(encoding='utf-8')); plan.update(candidates=study['candidates'],benchmark=study['cohort'],evaluator_sha256=manifest['evaluator_sha256'])
plan['research_program_protocol'].update(_study_scope(study),study_path=relative,study_sha256=sha256_file(b/relative))
validate_document('experiment_plan',plan,b); verify_required_baselines(plan,b,run_tests=True)
value=status(b); assert value['ready'] and value['scoring_authorized'] and not value['paid_run_pending'] and value['experiment_id'] is None
events=read_jsonl(b/'research/events.jsonl')
charges={e['charge_id']:e['seconds'] for e in events if e.get('event')=='research_program_aux_fit_charged'}
reservations=[e for e in events if e.get('event')=='research_program_aux_fit_reserved' and str(e.get('charge_id','')).startswith('PVM01-FRESH-FINAL-')]
effective=sum(charges.get(e['charge_id'],e['seconds_cap']) for e in reservations)
assert effective<=3600
assert value['fit_seconds_remaining']-study['resources']['fit_seconds_study_cap']-(3600-effective)>=20800
reserves=study['programme_reserves']; assert value['unreserved_fit_seconds_remaining']-study['resources']['fit_seconds_study_cap']>=reserves['fresh_final_and_replication_min_seconds_unspent_after_worst_case_this_study']
assert value['continuation_registration_attempts_cap']-value['continuation_registration_attempts_used']-1>=reserves['remaining_registration_tickets_min_after_this_study']
atomic_write_json(b/'research/reviews/PVM01-FRESH-FINAL-prepaid-gates-V1.json',{'created_at':utc_now(),'commands':commands,'all85_semantic_source_records_and_schema':True,'can_create_plan':True,'readiness_integrity_preflight':True,'new_private_seed_data_fit_registration':False,'full_regression':counts,'minimum_future_reserves':reserves})
print('Ready,doctor,lab,all85 semantics/schema/scope/budget/reserves: PASS',flush=True)
