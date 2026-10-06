from pathlib import Path
from copy import deepcopy
from nextai_autoresearch.research_program import status,auxiliary_reserve
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import load_json,atomic_write_json,sha256_file,utc_now
root=Path.cwd();identity='ASM01-EXPOSED-LEXICAL-DIAGNOSIS-V3';path=root/f'research/plans/{identity}.json';assert not path.exists()
wallet=status(root);assert wallet['fit_seconds_remaining']-47000>=300 and not wallet['scoring_authorized']
parent='research/plans/ASM01-EXPOSED-LEXICAL-DIAGNOSIS-V2.json';receipt='research/laboratory/ASM01-EXPOSED-LEXICAL-DIAGNOSIS-COMPLETION-V2.receipt.json';prior=load_json(root/receipt)
assert prior['fixture_executions']==prior['controller_executions']==prior['known_file_reads']==0
plan=deepcopy(load_json(root/parent));plan.update(id=identity,cycle=335,created_at=utc_now(),clock_start='2026-10-06T04:03:00Z',deadline='2026-10-06T04:08:00Z',auxiliary_seconds_cap=300,B_wallet_at_freeze=wallet,parent_plan_path=parent,parent_plan_sha256=sha256_file(root/parent),parent_unstarted_receipt_sha256=sha256_file(root/receipt),prior_turn_classification='NO VERIFIED SCIENTIFIC PROGRESS: V1/V2 never tested or read. New execution binding only, no changed classifier or fixtures.',metadata_repair='NONE. Exact V2 classifier and four short-ID fixtures unchanged; V2 metadata correction was frozen before any test. New immutable clock/intake execution binding before V3 driver. One first fixture execution then one already-exposed17:74 lexical-only read; failure stops unstarted scope. All original300 and V2 360 charges retained.')
for p in [parent,receipt,'research/reviews/ASM01-LEXICAL-DIAG-SOURCE-BINDING-V2.json','research/preparations/ASM01-EXPOSED-LEXICAL-DIAGNOSIS-V2/classifier.py','research/preparations/ASM01-EXPOSED-LEXICAL-DIAGNOSIS-V2/test_classifier.py']:plan['parent_bindings'][p]=sha256_file(root/p)
atomic_write_json(path,plan);append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_preregistered','created_at':utc_now(),'cycle':335,'plan_id':identity,'plan_sha256':sha256_file(path),'before_V3_driver_or_first_fixture_or_known_read':True});auxiliary_reserve(root,identity,300)
print({'plan_sha256':sha256_file(path),'reserved':300},flush=True)
