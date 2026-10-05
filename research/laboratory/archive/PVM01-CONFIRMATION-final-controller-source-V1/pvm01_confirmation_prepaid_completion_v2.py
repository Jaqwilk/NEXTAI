from pathlib import Path
import json,subprocess
from nextai_autoresearch.research_program import status,_study_scope
from nextai_autoresearch.ledger import read_jsonl,append_jsonl
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate,verify_required_baselines
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.gates import ensure_can_create_plan
from nextai_autoresearch.report import write_report
b=Path.cwd(); failed=json.loads((b/'research/reviews/PVM01-CONFIRMATION-prepaid-V1.json').read_text(encoding='utf-8'))
assert failed['result']['returncode']==1 and failed['seconds_charged']==349
trace=(b/'research/reviews/PVM01-CONFIRMATION-prepaid-V1.stderr.txt').read_text(encoding='utf-8')
assert "assert value['fit_seconds_remaining']-study['resources']['fit_seconds_study_cap']-(3600-charged)>=24000" in trace
for label in ('doctor','lab'):
    assert (b/f'research/reviews/PVM01-CONFIRMATION-prepaid-{label}-V1.stderr.txt').read_bytes()==b''
assert 'Doctor: PASS' in (b/'research/reviews/PVM01-CONFIRMATION-prepaid-doctor-V1.stdout.txt').read_text(encoding='utf-8')
lab=json.loads((b/'research/reviews/PVM01-CONFIRMATION-prepaid-lab-V1.stdout.txt').read_text(encoding='utf-8'))
assert lab['errors']==[] and lab['scoring_ready'] is True
source=b/'research/tmp/pvm01_confirmation_prepaid_v1.py'; arc=b/'research/laboratory/archive/PVM01-CONFIRMATION-readiness-budget-guard-before-V1';arc.mkdir()
(arc/source.name).write_bytes(source.read_bytes())
relative='research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json'; study=json.loads((b/relative).read_text(encoding='utf-8'))
write_report(b); value=status(b); events=read_jsonl(b/'research/events.jsonl')
charges={e['charge_id']:e['seconds'] for e in events if e.get('event')=='research_program_aux_fit_charged'}
reservations=[e for e in events if e.get('event')=='research_program_aux_fit_reserved' and str(e.get('charge_id','')).startswith('PVM01-CONFIRMATION-')]
effective=sum(charges.get(e['charge_id'],e['seconds_cap']) for e in reservations)
remaining_after_worst_case=value['fit_seconds_remaining']-study['resources']['fit_seconds_study_cap']-(3600-effective)
assert remaining_after_worst_case>=24000 and effective<=3600
assert value['ready'] and value['scoring_authorized'] and not value['paid_run_pending'] and value['experiment_id'] is None
assert verify_manifest(b)['ok'];verify_preflight_certificate(b);ensure_can_create_plan(b)
plan=json.loads((b/'research/plans/EXP-20261005-0003.json').read_text(encoding='utf-8'));plan.update(candidates=study['candidates'],benchmark=study['cohort'])
plan['research_program_protocol'].update(_study_scope(study),study_path=relative,study_sha256=sha256_file(b/relative));validate_document('experiment_plan',plan,b)
verify_required_baselines(plan,b,run_tests=False)
rel='research/plans/PVM01-CONFIRMATION-READINESS-BUDGET-GUARD-ADDENDUM-V1.json';assert not (b/rel).exists()
atomic_write_json(b/rel,{'id':'PVM01-CONFIRMATION-READINESS-BUDGET-GUARD-ADDENDUM-V1','created_at':utc_now(),'parent_study_path':relative,'parent_study_sha256':sha256_file(b/relative),'failed_receipt':'research/reviews/PVM01-CONFIRMATION-prepaid-V1.json','failed_source_raw_archive':arc.relative_to(b).as_posix(),'cause':'status.fit_seconds_remaining already deducts uncharged live auxiliary reservations. The additional final-reserve guard subtracted that live500s again because it counted only completed charges. Correct effective auxiliary uses charged seconds or current reserved caps,matching trusted programme accounting.','completed_doctor_lab_semantic_tests_and_schema_not_repeated':True,'fixed_guard_effective_current_auxiliary':effective,'minimum_remaining_after_all_current_worst_case_costs':remaining_after_worst_case,'fresh_final_reserve_seconds':24000,'current_limits_metrics_recipe_data_and_readiness_receipt_unchanged':True,'all_failed_costs_and_outcomes_preserved':True,'research_seed_data_fit_EXP_before_guard_completion':False})
append_jsonl(b/'research/events.jsonl',{'event':'laboratory_preparation_budget_guard_corrected','created_at':utc_now(),'cycle':315,'addendum_path':rel,'addendum_sha256':sha256_file(b/rel),'before_research_seed_data_fit_EXP':True,'scientific_contract_unchanged':True})
out='research/reviews/PVM01-CONFIRMATION-prepaid-gates-V1.json';assert not (b/out).exists()
atomic_write_json(b/out,{'created_at':utc_now(),'certifying_check_receipt':'research/reviews/PVM01-CONFIRMATION-prepaid-V2.json','doctor':'PASS prior exact retained output','lab':'PASS prior exact retained output','all85_semantic_source_records_and_schema':True,'semantic_tests_completed_before_V1_budget_only_assertion':True,'can_create_plan':True,'readiness_integrity_preflight':True,'new_private_seed_data_fit_registration':False,'minimum_final_seconds_after_all_current_worst_case':remaining_after_worst_case,'corrected_guard_addendum_path':rel,'corrected_guard_addendum_sha256':sha256_file(b/rel)})
p=b/'research/tmp/pvm01_confirmation_commit_certified_v1.py';text=p.read_text(encoding='utf-8').replace('PVM01-CONFIRMATION-prepaid-V1.json','PVM01-CONFIRMATION-prepaid-V2.json');p.write_text(text,encoding='utf-8',newline='\n')
write_report(b);print('All retained doctor/lab/semantics/schema and corrected conservative24000s final reserve PASS:',remaining_after_worst_case,flush=True)
