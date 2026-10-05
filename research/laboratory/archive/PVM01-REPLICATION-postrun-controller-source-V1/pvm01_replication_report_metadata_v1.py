from pathlib import Path
import json,subprocess
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd()
subprocess.run(['uv','run','--no-sync','python','research/tmp/pvm01_replication_report_v1.py'],check=True)
a=json.loads((b/'research/reviews/EXP-20261005-0002-PVM01-replication-analysis.json').read_text())
assert a['valid_comparison'] and not a['economic_screen_qualified']
selected=a['selected_classical_route_confirmation'];assert not selected['screen_qualified']
failed=[key for key,value in selected['economic_gates'].items() if not value]
assert set(failed)=={'0.04:K32:accuracy','0.04:K128:accuracy','0.04:K512:accuracy'}
diagnostic={'created_at':utc_now(),'experiment_id':'EXP-20261005-0002','no_new_data_fit_or_model':True,'failed_selected_gates':{key:selected['economic_simultaneous_intervals'][key] for key in failed},'unit_metrics':{arm:{noise:{i:{key:u[key] for key in ['accuracy','unknown','false_abstention','retained','updated']} for i,u in units.items()} for noise,units in a['arms'][arm].items()} for arm in ['dense','dense_cached_cpu','ridge_pca_scan','transport_pca']},'interpretation':'Positive mean selected-minus-reference differences; negative interval lower limits from n5 paired variation. Qualification remains failed. Keep all fixed gates and preserve outcome; test reference training-noise robustness prospectively.'}
atomic_write_json(b/'research/reviews/EXP-20261005-0002-reference-variance-diagnosis-V1.json',diagnostic)
header=('# Completed cycle313 — independent replication EXP-20261005-0002\n\nAll70 workers/1260 trials complete, five NEW paired units; integrity passed.\nAll8 neural learning/compression gates pass; no full neural economic qualification.\nSelected ridge/PCA passes competence/UNKNOWN/FA and15/18 economic gates.\nThree adverse-noise noninferiority CIs fail unchanged-2pp gate despite positive means;\none weaker reference unit drives the variance. No selected-route promotion/fresh final.\nAnalysis: research/analyses/EXP-20261005-0002.md; immutable plan/results preserved.\nCurrent v7 is maintenance,scoring=false; finite A remains active, B unspent/inactive.\nNext bounded question: preregister fresh five-pair dense-reference stability ablation,\ntraining dense-set noise0.02 versus mixed0.02/0.04 only; same architecture,\n4096 alignment pairs,2048 transport and1024 decoder steps, unchanged calibration,\nmetrics,thresholds,3K,updates0/1/4, two dev noises and strong classical controls.\nNo next implementation/data/fit/EXP in cycle313. Reserve fresh final; no retry,\nWT8-9,external models/APIs or schedule change. Expanded goal remains open.\nPrevious sections below are preserved history.\n\n')
for rel in ['AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md']:
    p=b/rel;p.write_bytes(header.encode()+p.read_bytes())
m=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
print('Report/variance diagnosis/durable queue, maintenance freeze:',len(m['files']),flush=True)
