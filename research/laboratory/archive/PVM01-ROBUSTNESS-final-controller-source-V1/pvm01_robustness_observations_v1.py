from pathlib import Path
import json,numpy as np
p=Path('research/reviews/EXP-20261005-0003-PVM01-dense-noise-analysis.json');a=json.loads(p.read_text(encoding='utf-8'))
s=a['reference_selection']
print('reference_intervals',json.dumps(s['primary_simultaneous_intervals']))
print('learning_all_pass',all(a['primary_gates'].values()))
for arm in ['dense','dense_mixed','dense_cached_cpu_mixed','transport_pca','ridge_pca_scan']:
 for noise in ['0.02','0.04']:
  u=list(a['arms'][arm][noise].values());print(arm,noise,{k:float(np.mean([x[k] for x in u])) for k in ['accuracy','unknown','false_abstention','known_fact_top1_accuracy','retained','updated','full_workload_seconds','p95_us','state_bytes']})
for name in ['neural_economics_against_mixed_reference','selected_classical_route_confirmation']:
 v=a[name];print(name,{'qualified':v['screen_qualified'],'gates':sum(v['economic_gates'].values()),'dominators':v['matched_quality_dominators'],'failed':[k for k,x in v['economic_gates'].items() if not x]})
