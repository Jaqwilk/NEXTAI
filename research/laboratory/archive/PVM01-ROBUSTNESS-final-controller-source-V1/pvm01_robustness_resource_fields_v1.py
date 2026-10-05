from pathlib import Path
import json
p=Path('research/tmp/EXP-20261005-0002/pvm01_tc_dense_cached_cuda_s0.supervisor.json');r=json.loads(p.read_text())
print('execution',r['execution'])
print('trial_resource_keys',{k:r['trials'][0][k] for k in r['trials'][0] if any(s in k for s in ['peak','memory','rss','gpu','operation','ops','bytes','seconds'])})
print('fit_resource_keys',{k:r['trials'][0]['fit_report'][k] for k in r['trials'][0]['fit_report'] if any(s in k for s in ['peak','memory','rss','gpu','bytes','seconds'])})
