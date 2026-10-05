from pathlib import Path
import copy,json,subprocess,shutil
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import status
b=Path.cwd()
assert not subprocess.check_output(['git','status','--porcelain'],text=True).strip()
old_rel='research/plans/PVM01-TRANSPORT-COMPRESSION-ADVERSE-V2.json'
new_rel='research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json'
addon_rel='research/plans/PVM01-REPLICATION-CLASSICAL-ECONOMICS-V1.json'
assert not (b/new_rel).exists() and not (b/addon_rel).exists()
source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
tracked=[x for x in subprocess.check_output(['git','ls-files','-z']).decode().split('\0') if x and (b/x).is_file()]
prefixes={x:{'length':(b/x).stat().st_size,'sha256':sha256_file(b/x)} for x in ['research/events.jsonl','research/plan_registry.jsonl','research/experiments.tsv','research/hypothesis_events.jsonl','research/sources.jsonl']}
atomic_write_json(b/'research/checks/PVM01-REPLICATION-history-snapshot-V1.json',
 {'source_commit':source,'raw_files':{x:sha256_file(b/x) for x in tracked},'prefixes':prefixes})
manifest=json.loads((b/'research/eval_manifest.json').read_text())
arc=b/'research/laboratory/archive/PVM01-REPLICATION-previous-source-V1'
for rel in [*manifest['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json','docs/CURRENT_STATUS.md']:
 p=arc/('root.gitattributes.raw' if rel=='.gitattributes' else rel)
 p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes((b/rel).read_bytes())
old=json.loads((b/old_rel).read_text());s=copy.deepcopy(old)
for key in ['preseed_metadata_correction','prospective_feasibility']:s.pop(key,None)
s.update(id='PVM01-INDEPENDENT-REPLICATION-V1',cohort='paired_view_mutable_memory_v7',stage='replication_and_fresh_final',
 prepared_source_commit=source,study_started_at='2026-10-05T01:54:18Z',study_deadline_at='2026-10-05T05:54:18Z',
 auxiliary_charge_id_prefix='PVM01-REPLICATION-',
 question='Independently replicate the frozen transport/PCA learning/compression/adverse comparison and confirm selected ridge/PCA-scan matched-quality full-cost performance versus competent dense/cache and all strong alternatives on five fresh paired units; no empirical pooling with the selecting experiment.',
 implementation_scope='No candidate,task law,scoring,cost,batch,grid,loss,optimizer or model changes. Add only versioned v7 wrapper delegating v6, v7 audited dispatcher/schema/registry support and pre-array freshness guard including EXP-20261005-0001. Reuse all existing70 candidate aliases unchanged. Reuse stored-result primary analyzer plus a small prospective selected-route secondary analysis. Validate meaningful negative guards and full regression in independent clone before freeze/preflight/readiness.',
 freshness_policy='Five fresh independent runner model seeds and256-bit nonces, checked before arrays against all consumed PVM0004..0008 and EXP-20261005-0001. Collision invalidates without replacement. No saved data/weights/thresholds; all14 arms and two noise conditions paired within a fresh unit.',
 decision_policy='Validity and unchanged eight primary/reference/18 neural economics/60 strong-classical gates exactly as parent. No pooling prior units into this independent n5 replica. Independently KEEP exact learned transport only if original gates pass; no neural full economic claim while a matched strong classical dominator remains. KEEP selected classical route for frozen fresh-final validation only if it separately meets original competence,18 matched-quality CPU-cache gates and60 fixed-comparator non-domination checks; otherwise INCONCLUSIVE/DISCARD exact selected economic route. A failure does not close expanded goal. No retry,threshold rescue,tuning or architecture promotion.',
 next_alternatives='After valid replication freeze selected recipe and final contract before fresh final. After final resolution close/account A and activate authorized B carrying all consumed budgets; transfer to two independent families including licensed public real data and minimal local fact/source/update/UNKNOWN prototype. If selected recipe fails, assess justified alternatives under remaining caps without post-result gate weakening.')
s['resources']['auxiliary_test_seconds_cap']=3600
s['data']['tag']=s['id']
registry=json.loads((b/'config/baseline_semantics.json').read_text())
scientific={rel:sha256_file(b/rel) for candidate in s['candidates'] for rel in registry['baselines'][candidate]['implementation_files']}
for rel in ['src/nextai_autoresearch/pvm01_task.py','src/nextai_autoresearch/pvm01_adverse_task.py','src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v6.py','src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v3.py','scripts/analyze_pvm01_transport.py']:
 scientific[rel]=sha256_file(b/rel)
s['independent_replication']={'selecting_experiment':'EXP-20261005-0001','selecting_study_path':old_rel,
 'selecting_study_sha256':sha256_file(b/old_rel),'scientific_source_sha256_unchanged':scientific,
 'selection_fixed_before_new_data':True,'no_empirical_pooling':True,'new_cohort_reason':'pre-array freshness history and versioned integration only; unchanged task/model/scoring recipes',
 'strong_controls_all14_preserved':True,'prepared_clone':str(b)}
s['selected_classical_route_confirmation']={
 'candidate':'ridge_pca_scan','competent_reference':'dense_cached_cpu',
 'competence_gates':'Exact existing reference_gates separately in each noise; all three scales retained.',
 'economic_pair_family':{'comparisons':18,'interval_level':1-.05/18,'metrics':['accuracy_difference','full_workload_seconds_ratio','p95_us_ratio'],
 'quality_ci_lower_min':-.02,'service_ratio_ci_upper_max':.8,'p95_ratio_ci_upper_max':.9,
 'per_cell_unknown_min':.95,'per_cell_false_abstention_max':.02},
 'non_domination_family':{'comparisons':60,'interval_level':1-.05/60,
 'fixed_comparators':['ridge','ridge32','ridge_pca_tree','kernel','transport_pca'],
 'quality_control_minus_candidate_ci_lower_min':-.02,'control_service_ratio_ci_upper_strict_max':1.,
 'control_state_no_greater':True,'control_accuracy_min':.95,'control_unknown_min':.95,'control_false_abstention_max':.02},
 'families_reported_separately':'Each declared family has95% coverage; not a joint95% claim across all families. No comparator/endpoint selection after results.',
 'non_domination_is_not_novelty_or_transfer':True}
s['programme_reserves']={'fresh_final_and_replication_min_seconds_unspent_after_worst_case_this_study':20800,
 'remaining_registration_tickets_min_after_this_study':2,'stage_b_not_activated_or_spent':True}
for key in ['recipe','roles','candidates','matrix','primary_endpoints','diagnosis_gates','reference_gates','economic_gates','economic_measurement','diagnostics']:
 assert s[key]==old[key],key
atomic_write_json(b/new_rel,s)
add=copy.deepcopy(json.loads((b/'research/plans/PVM01-TRANSPORT-CLASSICAL-ECONOMICS-V1.json').read_text()))
add.update(id='PVM01-REPLICATION-CLASSICAL-ECONOMICS-V1',created_at=utc_now(),parent_study_path=new_rel,parent_study_sha256=sha256_file(b/new_rel),
 unchanged='Exact original neural/classical60-interval checks and8/18 parent gates, frozen again for independent replication before code/private data. Selected-route secondary18/60 families are prospectively fixed in parent contract, not a retrospective rescue.')
atomic_write_json(b/addon_rel,add)
append_jsonl(b/'research/events.jsonl',{'event':'research_program_study_frozen','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1',
 'study_path':new_rel,'study_sha256':sha256_file(b/new_rel),'before_implementation':True,'new_arrays_fit_EXP':False,'cycle':313})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_classical_economic_contract_frozen','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1',
 'study_path':new_rel,'contract_path':addon_rel,'contract_sha256':sha256_file(b/addon_rel),'before_implementation':True,'new_arrays_fit_EXP':False})
p=b/'config/research.toml';raw=p.read_bytes();oldbytes=f'study_path = "{old_rel}"'.encode();assert raw.count(oldbytes)==1
p.write_bytes(raw.replace(oldbytes,f'study_path = "{new_rel}"'.encode()))
header=('# Prospective cycle313 — independent fixed-recipe replication\n\nPVM01-INDEPENDENT-REPLICATION-V1 frozen before code/new data.\nAll14 arms and scientific recipes unchanged;5 fresh paired units,K32/128/512,\nupdates0/1/4,noise0.02/0.04. New v7 integration extends pre-array freshness\nthrough EXP-20261005-0001; no new candidate architecture or data law.\nOriginal8/18/60 gates retained; selected ridge/PCA route has prospective18/60\nsecondary cost/quality/non-domination families. No pooling selecting units.\nFull workers16800s,aux3600s including startup171s and administration180s;\ndeadline2026-10-05T05:54:18Z. Keep20800s and2 tickets for replication/fresh final.\nMaintenance/scoring=false until clone tests,freeze/preflight/readiness pass.\nExactly one audited EXP,no retry,WT8-9/API/schedule changes.\nPending original cycle312 doctor/lab now PASS; old receipt/costs preserved.\nA remains active; authorized B inactive. Transfer/prototype goal remains open.\nPrevious sections below are preserved history.\n\n')
for rel in ['AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md']:
 p=b/rel;p.write_bytes(header.encode('utf-8')+p.read_bytes())
value=status(b)
assert not value['scoring_authorized'] and not value['paid_run_pending']
assert value['fit_seconds_remaining']-16800-3600>=20800
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','research/events.jsonl',
 'research/plans/PVM01-INDEPENDENT-REPLICATION-','research/plans/PVM01-REPLICATION-CLASSICAL-',
 'research/checks/PVM01-REPLICATION-history-snapshot-','research/laboratory/archive/PVM01-REPLICATION-previous-source-')
assert all(x.startswith(allowed) for x in paths),[x for x in paths if not x.startswith(allowed)]
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
with (b/'research/tmp/PVM01-REPLICATION-preregistration-whitespace-V1.txt').open('xb') as out:
 subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],stdout=out,stderr=out,check=True)
subprocess.run(['git','commit','-q','-m','Preregister independent transport replication and selected classical cost confirmation'],check=True)
print(json.dumps({'study':new_rel,'study_sha256':sha256_file(b/new_rel),'classical_contract_sha256':sha256_file(b/addon_rel),
 'preregistration_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'scientific_source_files_unchanged':len(scientific),'new_scientific_implementation_arrays_fit_EXP':False}),flush=True)
