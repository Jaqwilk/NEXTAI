from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
from nextai_autoresearch.research_program import status,auxiliary_reserve,auxiliary_charge
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import read_jsonl,append_jsonl
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.report import write_report
b=Path.cwd();o=b.parent/'NEXTAI';eid='EXP-20261005-0003'
check=json.loads((b/'research/reviews/PVM01-ROBUSTNESS-original-closure-V1.json').read_text());assert check['result']['returncode']==0 and not check['error']
original=json.loads((b/'research/reviews/PVM01-ROBUSTNESS-original-gates-V1.json').read_text());assert original['history_integrity_preflight_doctor_lab']
cid='PVM01-ROBUSTNESS-final-administration-prepaid-V1';seconds=300
used=sum(e['seconds'] for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-ROBUSTNESS-'))
assert used+seconds<=3600
auxiliary_reserve(b,cid,seconds);auxiliary_charge(b,cid,seconds)
program=status(b);assert program['study_terminal'] and not program['program_closed'] and not program['scoring_authorized'] and program['continuation_registration_attempts_used']==8
pub=json.loads((b/f'research/laboratory/{eid}-publication-V2.json').read_text())
for root in (b,o):
 for old in ('EXP-20261005-0001','EXP-20261005-0002','EXP-20261005-0003'):
  meta=json.loads((root/f'research/laboratory/{old}-publication-V2.json').read_text());assert sha256_file(root/meta['native_path'])==meta['native_sha256']
 assert verify_manifest(root)['ok'];verify_preflight_certificate(root)
 for rel in ('STOP','PAUSE','research/run.lock'):assert not (root/rel).exists()
generated=['research/REPORT.md','research/REPORT.provenance.json']
changed=subprocess.check_output(['git','diff','--name-only'],cwd=o,text=True).splitlines();assert set(changed)<=set(generated),changed
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=o,text=True).strip()
arc=b/'research/laboratory/archive/PVM01-ROBUSTNESS-original-validated-generated-reports-V1';arc.mkdir()
for rel in generated:
 target=arc/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((o/rel).read_bytes())
a_path=f'research/reviews/{eid}-PVM01-dense-noise-analysis.json';a=json.loads((b/a_path).read_text());r=json.loads((b/f'research/results/{eid}.json').read_text())
s=a['reference_selection'];neural=a['neural_economics_against_mixed_reference'];classic=a['selected_classical_route_confirmation']
run=json.loads((b/'research/reviews/PVM01-ROBUSTNESS-audited-run-overhead-V1.json').read_text());ready=json.loads((b/'research/laboratory/PVM01-DENSE-NOISE-ROBUSTNESS-V1-readiness.receipt.json').read_text())
study_path='research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json';study=json.loads((b/study_path).read_text())
assert datetime.now(timezone.utc)<datetime.fromisoformat(study['study_deadline_at'].replace('Z','+00:00'))
aux=sum(e['seconds'] for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-ROBUSTNESS-'))
diagnostic=json.loads((b/f'research/reviews/{eid}-reference-noise-diagnosis-V1.json').read_text())
receipt_path='research/laboratory/PVM01-CYCLE-314-COMPLETION-V1.receipt.json';assert not (b/receipt_path).exists()
receipt={'created_at':utc_now(),'cycle':314,'experiment_id':eid,'immutable_plan_path':f'research/plans/{eid}.json','immutable_plan_raw_sha256':sha256_file(b/f'research/plans/{eid}.json'),'study_path':study_path,'study_raw_sha256':sha256_file(b/study_path),'preregistration_revision':ready['preregistration_git_commit'],'source_validated_revision':ready['validated_source_git_commit'],'evaluated_source_revision':run['prepared_source_git_commit'],'original_validated_integration_revision':original['source_revision'],'clone_root':str(b),'original_root':str(o),'research_comparison_complete':True,'technical_postrun_scope_complete':True,'one_registered_scored_experiment_no_retry':True,'five_fresh_paired_units':True,'completed_workers':sum(x['status']=='complete' for x in r['candidates']),'completed_trials':sum(len(x['trials']) for x in r['candidates']),'answers':sum(len(m['predictions']) for x in r['candidates'] for t in x['trials'] for m in t['measurements']),'full_tests':{'passed':1198,'failed':0,'skipped':0,'receipt':'research/reviews/PVM01-ROBUSTNESS-full-V2.json'},'targeted_tests_passed':62,'checkout_metadata_tests_passed':71,'checkout_byte_bridge_addendum':'research/plans/PVM01-ROBUSTNESS-CHECKOUT-BYTES-ADDENDUM-V1.json','checkout_byte_conformance':'research/reviews/PVM01-ROBUSTNESS-checkout-bytes-conformance-V2.json','failed_predata_checks_preserved':['research/reviews/PVM01-ROBUSTNESS-targeted-V1.json','research/reviews/PVM01-ROBUSTNESS-checkout-bytes-V1.json','research/reviews/PVM01-ROBUSTNESS-checkout-metadata-tests-V1.json'],'all80_parent_scientific_source_hashes_unchanged':True,'analysis_path':f'research/analyses/{eid}.md','analysis_raw_sha256':sha256_file(b/f'research/analyses/{eid}.md'),'machine_analysis_path':a_path,'machine_analysis_raw_sha256':sha256_file(b/a_path),'valid_comparison':a['valid_comparison'],'reference_qualified':s['adequate_for_prospective_selection'],'causal_false_abstention_improvement':s['causal_false_abstention_improvement'],'reference_failed_primary_gates':[key for key,value in s['primary_gates'].items() if not value],'reference_failed_unit_guards':[key for key,value in s['each_unit_false_abstention_guards'].items() if not value],'neural_primary_gates_all_pass':all(a['primary_gates'].values()),'neural_economic_screen_qualified':neural['screen_qualified'],'selected_route_screen_qualified':classic['screen_qualified'],'selected_route_failed_economic_gates':[key for key,value in classic['economic_gates'].items() if not value],'decision':s['decision']+'; '+neural['decision']+'; '+classic['decision'],'matched_quality_classical_dominators_of_neural':neural['matched_quality_dominators'],'native_result_sha256':pub['native_sha256'],'lossless_publication':pub,'source_archive':f'research/laboratory/archive/{eid}-evaluated-source','runtime_archive_manifest':f'research/laboratory/{eid}-runtime-archive.json','worker_log_archive_manifest':f'research/laboratory/{eid}-worker-log-archive-V1.json','audited_run_accounting':run,'study_auxiliary_seconds_charged':aux,'study_auxiliary_seconds_cap':3600,'full_study_worker_and_auxiliary_charge_seconds':run['worker_full_wall_seconds_already_charged']+aux,'supervised_fit_seconds':sum(x['execution']['supervised_fit_seconds'] for x in r['candidates']),'stage_started_at':study['study_started_at'],'stage_deadline':study['study_deadline_at'],'all_scored_execution_and_checks_before_deadline':True,'original_doctor':'PASS','original_lab_status':'PASS','original_check_receipt':'research/reviews/PVM01-ROBUSTNESS-original-closure-V1.json','integrity_clone':verify_manifest(b),'integrity_original':verify_manifest(o),'preflight_both':True,'prior_budgets_reset':False,'program_accounting':program,'stage_a_remaining_new_registrations':17-program['continuation_registration_attempts_used'],'stage_b_authorized_but_not_activated':{'registrations':12,'compute_seconds':72000,'spent_registrations':0,'spent_compute_seconds':0},'extended_goal_completed':False,'exact_next_discriminating_experiment':diagnostic['exact_next_discriminating_experiment_proposal'],'restrictions':{'no_WT_8_9':True,'no_external_models_apis':True,'no_schedule_changes':True,'no_failed_outcomes_hidden':True}}
atomic_write_json(b/receipt_path,receipt)
append_jsonl(b/'research/events.jsonl',{'event':'research_program_cycle_completed','created_at':utc_now(),'program_id':program['id'],'cycle':314,'experiment_id':eid,'receipt_path':receipt_path,'receipt_sha256':sha256_file(b/receipt_path),'research_comparison_complete':True,'technical_postrun_scope_complete':True,'scoring':False,'extended_goal_completed':False})
write_report(b)
for rel in generated:(o/rel).write_bytes(subprocess.check_output(['git','show','HEAD:'+rel],cwd=o))
assert not subprocess.check_output(['git','status','--porcelain'],cwd=o).strip()
print('Completion receipt and full accounting ready:',aux,program['fit_seconds_remaining'],flush=True)
