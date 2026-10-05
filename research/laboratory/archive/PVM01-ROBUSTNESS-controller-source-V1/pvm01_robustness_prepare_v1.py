from pathlib import Path
import copy,json,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import status,auxiliary_reserve,auxiliary_charge
from nextai_autoresearch.report import write_report
b=Path.cwd()
startup=json.loads((b/'research/reviews/PVM01-ROBUSTNESS-startup-V1.json').read_text())
assert startup['result']['returncode']==0 and startup['error'] is None
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip().startswith('??')
for rel in ['STOP','PAUSE','research/run.lock']:assert not (b/rel).exists(),rel
dirty=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('research/events.jsonl','research/REPORT.md','research/REPORT.provenance.json','research/reports/','research/reviews/PVM01-ROBUSTNESS-startup-','research/laboratory/archive/PVM01-ROBUSTNESS-startup-')
assert all(x.startswith(allowed) for x in dirty),dirty
for i in range(0,len(dirty),100):subprocess.run(['git','add','--',*dirty[i:i+100]],check=True)
subprocess.run(['git','commit','-q','-m','Preserve cycle314 unchanged-source startup and charged doctor/lab checks'],check=True)
source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
old_rel='research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json'
new_rel='research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json'
addon_rel='research/plans/PVM01-ROBUSTNESS-CLASSICAL-ECONOMICS-V1.json'
assert not (b/new_rel).exists() and not (b/addon_rel).exists()
tracked=[x for x in subprocess.check_output(['git','ls-files','-z']).decode().split('\0') if x and (b/x).is_file()]
prefixes={x:{'length':(b/x).stat().st_size,'sha256':sha256_file(b/x)} for x in ['research/events.jsonl','research/plan_registry.jsonl','research/experiments.tsv','research/hypothesis_events.jsonl','research/sources.jsonl']}
atomic_write_json(b/'research/checks/PVM01-ROBUSTNESS-history-snapshot-V1.json',{'source_commit':source,'raw_files':{x:sha256_file(b/x) for x in tracked},'prefixes':prefixes})
manifest=json.loads((b/'research/eval_manifest.json').read_text())
arc=b/'research/laboratory/archive/PVM01-ROBUSTNESS-previous-source-V1'
for rel in [*manifest['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json','docs/CURRENT_STATUS.md']:
 p=arc/('root.gitattributes.raw' if rel=='.gitattributes' else rel)
 p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes((b/rel).read_bytes())
old=json.loads((b/old_rel).read_text());s=copy.deepcopy(old)
s.update(id='PVM01-DENSE-NOISE-ROBUSTNESS-V1',cohort='paired_view_mutable_memory_v8',stage='reference_and_alternatives',
 study_kind='paired_view_dense_noise_robustness',prepared_source_commit=source,
 study_started_at='2026-10-05T03:33:50Z',study_deadline_at='2026-10-05T07:33:50Z',auxiliary_charge_id_prefix='PVM01-ROBUSTNESS-',
 question='Does training-only mixed observation noise improve dense-reference robustness without altering architecture, steps, alignment, calibration or inference, and can the fixed learned/classical routes meet unchanged matched-quality full-cost gates against this competent reference?',
 implementation_scope='New15 aliases and one dense wrapper over unchanged reproducible core. Add independent Gaussian noise to odd-index T-set context/query arrays only; preserve input arrays. New v8 wrapper delegates unchanged v6 evaluator, audited dispatcher/schema/registry support and freshness through0002. New protected stored-result analyzer/check wrapper. No task/model/scoring/cost/grid/step changes.',
 freshness_policy='Five NEW independent runner model seeds and256-bit nonces checked before arrays against PVM0004..0008 and20261005-0001/0002; collision invalidates without replacement. All85 workers share unchanged base T/D arrays. No pooling earlier data,weights,thresholds or units.',
 decision_policy='Invalid fit/cache/data identity or missing outcomes makes comparison INCONCLUSIVE. Select mixed reference prospectively only if all six primary noninferiority endpoints, unchanged reference competence for all dense variants, and mixed known false-abstention<=.02 in EACH unit/noise pass. Improvement claim additionally needs adverse FA mean reduction>=.002 and simultaneous lower>0. KEEP an adequate mixed recipe without claiming improvement on a null. Otherwise DISCARD this exact augmentation or INCONCLUSIVE if controls fail. Fixed classical/neural economic recipes qualify separately against mixed CPU-cache only under original18/60 gates and all original learning gates; no promotion until independent replication/fresh final. No retry or post-result rescue.',
 next_alternatives='After a qualified prospective selection, freeze an independent replication/fresh-final recipe on new units before data; otherwise assess cheaper reference alternatives under remaining stage caps without weakening gates or simply adding steps. Explicitly close/account A before activating authorized B for two transfer families and local fact/source/update/UNKNOWN prototype.')
s.pop('independent_replication',None)
scientific=old['independent_replication']['scientific_source_sha256_unchanged']
s['parent_evidence']={'parent_study_path':old_rel,'parent_study_sha256':sha256_file(b/old_rel),'last_experiment':'EXP-20261005-0002','scientific_source_sha256_unchanged':scientific,'no_empirical_pooling':True}
s['recipe']['dense_noise_augmentation']={'base_noise':.02,'augmented_noise':.04,'augmented_episode_parity':1,'independent_added_gaussian_std':(.04**2-.02**2)**.5,'noise_rng_seed_xor':0x504D584E,'context_then_query_by_ascending_K':True,'base_observation_count_unchanged':True,'noise_is_training_only':True}
for arm in ('dense_mixed','dense_cached_cpu_mixed','dense_cached_cuda_mixed'):
 for i in range(5):
  name=f'pvm01_noise_{arm}_s{i}';s['candidates'].append(name);s['roles'][name]={'arm':arm,'seed_index':i,'fit_steps':2048}
s['data']['tag']=s['id']
s['data']['legal_training_sets']='Same128 base episodes/K32/128,8 queries,zero updates; all roles receive identical legal base arrays. Mixed dense roles copy arrays and add seeded independent Gaussian noise std sqrt(.04^2-.02^2) to contexts AND queries of odd-index64 episodes/K, leaving even64 and all labels unchanged. Marginal training noise .02/.04; no new identities, extra episodes, K512 support or D reuse. All alignment/validation/calibration remains .02.'
s['data']['adverse_pairing']='D conditions retain unchanged same latent/truth/draw pairing at noise.02/.04. No D arrays are used for augmentation or calibration. Base T-array hashes shared across85 roles; effective mixed T-set hashes separately recorded and exact across three mixed dense/cache roles.'
s['resources']['fit_seconds_study_cap']=20400
s['dense_noise_reference_gates']={'primary_comparisons':6,'interval_level':1-.05/6,'independent_units':5,'endpoints':['mixed_minus_base_full_at_each_noise','mixed_minus_base_UNKNOWN_at_each_noise','base_minus_mixed_false_abstention_at_each_noise'],'full_and_unknown_ci_lower_min':-.02,'false_abstention_reduction_ci_lower_min':-.002,'mixed_each_unit_noise_false_abstention_max':.02,'causal_improvement_adverse_false_abstention_mean_min':.002,'causal_improvement_adverse_false_abstention_ci_lower_strict_min':0.,'adequacy_is_not_causal_improvement':True}
s['selected_classical_route_confirmation']['competent_reference']='dense_cached_cpu_mixed'
s['economic_measurement']['reference_arm']='dense_cached_cpu_mixed'
s['diagnostics']['reproducibility'].append('Mixed dense/cache exact initialization,noise RNG,effective arrays,2048 encoder losses/hash,1024 decoder losses/hash,predictions; original baseline three-cache identity separately preserved')
s['programme_reserves']['fresh_final_and_replication_min_seconds_unspent_after_worst_case_this_study']=20800
s['prepaid_startup_seconds']=startup['seconds_charged']
s['prepaid_administration_seconds']=180
for rel,digest in scientific.items():assert sha256_file(b/rel)==digest,rel
atomic_write_json(b/new_rel,s)
add=copy.deepcopy(json.loads((b/'research/plans/PVM01-REPLICATION-CLASSICAL-ECONOMICS-V1.json').read_text()))
add.update(id='PVM01-ROBUSTNESS-CLASSICAL-ECONOMICS-V1',created_at=utc_now(),parent_study_path=new_rel,parent_study_sha256=sha256_file(b/new_rel),unchanged='Original strong-classical60 checks and8 learning/18 economics thresholds retained. Reference changes only to prospectively mixed-noise CPU-cache; original reference remains visible. Selected-route18/60 family separately retained, no joint95% claim.')
atomic_write_json(b/addon_rel,add)
append_jsonl(b/'research/events.jsonl',{'event':'research_program_study_frozen','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','study_path':new_rel,'study_sha256':sha256_file(b/new_rel),'before_implementation':True,'new_arrays_fit_EXP':False,'cycle':314})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_classical_economic_contract_frozen','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','study_path':new_rel,'contract_path':addon_rel,'contract_sha256':sha256_file(b/addon_rel),'before_implementation':True,'new_arrays_fit_EXP':False})
p=b/'config/research.toml';raw=p.read_bytes();needle=f'study_path = "{old_rel}"'.encode();assert raw.count(needle)==1;p.write_bytes(raw.replace(needle,f'study_path = "{new_rel}"'.encode()))
auxiliary_reserve(b,'PVM01-ROBUSTNESS-administration-prepaid-V1',180);auxiliary_charge(b,'PVM01-ROBUSTNESS-administration-prepaid-V1',180)
header=('# Prospective cycle314 — dense training-noise robustness\n\nPVM01-DENSE-NOISE-ROBUSTNESS-V1 frozen before implementation/new data.\nFive fresh paired units,17 arms,85 workers,K32/128/512,updates0/1/4,D noise.02/.04.\nOnly odd-half dense training contexts/queries receive independent Gaussian noise\nto marginal.04; model,4096 alignment pairs,2048/1024 steps and calibration unchanged.\nOriginal14 controls retained; six simultaneous primary noninferiority endpoints,\nseparate causal FA claim, and original learning/competence/economic gates frozen.\nFull worker cap20400s,aux3600s including startup and180s prepaid bookkeeping;\ndeadline2026-10-05T07:33:50Z. Reserve20800s and2 registrations for replication/final.\nMaintenance/scoring=false until clone conformance,freeze/preflight/readiness.\nOne audited EXP,no retry,WT8-9,external model/API or schedule change.\nA active; B inactive; extended transfer/prototype goal remains open.\nEarlier sections preserved as history.\n\n')
for rel in ['AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md']:
 p=b/rel;p.write_bytes(header.encode()+p.read_bytes())
write_report(b)
value=status(b);assert not value['scoring_authorized'] and not value['paid_run_pending']
assert value['fit_seconds_remaining']-20400-3600>=20800
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','research/events.jsonl','research/REPORT.md','research/REPORT.provenance.json','research/reports/','research/plans/PVM01-DENSE-NOISE-','research/plans/PVM01-ROBUSTNESS-CLASSICAL-','research/checks/PVM01-ROBUSTNESS-history-snapshot-','research/laboratory/archive/PVM01-ROBUSTNESS-previous-source-')
assert all(x.startswith(allowed) for x in paths),[x for x in paths if not x.startswith(allowed)]
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
with (b/'research/tmp/PVM01-ROBUSTNESS-preregistration-whitespace-V1.txt').open('xb') as out:subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],stdout=out,stderr=out,check=True)
subprocess.run(['git','commit','-q','-m','Preregister paired dense training-noise robustness and unchanged full-cost gates'],check=True)
print(json.dumps({'study':new_rel,'study_sha256':sha256_file(b/new_rel),'classical_contract_sha256':sha256_file(b/addon_rel),'preregistration_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'unchanged_scientific_files':len(scientific),'new_arrays_fit_EXP':False}),flush=True)
