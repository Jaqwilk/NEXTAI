from pathlib import Path
import json
root=Path.cwd();eid='EXP-20261005-0003'
rows=[json.loads(p.read_text()) for p in sorted((root/f'research/tmp/{eid}').glob('*.supervisor.json'))]
print(json.dumps({'experiment_id':eid,'supervisor_records':len(rows),'completed_workers':sum(r['status']=='complete' for r in rows),'failed_records':[{'candidate':r['candidate'],'status':r['status'],'error':r.get('error')} for r in rows if r['status']!='complete'],'completed_trials':sum(len(r['trials']) for r in rows),'worker_wall_so_far':sum(r['execution'].get('wall_seconds',0) for r in rows),'fit_seconds_so_far':sum(r['execution'].get('supervised_fit_seconds',0) for r in rows)},ensure_ascii=False))
