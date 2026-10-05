from pathlib import Path
p=Path('research/tmp/pvm01_robustness_report_v1.py');s=p.read_text()
s=s.replace('import json, numpy as np','import json, numpy as np, sys\nsys.path.insert(0,str(Path.cwd()/"scripts"))\nfrom analyze_pvm01_transport import interval')
needle="lines+=['','## INTERPRETATION','',"
addition="""lines += ['', '| paired mixed-minus-base secondary endpoint | descriptive95% mean [CI] pp |','|---|---:|']
for noise in ('0.02','0.04'):
 for metric in ('known_fact_top1_accuracy','retained','updated'):
  left,right=(a['arms'][arm][noise] for arm in ('dense_mixed','dense'))
  values=[left[i][metric]-right[i][metric] for i in sorted(left) if left[i].get(metric) is not None and right[i].get(metric) is not None]
  value=interval(values,.95)
  lines.append(f'| {noise}:{metric} | {bounds(value,100)} |')
lines += ['', 'These secondary95% intervals are descriptive and do not enter the frozen selection decision or imply simultaneous95% coverage. Ranking remains separate from abstention.']
"""
assert s.count(needle)==1;s=s.replace(needle,addition+needle);p.write_text(s,encoding='utf-8',newline='\n')
