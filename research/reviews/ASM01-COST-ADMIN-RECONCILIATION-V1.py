from pathlib import Path
from datetime import datetime, timezone
from nextai_autoresearch.research_program import auxiliary_reserve,auxiliary_charge
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now,load_json
root=Path.cwd();identity='ASM01-COST-CLOSING-ADMIN-RECONCILIATION-V1'
plan_path=root/f'research/plans/{identity}.json';assert not plan_path.exists()
parent=root/'research/laboratory/ASM01-COST-PREP-COMPLETION-V1.receipt.json'
plan={'id':identity,'created_at':utc_now(),'cycle':331,'study_kind':'preparation_only','scope':'Administrative preservation and exact budget reconciliation ONLY; no extension/retry of synthetic probe or science. Original600s limit remains unchanged and its closing overrun is disclosed.','clock_start':'2026-10-06T03:37:00Z','deadline':'2026-10-06T03:42:00Z','auxiliary_seconds_cap':300,'fit_seconds_cap':0,'EXP_cap':0,'native_execution_authority':False,'parent_receipt_sha256':sha256_file(parent),'trigger':'Last publication ended03:37:09Z,9s after original03:37 deadline; plus independent framework review found aggregate worker overshoot and double reservation of own prior preparation.','decision':'Original finite probe192/192 valid; entire original600s stage administration INCOMPLETE through9s overrun. Financial whole-screen readiness NOT ESTABLISHED. Preserve original source/results/receipts and add separate full conservative administrative charge.','forbidden':['new test or probe','native bytes','fit/EXP/registration','implementation of budget fixes','threshold or cap repair of original stage','retry','protected7tickets/47000s spending','schedule change']}
atomic_write_json(plan_path,plan)
append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_preregistered','created_at':utc_now(),'cycle':331,'plan_id':identity,'plan_sha256':sha256_file(plan_path),'administrative_only':True})
auxiliary_reserve(root,identity,300)
auxiliary_charge(root,identity,300)
out=root/'research/laboratory/ASM01-COST-ADMIN-RECONCILIATION-V1.receipt.json'
cutoff=datetime.now(timezone.utc)
atomic_write_json(out,{'created_at':utc_now(),'id':identity,'plan_sha256':sha256_file(plan_path),'parent_receipt_sha256':sha256_file(parent),'original_stage_admin_limit_status':'EXCEEDED; first observed finalpublication9seconds after deadline; original cap not changed','original192_call_probe_status':'PASS finite synthetic scope only','new_scope':'administrative reconciliation, not retry','charged_extra_seconds':300,'original_charge_seconds':600,'combined_conservative_seconds':900,'clock_start':plan['clock_start'],'deadline':plan['deadline'],'elapsed_at_cutoff_seconds':(cutoff-datetime.fromisoformat('2026-10-06T03:37:00+00:00')).total_seconds(),'closing_administration_in300charge':True,'fit_seconds':0,'native_bytes':0,'EXP':0,'registrations':0,'protected_seconds':47000,'protected_tickets':7,'unprotected_B_seconds_remaining':1967.449759799929,'financial2200_attempt_now_affordable':False,'full_goal_status':'ACTIVE, INCOMPLETE','framework_blockers':['runner totalcap is pre-role check; up to184s overshoot','reserve guard deducts whole immutable study cap after earlier own preparation already charged']})
append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_closed','created_at':utc_now(),'cycle':331,'plan_id':identity,'receipt_sha256':sha256_file(out),'decision':'Preserve probe; original stage administrative overrun; no science readiness'})
report='''# Cycle331 — korekta końcowego rozliczenia

Oryginalna prerejestracja i receipt pozostają niezmienione. Syntetyczny probe
192/192 PASS zakończył się w limicie. Końcowa publikacja dodatkowego przeglądu
zakończyła się03:37:09Z,9s po niezmienionym deadline03:37:00Z. Cały pierwotny
etap administracyjnie **INCOMPLETE przez przekroczenie**, mimo ważnego skończonego
wyniku runtime. To nie jest dowód scientific/native feasibility.

Zachowanie przekroczenia i dodatkowego niezależnego przeglądu rozliczono osobno:
administracyjne300s od03:37 do03:42 obejmują także finalizację/Git. Łączna
konserwatywna opłata900s; fit0/EXP0. Bez powtórzenia probe, nowych nativebytes
lub naprawiania modeli/geometry/gates. Protected7tickets/47000s zachowane;
pozostałe niechronione B1967.4497598s. Dawna warunkowa próba2200s jest teraz
**NIEFINANSOWALNA** z tego marginesu.

Przed jakimkolwiek nowym scope trzeba także prospektywnie rozwiązać dwa fakty:
runner sprawdza totalcap przed rolą, dolicza koszt po jej zakończeniu i może
przekroczyć1000 o niemal184s; reserve guard ponownie odejmuje cały studycap
po już rozliczonych własnych kosztach przygotowania. Żadnego pominięcia kosztów,
zwiększenia portfela lub osłabienia naukowych bramek. NOWY poprawny scope musi
zamrozić oraz zweryfikować hard aggregate budget zteardown i dokładną semantykę
pozostałej rezerwy. Nie zaimplementowano ich w tym etapie.

Pełny cel pozostaje ACTIVE i niedokończony. Wszystkie pierwotne plany, hash-bound
źródła,192latencysamples, losslessarchive i wcześniejsze błędy zachowane. Receipt:
research/laboratory/ASM01-COST-ADMIN-RECONCILIATION-V1.receipt.json.
'''
(root/'research/analyses/ASM01-CYCLE331-ACCOUNTING-ADDENDUM-V1.md').write_text(report,encoding='utf-8',newline='\n')
print({'combined_charge':900,'unprotected_remaining':1967.449759799929,'original_admin_stage':'overrun','probe':'192PASS','full_goal':'ACTIVE'},flush=True)
