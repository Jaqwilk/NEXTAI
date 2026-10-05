from pathlib import Path
p=Path('research/tmp/pvm01_robustness_report_v1.py');s=p.read_text(encoding='utf-8')
print([(i+1,line.encode('ascii','backslashreplace').decode()) for i,line in enumerate(s.splitlines()) if not line.isascii()])
arc=Path('research/laboratory/archive/PVM01-ROBUSTNESS-unexecuted-report-format-V1');arc.mkdir(parents=True,exist_ok=False)
for name in ['pvm01_robustness_report_v1.py','pvm01_robustness_report_full_resources_v1.py']:(arc/name).write_bytes((Path('research/tmp')/name).read_bytes())
lines=s.splitlines();bad=[i for i,line in enumerate(lines) if not line.isascii()]
assert len(bad)==1 and 'paired training-noise' in lines[bad[0]]
lines[bad[0]]=lines[bad[0]][:lines[bad[0]].index(' - ')] if False else lines[bad[0]]
start=lines[bad[0]].index('paired training-noise')
prefix=lines[bad[0]][:lines[bad[0]].index('}')]+'}'
lines[bad[0]]=prefix+' - '+lines[bad[0]][start:]
p.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
q=Path('research/tmp/pvm01_robustness_report_full_resources_v1.py');t=q.read_text(encoding='utf-8').replace('s=p.read_text()','s=p.read_text(encoding="utf-8")');q=Path('research/tmp/pvm01_robustness_report_full_resources_v2.py');q.write_text(t,encoding='utf-8',newline='\n')
compile(p.read_text(encoding='utf-8'),str(p),'exec')
print('Unexecuted report title restored to ASCII; failed formatter source preserved')
