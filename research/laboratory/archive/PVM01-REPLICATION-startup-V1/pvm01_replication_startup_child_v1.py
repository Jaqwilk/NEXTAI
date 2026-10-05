from pathlib import Path
import json,subprocess
b=Path.cwd()
for label,args in [('doctor',['doctor']),('lab',['lab','status'])]:
 stem=b/'research/reviews'/f'PVM01-REPLICATION-startup-{label}-V1'
 with stem.with_suffix('.stdout.txt').open('xb') as out,stem.with_suffix('.stderr.txt').open('xb') as err:
  r=subprocess.run(['uv','run','--no-sync','nextai',*args],cwd=b,stdout=out,stderr=err)
 assert r.returncode==0,(label,r.returncode)
 text=stem.with_suffix('.stdout.txt').read_text(encoding='utf-8')
 if label=='doctor':assert 'Doctor: PASS' in text
 else:
  value=json.loads(text);assert value['errors']==[] and value['scoring_ready'] is False
 print('Startup',label,'PASS',flush=True)
