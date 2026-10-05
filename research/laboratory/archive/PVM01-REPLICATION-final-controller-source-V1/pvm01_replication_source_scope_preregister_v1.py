from pathlib import Path
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl
b=Path.cwd();relative='research/plans/PVM01-SOURCE-SCOPE-METADATA-REPAIR-V1.json'
assert not (b/relative).exists()
plan={'id':'PVM01-SOURCE-SCOPE-METADATA-REPAIR-V1','created_at':utc_now(),'cycle':313,'scoring':False,'fit':False,'registration':False,'trigger':'Original doctor V2 rejects checked_scope on three new append-only source records. Preserve records and both failed checks.','scope':'Declare only optional checked_scope nonempty non-whitespace bounded1024 text in source.schema; keep additionalProperties=false, all existing required/properties unchanged. Add meaningful positive/negative source validation tests; no scientific recipe/model/data/metric/threshold change.','source_schema_before_sha256':sha256_file(b/'schemas/source.schema.json'),'auxiliary_compute_cap':600,'current_study_auxiliary_cap_unchanged':3600,'validation':'Old/new source records accepted; undeclared fields,blank,nontext and overlong scope rejected; existing integrity/schema tests, manifest/preflight and repaired original doctor/lab.','completed_EXP_plan_result_immutable':True,'no_retry_of_research':True}
atomic_write_json(b/relative,plan)
arc=b/'research/laboratory/archive/PVM01-SOURCE-SCOPE-METADATA-REPAIR-V1-before'
for rel in ['schemas/source.schema.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json']:
    target=arc/rel;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_bytes((b/rel).read_bytes())
append_jsonl(b/'research/events.jsonl',{'event':'maintenance_repair_preregistered','created_at':utc_now(),'plan_path':relative,'plan_sha256':sha256_file(b/relative),'before_implementation':True,'scoring':False,'fit':False,'registration':False})
print('Bounded metadata conformance preregistered before code/tests',flush=True)
