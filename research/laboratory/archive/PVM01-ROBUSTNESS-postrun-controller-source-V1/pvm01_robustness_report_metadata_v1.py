from pathlib import Path
import json,subprocess
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();eid='EXP-20261005-0003'
subprocess.run(['uv','run','--no-sync','python','research/tmp/pvm01_robustness_report_v1.py'],check=True)
a=json.loads((b/f'research/reviews/{eid}-PVM01-dense-noise-analysis.json').read_text());r=json.loads((b/f'research/results/{eid}.json').read_text())
s=a['reference_selection'];neural=a['neural_economics_against_mixed_reference'];classic=a['selected_classical_route_confirmation']
next_test=('Independent unchanged-recipe confirmation of selected mixed-noise reference and ridge/PCA-scan, five NEW paired units, all3K,bothnoise,updates0/1/4,strongcontrols and exact frozen metrics/caps. If confirmed, separately preregister a fresh five-pair final.' if classic['screen_qualified'] else
 'Prospective bounded alternative targeting the exact failed reference/economic gates with NEW paired units, same model/full-cost controls and unchanged original margins; compare reference/calibration or precision alternatives before any new arrays, reserve independent confirmation/fresh final. No automatic more steps or failed-recipe final.')
diagnostic={'created_at':utc_now(),'experiment_id':eid,'no_new_data_fit_or_model':True,'valid_comparison':a['valid_comparison'],'reference_selection':s,'neural_economics':neural,'selected_classical_economics':classic,'unit_metrics':{arm:{noise:{i:{key:u.get(key) for key in ['accuracy','unknown','false_abstention','retained','updated','known_fact_top1_accuracy','full_workload_seconds','p95_us','state_bytes']} for i,u in units.items()} for noise,units in a['arms'][arm].items()} for arm in ['dense','dense_mixed','dense_cached_cpu','dense_cached_cpu_mixed','ridge_pca_scan','transport_pca']},'exact_next_discriminating_experiment_proposal':next_test,'not_a_new_execution_plan':True,'expanded_goal_complete':False}
atomic_write_json(b/f'research/reviews/{eid}-reference-noise-diagnosis-V1.json',diagnostic)
header=(f'# Completed cycle314 — paired training-noise intervention {eid}\n\n'
 f"Workers {len(r['candidates'])}, complete {sum(o['status']=='complete' for o in r['candidates'])}, trials {sum(len(o['trials']) for o in r['candidates'])}; five NEW paired units; valid={a['valid_comparison']}.\n"
 f"Reference decision: {s['decision']}; causal false-abstention improvement={s['causal_false_abstention_improvement']}.\n"
 f"Neural economic qualification={neural['screen_qualified']}; selected classical qualification={classic['screen_qualified']}.\n"
 'Both original/mixed references show0% known false abstention; previous weak unit did not recur.\n'
 'Adequacy is established within frozen margins; augmentation benefit is not established.\n'
 'All frozen metrics,thresholds,cost gates and failed/partial outcomes remain preserved.\n'
 f'Analysis: research/analyses/{eid}.md; exact unit/gate diagnosis: research/reviews/{eid}-reference-noise-diagnosis-V1.json.\n'
 'Current v8 is maintenance,scoring=false; finite A stays active, B authorized/unspent/inactive.\n'
 f'Next bounded question (prospective only): {next_test}\n'
 'No next implementation/data/fit/EXP in cycle314. Reserve final/replication; no paid-plan retry,\n'
 'WT8-9,external models/APIs or schedule changes. Expanded transfer/prototype goal remains open.\n'
 'Previous sections below are preserved history.\n\n')
for rel in ['AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md']:
 p=b/rel;p.write_bytes(header.encode()+p.read_bytes())
m=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
print('Report, exact failed/pass gate diagnosis, durable next question, maintenance freeze:',len(m['files']),flush=True)
