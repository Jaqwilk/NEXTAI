from pathlib import Path
from datetime import datetime,timezone
import copy,json,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl,read_jsonl
from nextai_autoresearch.research_program import status,auxiliary_reserve,auxiliary_charge
from nextai_autoresearch.report import write_report
b=Path.cwd();o=b.parent/'NEXTAI';parent='28cff0932543303de1c065ba01205c3096125757';prefix='PVM01-FRESH-FINAL-'
startup=json.loads((b/'research/reviews/PVM01-FRESH-FINAL-startup-observation-V1.json').read_text(encoding='utf-8'))
assert startup['doctor_returncode']==startup['lab_returncode']==0 and startup['source_revision']==parent
assert startup['charge_completed'] and startup['reserved_before_testing']
assert 'Doctor: PASS' in (b/'research/reviews/PVM01-FRESH-FINAL-startup-doctor-V1.stdout.txt').read_text(encoding='utf-8')
lab=json.loads((b/'research/reviews/PVM01-FRESH-FINAL-startup-lab-V1.stdout.txt').read_text(encoding='utf-8'));assert lab['errors']==[] and not lab['scoring_ready']
for root in (b,o):
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
    for rel in ('STOP','PAUSE','research/run.lock'):assert not (root/rel).exists(),(root,rel)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=o).strip()
dirty=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
assert all(x.startswith('research/reviews/PVM01-FRESH-FINAL-startup-') or x=='research/events.jsonl' for x in dirty),dirty
initial=status(b);assert initial['study_terminal'] and not initial['program_closed'] and initial['continuation_registration_attempts_used']==10
assert initial['stage_registration_attempts']['reference_and_alternatives']==5 and initial['stage_registration_attempts']['replication_and_fresh_final']==2
charges=[e for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and e.get('charge_id')==startup['charge_id']]
assert len(charges)==1 and charges[0]['seconds']==295
subprocess.run(['git','add','--',*dirty],check=True)
subprocess.run(['git','commit','-q','-m','Preserve cycle317 startup checks reserved and charged before testing'],check=True)
source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
tracked=[x for x in subprocess.check_output(['git','ls-files','-z']).decode().split('\0') if x and (b/x).is_file()]
prefixes={x:{'length':(b/x).stat().st_size,'sha256':sha256_file(b/x)} for x in ('research/events.jsonl','research/plan_registry.jsonl','research/experiments.tsv','research/hypothesis_events.jsonl','research/sources.jsonl')}
snapshot=b/'research/checks/PVM01-FRESH-FINAL-history-snapshot-V1.json';assert not snapshot.exists()
atomic_write_json(snapshot,{'source_commit':source,'original_parent_commit':parent,'raw_files':{x:sha256_file(b/x) for x in tracked},'prefixes':prefixes})
manifest=json.loads((b/'research/eval_manifest.json').read_text(encoding='utf-8'));arc=b/'research/laboratory/archive/PVM01-FRESH-FINAL-previous-source-V1';assert not arc.exists()
for rel in dict.fromkeys([*manifest['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json','docs/CURRENT_STATUS.md','.gitignore']):
    target=arc/('root.gitattributes.raw' if rel=='.gitattributes' else 'root.gitignore.raw' if rel=='.gitignore' else rel)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((b/rel).read_bytes())
old_rel='research/plans/PVM01-BASE-REFERENCE-CONFIRMATION-V1.json';new_rel='research/plans/PVM01-FRESH-FINAL-V1.json';addon_rel='research/plans/PVM01-FRESH-FINAL-CLASSICAL-ECONOMICS-V1.json'
assert not (b/new_rel).exists() and not (b/addon_rel).exists()
old=json.loads((b/old_rel).read_text(encoding='utf-8'));s=copy.deepcopy(old)
s.update(id='PVM01-FRESH-FINAL-V1',cohort='paired_view_mutable_memory_v11',stage='replication_and_fresh_final',study_kind='paired_view_frozen_fresh_final',prepared_source_commit=source,
    study_started_at=startup['stage_started_at'],study_deadline_at=startup['stage_deadline_at'],auxiliary_charge_id_prefix=prefix,
    evaluation_data_role='frozen_fresh_final_v1',
    question='On five entirely new independent paired units and all three scales, do the prospectively selected learned transport/PCA and classical ridge/PCA-scan separately reproduce their complete frozen quality and full-service cost qualification against competent unaugmented dense_cached_cpu and strong classical controls? This is a final for the visible same-law local PVM task, not blinded generalization or transfer.',
    implementation_scope='No candidate,model,optimizer,steps,pair count,task law,training,calibration,grids,metrics,thresholds,baseline,service law or scientific gate changes. New v11 delegates frozen v10/v9/v8/v6; extend freshness through0005, audited schema/dispatch and protected saved-outcome analysis. Require final data role. Before any final D arrays, trusted wrapper snapshots exactly five fixed source-fit arm groups and all five units for later genuinely source-trained transfer controls. Snapshot only already fitted model/decoder/FP32 ridge/PCA and T-calibrated threshold, no fit replay and no final-dependent choice. Snapshot overhead remains in trusted fit-phase and worker wall; its separately measured cost is disclosed, never hidden in inference.',
    freshness_policy='Five NEW runner model seeds and256-bit unit nonces checked before arrays against all consumed PVM units from20261004-0004 through0008 and20261005-0001 through0005,including failures. Collision invalidates without replacement. Same85 roles share new legal arrays. No earlier unit,fit,calibration,weight or outcome is pooled. Fixed T-fitting/T-calibration then D declared frozen fresh final; D cannot tune or select any parameter,baseline or stopping rule.',
    decision_policy='Invalid/partial source,fit,cache,data,resources,export or missing five independent units => INCONCLUSIVE. All original base competence gates and ten <=2% each-unit/noise base false-abstention guards must pass. Selected ridge/PCA and neural transport/PCA qualify separately only with the same original8 learning/compression,18 economic/per-cell quality/UNKNOWN/FA and60 fixed-comparator non-domination checks. Ancillary mixed six NI formulas/thresholds retained separately; they cannot alter this base-final decision. KEEP each qualifying exact locally validated route as source evidence for separately preregistered transfer. Competent failed qualification DISCARD exact; failed reference controls INCONCLUSIVE. No promotion,novelty,transfer claim or final-guided rescue. Point-estimate cheaper classic is not statistical domination. Preserve every outcome and cost, no paid retry.',
    next_alternatives='After this final and full durable current charges, explicitly resolve/account stage A in a separate bounded cycle before activating authorized B. B separately preregisters two independent transfer families,one licensed public real dataset,and a minimal evidence-selected local fact/source/update/UNKNOWN prototype. No additional A reference rescue or another EXP in this cycle. Expanded goal remains open even if local final is negative or inconclusive.')
science=copy.deepcopy(old['parent_evidence']['scientific_source_sha256_unchanged'])
for rel in ('src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v10.py','scripts/analyze_pvm01_base_reference.py','scripts/run_pvm01_base_reference_check.py','tests/test_pvm01_base_reference.py','scripts/restore_pvm01_base_reference_result.py'):science[rel]=sha256_file(b/rel)
for rel,digest in science.items():assert sha256_file(b/rel)==digest,rel
s['parent_evidence']={'parent_study_path':old_rel,'parent_study_sha256':sha256_file(b/old_rel),'last_experiment':'EXP-20261005-0005','selected_result_sha256':sha256_file(b/'research/results/EXP-20261005-0005.json'),'selected_analysis_sha256':sha256_file(b/'research/reviews/EXP-20261005-0005-PVM01-base-reference-analysis.json'),'scientific_source_sha256_unchanged':science,'no_empirical_pooling':True,'all_previous_decisions_preserved':True}
s['independent_confirmation'].update(selected_reference='dense_cached_cpu',selected_route='ridge_pca_scan',selected_neural_route='transport_pca',fresh_final_separate_future_contract=False,final_for_visible_same_law_only=True,unseen_final_units_before_freeze=True)
s['frozen_final']={'recipe_selected_before_new_units':True,'independent_paired_units':5,'prior_selection_units_excluded':True,'model_weights_from_initialization':True,'final_arrays_only_after_registration_freeze_readiness':True,'legal_training_validation_and_calibration_T_only':True,'D_split_final_role':'frozen_fresh_final_v1','independent_blind_evaluator':False,'no_final_guided_tuning_or_source_unit_selection':True,'all_final_outcomes_preserved':True}
s['fitted_source_state_export']={'version':'PVM01-FITTED-SOURCE-STATE-V1','before_final_D_arrays':True,'arms':['transport_pca','transport_pca_untrained','transport_pca_shuffled','ridge_pca_scan','dense_cached_cpu'],'units_per_arm':5,'expected_exports':25,'parameter_fields':['model.state_dict','decoder.state_dict','weights','projection'],'scalar_fields':['threshold','arm','seed','seed_index'],'recipe_included':True,'forbidden':['training_arrays','training_labels','final_arrays','final_labels','private_nonce','generator_rotation','optimizer_state','runtime_episode_memory','final_dependent_selection'],'codec':'numpy savez uncompressed,allow_pickle=False on read; UTF8 JSON metadata; named finite float32 arrays only, per-array hashes and exact fit_report_sha256 provenance','max_parameter_file_bytes_per_export':2097152,'max_metadata_file_bytes_per_export':65536,'max_total_export_bytes':54067200,'no_overwrite':True,'bound_to_runner_private_experiment_directory':True,'fit_report_hash_unchanged':True,'export_descriptor_outer_fit_event_only':True,'all_copy_serialization_hash_cost_in_fit_phase_and_worker_wall':True,'inference_service_includes_all_existing_boundaries_unchanged':True,'future_transfer_no_source_refit':True,'restoration_is_parameter_copy_not_fit':True,'failure_invalidates_without_retry':True,'publish_small_lossless_fitted_state_bundle_with_hashes':True,'max_compressed_public_bundle_bytes':10485760}
s['data']['tag']=s['id']
s['resources'].update(fit_seconds_per_role_cap=90,fit_seconds_study_cap=10200,worker_seconds_cap=116,worker_charge_ceiling_with_monitor_margin=120,auxiliary_test_seconds_cap=3600)
s['prospective_tighter_resource_caps']={'scientific_workload_unchanged':True,'evidence':'All85 prior identical-recipe workers passed under same90s fit/116s internal/120s external bounds; tiny bounded parameter export charged prospectively in fit. Timeout invalidates without retry.','total_max_worker_plus_auxiliary_seconds':13800}
s['programme_reserves']['fresh_final_and_replication_min_seconds_unspent_after_worst_case_this_study']=20800
s['programme_reserves']['remaining_registration_tickets_min_after_this_study']=0
s['programme_reserves']['A_final_ticket_consumed_by_this_study']=True
s['programme_reserves']['B_authorized_additional_seconds_not_activated']=72000
s['prepaid_startup_seconds']=295;s['prepaid_administration_seconds']=300
atomic_write_json(b/new_rel,s)
addon=copy.deepcopy(json.loads((b/'research/plans/PVM01-BASE-REFERENCE-CLASSICAL-ECONOMICS-V1.json').read_text(encoding='utf-8')))
addon.update(id='PVM01-FRESH-FINAL-CLASSICAL-ECONOMICS-V1',created_at=utc_now(),parent_study_path=new_rel,parent_study_sha256=sha256_file(b/new_rel),unchanged='Exact previous original8/18/60 and selected18/60 gates,comparators and intervals; five new final units only. Main unaugmented dense_cached_cpu reference and ten base-unit/noise FA guards,all17 arms unchanged. Ancillary mixed6NI preserved separately. No pooled prior units,blinded/general-transfer or joint95% claim across families.')
atomic_write_json(b/addon_rel,addon)
append_jsonl(b/'research/events.jsonl',{'event':'research_program_study_frozen','created_at':utc_now(),'program_id':initial['id'],'study_path':new_rel,'study_sha256':sha256_file(b/new_rel),'before_implementation':True,'new_arrays_fit_EXP':False,'cycle':317})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_classical_economic_contract_frozen','created_at':utc_now(),'program_id':initial['id'],'study_path':new_rel,'contract_path':addon_rel,'contract_sha256':sha256_file(b/addon_rel),'before_implementation':True,'new_arrays_fit_EXP':False})
p=b/'config/research.toml';raw=p.read_bytes();needle=f'study_path = "{old_rel}"'.encode();assert raw.count(needle)==1;p.write_bytes(raw.replace(needle,f'study_path = "{new_rel}"'.encode()))
auxiliary_reserve(b,prefix+'administration-prepaid-V1',300);auxiliary_charge(b,prefix+'administration-prepaid-V1',300)
header=('# Prospective cycle317 - frozen five-pair fresh final\n\nPVM01-FRESH-FINAL-V1 frozen before implementation/new data.\nSame17 arms,4096 pairs,2048/1024 steps,calibration,3K,updates0/1/4,noise.02/.04.\nFixed unaugmented dense_cached_cpu; neural transport/PCA and classic ridge/PCA assessed separately.\nOriginal8/18/60 and ten base-unit FA guards unchanged;mixed6NI ancillary unchanged.\nFive NEW final units; no earlier units,weights or outcomes pooled. Visible local same-law final,not blinded or transfer evidence.\nBefore final arrays,export25 bounded fitted-source states with full charged copy/serialization cost for separately preregistered B transfer.\nFull workers10200s,aux3600s,fit90s/worker116s/external120s.\nDeadline2026-10-05T12:58:30Z; last replication_and_fresh_final ticket,no rescue/retry.\nMaintenance/scoring=false until clone conformance,freeze/preflight/readiness.\nExactly one audited EXP,WT8-9/external models/APIs/schedule changes forbidden.\nAfter complete charges,explicit A resolution/accounting in next bounded cycle before B activation.\nA active,B authorized/unspent/inactive;expanded transfer/prototype goal remains open. Earlier sections are history.\n\n')
for rel in ('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md'):
    p=b/rel;p.write_bytes(header.encode('utf-8')+p.read_bytes())
p=b/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n# Preserve native byte hashes of fresh-final conformance and startup records.\nresearch/checks/PVM01-FRESH-FINAL-* -text\nresearch/reviews/PVM01-FRESH-FINAL-startup*.json -text\n')
write_report(b);value=status(b)
assert not value['scoring_authorized'] and not value['paid_run_pending']
consumed=595
assert value['fit_seconds_remaining']-10200-(3600-consumed)>=20800
assert datetime.now(timezone.utc)<datetime.fromisoformat(s['study_deadline_at'].replace('Z','+00:00'))
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('.gitattributes','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','research/events.jsonl','research/REPORT','research/reports/','research/plans/PVM01-FRESH-FINAL-','research/checks/PVM01-FRESH-FINAL-','research/laboratory/archive/PVM01-FRESH-FINAL-')
assert all(x.startswith(allowed) for x in paths),[x for x in paths if not x.startswith(allowed)]
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Preregister frozen five-pair fresh final and charged fitted-source preservation'],check=True)
receipt={'study_path':new_rel,'study_sha256':sha256_file(b/new_rel),'classical_contract_sha256':sha256_file(b/addon_rel),'preregistration_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'unchanged_scientific_files':len(science),'new_arrays_fit_EXP':False,'full_reserve_after_worst_current_cost':value['fit_seconds_remaining']-10200-(3600-consumed)}
atomic_write_json(b/'research/tmp/PVM01-FRESH-FINAL-preregistration-V1.json',receipt)
print(json.dumps(receipt),flush=True)