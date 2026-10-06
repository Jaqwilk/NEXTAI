from pathlib import Path
from datetime import datetime, timezone
import hashlib
import shutil
import zipfile
from nextai_autoresearch.research_program import auxiliary_charge,status
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json,load_json,sha256_file,utc_now
root=Path.cwd();clone=root.parent/'NEXTAI-VALIDATION-20261002';identity='ASM01-SYNTHETIC-COST-PREPARATION-V1'
receipt_path=root/'research/laboratory/ASM01-COST-PREP-COMPLETION-V1.receipt.json';assert not receipt_path.exists()
plan=load_json(root/f'research/plans/{identity}.json');controller=load_json(root/'research/reviews/ASM01-COST-PREP-CONTROLLER-V1.json')
proof_path=root/'research/reviews/ASM01-COST-PREP-CLONE-V1.json'
if (clone/proof_path.relative_to(root)).exists():shutil.copyfile(clone/proof_path.relative_to(root),proof_path)
proof=load_json(proof_path) if proof_path.exists() else {'complete':False}
for name,digest in plan['parent_file_bindings'].items():assert sha256_file(root/name)==digest,name
for name,binding in plan['ledger_prefixes'].items():assert hashlib.sha256((root/'research'/name).read_bytes()[:binding['bytes']]).hexdigest()==binding['sha256'],name
archive=root/'research/laboratory/archive/ASM01-SYNTHETIC-COST-EVIDENCE-V1.zip';bindings={}
paths=[root/f'research/plans/{identity}.json']+sorted((root/'research/reviews').glob('ASM01-COST-PREP-*'))
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for item in paths:
  if item.is_file():name=item.relative_to(root).as_posix();z.write(item,name);bindings[name]=sha256_file(item)
cutoff=datetime.now(timezone.utc);elapsed=(cutoff-datetime.fromisoformat('2026-10-06T03:27:00+00:00')).total_seconds()
auxiliary_charge(root,identity,600);wallet=status(root)
complete=proof.get('complete',False) and controller['complete'] and elapsed<=600
decision='KEEP runtime evidence only' if complete and proof['engineering_proxy_pass'] else 'INCONCLUSIVE; full screen cost not justified' if complete else 'INCOMPLETE exact cost probe'
receipt={'created_at':utc_now(),'id':identity,'cycle':331,'complete_technical_probe':complete,'decision':decision,'scientific_comparison':'INCONCLUSIVE; no native/fit/EXP','plan_sha256':sha256_file(root/f'research/plans/{identity}.json'),'preregistration_commit':'b8d4835','source_binding':load_json(root/'research/reviews/ASM01-COST-PREP-source-binding-V1.json'),'clone_proof':proof,'controller':controller,'lossless_archive_sha256':sha256_file(archive),'native_file_bindings':bindings,'parent_hashes_and_ledger_prefixes_preserved':True,'clock_start':plan['clock_start'],'deadline':plan['deadline'],'elapsed_seconds_at_cutoff':elapsed,'auxiliary_seconds_charged':600,'auxiliary_cap':600,'closing_admin_in_full600_charge':True,'fit_seconds':0,'native_bytes':0,'EXP':0,'registrations':0,'retry':False,'scoring':False,'full_goal_status':'ACTIVE, INCOMPLETE','unprotected_B_seconds_remaining':wallet['fit_seconds_remaining']-47000,'B_seconds_charged':wallet['stage_b_compute_seconds_charged'],'protected_tickets':wallet['protected_future_registration_attempts'],'protected_seconds':wallet['protected_future_compute_seconds'],'limitations':plan['limitations']}
atomic_write_json(receipt_path,receipt)
append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_closed','created_at':utc_now(),'cycle':331,'plan_id':identity,'receipt_sha256':sha256_file(receipt_path),'decision':decision,'native':0,'fit':0,'EXP':0})
forecast=proof.get('forecast_seconds',{})
report=f'''# ASM01 — cykl331: zamrożony syntetyczny pomiar kosztów

Prerejestracja b8d4835 przed implementacją i jedynym pomiarem w klonie.
Pełny screen niezmienionych45roles/810trials wymaga32040 DTW calls i1007380 transformów, poza intake/old74 checks.
Probe wykonał48 DTW calls (16/K16/32/64) i144 transformy (16×3lengths39/213/691×3views), wszystkie z pierwszym wywołaniem. Sprawdzano kształt, dtype i finite; nie oceniano jakości. Complete={complete}.

Prognoza inżynierska seconds: {forecast}. Decyzja: **{decision}**.
Zamrożona formuła2×10680×sum(maxDTW/K)+2×1007380×max(transform)+2×HAR180.5502402; próg worker1000s, przyszły wholecap2200 zaux1200. Mnożnik2 i historyczny HAR residual nie stanowią statystycznego ograniczenia kosztów ASM. Maxima małej próbki zależą od obciążenia maszyny; zimne wywołania pozostają w danych. Nie ma gwarancji kosztu kalibracji, innych40workers, intake/checks ani administracji.

Koszt całego etapu od03:27Z, obejmujący odczyty/delegację/prerejestrację/kod/pomiar/Git/raport: konserwatywnie600/600s, fit0/EXP0. Cutoff={elapsed:.3f}s; closing jest wewnątrz600. Jedyny job i jego potomkowie: {controller}. Rezerwa7tickets/47000s zachowana; pozostałe niechronione B={receipt['unprotected_B_seconds_remaining']:.6f}s.

Nie zmieniono modeli, geometrii, gridów, bramek, aktywnego loadera ani starych wyników. Bez nowych nativebytes, NPZ, fitu, rejestracji, retry, WT8–9, futurewriters, externalmodel/API i zmian harmonogramu. Dawny Labtimeout zachowany i nie powtórzony.

Wynik jest wyłącznie dowodem kosztu skończonego syntetycznego probe. Nie dowodzi native1830 feasibility, zgodności old74 ani drugiej rodziny transferu. Pełny cel pozostaje ACTIVE: transfer, niezależne replikacje, świeże finały i lokalny fact/source/update/UNKNOWN prototype są niedokończone. Następny scope wymaga nowej prerejestracji i finansowania przed nowymi bytes/code; jeśli koszt nie jest uzasadniony, nie wolno zmieniać DTW/modeli/gate po pomiarze ani konsumować chronionej rezerwy.

Surowe latencje, bindingi i źródła: research/laboratory/archive/ASM01-SYNTHETIC-COST-EVIDENCE-V1.zip. Receipt: research/laboratory/ASM01-COST-PREP-COMPLETION-V1.receipt.json.
'''
(root/'research/analyses/ASM01-CYCLE331-SYNTHETIC-COST-PREPARATION-V1.md').write_text(report,encoding='utf-8',newline='\n')
print({'decision':decision,'forecast':forecast,'elapsed':elapsed,'charged':600,'remaining':receipt['unprotected_B_seconds_remaining']},flush=True)
