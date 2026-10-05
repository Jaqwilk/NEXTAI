from pathlib import Path
import json,sys,xml.etree.ElementTree as ET
import numpy as np
sys.path.insert(0,str(Path.cwd()/'scripts'))
from analyze_pvm01_transport import interval
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now

b=Path.cwd(); eid='EXP-20261005-0005'
def read(rel): return json.loads((b/rel).read_text(encoding='utf-8'))
r=read(f'research/results/{eid}.json'); plan=read(f'research/plans/{eid}.json'); study=read(plan['research_program_protocol']['study_path'])
a=read(f'research/reviews/{eid}-PVM01-base-reference-analysis.json'); confirmed=a['independent_confirmation']
mixed=a['reference_selection']; selection=a['base_reference_confirmation']; neural=a['unaugmented_reference_economics']['transport_pca']; classic=a['unaugmented_reference_economics']['ridge_pca_scan']
run=read('research/reviews/PVM01-BASE-REFERENCE-audited-run-overhead-V1.json'); ready=read('research/laboratory/PVM01-BASE-REFERENCE-CONFIRMATION-V1-readiness.receipt.json')
pub=read(f'research/laboratory/{eid}-publication-V2.json'); program=status(b)
def fmt(value,scale=1.,digits=4): return 'not available' if value is None else f'{value*scale:.{digits}f}'
def avg(arm,noise,key,K=None):
    units=a['arms'].get(arm,{}).get(noise,{}).values()
    values=[(u if K is None else u['by_K'][str(K)]).get(key) for u in units]
    values=[v for v in values if v is not None]
    return float(np.mean(values)) if values else None
def bounds(value,scale=1.): return f"{fmt(value['mean'],scale)} [{fmt(value['low'],scale)},{fmt(value['high'],scale)}] (n={value['n']})"
order=('transport_pca','transport_full','transport_pca_untrained','transport_pca_shuffled','dense','dense_cached_cpu','dense_cached_cuda','dense_mixed','dense_cached_cpu_mixed','dense_cached_cuda_mixed','delta','ridge','ridge32','ridge_pca_scan','ridge_pca_tree','kernel','raw')
lines=[f'# {eid} - independent unaugmented-reference economic comparison','', '## OBSERVATION','',
    f"Immutable plan: research/plans/{eid}.json; raw SHA {sha256_file(b/f'research/plans/{eid}.json')}.",
    f"Prospective study: {plan['research_program_protocol']['study_path']}; SHA {plan['research_program_protocol']['study_sha256']}.",
    f"Preregistration {ready['preregistration_git_commit']}; validated {ready['validated_source_git_commit']}; evaluated {run['prepared_source_git_commit']}.",
    'Five NEW paired independent train/dev data/model-seed units,all17 original arms,K32/128/512,updates0/1/4,paired noises0.02/0.04. No selecting/earlier replication outcomes are pooled.',
    'All107 selected scientific source bytes and candidate recipes remain unchanged:4096 alignment pairs,2048 alignment steps,1024 dense decoder steps,128 training episodes/K32/128 and8 queries. Architecture,optimizer,calibration,PCA/classical grids,metrics and thresholds are identical.',
    'The mixed dense reference retains the exact independent odd-half training noise intervention; no new T identities,extra training episodes,K512 support or D-guided selection. Control/reference cache families retain exact initialization,loss,encoder/decoder/effective-input hashes and discrete prediction identity with score drift<=1e-5.',
    f"Workers {len(r['candidates'])}; complete {sum(x['status']=='complete' for x in r['candidates'])}; trials {sum(len(x['trials']) for x in r['candidates'])}; valid comparison={a['valid_comparison']}; trusted final resource evidence={confirmed['trusted_resources_complete']}.",
    '', '| noise | arm | full % | UNKNOWN % | known FA % | retained % | updated % | known top1 % | service s/unit | p95 us | logical state bytes |',
    '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for noise in ('0.02','0.04'):
    for arm in order:
        keys=('accuracy','unknown','false_abstention','retained','updated','known_fact_top1_accuracy','full_workload_seconds','p95_us','state_bytes')
        lines.append(f'| {noise} | {arm} | '+' | '.join(fmt(avg(arm,noise,k),100. if i<6 else 1.,6 if i==6 else 2 if i>6 else 4) for i,k in enumerate(keys))+' |')
lines += ['', 'Ranking is separate from abstention and value correctness. Compact delta exposes no comparable fact handle; its top1 metric remains not applicable. High UNKNOWN coupled to high known false abstention is an incompetent control.',
    'The public timestamp/latest-write rule is hand-written. Correct updates/retention do not establish a learned update controller; update rounds are not reasoning depth.',
    '', '| noise | K | arm | full % | UNKNOWN % | known FA % | retained % | updated % | service s | p95 us | state bytes |',
    '|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for noise in ('0.02','0.04'):
    for K in (32,128,512):
        for arm in ('dense_cached_cpu','dense_cached_cpu_mixed','transport_pca','ridge_pca_scan'):
            keys=('accuracy','unknown','false_abstention','retained','updated','full_workload_seconds','p95_us','state_bytes')
            lines.append(f'| {noise} | {K} | {arm} | '+' | '.join(fmt(avg(arm,noise,k,K),100. if i<5 else 1.,6 if i==5 else 2 if i>5 else 4) for i,k in enumerate(keys))+' |')
lines += ['', '## UNCERTAINTY','', 'Independent unit n5; paired Student-t df4 intervals,unchanged equal K/update/episode weights. Queries are not independent replicas. Coverage is nominal under the frozen t assumptions,not distribution-free; zero observed errors do not prove zero future error.',
    'Ancillary mixed-reference6 endpoints use99.166667% intervals; original8 learning/compression99.375%; each selected/neural18 economic family99.722222%; each fixed60 non-domination family99.916667%. Each family separately has nominal95% coverage; no joint95% statement across all families.',
    'Frozen margins remain: full/UNKNOWN NI lower>=-2pp; base-minus-mixed known-FA lower>=-0.2pp; each mixed unit/noise FA<=2%; all six dense variants competent for the ancillary augmentation qualification. The distinct main base-reference question requires all three base variants competent and each base CPU-cache unit/noise FA<=2%,without a base-versus-itself NI test. A causal adverse FA improvement additionally needs mean>=0.2pp and lower>0.',
    '', '| reference endpoint | mean [CI] pp | gate |','|---|---:|---|']
for key,value in mixed['primary_simultaneous_intervals'].items(): lines.append(f"| ancillary mixed {key} | {bounds(value,100.)} | {mixed['primary_gates'][key]} |")
lines += ['', '| learned/compressed endpoint | mean [CI] pp | gate |','|---|---:|---|']
for key,value in a['primary_simultaneous_intervals'].items(): lines.append(f"| {key} | {bounds(value,100.)} | {a['primary_gates'][key]} |")
for name,route in (('ridge/PCA-scan',classic),('neural transport/PCA',neural)):
    lines += ['', f'| {name} vs UN-AUGMENTED CPU-cache endpoint | mean [CI] | gate |','|---|---:|---|']
    for key,value in route['economic_simultaneous_intervals'].items(): lines.append(f"| {key} | {bounds(value,100. if key.endswith(':accuracy') else 1.)} | {route['economic_gates'][key]} |")
    lines += ['', 'Quality values are pp; service and p95 are candidate/reference ratios. Unchanged gates require quality lower>=-2pp,service upper<=0.8,p95 upper<=0.9,competence/UNKNOWN/FA and fixed-comparator non-domination.']
secondary={}
lines += ['', '| ranking/update mixed-minus-base endpoint | descriptive95% mean [CI] pp |','|---|---:|']
for noise in ('0.02','0.04'):
    for metric in ('known_fact_top1_accuracy','retained','updated'):
        left,right=(a['arms'].get(arm,{}).get(noise,{}) for arm in ('dense_mixed','dense'))
        values=[left[i][metric]-right[i][metric] for i in sorted(set(left)&set(right)) if left[i].get(metric) is not None and right[i].get(metric) is not None]
        secondary[f'{noise}:{metric}']=interval(values,.95)
        lines.append(f'| {noise}:{metric} | {bounds(secondary[f"{noise}:{metric}"],100.)} |')
lines += ['', 'Secondary95% intervals are descriptive and do not alter selection or imply simultaneous coverage.',
    '', '## INTERPRETATION','',f"Independent confirmation: {confirmed['decision']}. Reference confirmed={confirmed['reference_independently_confirmed']}; selected route confirmed={confirmed['selected_route_independently_confirmed']}.",
    f"Main base reference: {selection['decision']}; competent={selection['base_reference_competent']}; all ten unit/noise guards={all(selection['each_unit_false_abstention_guards'].values())}.",
    f"Ancillary augmentation: {mixed['decision']}; causal false-abstention improvement={mixed['causal_false_abstention_improvement']}; failed NI gates={[k for k,v in mixed['primary_gates'].items() if not v]}.",
    f"Neural economics vs BASE: {neural['decision']}; fixed matched-quality dominators={neural['matched_quality_dominators']}.",
    f"Classical economics vs BASE: {classic['decision']}; fixed matched-quality dominators={classic['matched_quality_dominators']}.",
    'Reference adequacy alone does not establish augmentation benefit. The separately preregistered main question compares fixed routes with the competent unaugmented Transformer; all earlier mixed-reference qualifications and failures remain unchanged. No prior unit or weight is pooled into this new five-unit result.',
    'Joint qualification uses the original eight learning/compression endpoints,18 economic and60 fixed-comparator checks plus competent base controls and ten unit/noise FA guards. The old six mixed NI endpoints are ancillary in this prospectively distinct study and retain their own interpretation. The main economic result does not rescue the completed mixed-reference qualification.',
    'A learned alignment effect may coexist with a cheaper classical transport solution. The eventual prototype route is selected from evidence,including strong classical alternatives. No transfer,architectural novelty,LLM replacement,general intelligence or scaling-law claim follows from this synthetic family.',
    '', '## ALTERNATIVE EXPLANATIONS','', 'The public synthetic identity law may favour linear transport/retrieval. Exact cache parity checks inference implementation,not generalization. Fresh units address seed/data repeatability in one family; they do not establish cross-family transfer. Rare abstention errors and hardware/load-dependent timings remain possible. Strong classical controls,three scales and the separate fresh final are required to distinguish these explanations.',
    '', '## CONFIDENCE','', 'Confidence follows all five independent units,unchanged simultaneous intervals and controls. A passing independent comparison justifies a separately frozen fresh final,not promotion. Invalid controls/telemetry make the comparison inconclusive; no missing/failed outcome is discarded.',
    '', '## FULL COST AND RESOURCE BOUNDARY','',
    'Measured service includes raw copies,normalization/encoding,allocation,ingest,indices/cache construction and maintenance,updates,warmup,query,retrieval,decode,synchronization and Python output. Updates are a subset of ingest and are not added twice. Research fit/grids/calibration,startup and evaluation are separately disclosed and fully charged.',
    'V10 uses unchanged V9 trusted CUDA snapshots synchronize only at worker phase transitions,outside timed service/query intervals. GPU peaks are cumulative since worker start,not phase-specific or inference-only; reserved bytes are PyTorch allocator reservations,not all driver/context physical VRAM. Instantaneous root RSS and parent sampled process-tree peaks are separate. Energy remains unmeasured; timing does not establish asymptotic complexity.',
    '', '| arm | worker s/unit | trusted fit s/unit | max sampled tree RSS MiB | max final CUDA allocated MiB | max final CUDA reserved MiB |',
    '|---|---:|---:|---:|---:|---:|---:|']
for arm in order:
    executions=list(a['resources'].get(arm,{}).values())
    if not executions: continue
    final=[e.get('resource_peaks',{}).get('snapshots',[])[-1] for e in executions if e.get('resource_peaks',{}).get('snapshots')]
    lines.append(f"| {arm} | {np.mean([x['wall_seconds'] for x in executions]):.6f} | {np.mean([x['supervised_fit_seconds'] for x in executions]):.6f} | {max(x['peak_rss_bytes'] for x in executions)/1024**2:.2f} | {fmt(max((x['cuda_peak_allocated_bytes'] for x in final),default=None),1/1024**2,2)} | {fmt(max((x['cuda_peak_reserved_bytes'] for x in final),default=None),1/1024**2,2)} |")
lines += ['', '| noise | candidate | R whole workloads | mean candidate fit+service s | mean reference fit+service s |','|---|---|---:|---:|---:|']
amortization=a['descriptive_fit_amortization']['units']
for noise in ('0.02','0.04'):
    for arm in ('ridge_pca_scan','transport_pca'):
        units=[value for key,value in amortization.items() if key.startswith(f'{noise}:{arm}:')]
        for reuse in study['amortization_report']['reuse_counts']:
            costs=[x['by_reuse'][str(reuse)] for x in units]
            lines.append(f"| {noise} | {arm} | {reuse} | {fmt(float(np.mean([x['candidate_seconds'] for x in costs])) if costs else None,1.,6)} | {fmt(float(np.mean([x['reference_seconds'] for x in costs])) if costs else None,1.,6)} |")
        crossing=[x['faster_service_break_even_workloads'] for x in units if x['faster_service_break_even_workloads'] is not None]
        lines.append(f"| {noise} | {arm} | break-even range | {fmt(min(crossing) if crossing else None,1.,6)} | {fmt(max(crossing) if crossing else None,1.,6)} |")
lines += ['', 'R counts complete fixed service workloads at one noise across all3K and updates0/1/4,not individual queries. Formula is trusted fit-phase seconds + R*service seconds; fit/calibration counted once. These prospective reuse scenarios are descriptive,not extra scored observations or new gates. Full cold worker/startup costs are disclosed separately above; they are not silently removed from programme accounting.',
    '', '| K | arm | coarse query-operation estimate |','|---:|---|---:|']
roles=plan['research_program_protocol']['roles']
for K in (32,128,512):
    for arm in ('dense_cached_cpu','dense_cached_cpu_mixed','transport_pca','ridge_pca_scan'):
        values=[t['mean_query_ops'] for o in r['candidates'] if roles[o['candidate']]['arm']==arm for t in o['trials'] if t['knowledge_size']==K]
        lines.append(f'| {K} | {arm} | {fmt(float(np.mean(values)) if values else None,1.,2)} |')
lines += ['', 'Operation counts are model-reported scalar estimates,not audited machine instructions.',
    '', '## INTEGRITY AND BUDGET','',
    f"Integrity before/after={r['integrity_before']['ok']}/{r['integrity_after']['ok']}; source guards107 unchanged; full regression1272 and targeted98 passed. Old raw files,ledgers,registry and EOL history remain preserved.",
    f"Trusted fit total={sum(o['execution'].get('supervised_fit_seconds',0.) for o in r['candidates']):.6f}s; charged full worker wall={run['worker_full_wall_seconds_already_charged']:.6f}s; controller wall={run['wall_seconds']:.6f}s; extra controller overhead charge={run['overhead_seconds_charged_conservatively']}s.",
    f"Auxiliary charged at report creation={sum(e['seconds'] for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-BASE-REFERENCE-'))}s/3600s; final verification/admin charges remain append-only in the completion receipt.",
    'Every auxiliary check,including a failed check if one occurred,is retained and charged. Current-cycle failed receipts are listed in the completion record. No paid-plan retry or scientific gate change is permitted. The readiness reserve counts completed charges OR live reserved caps once.',
    f"A remaining at report creation={program['fit_seconds_remaining']:.6f}s; new registrations used={program['continuation_registration_attempts_used']}/17. Prior3/2655.336485s unchanged; B12/72000s authorized,unspent,inactive.",
    f"Full worker cap10200s,per-fit90s,per-worker116s with external120s bound; auxiliary3600s; unchanged deadline{study['study_deadline_at']}. No retry,WT8-9,external models/APIs or schedule change.",
    f"Complete native result SHA{pub['native_sha256']} ({pub['native_bytes']}bytes); lossless gzip SHA{pub['bundle_sha256']} ({pub['bundle_bytes']}bytes). All predictions,failures,fit diagnostics,private provenance and resource journals are preserved with evaluated source/runtime/log archives.",
    'Fresh checkout restores all five exact complete native records before doctor/lab:', '',
    '    uv run --no-sync python scripts/restore_pvm01_transport_result.py',
    '    uv run --no-sync python scripts/restore_pvm01_replication_result.py',
    '    uv run --no-sync python scripts/restore_pvm01_dense_noise_result.py',
    '    uv run --no-sync python scripts/restore_pvm01_confirmation_result.py',
    '    uv run --no-sync python scripts/restore_pvm01_base_reference_result.py',
    '', '## DECISION AND NEXT DISCRIMINATING EXPERIMENT','', confirmed['decision']+'.']
if confirmed['selected_route_independently_confirmed'] or confirmed['neural_route_independently_confirmed']:
    selected='ridge/PCA-scan' if confirmed['selected_route_independently_confirmed'] else 'neural transport/PCA'
    next_step=f'Preregister a separately frozen fresh-final five-pair comparison of exact {selected} against the UN-AUGMENTED dense_cached_cpu reference,all17 arms,three scales,both noises,updates0/1/4,strong controls and unchanged scientific thresholds. Exclude ALL prior selecting/replication/confirmation train/dev units,seeds,nonces and weights. Validate in clone,freeze/preflight/readiness before fresh arrays and exactly one audited EXP in a NEW cycle. Keep the ancillary mixed NI assay distinct. Use the remaining final-stage ticket and at least24000s reserved; no promotion from this cohort.'
else:
    next_step='Close this exact base-reference qualification as negative or inconclusive according to the frozen controls. The reference_and_alternatives cap is exhausted; do not add steps or silently weaken a failed gate. Explicitly account for stage A and all consumed tickets/costs,including the exact unexecuted final scope,before activating authorized stage B for alternative task/prototype routes. Preserve existing final funds and all outcomes; a new distinct question needs a prospective contract and fresh data.'
lines += [next_step,'', 'After explicit A accounting,authorized B covers two independent transfer families,one licensed real public dataset,and a minimal local fact/source/update/UNKNOWN memory prototype selected from evidence. Final/transfer/prototype scope remains open; the whole goal is active.']
path=b/f'research/analyses/{eid}.md'; assert not path.exists(); path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
diagnostic={'created_at':utc_now(),'experiment_id':eid,'analysis_sha256':sha256_file(path),'independent_confirmation':confirmed,'separate_secondary_ranking_update_intervals':secondary,'base_reference_failed_competence':[k for k,v in selection['competence_gates'].items() if not all(v.values())],'ancillary_mixed_failed_gates':[k for k,v in mixed['primary_gates'].items() if not v],'classical_failed_gates':[k for k,v in classic['economic_gates'].items() if not v],'exact_next_discriminating_experiment_proposal':next_step,'next_is_not_execution_authority':True,'whole_goal_complete':False}
atomic_write_json(b/f'research/reviews/{eid}-confirmation-diagnosis-V1.json',diagnostic)
print('Complete report with uncertainty,separate ranking/updates/UNKNOWN,fit/service/RAM/CUDA/amortization and unchanged decisions',flush=True)
