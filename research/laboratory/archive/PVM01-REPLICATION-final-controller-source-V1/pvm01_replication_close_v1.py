from pathlib import Path
import json,subprocess,shutil
from nextai_autoresearch.research_program import status,auxiliary_reserve,auxiliary_charge
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import read_jsonl,append_jsonl
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.report import write_report
b=Path.cwd();o=b.parent/'NEXTAI';eid='EXP-20261005-0002'
check=json.loads((b/'research/reviews/PVM01-REPLICATION-original-closure-V3.json').read_text())
assert check['result']['returncode']==0 and not check['error']
assert json.loads((b/'research/reviews/PVM01-REPLICATION-original-gates-V3.json').read_text())['history_integrity_preflight_doctor_lab']
cid='PVM01-REPLICATION-final-administration-prepaid-V1';seconds=300
used=sum(e['seconds'] for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-REPLICATION-'))
assert used+seconds<=3600
auxiliary_reserve(b,cid,seconds);auxiliary_charge(b,cid,seconds)
program=status(b);assert program['study_terminal'] and not program['program_closed'] and not program['scoring_authorized']
assert program['continuation_registration_attempts_used']==7
pub=json.loads((b/f'research/laboratory/{eid}-publication-V2.json').read_text())
for root in [b,o]:
    assert sha256_file(root/pub['native_path'])==pub['native_sha256']
    assert verify_manifest(root)['ok'];verify_preflight_certificate(root)
    for rel in ['STOP','PAUSE','research/run.lock']:assert not (root/rel).exists()
generated=['research/REPORT.md','research/REPORT.provenance.json']
changed=subprocess.check_output(['git','diff','--name-only'],cwd=o,text=True).splitlines()
assert set(changed)<=set(generated),changed
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=o,text=True).strip()
arc=b/'research/laboratory/archive/PVM01-REPLICATION-original-validated-generated-reports-V1';arc.mkdir()
for rel in generated:
    target=arc/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((o/rel).read_bytes())
a_path=f'research/reviews/{eid}-PVM01-replication-analysis.json';a=json.loads((b/a_path).read_text());selected=a['selected_classical_route_confirmation']
assert a['valid_comparison'] and not a['economic_screen_qualified'] and not selected['screen_qualified']
run=json.loads((b/'research/reviews/PVM01-REPLICATION-audited-run-overhead-V1.json').read_text())
aux=sum(e['seconds'] for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-REPLICATION-'))
receipt_path='research/laboratory/PVM01-CYCLE-313-COMPLETION-V1.receipt.json'
receipt={'created_at':utc_now(),'cycle':313,'experiment_id':eid,'immutable_plan_path':f'research/plans/{eid}.json','immutable_plan_raw_sha256':sha256_file(b/f'research/plans/{eid}.json'),'study_path':'research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json','study_raw_sha256':sha256_file(b/'research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json'),'preregistration_revision':'430e4e45a249ce0ec69e335bb04adda7f81ff913','source_validated_revision':'90ed00750c79f5d614bcd32149218d63d85783b7','evaluated_source_revision':'2635d03fd28c62e90d19400c9c9b29cb9a75a8aa','original_validated_integration_revision':json.loads((b/'research/reviews/PVM01-REPLICATION-original-gates-V3.json').read_text())['source_revision'],'clone_root':str(b),'original_root':str(o),'research_comparison_complete':True,'technical_postrun_scope_complete':True,'one_registered_scored_experiment_no_retry':True,'five_fresh_paired_units':True,'completed_workers':70,'completed_trials':1260,'answers':403200,'full_tests':{'passed':1159,'failed':0,'skipped':0,'receipt':'research/reviews/PVM01-REPLICATION-full-V1.json'},'targeted_tests_passed':32,'postrun_source_scope_tests_passed':16,'postrun_source_scope_test_receipt':'research/reviews/PVM01-REPLICATION-source-scope-tests-V2.json','postrun_no_scoring_metadata_repair_plan':'research/plans/PVM01-SOURCE-SCOPE-METADATA-REPAIR-V1.json','required_literature_review':'research/reviews/PVM01-LITERATURE-CYCLE-313-V1.md','failed_postrun_checks_preserved':['research/reviews/PVM01-REPLICATION-original-closure-V1.json','research/reviews/PVM01-REPLICATION-original-closure-V2.json'],'postdoctor_test_only_fixture_selection_stabilized':True,'all80_scientific_source_hashes_unchanged':True,'analysis_path':f'research/analyses/{eid}.md','analysis_raw_sha256':sha256_file(b/f'research/analyses/{eid}.md'),'machine_analysis_path':a_path,'machine_analysis_raw_sha256':sha256_file(b/a_path),'valid_comparison':a['valid_comparison'],'neural_primary_gates_all_pass':all(a['primary_gates'].values()),'neural_economic_screen_qualified':False,'selected_route_screen_qualified':False,'selected_route_failed_gates':[key for key,value in selected['economic_gates'].items() if not value],'decision':'KEEP replicated learned transport/PCA reference; no full neural economic advantage. DISCARD exact selected-route economic qualification; adverse-noise paired CI uncertainty prevents automatic fresh-final promotion, despite positive mean differences.','matched_quality_classical_dominators_of_neural':a['matched_quality_classical_dominators'],'reference_variance_diagnosis':'research/reviews/EXP-20261005-0002-reference-variance-diagnosis-V1.json','native_result_sha256':pub['native_sha256'],'lossless_publication':pub,'source_archive':f'research/laboratory/archive/{eid}-evaluated-source','runtime_archive_manifest':f'research/laboratory/{eid}-runtime-archive.json','worker_log_archive_manifest':f'research/laboratory/{eid}-worker-log-archive-V1.json','audited_run_accounting':run,'study_auxiliary_seconds_charged':aux,'study_auxiliary_seconds_cap':3600,'full_study_worker_and_auxiliary_charge_seconds':run['worker_full_wall_seconds_already_charged']+aux,'stage_deadline':'2026-10-05T05:54:18Z','all_scored_execution_and_checks_before_deadline':True,'original_doctor':'PASS','original_lab_status':'PASS','original_check_receipt':'research/reviews/PVM01-REPLICATION-original-closure-V3.json','integrity_clone':verify_manifest(b),'integrity_original':verify_manifest(o),'preflight_both':True,'prior_budgets_reset':False,'program_accounting':program,'stage_a_remaining_new_registrations':17-program['continuation_registration_attempts_used'],'stage_b_authorized_but_not_activated':{'registrations':12,'compute_seconds':72000,'spent_registrations':0,'spent_compute_seconds':0},'extended_goal_completed':False,'exact_next_discriminating_experiment':'Prospective fresh five-pair dense-reference robustness ablation: same model,4096 pairs/2048 transport/1024 dense steps; dense training-set noise0.02 versus fixed mixed0.02/0.04 only; unchanged calibration,metrics,thresholds,three K,updates0/1/4,two dev noises and strong classical controls. Preregister before code/data, clone conformance/freeze/preflight/readiness then one audited EXP in next bounded cycle. Reserve fresh-final resources; no current study retry.','restrictions':{'no_WT_8_9':True,'no_external_models_apis':True,'no_schedule_changes':True,'no_failed_outcomes_hidden':True}}
atomic_write_json(b/receipt_path,receipt)
append_jsonl(b/'research/events.jsonl',{'event':'research_program_cycle_completed','created_at':utc_now(),'program_id':program['id'],'cycle':313,'experiment_id':eid,'receipt_path':receipt_path,'receipt_sha256':sha256_file(b/receipt_path),'research_comparison_complete':True,'technical_postrun_scope_complete':True,'scoring':False,'extended_goal_completed':False})
write_report(b)
for rel in generated:
    (o/rel).write_bytes(subprocess.check_output(['git','show','HEAD:'+rel],cwd=o))
assert not subprocess.check_output(['git','status','--porcelain'],cwd=o).strip()
print('Receipt/accounting ready:',aux,program['fit_seconds_remaining'],flush=True)



