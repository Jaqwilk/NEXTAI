from pathlib import Path
p=Path('research/tmp/pvm01_robustness_report_v1.py');s=p.read_text();needle="'Independent paired unit n5; Student-t df4 intervals, equal frozen K/update/episode weights. Query counts are not replication units.',"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n 'Coverage is nominal under the preregistered Student-t assumptions. Five units do not give distribution-free coverage; zero observed errors do not establish a zero future error probability.',")
p.write_text(s,encoding='utf-8',newline='\n')
