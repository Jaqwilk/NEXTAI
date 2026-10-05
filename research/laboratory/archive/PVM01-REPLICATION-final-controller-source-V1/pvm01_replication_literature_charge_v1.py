from pathlib import Path
from nextai_autoresearch.research_program import auxiliary_reserve,auxiliary_charge
b=Path.cwd();cid='PVM01-REPLICATION-literature-prepaid-V1'
auxiliary_reserve(b,cid,180);auxiliary_charge(b,cid,180)
print('180s literature maintenance charged; no fit/scoring')
