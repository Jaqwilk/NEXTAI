from pathlib import Path
from nextai_autoresearch.research_program import auxiliary_charge
from nextai_autoresearch.utils import atomic_write_json,utc_now,sha256_file
from nextai_autoresearch.ledger import append_jsonl
import zipfile
root=Path.cwd(); identity='ASM01-EXPOSED-LEXICAL-DIAGNOSIS-V2'
assert not (root/'research/reviews/ASM01-LEXICAL-DIAG-CONTROLLER-V2.started.json').exists()
auxiliary_charge(root,identity,360)
archive=root/'research/laboratory/archive/ASM01-EXPOSED-LEXICAL-DIAGNOSIS-UNSTARTED-V2.zip'
paths=[root/f'research/plans/{identity}.json',root/'research/reviews/ASM01-LEXICAL-DIAG-SOURCE-BINDING-V2.json',root/'research/reviews/ASM01-LEXICAL-DIAG-CLONE-V2.py',root/'research/reviews/ASM01-LEXICAL-DIAG-CONTROLLER-V2.py']+list((root/f'research/preparations/{identity}').glob('*.py'))
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in paths:z.write(p,p.relative_to(root).as_posix())
receipt={'created_at':utc_now(),'id':identity,'status':'INCOMPLETE_UNSTARTED','decision':'Stop unstarted scope: frozen 90s closing reserve expired before launch','guard_latest_start':'2026-10-06T04:01:30Z','observed_after_clone_sync':'2026-10-06T04:01:46.3483162Z','whole_clock_start':'2026-10-06T03:57:00Z','deadline':'2026-10-06T04:03:00Z','charged_seconds':360,'fixture_executions':0,'controller_executions':0,'known_file_reads':0,'new_native_samples':0,'coordinate_conversions':0,'fit':0,'EXP':0,'retry':False,'source_freeze_commit':'19b2610','archive_sha256':sha256_file(archive),'protected_seconds':47000,'protected_tickets':7,'unprotected_B_seconds_remaining':530.4497597999289,'full_goal_status':'ACTIVE, INCOMPLETE'}
out=root/f'research/laboratory/{identity}-COMPLETION-V2.receipt.json'
out=root/'research/laboratory/ASM01-EXPOSED-LEXICAL-DIAGNOSIS-COMPLETION-V2.receipt.json';atomic_write_json(out,receipt)
append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_closed','created_at':utc_now(),'cycle':334,'plan_id':identity,'receipt_sha256':sha256_file(out),'decision':receipt['decision'],'fit':0,'EXP':0})
(root/'research/analyses/ASM01-CYCLE334-EXPOSED-LEXICAL-DIAGNOSIS-V1.md').write_text('# ASM01 — cykl334: diagnoza V2 niewystartowana\n\nStatus: INCOMPLETE_UNSTARTED. Prerejestracja V2 poprzedziła kod; zamrożony kod19b2610 skopiowano do niezależnego klonu. Synchronizacja zakończyła się04:01:46.3483162Z, po zamrożonej granicy startu04:01:30Z. Nie uruchomiono kontrolera, testów ani odczytu znanego17:74. Nie uzyskano nowego dowodu o rodzaju trzech ujemnych tokenów. Nie utożsamiać minus-zero z niezerową współrzędną.\n\nPełne360s03:57–04:03Z naliczono, w tym przygotowanie i zamknięcie. Fit0, EXP0, retry=false. V1 i V2, źródła, niepowodzenia oraz historia zachowane. Pozostały wolny budżet B530.4497597999289s; protected7tickets47000s bez zmian. Cel pełny ACTIVE/INCOMPLETE: brak drugiej udanej naukowej rodziny transferu, replikacji/finałów B i prototypu. Nic nie potwierdza nowej naukowej wykonalności.\n',encoding='utf-8',newline='\n')
print(receipt,flush=True)
