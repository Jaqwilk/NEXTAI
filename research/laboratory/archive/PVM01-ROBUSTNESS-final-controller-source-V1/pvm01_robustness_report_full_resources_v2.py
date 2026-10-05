from pathlib import Path
p=Path('research/tmp/pvm01_robustness_report_v1.py');s=p.read_text(encoding="utf-8")
s=s.replace('learned or classical representation','neural or classical representation')
s=s.replace('Logical state bytes differ from sampled process RSS and GPU allocated/reserved peaks.', 'Logical state bytes differ from sampled process RSS. This PVM harness does not measure peak GPU allocated/reserved VRAM or power; the economic gates concern the declared service,p95 and logical-state axes. No complete physical VRAM/energy advantage is claimed.')
needle="fits=sum(o['execution']['supervised_fit_seconds'] for o in r['candidates'])"
addition="""lines += ['', '| arm | full worker s/unit | supervised fit s/unit | max sampled worker RSS MiB |','|---|---:|---:|---:|']
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
"""
assert s.count(needle)==1;s=s.replace(needle,addition+needle)
p.write_text(s,encoding='utf-8',newline='\n')
