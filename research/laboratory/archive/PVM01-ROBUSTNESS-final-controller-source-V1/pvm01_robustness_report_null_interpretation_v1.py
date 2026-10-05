from pathlib import Path
p=Path('research/tmp/pvm01_robustness_report_v1.py');s=p.read_text(encoding='utf-8')
needle="'The augmentation comparison changes training observation-noise exposure alone."
assert s.count(needle)==1
index=s.index(needle)
s=s[:index]+"'In this fresh cohort BOTH original and mixed dense models have100% observed known-fact ranking,updated/retained correctness and0% known false abstention at both noises. The weaker original reference unit from the previous experiment did not recur; augmentation therefore cannot be credited with repairing that earlier variance.',\n 'Adverse-noise mixed-minus-base full-answer gain is+0.013889pp,99.166667% CI[-0.027370,+0.055148]pp; UNKNOWN gain+0.055556pp,CI[-0.109479,+0.220590]pp. Both include zero; false-abstention gain is0. The frozen causal improvement criterion is not met.',\n "+s[index:]
p.write_text(s,encoding='utf-8',newline='\n')
q=Path('research/tmp/pvm01_robustness_report_metadata_v1.py');s=q.read_text(encoding='utf-8');needle=" 'All frozen metrics,thresholds,cost gates and failed/partial outcomes remain preserved.\\n'"
assert s.count(needle)==1;s=s.replace(needle," 'Both original/mixed references show0% known false abstention; previous weak unit did not recur.\\n'\n 'Adequacy is established within frozen margins; augmentation benefit is not established.\\n'\n"+needle)
q.write_text(s,encoding='utf-8',newline='\n')
for p in [p,q]:compile(p.read_text(encoding='utf-8'),str(p),'exec')
print('Null causal result and independent next-step distinction added without changing any gate')
