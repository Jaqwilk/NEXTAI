from pathlib import Path
import json,numpy as np
from nextai_autoresearch.utils import utc_now,sha256_file
from nextai_autoresearch.research_program import status
from nextai_autoresearch.ledger import read_jsonl
b=Path.cwd();eid='EXP-20261005-0002';analysis=json.loads((b/f'research/reviews/{eid}-PVM01-replication-analysis.json').read_text())
result=json.loads((b/f'research/results/{eid}.json').read_text());plan=json.loads((b/f'research/plans/{eid}.json').read_text())
study_path='research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json';study=json.loads((b/study_path).read_text())
selected=analysis['selected_classical_route_confirmation'];run=json.loads((b/'research/reviews/PVM01-REPLICATION-audited-run-overhead-V1.json').read_text())
pub=json.loads((b/f'research/laboratory/{eid}-publication-V2.json').read_text())
path=b/f'research/analyses/{eid}.md';assert not path.exists()
def avg(arm,noise,metric):
    units=analysis['arms'].get(arm,{}).get(noise,{})
    return float(np.mean([u[metric] for u in units.values()])) if units else float('nan')
def bounds(value,percentage=False):
    scale=100 if percentage else 1
    if value['low'] is None:return 'incomplete'
    return f"{value['mean']*scale:.4f} [{value['low']*scale:.4f},{value['high']*scale:.4f}]"
lines=[f'# {eid} — independent unchanged-recipe replication', '', '## OBSERVATION', '',
f"Immutable plan: research/plans/{eid}.json; raw SHA {sha256_file(b/f'research/plans/{eid}.json')}.",
f"Prospective study: {study_path}; SHA {sha256_file(b/study_path)}.",
'Source preregistered at430e4e45a249ce0ec69e335bb04adda7f81ff913; validated at90ed00750c79f5d614bcd32149218d63d85783b7; evaluated at2635d03fd28c62e90d19400c9c9b29cb9a75a8aa.',
'All80 scientific source hashes, task/model/optimizer/grids and original gates unchanged. V7 only extends private freshness and audited integration.',
'Five NEW paired seed/data units, all14 arms, K32/128/512, updates0/1/4, noise0.02/0.04; no pooling with selecting EXP-20261005-0001.',
f"Workers {len(result['candidates'])}, completed {sum(x['status']=='complete' for x in result['candidates'])}; trials {sum(len(x['trials']) for x in result['candidates'])}; valid_comparison={analysis['valid_comparison']}.",
'Exact training/PCA/source/dense-cache prediction identity and truth pairing are retained in the machine report.',
'', '| noise | arm | full answer % | UNKNOWN % | known false abstention % | retained % | updated % | full service s/unit | p95 us | logical state bytes |',
'|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for noise in ('0.02','0.04'):
    for arm in ('transport_pca','transport_full','transport_pca_untrained','transport_pca_shuffled','dense','dense_cached_cpu','dense_cached_cuda','delta','ridge','ridge32','ridge_pca_scan','ridge_pca_tree','kernel','raw'):
        values=[avg(arm,noise,x) for x in ('accuracy','unknown','false_abstention','retained','updated','full_workload_seconds','p95_us','state_bytes')]
        lines.append(f"| {noise} | {arm} | "+' | '.join(f'{v*100:.4f}' if i<5 else f'{v:.6f}' if i==5 else f'{v:.2f}' for i,v in enumerate(values))+' |')
lines+=['', 'Frozen/no-learning is an update-operator control. High UNKNOWN alone does not show competent retrieval; false abstention and known ranking must be read separately.',
'The timestamp/latest-write update law remains explicitly hand-written, not a learned update controller. Update rounds are not reasoning depth.',
'', '## UNCERTAINTY', '',
'Independent unit n5; paired Student-t df4 intervals. Queries are not independent replication units.',
'Original eight learning/compression endpoints:99.375% intervals, familywise95%. Original18 neural economic endpoints:99.722222%; original60 fixed-classical dominance endpoints:99.916667%.',
'Selected ridge/PCA economic18 and fixed-comparator non-domination60 were prospectively fixed; same respective levels, each family separately95%. No joint95% claim across families.',
'All unit values/cells are stored in the machine report; selecting and new experiments stay separate.',
'', '| original primary endpoint | mean [CI] pp | gate |','|---|---:|---|']
for key,value in analysis['primary_simultaneous_intervals'].items():
    lines.append(f"| {key} | {bounds(value,True)} | {analysis['primary_gates'][key]} |")
lines+=['', '| selected ridge/PCA vs competent CPU-cache | mean [CI] | gate |','|---|---:|---|']
for key,value in selected['economic_simultaneous_intervals'].items():
    lines.append(f"| {key} | {bounds(value,key.endswith(':accuracy'))} | {selected['economic_gates'][key]} |")
lines+=['','Accuracy intervals above are pp; other intervals are candidate/reference cost ratios. Strict known/UNKNOWN/FA competence and per-cell guards are additional gates.',
'', '## INTERPRETATION AND CONFIDENCE', '',
f"Neural decision: {analysis['decision']}; full neural economic qualification={analysis['economic_screen_qualified']}.",
f"Matched-quality classical dominators of neural transport/PCA: {analysis['matched_quality_classical_dominators']}.",
f"Selected classical decision: {selected['decision']}; screen_qualified={selected['screen_qualified']}; fixed-comparator dominators={selected['matched_quality_dominators']}.",
'The selected classical route passes all competence, UNKNOWN/FA and15/18 economic gates; three adverse-noise quality intervals fail the unchanged -2pp noninferiority boundary. Their mean differences are positive, not evidence of inferior classical mean quality.',
'Adverse-noise lower limits at K32/128/512 are-3.9418/-2.5588/-2.6908pp. A reference-unit gain difference of+3.4375/+2.1875/+2.3958pp drives paired variability. This is an uncertainty failure despite ordinary competence gates passing. It does not falsify classical retrieval or justify weakening the frozen test.',
'The correct next question is reference robustness and UNKNOWN stability, rather than automatically adding steps or changing the selected classical method.',
'This independently tests this exact visible-development recipe. It is not architectural novelty, general intelligence, a scaling law or transfer to another task family.',
'End-to-end service includes allocation, parser/copies, ingest, updates, cache/index maintenance, queries, decoding and synchronization. Fit/calibration/controller costs are reported separately, without shifting work out of accounting.',
'Logical state counts and measured process/GPU peaks are distinct. Operation estimates are labelled estimates; this hardware/load cannot establish asymptotic complexity.',
'', '## DECISION', '',
f"{analysis['decision']}. {selected['decision']}.",
'A passing selected route only authorizes prospective fresh-final validation, not an economic/transfer promotion. Failure retains alternative recipes and all outcomes; no retry or threshold rescue.',
'', '## INTEGRITY AND BUDGET', '']
fits=sum(x['execution']['supervised_fit_seconds'] for x in result['candidates'])
reported_fits=sum(x['trials'][0]['fit_report']['fit_seconds'] for x in result['candidates'] if x['trials'])
used=sum(e['seconds'] for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-REPLICATION-'))
value=status(b)
lines += [f"Audited supervised fit phases summed once per worker={fits:.6f}s; model-reported fit={reported_fits:.6f}s (both included in full worker wall, not double charged).",
f"Full worker wall charged={run['worker_full_wall_seconds_already_charged']:.6f}s; controller wall={run['wall_seconds']:.6f}s; extra overhead conservatively charged={run['overhead_seconds_charged_conservatively']}s.",
f"Auxiliary charged so far={used}s /3600s, including startup171s and prepaid administration180s, all tests, controller overhead and publication checks. Later closure charges remain append-only in the completion receipt.",
f"Global A remaining at report creation={value['fit_seconds_remaining']:.6f}s, additional registration tickets used={value['continuation_registration_attempts_used']}/17. Prior3 tickets/2655.336485s are preserved. B12 tickets/72000s is authorized but inactive/unspent.",
'Clone regression1159/1159, no failures/skips; targeted32/32. Prepaid doctor/lab,70-role semantic conformance/schema, history33581 files and append-only prefixes passed before registration.',
f"Result integrity before={result['integrity_before']['ok']}, after={result['integrity_after']['ok']}. Native raw SHA {pub['native_sha256']}, bytes {pub['native_bytes']}; lossless gzip bytes {pub['bundle_bytes']} / SHA {pub['bundle_sha256']}.",
'All runtime journals, failed/partial/completed outcomes and evaluated source archived before maintenance. Secondary analyzer matches its pre-data validated-source hash; source is archived alongside protected files.',
'After fresh checkout restore both exact native records before doctor/lab:',
'', '    uv run --no-sync python scripts/restore_pvm01_transport_result.py','    uv run --no-sync python scripts/restore_pvm01_replication_result.py','',
'Restoration verifies full size/hashes and refuses to overwrite a differing existing record. No WT8-9, external models/APIs or schedule changes.',
'', '## NEXT DISCRIMINATING EXPERIMENT', '',
'If the selected route qualifies: preregister a frozen fresh-final comparison before data, same exact ridge/PCA-scan, neural references and strong controls, at least five NEW paired units, all three scales, explicit updates, UNKNOWN/known ranking separately and full cost.',
'Because the selected route did not qualify, no automatic fresh-final promotion follows. Next preregister a five-pair dense-reference robustness ablation: unchanged4096 alignment pairs/2048 transport steps/1024 dense steps and model, training-only dense-set observation noise0.02 versus prospectively mixed0.02/0.04, paired fresh data/model seeds, unchanged calibration,3K,updates0/1/4, both dev noises and strong classical controls. Change only training observation-noise exposure, not architecture, thresholds or decision gates.',
'Before implementing or seeing new arrays, freeze that alternative contract, costs and decision, then clone conformance/preflight/readiness and one audited EXP in the next bounded cycle. Preserve current0002, reserve fresh-final resources and do not retry it. A fresh final follows only a qualified prospectively selected recipe.',
'After explicit A accounting, activate authorized B for transfer on two independent families (one licensed real public dataset) and a minimal local updateable fact/source/UNKNOWN prototype chosen from evidence.',
'Extended user goal remains active; no final/transfer/prototype completion is claimed.', '']
path.write_text('\n'.join(lines),encoding='utf-8',newline='\n')
print('Independent replication report written',path,flush=True)


