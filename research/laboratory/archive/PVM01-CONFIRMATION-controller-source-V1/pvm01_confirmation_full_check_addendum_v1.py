from pathlib import Path
import json
import psutil
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl
b=Path.cwd(); failed=json.loads((b/'research/reviews/PVM01-CONFIRMATION-full-V1.json').read_text(encoding='utf-8'))
assert failed['result']['reason']=='timeout' and failed['seconds_charged']==513
pids=failed['result']['exit_live_descendant_pids']; assert not any(psutil.pid_exists(p) for p in pids)
rel='research/plans/PVM01-CONFIRMATION-FULL-CHECK-BOUND-ADDENDUM-V1.json'; assert not (b/rel).exists()
value={'id':'PVM01-CONFIRMATION-FULL-CHECK-BOUND-ADDENDUM-V1','created_at':utc_now(),'study_path':'research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json','study_sha256':sha256_file(b/'research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json'),'failed_checks_preserved':['research/reviews/PVM01-CONFIRMATION-full-V1.json','research/reviews/PVM01-CONFIRMATION-history-source-V1.json'],'observed':'Full1238 regression passed emitted checks through98% but its500s external timeout terminated the process tree before final JUnit. Previous full1198 used432.1s versus earlier371.9s,with increasing stored scientific history. No assertion failure emitted; this is an incomplete technical check,not a passing suite. History controller correctly rejected it.','prospective_next_technical_check':{'id':'PVM01-CONFIRMATION-full-V2','whole_tree_timeout_seconds':800,'reservation_seconds':840,'all_tests_unchanged':True,'full_JUnit_required_no_skips':True},'frozen_study_auxiliary_cap_unchanged':3600,'failed_costs_remain_consumed':True,'terminated_descendant_pids_verified_absent':pids,'research_arrays_seeds_fit_EXP':False,'no_paid_plan_retry':True,'no_scientific_metric_recipe_threshold_or_data_change':True}
atomic_write_json(b/rel,value)
append_jsonl(b/'research/events.jsonl',{'event':'laboratory_preparation_check_bound_addendum','created_at':utc_now(),'cycle':315,'addendum_path':rel,'addendum_sha256':sha256_file(b/rel),'before_research_seed_data_fit_EXP':True,'study_auxiliary_cap_unchanged':3600})
for name in ('pvm01_confirmation_history_v1.py','pvm01_confirmation_commit_validated_v1.py','pvm01_confirmation_prepaid_v1.py'):
    p=b/'research/tmp'/name; text=p.read_text(encoding='utf-8').replace('PVM01-CONFIRMATION-full-V1','PVM01-CONFIRMATION-full-V2')
    if name=='pvm01_confirmation_prepaid_v1.py': text=text.replace("'PVM01-CONFIRMATION-history-source-V1'","'PVM01-CONFIRMATION-history-source-V2'")
    p.write_text(text,encoding='utf-8',newline='\n')
print('Prospective technical bound; all failed bytes/costs and scientific contract preserved',flush=True)
