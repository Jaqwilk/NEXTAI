from pathlib import Path
from datetime import datetime,timezone
import hashlib
import math
import shutil
import zipfile
from nextai_autoresearch.research_program import auxiliary_charge,status
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json,load_json,sha256_file,utc_now
root=Path.cwd();clone=root.parent/'NEXTAI-VALIDATION-20261002';identity='ASM01-POINT-SERIAL-NATIVE-CONFORMANCE-V1'
path=root/'research/laboratory/ASM01-NATIVE-CONFORMANCE-COMPLETION-V1.receipt.json';assert not path.exists()
plan=load_json(root/f'research/plans/{identity}.json')
for name,digest in plan['parent_file_bindings'].items():assert sha256_file(root/name)==digest,name
for name,b in plan['ledger_prefixes'].items():assert hashlib.sha256((root/'research'/name).read_bytes()[:b['bytes']]).hexdigest()==b['sha256'],name
native_paths=sorted((clone/'research/reviews').glob('ASM01-NATIVE-CONFORMANCE-FIXTURES-V1.*'))
native_paths.append(clone/f'research/data_manifests/{identity}.json')
for original in native_paths:
 target=root/original.relative_to(clone);assert not target.exists();shutil.copyfile(original,target)
proof=load_json(root/f'research/data_manifests/{identity}.json');fixtures=load_json(root/'research/reviews/ASM01-NATIVE-CONFORMANCE-FIXTURES-V1.json')
controllers={kind:load_json(root/f'research/reviews/ASM01-NATIVE-CONFORMANCE-CONTROLLER-{kind}-V1.json') for kind in ('fixtures','intake')}
assert fixtures['counts']=={'tests':46,'failures':0,'errors':0,'skipped':0}
assert not proof['complete'] and proof['current_sample']=='17:74' and proof['error_category']=='normalize'
assert proof['old74_compared']==74 and proof['native_files_attempted']==1172 and proof['native_files_converted']==1171 and proof['D_samples_opened']==257
assert not (clone/f'research/data/{identity}').exists() and not (root/f'research/data/{identity}').exists()
assert all(c['result']['exit_job_active_process_count']==0 and not c['result']['exit_live_descendant_pids'] for c in controllers.values())
review_path=root/'research/reviews/ASM01-NATIVE-CONFORMANCE-INDEPENDENT-REVIEW-V1.json'
review=load_json(review_path);assert review['status']=='PASS_preservation_and_exact_old74_only'
archive=root/'research/laboratory/archive/ASM01-POINT-SERIAL-NATIVE-CONFORMANCE-EVIDENCE-V1.zip'
paths=[root/f'research/plans/{identity}.json',root/'research/reviews/ASM01-POINT-SERIAL-NATIVE-SOURCE-BINDINGS-V1.json',root/f'research/data_manifests/{identity}.json',review_path]
paths.extend(root/name for name in plan['implementation_paths'])
paths.extend(p for p in sorted((root/'research/reviews').glob('ASM01-NATIVE-CONFORMANCE-*')) if p.is_file())
paths=list(dict.fromkeys(paths));bindings={}
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in paths:
  name=p.relative_to(root).as_posix();z.write(p,name);bindings[name]=sha256_file(p)
cutoff=datetime.now(timezone.utc);elapsed=(cutoff-datetime.fromisoformat('2026-10-06T03:39:20+00:00')).total_seconds()
assert elapsed+120<=900,'Stop scope: closing allowance would exceed unchanged900 cap'
charged=math.ceil(elapsed)+120
auxiliary_charge(root,identity,charged);wallet=status(root)
receipt={'created_at':utc_now(),'id':identity,'cycle':332,'status':'INVALID_native_intake_unstarted_scope_stopped','decision':'KEEP exact74 historical array/view compatibility; DISCARD current complete-intake feasibility claim','scientific_comparison':'INCONCLUSIVE through intake invalidity; not learning/transfer/economic null','plan_sha256':sha256_file(root/f'research/plans/{identity}.json'),'preregistration_commit':'26d4169','source_freeze_commit':'8895d20','fixture_counts':fixtures['counts'],'native_intake':proof,'controllers':controllers,'independent_review':review,'all_parent_protected_files_and_ledger_prefixes_preserved':True,'remaining_native_files_unstarted':658,'new_numeric_samples_beyond_prior74':1097,'all915T_samples_converted':True,'D_samples_converted':256,'native_reference_reparses':74,'NPZ':0,'research_fit_seconds':0,'registrations':0,'EXP':0,'scoring':False,'retry':False,'active_integration':False,'future_writer_access':False,'external_model_API':False,'schedule_change':False,'lossless_archive_sha256':sha256_file(archive),'native_file_bindings':bindings,'clock_start':plan['clock_start'],'deadline':plan['deadline'],'elapsed_seconds_at_cutoff':elapsed,'auxiliary_seconds_cap':900,'auxiliary_seconds_charged':charged,'closing_allowance_seconds':120,'B_seconds_charged':wallet['stage_b_compute_seconds_charged'],'unprotected_B_seconds_remaining':wallet['fit_seconds_remaining']-47000,'protected_tickets':wallet['protected_future_registration_attempts'],'protected_seconds':wallet['protected_future_compute_seconds'],'full_goal_status':'ACTIVE, INCOMPLETE','failure_cause_limit':'Only normalize category is instrumented. Prior lexical metadata lists3 signedY forms in17:74, but literal tokens/values were never emitted; exact failing rule remains unidentified. No same-cycle raw diagnosis or rescue.'}
atomic_write_json(path,receipt)
append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_closed','created_at':utc_now(),'cycle':332,'plan_id':identity,'receipt_sha256':sha256_file(path),'decision':receipt['decision'],'native_attempted':1172,'native_converted':1171,'EXP':0,'fit':0})
report=f'''# ASM01 — cykl332: pełna conformance native zatrzymana

## OBSERVATION

Nowy kontrakt26d4169 zamrożony przed implementacją/nowymi bytes; źródła8895d20 przed jedynym46-case clone run i jedynym intake. **46/46 PASS**,0fail/error/skip. Wszystkie1830 metadata i hashmaps zweryfikowane przed payload. **74/74 dawnych tablic float32 i write/nominal/adverse są identyczne bajtowo**; zapisano nowe array/descriptorhashes, zamiast udawać istnienie starych zapisanych hashy.

Próba zatrzymała się na **W17/sample74**, kategoria **normalize**. Attempted1172,converted1171,validated1171,old74compared74,Dopened257. Wszystkie915T i256D przekonwertowane;658dalszych plików nieuruchomionych.1097nowych konwersji poza prior74, plus74referencereparses. Nie utworzono NPZ; fit0/EXP0/registration0. Nie kontynuowano intake ani diagnozy raw po failure. Oba drzewa procesów zamknięte bez żywych potomków.

## INTERPRETATION

Techniczny postęp jest konkretny: dawny accepted zakres zachowuje dokładną geometrię i trzy widoki, a jawne seriale rozwiązują wcześniejsze problemy markerów dla1171próbek. **Cały wymagany screen nie jest wykonalny pod tą dokładną zamrożoną regułą.** Nie jest to ujemny wynik uczenia, transferu ani ekonomii; scientific comparison pozostaje INCONCLUSIVE. D nie jest blind/fresh: przed etapem915D było lexically exposed, teraz257D raw attempted/256numeric. Futurewriters6–15/21–30 pozostają unopened.

## CONFIDENCE

Wysoka dla46syntheticcases i74exactnativecomparisons oraz udokumentowanego stopu. Brak wiedzy o wynikach modeli: żadnego fitu/query-evaluation. Redacted inventory wcześniej wskazało3signedY forms w17:74; nie ujawniało ich literalnej postaci lub wartości. Genericnormalize nie ustala, czy odrzucił signedspelling, state/serial/monotonicity lub inną zadeklarowaną regułę. **Nie przypisujemy exact przyczyny bez osobno zamrożonej diagnozy.**

## ALTERNATIVE EXPLANATIONS

Ewentualny wariant zapisu negativezero byłby problemem serialization; rzeczywista niezerowa wartość ujemna lub geometric/bounds failure zamyka tę dokładną trasę. Nie stosowaćabs/clamp/offset, filtrowania punktów/próbek lub wymiany writerów. Nawet ewentualna przyszła metadatarepair wymaga osobnego concretefreeze, zachowania wszystkich1171nowych acceptedarrayhashes i niezależnego pełnego conformance, bez zmiany modelów/grids/gates. Ten etap nie uprawnia takiej naprawy.

## DECISION

**{receipt['decision']}**. Stop wszystkichunstarted. Konserwatywny pełny charge **{charged}/900s**, cutoff{elapsed:.3f}s+120sclosing; includesallstartup/delegation/code/failures/tests/intake/admin/Git, bez ponownego sumowania nestedjobs. B{wallet['stage_b_compute_seconds_charged']:.6f}/72000s,1/12tickets. Protected7tickets/47000s intact; remainingunprotected{receipt['unprotected_B_seconds_remaining']:.6f}s. Zero retry,WT8–9,externalmodels/API,schedulechange i sourcefitreplay. Activeframework/config/schema/models/geometry unchanged. Wcześniejszy administrativeoverrun331 i Labtimeout zachowane, nie naprawiane przez ten result.

## NEXT DISCRIMINATING STEP

Osobny preparation-only SHA-bound classifier wyłącznie already-exposed17:74 mógłby rozróżnić signedzero spelling od nonzero signed categories oraz sprawdzić stan/serial bez liczb i coordinate/name emission. To diagnoza, nie retry lub geometryrepair. Jeśli exact route jest niewykonalna, zachować invalidity i ocenić niezależnie uzasadnioną rodzinę bez outcome-based sample replacement. Ponadto przed nowym scientific scope konieczne są hardaggregate worker limits i ownstudy auxiliary reserve semantics wskazane w cyklu331. Żaden budżet nie został zwiększony.

Pełny cel pozostaje ACTIVE: drugi naukowy screen, niezależne replikacje, świeże finały i evidence-selected lokalny fact/source/update/UNKNOWN prototype są niedokończone. Receipt:research/laboratory/ASM01-NATIVE-CONFORMANCE-COMPLETION-V1.receipt.json; source/output losslessZIP:research/laboratory/archive/ASM01-POINT-SERIAL-NATIVE-CONFORMANCE-EVIDENCE-V1.zip.
'''
(root/'research/analyses/ASM01-CYCLE332-NATIVE-CONFORMANCE-V1.md').write_text(report,encoding='utf-8',newline='\n')
print({'status':receipt['status'],'exact_old74':74,'attempted':1172,'converted':1171,'charged':charged,'remaining':receipt['unprotected_B_seconds_remaining']},flush=True)
