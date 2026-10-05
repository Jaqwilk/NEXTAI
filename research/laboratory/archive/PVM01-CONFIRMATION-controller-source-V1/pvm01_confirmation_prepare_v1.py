from pathlib import Path
import copy, json, subprocess
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import status, auxiliary_reserve, auxiliary_charge
from nextai_autoresearch.report import write_report

b = Path.cwd()
startup = json.loads((b/'research/reviews/PVM01-CONFIRMATION-startup-V1.json').read_text(encoding='utf-8'))
assert startup['result']['returncode'] == 0 and startup['error'] is None
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip() == 'ecbbb2b3cfebb331944350766e49b3f5f62d23f0'
for root in (b,b.parent/'NEXTAI'):
    for rel in ('STOP','PAUSE','research/run.lock'): assert not (root/rel).exists(), (root,rel)
dirty = [x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed = ('research/events.jsonl','research/REPORT.md','research/REPORT.provenance.json','research/reports/','research/reviews/PVM01-CONFIRMATION-startup-','research/laboratory/archive/PVM01-CONFIRMATION-startup-')
assert all(x.startswith(allowed) for x in dirty), dirty
for i in range(0,len(dirty),100): subprocess.run(['git','add','--',*dirty[i:i+100]],check=True)
subprocess.run(['git','commit','-q','-m','Preserve cycle315 startup and charged unchanged-source checks'],check=True)
source = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
old_rel = 'research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json'
new_rel = 'research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json'
addon_rel = 'research/plans/PVM01-CONFIRMATION-CLASSICAL-ECONOMICS-V1.json'
assert not (b/new_rel).exists() and not (b/addon_rel).exists()
tracked = [x for x in subprocess.check_output(['git','ls-files','-z']).decode().split('\0') if x and (b/x).is_file()]
prefixes = {x:{'length':(b/x).stat().st_size,'sha256':sha256_file(b/x)} for x in ('research/events.jsonl','research/plan_registry.jsonl','research/experiments.tsv','research/hypothesis_events.jsonl','research/sources.jsonl')}
atomic_write_json(b/'research/checks/PVM01-CONFIRMATION-history-snapshot-V1.json',{'source_commit':source,'raw_files':{x:sha256_file(b/x) for x in tracked},'prefixes':prefixes})
manifest = json.loads((b/'research/eval_manifest.json').read_text(encoding='utf-8'))
arc = b/'research/laboratory/archive/PVM01-CONFIRMATION-previous-source-V1'
for rel in dict.fromkeys([*manifest['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json','docs/CURRENT_STATUS.md','.gitignore']):
    target = arc/('root.gitattributes.raw' if rel=='.gitattributes' else 'root.gitignore.raw' if rel=='.gitignore' else rel)
    target.parent.mkdir(parents=True,exist_ok=True); assert not target.exists(); target.write_bytes((b/rel).read_bytes())
old = json.loads((b/old_rel).read_text(encoding='utf-8')); s = copy.deepcopy(old)
s.update(id='PVM01-DENSE-NOISE-CONFIRMATION-V1',cohort='paired_view_mutable_memory_v9',stage='replication_and_fresh_final',
    study_kind='paired_view_dense_noise_confirmation',prepared_source_commit=source,
    study_started_at='2026-10-05T05:26:48Z',study_deadline_at='2026-10-05T09:26:48Z',auxiliary_charge_id_prefix='PVM01-CONFIRMATION-',
    question='Independently confirm the selected unchanged mixed-noise dense reference and ridge/PCA-scan route against all17 fixed arms, at three scales and two noises, on five entirely new paired train/dev units. Separate a learned alignment effect from full-cost classical dominance.',
    implementation_scope='No candidate,model,optimizer,task,training,calibration,metrics,thresholds or grid changes. New v9 delegation to frozen v6/v8 task, freshness through0003, audited dispatch/schema and protected analyzer/check wrappers. Prospectively add trusted cumulative CUDA allocator peak snapshots at worker phase transitions and final result metadata; no instrumentation inside timed service/query intervals. Append-only documentation and history guards. No new architectures or new benchmark law.',
    freshness_policy='Five NEW independent runner model seeds and256-bit nonces checked before arrays against every consumed PVM0004..0008 and20261005-0001/0002/0003. A collision invalidates without replacement. All85 workers share the same fresh base arrays/pairing. No earlier unit,weights,calibration,data or outcomes pooled.',
    decision_policy='Invalid/missing fit,cache,data,source or trusted resource evidence makes this comparison INCONCLUSIVE. Independent reference confirmation requires all existing six primary noninferiority endpoints,all six dense competence controls and ten unit/noise false-abstention guards. Selected ridge/PCA confirmation additionally requires all original8 learning/compression gates,all selected18 economic endpoints,original competence/UNKNOWN/FA/each-cell constraints and fixed60 non-domination checks; neural qualification evaluated separately with unchanged gates. Passing independent confirmation is KEEP for a separately frozen fresh five-pair final,never promotion. Causal augmentation improvement still requires the original criterion; adequacy alone is not improvement. Failure preserves the exact outcome and prompts alternatives under remaining caps,without retry,threshold rescue or automatic extra steps.',
    next_alternatives='If independently confirmed, preregister a distinct fresh-final five-pair comparison of the same exact recipe and strong controls. Otherwise preserve the failed confirmation and assess another bounded route or explicit inconclusive closure without weakening gates. Explicitly account A before activating authorized B for two independent transfer families and a minimal local fact/source/update/UNKNOWN prototype.')
science = copy.deepcopy(old['parent_evidence']['scientific_source_sha256_unchanged'])
extra = ['src/nextai_autoresearch/candidates/pvm01_dense_noise_core.py','src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v7.py','src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v8.py','scripts/analyze_pvm01_replication.py','scripts/analyze_pvm01_dense_noise.py','scripts/run_pvm01_dense_noise_check.py','tests/test_pvm01_dense_noise.py']
extra += [f'src/nextai_autoresearch/candidates/{name}.py' for name,role in s['roles'].items() if role['arm'].endswith('_mixed')]
for rel in extra: science[rel] = sha256_file(b/rel)
for rel,digest in science.items(): assert sha256_file(b/rel)==digest,rel
s['parent_evidence'] = {'parent_study_path':old_rel,'parent_study_sha256':sha256_file(b/old_rel),'last_experiment':'EXP-20261005-0003','selected_result_sha256':sha256_file(b/'research/results/EXP-20261005-0003.json'),'selected_analysis_sha256':sha256_file(b/'research/reviews/EXP-20261005-0003-PVM01-dense-noise-analysis.json'),'scientific_source_sha256_unchanged':science,'no_empirical_pooling':True}
s['independent_confirmation'] = {'selected_reference':'dense_cached_cpu_mixed','selected_route':'ridge_pca_scan','all_original17_arms_unchanged':True,'new_independent_units':5,'selection_outcomes_excluded_from_intervals':True,'fresh_final_separate_future_contract':True,'minimum_full_learning_reference_economic_nondomination_gates_unchanged':True}
s['data']['tag'] = s['id']
s['diagnostics']['logging'] += ' V9 adds separately bound trusted worker-resource metadata; no replacement of fit reports,trial values,raw predictions or legacy sample journals.'
s['resource_measurement'] = {'version':'cumulative_cuda_phase_peaks_v1','phases':['initializing','fit','evaluation','complete'],'source':'Trusted WorkerResources,not model-reported counters; torch CUDA allocator peaks reset once at worker start and read after synchronization at phase boundaries; all overhead charged to worker wall.',
    'cuda_peak_allocated_bytes':'Cumulative since worker start,not per-phase incremental or inference-only.',
    'cuda_peak_reserved_bytes':'Cumulative PyTorch allocator reservation,not total driver/context physical VRAM.',
    'process_rss_bytes':'Instantaneous root-worker RSS at boundary; independent parent sampled process-tree peak remains a separate axis.',
    'unchanged_reserved_cap_bytes':s['resources']['max_cuda_reserved_bytes'],'not_inside_timed_service':True,'no_rng_data_weight_prediction_mutation':True,'energy_measured':False,'final_snapshot_required_for_all85_complete_workers':True}
s['amortization_report'] = {'scope':'Descriptive,not a new gate or selection criterion','reuse_counts':[1,4,16],'reuse_unit':'One complete fixed service workload per unit,all3K,updates0/1/4 at a single noise; repeating fresh workloads of the same measured sizes,not a count of individual queries.',
    'formula':'Per-unit trusted fit-phase seconds + R*measured complete service seconds; full process-startup/worker wall separately disclosed; fitted parameters/calibration reused only in this declared scenario.',
    'break_even':'(candidate_fit-reference_fit)/(reference_service-candidate_service) if denominator>0,clamped at zero; otherwise no finite faster-service crossover; descriptive paired5-unit ranges without an inferential gate.',
    'truthfully_charged_once':'No R multiplier on fit,update subsets not double counted; full every-arm grids/fit plus evaluation/testing charged to programme.'}
s['programme_reserves']['fresh_final_and_replication_min_seconds_unspent_after_worst_case_this_study'] = 20800
s['programme_reserves']['remaining_registration_tickets_min_after_this_study'] = 1
s['prepaid_startup_seconds'] = startup['seconds_charged']; s['prepaid_administration_seconds'] = 240
atomic_write_json(b/new_rel,s)
add = copy.deepcopy(json.loads((b/'research/plans/PVM01-ROBUSTNESS-CLASSICAL-ECONOMICS-V1.json').read_text(encoding='utf-8')))
add.update(id='PVM01-CONFIRMATION-CLASSICAL-ECONOMICS-V1',created_at=utc_now(),parent_study_path=new_rel,parent_study_sha256=sha256_file(b/new_rel),unchanged='Independent five-unit confirmation only. Exact original8/18/60 and selected18/60 thresholds,families,comparators and mixed CPU-cache reference retained. No empirical pooling or joint95% claim across families. Trusted RAM/CUDA and descriptive amortization added prospectively without changing any gate.')
atomic_write_json(b/addon_rel,add)
append_jsonl(b/'research/events.jsonl',{'event':'research_program_study_frozen','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','study_path':new_rel,'study_sha256':sha256_file(b/new_rel),'before_implementation':True,'new_arrays_fit_EXP':False,'cycle':315})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_classical_economic_contract_frozen','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','study_path':new_rel,'contract_path':addon_rel,'contract_sha256':sha256_file(b/addon_rel),'before_implementation':True,'new_arrays_fit_EXP':False})
p=b/'config/research.toml'; raw=p.read_bytes(); needle=f'study_path = "{old_rel}"'.encode(); assert raw.count(needle)==1; p.write_bytes(raw.replace(needle,f'study_path = "{new_rel}"'.encode()))
auxiliary_reserve(b,'PVM01-CONFIRMATION-administration-prepaid-V1',240); auxiliary_charge(b,'PVM01-CONFIRMATION-administration-prepaid-V1',240)
header=('# Prospective cycle315 - independent selected-route confirmation\n\nPVM01-DENSE-NOISE-CONFIRMATION-V1 frozen before code/new data.\nSame17 arms,4096 pairs,2048/1024 steps,calibration,all metrics/grids/thresholds.\nFive NEW paired units,K32/128/512,updates0/1/4,noise.02/.04; no old-unit pooling.\nAdd trusted cumulative CUDA allocator phase snapshots and descriptive fit/reuse costs;\nenergy and total driver/context VRAM remain unmeasured. Timed service unchanged.\nFull workers20400s,aux3600s including startup and240s prepaid bookkeeping.\nDeadline2026-10-05T09:26:48Z; reserve20800s and1 future final registration.\nMaintenance/scoring=false until clone conformance,freeze/preflight/readiness.\nExactly one audited EXP,no retry,WT8-9,external models/APIs or schedule change.\nA active,B authorized/unspent/inactive; transfer/prototype goal remains open.\nPrevious sections are preserved history.\n\n')
for rel in ('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md'):
    p=b/rel; p.write_bytes(header.encode('utf-8')+p.read_bytes())
p=b/'.gitattributes'; raw=p.read_bytes(); p.write_bytes(raw+b'\n# Preserve native byte hashes of independent confirmation check records.\nresearch/checks/PVM01-CONFIRMATION-* -text\n')
write_report(b); value=status(b)
assert not value['scoring_authorized'] and not value['paid_run_pending']
assert value['fit_seconds_remaining']-20400-3600>=20800
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('.gitattributes','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','research/events.jsonl','research/REPORT','research/reports/','research/plans/PVM01-DENSE-NOISE-CONFIRMATION-','research/plans/PVM01-CONFIRMATION-','research/checks/PVM01-CONFIRMATION-','research/laboratory/archive/PVM01-CONFIRMATION-')
assert all(x.startswith(allowed) for x in paths), [x for x in paths if not x.startswith(allowed)]
for i in range(0,len(paths),100): subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Preregister independent mixed-reference and classical-route confirmation with full resource disclosure'],check=True)
receipt={'study_path':new_rel,'study_sha256':sha256_file(b/new_rel),'classical_contract_sha256':sha256_file(b/addon_rel),'preregistration_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'unchanged_scientific_files':len(science),'new_arrays_fit_EXP':False}
atomic_write_json(b/'research/tmp/PVM01-CONFIRMATION-preregistration-V1.json',receipt)
print(json.dumps(receipt),flush=True)
