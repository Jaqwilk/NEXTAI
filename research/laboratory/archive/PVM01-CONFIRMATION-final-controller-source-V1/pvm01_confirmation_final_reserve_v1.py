from pathlib import Path
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl
b=Path.cwd(); rel='research/plans/PVM01-CONFIRMATION-FINAL-RESERVE-ADDENDUM-V1.json'; assert not (b/rel).exists()
atomic_write_json(b/rel,{'id':'PVM01-CONFIRMATION-FINAL-RESERVE-ADDENDUM-V1','created_at':utc_now(),'parent_study_path':'research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json','parent_study_sha256':sha256_file(b/'research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json'),'purpose':'Strengthen reserved funds for a same17-arm fresh final:20400 full workers+3600 auxiliary=24000s. No current metrics,recipe,data,budgets,deadline or scientific gate changes; no final activation.','minimum_remaining_A_seconds_after_worst_case_current_study':24000,'minimum_future_registration_tickets':1,'accounting_formula':'current A fit_seconds_remaining -20400 worker cap -(3600-current-study already charged auxiliary). Current auxiliary is counted once,including startup,failures and prepaid administration.','before_new_private_seed_data_fit_EXP':True,'B_not_borrowed_or_activated':True})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_final_reserve_strengthened','created_at':utc_now(),'cycle':315,'addendum_path':rel,'addendum_sha256':sha256_file(b/rel),'minimum_final_seconds':24000,'before_research_seed_data_fit_EXP':True,'scientific_contract_unchanged':True})
p=b/'research/tmp/pvm01_confirmation_prepaid_v1.py'; text=p.read_text(encoding='utf-8')
text=text.replace('from nextai_autoresearch.ledger import append_jsonl','from nextai_autoresearch.ledger import append_jsonl,read_jsonl')
needle="reserves=study['programme_reserves'];"
assert text.count(needle)==1
text=text.replace(needle,"charged=sum(e['seconds'] for e in read_jsonl(b/'research/events.jsonl') if e.get('event')=='research_program_aux_fit_charged' and str(e.get('charge_id','')).startswith('PVM01-CONFIRMATION-'))\nassert value['fit_seconds_remaining']-study['resources']['fit_seconds_study_cap']-(3600-charged)>=24000\nreserves=study['programme_reserves'];")
p.write_text(text,encoding='utf-8',newline='\n')
print('Strengthened same17-arm final reserve24000s; immutable current study unchanged',flush=True)
