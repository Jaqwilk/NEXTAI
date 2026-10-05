from pathlib import Path
from datetime import datetime,timezone
import copy,json,math,subprocess,time
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import status,auxiliary_reserve,auxiliary_charge
from nextai_autoresearch.report import write_report
b=Path.cwd();o=b.parent/'NEXTAI';parent='109f421bbae55f436224d97b7c9a9d22ecc6f340';prefix='PVM01-BASE-REFERENCE-'
startup=json.loads((b/'research/reviews/PVM01-BASE-REFERENCE-startup-observation-V1.json').read_text(encoding='utf-8'))
assert startup['doctor_returncode']==startup['lab_returncode']==0 and startup['source_revision']==parent
assert 'Doctor: PASS' in (b/'research/reviews/PVM01-BASE-REFERENCE-startup-doctor-V1.stdout.txt').read_text(encoding='utf-8')
lab=json.loads((b/'research/reviews/PVM01-BASE-REFERENCE-startup-lab-V1.stdout.txt').read_text(encoding='utf-8'));assert lab['errors']==[] and lab['scoring_ready'] is False
for root in (b,o):
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
    for rel in ('STOP','PAUSE','research/run.lock'):assert not (root/rel).exists(),(root,rel)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=o).strip()
dirty=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
assert all(x.startswith('research/reviews/PVM01-BASE-REFERENCE-startup-') for x in dirty),dirty
initial=status(b);assert initial['study_terminal'] and not initial['program_closed'] and initial['continuation_registration_attempts_used']==9
assert initial['stage_registration_attempts']['reference_and_alternatives']==4 and initial['stage_registration_attempts']['replication_and_fresh_final']==2
auxiliary_reserve(b,prefix+'startup-V1',int(startup['conservative_seconds_to_charge']));auxiliary_charge(b,prefix+'startup-V1',int(startup['conservative_seconds_to_charge']))
owned=[*dirty,'research/events.jsonl']
subprocess.run(['git','add','--',*owned],check=True)
subprocess.run(['git','commit','-q','-m','Preserve cycle316 startup checks and full conservative charge'],check=True)
source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
tracked=[x for x in subprocess.check_output(['git','ls-files','-z']).decode().split('\0') if x and (b/x).is_file()]
prefixes={x:{'length':(b/x).stat().st_size,'sha256':sha256_file(b/x)} for x in ('research/events.jsonl','research/plan_registry.jsonl','research/experiments.tsv','research/hypothesis_events.jsonl','research/sources.jsonl')}
snapshot=b/'research/checks/PVM01-BASE-REFERENCE-history-snapshot-V1.json';assert not snapshot.exists()
atomic_write_json(snapshot,{'source_commit':source,'original_parent_commit':parent,'raw_files':{x:sha256_file(b/x) for x in tracked},'prefixes':prefixes})
manifest=json.loads((b/'research/eval_manifest.json').read_text(encoding='utf-8'));arc=b/'research/laboratory/archive/PVM01-BASE-REFERENCE-previous-source-V1';assert not arc.exists()
for rel in dict.fromkeys([*manifest['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json','docs/CURRENT_STATUS.md','.gitignore']):
    target=arc/('root.gitattributes.raw' if rel=='.gitattributes' else 'root.gitignore.raw' if rel=='.gitignore' else rel)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((b/rel).read_bytes())
old_rel='research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json';new_rel='research/plans/PVM01-BASE-REFERENCE-CONFIRMATION-V1.json';addon_rel='research/plans/PVM01-BASE-REFERENCE-CLASSICAL-ECONOMICS-V1.json'
assert not (b/new_rel).exists() and not (b/addon_rel).exists()
old=json.loads((b/old_rel).read_text(encoding='utf-8'));s=copy.deepcopy(old)
s.update(id='PVM01-BASE-REFERENCE-CONFIRMATION-V1',cohort='paired_view_mutable_memory_v10',stage='reference_and_alternatives',study_kind='paired_view_unaugmented_reference_confirmation',prepared_source_commit=source,
    study_started_at='2026-10-05T07:26:46Z',study_deadline_at='2026-10-05T11:26:46Z',auxiliary_charge_id_prefix=prefix,
    question='On five entirely new paired train/dev units, does fixed learned transport/PCA or selected ridge/PCA-scan match the competent UN-AUGMENTED dense_cached_cpu Transformer at lower full service cost and survive the original strong classical non-domination checks? Preserve the failed mixed-reference assay as separate augmentation evidence.',
    implementation_scope='No candidate,model,optimizer,steps,pair count,task law,training,calibration,grids,diagnosis gates,competence or economic thresholds change. New v10 delegates the frozen v9/v8/v6 worker; extend pre-array freshness through0004, audited dispatch/schema, and a protected stored-outcome analyzer. Separate new unaugmented-reference claim-specific qualification from unchanged six mixed-reference NI endpoints; require the same <=2% each-unit/noise FA guard for the base family. Trusted synchronized CUDA/RSS snapshots and timed service remain unchanged.',
    freshness_policy='Five NEW runner model seeds and256-bit unit nonces checked before arrays against all consumed PVM units from20261004-0004 through0008 and20261005-0001 through0004,including failures. Collision invalidates without replacement. Same85 roles share new legal base arrays; no prior unit,weights,calibration or outcomes pooled.',
    decision_policy='Invalid/partial source,fit,cache,data,resources or missing independent units => INCONCLUSIVE. Base-reference confirmation requires original competence for all three unaugmented dense/cache variants at both noises and all ten <=2% base per-unit/noise false-abstention guards. Selected ridge/PCA qualification additionally requires all original8 causal-learning/compression gates and exact18 economic,per-cell quality/UNKNOWN/FA,60 fixed-comparator non-domination checks. Neural qualification separately requires the same conditions with its original five strong classical comparators. The mixed six NI endpoints and their old decisions remain separately reported,with unchanged formulas/thresholds; they cannot qualify or disqualify this distinct base-reference question. KEEP a qualifying fixed route only for a separately frozen five-pair fresh final. Failure of competent comparisons DISCARD this exact qualification; failed reference controls INCONCLUSIVE. No promotion,extra steps,tuning,threshold rescue or paid retry.',
    next_alternatives='If this separately frozen five-pair reference/route confirmation qualifies, use the remaining replication_and_fresh_final ticket for a fresh frozen final with the selected route,unaugmented reference and all strong controls. Otherwise explicitly resolve A negative/inconclusive with exact remaining scope and durable usage before activating authorized B for two independent transfer families and the evidence-selected local fact/source/update/UNKNOWN prototype. No further reference ticket is available after this study.')
science=copy.deepcopy(old['parent_evidence']['scientific_source_sha256_unchanged'])
for rel in ('src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v9.py','src/nextai_autoresearch/worker_resource_peaks.py','scripts/analyze_pvm01_confirmation.py','scripts/run_pvm01_confirmation_check.py','tests/test_pvm01_confirmation.py'):science[rel]=sha256_file(b/rel)
for rel,digest in science.items():assert sha256_file(b/rel)==digest,rel
s['parent_evidence']={'parent_study_path':old_rel,'parent_study_sha256':sha256_file(b/old_rel),'last_experiment':'EXP-20261005-0004','selected_result_sha256':sha256_file(b/'research/results/EXP-20261005-0004.json'),'selected_analysis_sha256':sha256_file(b/'research/reviews/EXP-20261005-0004-PVM01-confirmation-analysis.json'),'scientific_source_sha256_unchanged':science,'no_empirical_pooling':True,'parent_failed_qualification_preserved':True}
s['independent_confirmation']={'selected_reference':'dense_cached_cpu','selected_route':'ridge_pca_scan','all_original17_arms_unchanged':True,'new_independent_units':5,'selection_outcomes_excluded_from_intervals':True,'fresh_final_separate_future_contract':True,'minimum_full_learning_reference_economic_nondomination_gates_unchanged':True}
# The old mixed-study declarations are retained verbatim for the ancillary assay.
s['unaugmented_reference_confirmation']=copy.deepcopy(old['selected_classical_route_confirmation'])
s['unaugmented_reference_confirmation']['competent_reference']='dense_cached_cpu'
s['unaugmented_reference_guards']={'reference_variants':['dense','dense_cached_cpu','dense_cached_cuda'],'noise':[0.02,0.04],'independent_units':5,'each_unit_noise_false_abstention_max':0.02,'guards':10,'all_original_competence_gates_required':True,'base_vs_itself_noninferiority_assay_forbidden':True}
s['preserved_mixed_assay']={'six_endpoints_unchanged':True,'old_recipe_decisions_are_not_repaired':True,'not_a_gate_for_new_base_reference_question':True,'old_dense_noise_reference_gates_sha256':sha256_file(b/old_rel)}
s['data']['tag']=s['id']
s['resources'].update(fit_seconds_per_role_cap=90,fit_seconds_study_cap=10200,worker_seconds_cap=116,worker_charge_ceiling_with_monitor_margin=120,auxiliary_test_seconds_cap=3600)
s['prospective_tighter_resource_caps']={'scientific_workload_unchanged':True,'evidence':'All85 prior identical-recipe workers completed; slowest group mean<28s, trusted fit group mean<13s. New116s internal/120s external worker and90s fit bounds are conservative prospective limits. Timeout preserves the failed outcome without retry. The bound allows a full24000s fresh-final reserve.','total_max_worker_plus_auxiliary_seconds':13800}
s['programme_reserves']['fresh_final_and_replication_min_seconds_unspent_after_worst_case_this_study']=24000
s['programme_reserves']['remaining_registration_tickets_min_after_this_study']=1
s['prepaid_startup_seconds']=int(startup['conservative_seconds_to_charge']);s['prepaid_administration_seconds']=300
atomic_write_json(b/new_rel,s)
addon=copy.deepcopy(json.loads((b/'research/plans/PVM01-CONFIRMATION-CLASSICAL-ECONOMICS-V1.json').read_text(encoding='utf-8')))
addon.update(id='PVM01-BASE-REFERENCE-CLASSICAL-ECONOMICS-V1',created_at=utc_now(),parent_study_path=new_rel,parent_study_sha256=sha256_file(b/new_rel),unchanged='Exact original8/18/60 and selected18/60 calculations,thresholds and comparators retained. New base-reference claim fixed prospectively at dense_cached_cpu,with additional ten base per-unit/noise FA guards. All seventeen arms unchanged; ancillary mixed-reference six NI assay and original qualifications preserved separately. No old-unit pooling or joint95% claim across families.')
atomic_write_json(b/addon_rel,addon)
append_jsonl(b/'research/events.jsonl',{'event':'research_program_study_frozen','created_at':utc_now(),'program_id':initial['id'],'study_path':new_rel,'study_sha256':sha256_file(b/new_rel),'before_implementation':True,'new_arrays_fit_EXP':False,'cycle':316})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_classical_economic_contract_frozen','created_at':utc_now(),'program_id':initial['id'],'study_path':new_rel,'contract_path':addon_rel,'contract_sha256':sha256_file(b/addon_rel),'before_implementation':True,'new_arrays_fit_EXP':False})
p=b/'config/research.toml';raw=p.read_bytes();needle=f'study_path = "{old_rel}"'.encode();assert raw.count(needle)==1;p.write_bytes(raw.replace(needle,f'study_path = "{new_rel}"'.encode()))
auxiliary_reserve(b,prefix+'administration-prepaid-V1',300);auxiliary_charge(b,prefix+'administration-prepaid-V1',300)
header=('# Prospective cycle316 - distinct unaugmented-reference confirmation\n\nPVM01-BASE-REFERENCE-CONFIRMATION-V1 frozen before implementation/new data.\nSame17 arms,4096 pairs,2048/1024 steps,calibration,3K,updates0/1/4,noise.02/.04.\nNew claim uses fixed unaugmented dense_cached_cpu reference and ten base-unit FA guards.\nOriginal8/18/60 thresholds unchanged; mixed six NI assay retained separately.\nFive NEW paired units; failed315 qualification/history remain unchanged.\nFull workers10200s,aux3600s,fit90s/worker116s/external120s prospectively bounded.\nDeadline2026-10-05T11:26:46Z; reserve24000s and1 final registration.\nMaintenance/scoring=false until clone conformance,freeze/preflight/readiness.\nExactly one audited EXP,no retry,WT8-9,external models/APIs or schedule change.\nLast reference_and_alternatives ticket; A active,B authorized/unspent/inactive.\nExpanded final/transfer/prototype goal remains open. Earlier sections are history.\n\n')
for rel in ('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md'):
    p=b/rel;p.write_bytes(header.encode('utf-8')+p.read_bytes())
p=b/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n# Preserve native byte hashes of base-reference conformance records.\nresearch/checks/PVM01-BASE-REFERENCE-* -text\n')
write_report(b);value=status(b)
assert not value['scoring_authorized'] and not value['paid_run_pending']
# Startup/admin charges have already reduced remaining; only unspent aux bound is deducted.
consumed=s['prepaid_startup_seconds']+s['prepaid_administration_seconds']
assert value['fit_seconds_remaining']-10200-(3600-consumed)>=24000
assert datetime.now(timezone.utc)<datetime.fromisoformat(s['study_deadline_at'].replace('Z','+00:00'))
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('.gitattributes','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','research/events.jsonl','research/REPORT','research/reports/','research/plans/PVM01-BASE-REFERENCE-','research/checks/PVM01-BASE-REFERENCE-','research/laboratory/archive/PVM01-BASE-REFERENCE-')
assert all(x.startswith(allowed) for x in paths),[x for x in paths if not x.startswith(allowed)]
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Preregister distinct base-reference comparison with unchanged scientific gates and final reserve'],check=True)
receipt={'study_path':new_rel,'study_sha256':sha256_file(b/new_rel),'classical_contract_sha256':sha256_file(b/addon_rel),'preregistration_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'unchanged_scientific_files':len(science),'new_arrays_fit_EXP':False,'full_final_reserve_after_worst_current_cost':value['fit_seconds_remaining']-10200-(3600-consumed)}
atomic_write_json(b/'research/tmp/PVM01-BASE-REFERENCE-preregistration-V1.json',receipt)
print(json.dumps(receipt),flush=True)