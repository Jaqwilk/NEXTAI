from pathlib import Path
import json
r=json.loads(Path('research/tmp/EXP-20261005-0002/pvm01_tc_dense_cached_cuda_s0.supervisor.json').read_text())
print('outcome_keys',list(r));print('summary_resource_fields',{k:v for k,v in r.get('summary',{}).items() if any(s in k for s in ['memory','gpu','rss','peak','bytes'])})
print('fit_report_keys',list(r['trials'][0]['fit_report']))
