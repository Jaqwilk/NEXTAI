from pathlib import Path
import json, numpy as np, sys
sys.path.insert(0,str(Path.cwd()/"scripts"))
from analyze_pvm01_transport import interval
from nextai_autoresearch.utils import sha256_file
from nextai_autoresearch.research_program import status
from nextai_autoresearch.ledger import read_jsonl
b=Path.cwd();eid='EXP-20261005-0003'
a=json.loads((b/f'research/reviews/{eid}-PVM01-dense-noise-analysis.json').read_text())
r=json.loads((b/f'research/results/{eid}.json').read_text());plan=json.loads((b/f'research/plans/{eid}.json').read_text())
study_rel='research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json';study=json.loads((b/study_rel).read_text())
selection=a['reference_selection'];neural=a['neural_economics_against_mixed_reference'];classic=a['selected_classical_route_confirmation']
run=json.loads((b/'research/reviews/PVM01-ROBUSTNESS-audited-run-overhead-V1.json').read_text());pub=json.loads((b/f'research/laboratory/{eid}-publication-V2.json').read_text())
ready=json.loads((b/'research/laboratory/PVM01-DENSE-NOISE-ROBUSTNESS-V1-readiness.receipt.json').read_text())
path=b/f'research/analyses/{eid}.md';assert not path.exists()
def avg(arm,noise,key,k=None):
 units=a['arms'].get(arm,{}).get(noise,{})
 values=[(u['by_K'][str(k)] if k else u).get(key) for u in units.values()]
 values=[v for v in values if v is not None]
 return float(np.mean(values)) if values else None

def fmt(value,scale=1,digits=4):return 'not available' if value is None else f'{value*scale:.{digits}f}'
def bounds(value,scale=1):return 'incomplete' if value['low'] is None else f"{value['mean']*scale:.4f} [{value['low']*scale:.4f},{value['high']*scale:.4f}]"
if classic['screen_qualified']:
 next_test='Preregister an independent unchanged-recipe confirmation of this exact selected mixed-noise dense reference and ridge/PCA-scan route, five NEW paired units, all three K, both noises, updates0/1/4 and all fixed strong controls. Preserve current selection; freeze/source conformance/readiness before fresh arrays and one audited EXP in the next bounded cycle. If confirmed, conduct a separately frozen fresh-final five-pair comparison. No current paid-plan retry or promotion from this selection.'
elif selection['adequate_for_prospective_selection']:
 next_test='The mixed-noise reference is adequate, but the full selected-route economics did not qualify. Preregister one bounded alternative discriminating the exact failed quality/cost or classical non-domination gates, using fresh paired units and all strong controls. Keep thresholds fixed and reserve an independent confirmation and fresh final. Do not automatically increase steps or advance this failed qualification to final.'
else:
 next_test='Close this exact mixed-noise qualification with its frozen decision; no automatic fresh final. Before any next code/data, preregister a bounded reference/calibration alternative or a precision study on NEW paired units that separates known ranking from rejection, targets the exact failed gates, keeps the original model and full-cost controls, and reserves independent confirmation/fresh final. Reassess analytical/classical routes; do not use the current outcomes to weaken thresholds, alter this plan or retry it.'
lines=[f'# {eid} - paired training-noise robustness and full-cost controls','','## OBSERVATION','',
 f'Immutable plan: research/plans/{eid}.json; raw SHA {sha256_file(b/f"research/plans/{eid}.json")}.',
 f'Prospective study: {study_rel}; SHA {sha256_file(b/study_rel)}.',
 f"Preregistered source {ready['preregistration_git_commit']}; independently validated source {ready['validated_source_git_commit']}; evaluated source {run['prepared_source_git_commit']}.",
 'All80 parent scientific source hashes remain unchanged. V8 integrates one training-observation-noise intervention; the task, base architectures,4096 alignment pairs,2048 transport steps,1024 dense steps,optimizer,calibration,metrics,thresholds and original controls remain frozen.',
 'Each fresh unit has the same128 training episodes per K32/128,8 queries,zero updates. Mixed arms copy legal inputs and add independent Gaussian noise sqrt(0.04^2-0.02^2) to contexts and queries in the odd64 episodes; targets/even episodes are unchanged. A private local NumPy generator uses model_seed XOR0x504D584E, ascendingK,contexts thenqueries,without changing Torch initialization. No extra identities or train support at K512.',
 'Five NEW paired train/dev data/model-seed units;17 arms,3K32/128/512,updates0/1/4,dev noise0.02/0.04. The same fresh truth pairs and noise directions are shared; previous selecting/replication outcomes are not pooled.',
 f"Workers {len(r['candidates'])}, complete {sum(o['status']=='complete' for o in r['candidates'])}, trials {sum(len(o['trials']) for o in r['candidates'])}; valid_comparison={a['valid_comparison']}.",
 'All base and mixed cache variants pass their own exact fit/encoder/decoder/loss/input-hash checks; discrete predictions are identical within each family and score drift is bounded by the unchanged1e-5 tolerance. Augmentation copies/time are charged. Complete checks, unit/cell values and failures are in the machine report.',
 '', '| noise | arm | full answer % | UNKNOWN % | known false abstention % | retained % | updated % | known top1 % | service s/unit | p95 us | logical state bytes |',
 '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
order=('transport_pca','transport_full','transport_pca_untrained','transport_pca_shuffled','dense','dense_cached_cpu','dense_cached_cuda','dense_mixed','dense_cached_cpu_mixed','dense_cached_cuda_mixed','delta','ridge','ridge32','ridge_pca_scan','ridge_pca_tree','kernel','raw')
for noise in ('0.02','0.04'):
 for arm in order:
  keys=('accuracy','unknown','false_abstention','retained','updated','known_fact_top1_accuracy','full_workload_seconds','p95_us','state_bytes')
  values=[avg(arm,noise,key) for key in keys]
  lines.append(f'| {noise} | {arm} | '+' | '.join(fmt(v,100 if i<6 else 1,6 if i==6 else 2 if i>6 else 4) for i,v in enumerate(values))+' |')
lines+=['','Known top1 is reported only where handles are exposed; compact delta has no equivalent handle-ranking output. High UNKNOWN with near100% known false abstention is a failed retrieval control, not a competent answerer.',
 'The timestamp/latest-write rule is hand-written. Updated/retained correctness tests its execution with neural or classical representation; it is not evidence of a learned update controller. Update rounds are not reasoning depth.',
 '', '| noise | K | arm | full % | UNKNOWN % | known false abstention % | retained % | updated % | service s | p95 us | state bytes |',
 '|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for noise in ('0.02','0.04'):
 for k in (32,128,512):
  for arm in ('dense_cached_cpu','dense_cached_cpu_mixed','transport_pca','ridge_pca_scan'):
   keys=('accuracy','unknown','false_abstention','retained','updated','full_workload_seconds','p95_us','state_bytes')
   lines.append(f'| {noise} | {k} | {arm} | '+' | '.join(fmt(avg(arm,noise,key,k),100 if i<5 else 1,6 if i==5 else 2 if i>5 else 4) for i,key in enumerate(keys))+' |')
lines+=['','## UNCERTAINTY','',
 'Independent paired unit n5; Student-t df4 intervals, equal frozen K/update/episode weights. Query counts are not replication units.',
 'Coverage is nominal under the preregistered Student-t assumptions. Five units do not give distribution-free coverage; zero observed errors do not establish a zero future error probability.',
 'The six mixed-versus-base reference endpoints use99.166667% intervals (Bonferroni95% family). Full/UNKNOWN difference lower limits must be at least-2pp; base-minus-mixed false abstention lower limits at least-0.2pp. Ten per-unit/noise mixed false-abstention guards remain <=2%. Each of all six dense variants must pass the original reference competence at each noise.',
 'A causal adverse-noise false-abstention improvement additionally requires mean reduction>=0.2pp and CI lower>0. Mere noninferiority/adequacy does not establish improvement.',
 'The original eight learning/compression endpoints use99.375% intervals. Each selected/neural economic18 family uses99.722222%; each fixed-comparator non-domination60 family uses99.916667%. Families are separately95%, without a joint95% claim over all families. No endpoint/comparator selection after results.',
 '', '| reference endpoint | mean [CI] pp | frozen gate |', '|---|---:|---|']
for key,v in selection['primary_simultaneous_intervals'].items():lines.append(f"| {key} | {bounds(v,100)} | {selection['primary_gates'][key]} |")
lines+=['', '| original learning/compression endpoint | mean [CI] pp | gate |','|---|---:|---|']
for key,v in a['primary_simultaneous_intervals'].items():lines.append(f"| {key} | {bounds(v,100)} | {a['primary_gates'][key]} |")
for name,route in [('ridge/PCA-scan',classic),('neural transport/PCA',neural)]:
 lines += ['',f'| {name} vs mixed competent CPU cache endpoint | mean [CI] | gate |','|---|---:|---|']
 for key,v in route['economic_simultaneous_intervals'].items():lines.append(f"| {key} | {bounds(v,100 if key.endswith(':accuracy') else 1)} | {route['economic_gates'][key]} |")
 lines += ['', 'Accuracy intervals are pp; cost intervals are candidate/reference ratios. Candidate service upper<=0.8 and p95 upper<=0.9, quality lower>=-2pp, plus fixed competence/UNKNOWN/false-abstention/cell/non-domination guards.']
lines += ['', '| paired mixed-minus-base secondary endpoint | descriptive95% mean [CI] pp |','|---|---:|']
for noise in ('0.02','0.04'):
 for metric in ('known_fact_top1_accuracy','retained','updated'):
  left,right=(a['arms'][arm][noise] for arm in ('dense_mixed','dense'))
  values=[left[i][metric]-right[i][metric] for i in sorted(left) if left[i].get(metric) is not None and right[i].get(metric) is not None]
  value=interval(values,.95)
  lines.append(f'| {noise}:{metric} | {bounds(value,100)} |')
lines += ['', 'These secondary95% intervals are descriptive and do not enter the frozen selection decision or imply simultaneous95% coverage. Ranking remains separate from abstention.']
lines+=['','## INTERPRETATION','',
 f"Reference: {selection['decision']}. Prospective adequate selection={selection['adequate_for_prospective_selection']}; causal false-abstention improvement={selection['causal_false_abstention_improvement']}.",
 f"Neural economics: {neural['decision']}; qualified={neural['screen_qualified']}; matched-quality classical dominators={neural['matched_quality_dominators']}.",
 f"Selected classical economics: {classic['decision']}; qualified={classic['screen_qualified']}; matched-quality fixed dominators={classic['matched_quality_dominators']}.",
 'In this fresh cohort BOTH original and mixed dense models have100% observed known-fact ranking,updated/retained correctness and0% known false abstention at both noises. The weaker original reference unit from the previous experiment did not recur; augmentation therefore cannot be credited with repairing that earlier variance.',
 'Adverse-noise mixed-minus-base full-answer gain is+0.013889pp,99.166667% CI[-0.027370,+0.055148]pp; UNKNOWN gain+0.055556pp,CI[-0.109479,+0.220590]pp. Both include zero; false-abstention gain is0. The frozen causal improvement criterion is not met.',
 'The augmentation comparison changes training observation-noise exposure alone. Original versus mixed training arrays and identical encoder hashes separate decoder/noise effects from extra data, encoder learning or cache implementation. Exact effects are limited to this recipe and visible development family.',
 'The best prototype route must be chosen from these measurements, including classical alternatives; a learned alignment effect alone does not establish an economic architectural advantage.',
 '', '## CONFIDENCE','',
 'Confidence follows the frozen simultaneous intervals and all five independent units, not pooled query counts or the best seed. Passing selection warrants independent confirmation and a fresh final; current development evidence alone establishes no transfer, novelty, general intelligence or scaling law.',
 '', '## ALTERNATIVE EXPLANATIONS','',
 'Rare reference errors can produce wide paired quality intervals at n5. Neither positive means nor ordinary competence imply that noninferiority is established. A failed strict reference gate cannot be rescued by ignoring adverse noise or changing its margin.',
 'The public task observation law makes strong linear transport/ridge and retrieval plausible explanations. The explicit latest-write controller,training-only calibration, PCA/state compression and cache costs are disclosed. These are not hidden learned reasoning.',
 'Measured timings depend on this hardware/load and include the frozen system boundary; they do not prove asymptotic complexity or power/energy efficiency. Logical state bytes differ from sampled process RSS. This PVM harness does not measure peak GPU allocated/reserved VRAM or power; the economic gates concern the declared service,p95 and logical-state axes. No complete physical VRAM/energy advantage is claimed.',
 '', '## DECISION','',f"{selection['decision']}. {neural['decision']}. {classic['decision']}.",
 'A passing current route is a development selection, not final promotion. Every negative/null/crashed outcome remains preserved. No paid-plan retry, threshold rescue or next scored run occurs in this cycle.',
 '', '## INTEGRITY AND BUDGET','']
lines += ['', '| arm | full worker s/unit | supervised fit s/unit | max sampled worker RSS MiB |','|---|---:|---:|---:|']
for arm in order:
 executions=list(a['resources'].get(arm,{}).values())
 if executions:
  lines.append(f"| {arm} | {np.mean([x['wall_seconds'] for x in executions]):.6f} | {np.mean([x['supervised_fit_seconds'] for x in executions]):.6f} | {max(x['peak_rss_bytes'] for x in executions)/1024**2:.2f} |")
lines += ['', 'Worker figures include startup/imports,fit/calibration and both-noise evaluation; their RSS is not inference-only resident state. The model-reported operation numbers below are coarse scalar estimates,not audited machine instructions or an asymptotic proof.', '', '| K | arm | mean query operations estimate |', '|---:|---|---:|']
roles=plan['research_program_protocol']['roles']
for k in (32,128,512):
 for arm in ('dense_cached_cpu_mixed','transport_pca','ridge_pca_scan'):
  estimates=[row.get('mean_query_ops') for o in r['candidates'] if roles[o['candidate']]['arm']==arm for row in o['trials'] if row['knowledge_size']==k]
  estimates=[x for x in estimates if x is not None]
  lines.append(f"| {k} | {arm} | {fmt(float(np.mean(estimates)) if estimates else None,1,2)} |")
fits=sum(o['execution']['supervised_fit_seconds'] for o in r['candidates'])
reported=sum(o['trials'][0]['fit_report']['fit_seconds'] for o in r['candidates'] if o['trials'])
used=sum(e['seconds'] for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-ROBUSTNESS-'))
v=status(b)
lines += [f'Audited supervised fit={fits:.6f}s; model-reported fit={reported:.6f}s, both included once in full worker wall.',
 f"Full worker wall charged={run['worker_full_wall_seconds_already_charged']:.6f}s; controller wall={run['wall_seconds']:.6f}s; additional conservative overhead charge={run['overhead_seconds_charged_conservatively']}s.",
 f'Auxiliary charge at report creation={used}s/3600s, including startup212s, prepaid administration180s, all tests/check failures, controller overhead,stored analysis and publication. Final administration/check charges remain append-only in the completion receipt.',
 f"A remaining at report creation={v['fit_seconds_remaining']:.6f}s; new registration attempts used={v['continuation_registration_attempts_used']}/17. Prior3 registrations and2655.336485s remain consumed. B12/72000s is authorized but not activated or spent.",
 'Worker study cap20400s includes fit and development evaluation; per-fit210s/per-worker236s with external240s bound. Auxiliary cap3600s. Deadline2026-10-05T07:33:50Z is unchanged.',
 'Full clone regression1198/1198 passed with no skips. Targeted62 and post-format metadata71 passed. All80 parent scientific hashes,38063 nonmutable historical file bytes,old .gitattributes prefix,old registry records and five ledger prefixes preserved. The format-only bridge proved exact native checkout bytes under both autocrlf policies.',
 'Pre-seed failed checks are preserved and charged: targeted-V1 API fixture, checkout-bytes-V1 stale Git EOL cache,checkout-metadata-tests-V1 missing test filename. Their corrected checks did not retry a paid experiment or alter scientific gates.',
 f"Before/after result integrity={r['integrity_before']['ok']}/{r['integrity_after']['ok']}; protected1275 files. Native raw SHA{pub['native_sha256']} ({pub['native_bytes']}bytes); full lossless gzip SHA{pub['bundle_sha256']} ({pub['bundle_bytes']}bytes).",
 'Raw evaluated source,protected analyzers,all runtime/private provenance journals,fit diagnostics,worker logs,failures and full predictions are archived. Full service includes allocation,copies/parser/ingest,indices/updates/cache,query/decode and synchronization; no work is shifted out of accounting.',
 'Fresh checkout restores all three exact complete native records before doctor/lab:', '',
 '    uv run --no-sync python scripts/restore_pvm01_transport_result.py',
 '    uv run --no-sync python scripts/restore_pvm01_replication_result.py',
 '    uv run --no-sync python scripts/restore_pvm01_dense_noise_result.py','',
 'Restoration checks full hashes/sizes and refuses to overwrite a differing existing record. WT8-9,external models/APIs and schedule changes remain unused.',
 '', '## NEXT DISCRIMINATING EXPERIMENT','',next_test,'',
 'After explicit A accounting, activate the authorized B for two independent transfer families,one licensed real public dataset,and a minimal local updateable fact/source/UNKNOWN prototype chosen from evidence. Transfer/final/prototype scope remains unexecuted; the expanded user goal stays active.','']
path.write_text('\n'.join(lines),encoding='utf-8',newline='\n')
print('Report with all frozen endpoints,units,three scales,full costs and conditional next experiment:',path,flush=True)
