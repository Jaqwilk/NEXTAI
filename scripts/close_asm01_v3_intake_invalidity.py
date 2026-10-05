"""Close the failed V3 native intake after complete clone checks and accounting."""
from datetime import datetime, timezone
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == 'NEXTAI'
study_path = 'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json'
task_path = 'research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json'
analysis_path = 'research/analyses/ASM01-CYCLE324-INTAKE-INVALIDITY-V1.md'
receipt_path = 'research/laboratory/ASM01-CYCLE324-COMPLETION-V1.receipt.json'
assert not (root / analysis_path).exists() and not (root / receipt_path).exists()
assert sha256_file(root / study_path) == 'a3e338f334aeccf7543f72e9e1c6133188ac39acbd23a53792a4607c3f57d217'
assert sha256_file(root / task_path) == 'd34bf101fe22ad5fbe739d6ff05a24b96ce4939eca57720f76b8eb89063c4dd1'
study = json.loads((root / study_path).read_text())
assert datetime.now(timezone.utc) < datetime.fromisoformat(study['study_deadline_at'].replace('Z', '+00:00'))
events = [e for e in read_jsonl(root / 'research/events.jsonl')
          if str(e.get('charge_id', '')).startswith('NEXTAI-B-324-')]
reserved = {e['charge_id'] for e in events if e['event'] == 'research_program_aux_fit_reserved'}
charges = {e['charge_id']: e['seconds'] for e in events if e['event'] == 'research_program_aux_fit_charged'}
assert reserved == set(charges)
cycle_seconds = sum(charges.values())
assert cycle_seconds <= study['resources']['auxiliary_test_seconds_cap'] == 2500
checks = {}
for identifier, amount in charges.items():
    relative = f'research/reviews/{identifier}.json'
    item = json.loads((root / relative).read_text())
    assert item['seconds_charged'] == amount
    for filename, digest in item.get('raw_outputs', {}).items():
        assert sha256_file(root / 'research/reviews' / filename) == digest
    if item.get('result'):
        assert item['result']['exit_job_active_process_count'] == 0
        assert not item['result']['exit_live_descendant_pids']
    checks[relative] = sha256_file(root / relative)
for suffix in ('startup-doctor', 'startup-lab', 'clone-conformance-V1', 'maintenance-seal-V1',
               'closing-doctor-V1', 'clone-lab-lifecycle-V1'):
    item = json.loads((root / f'research/reviews/NEXTAI-B-324-{suffix}.json').read_text())
    assert item['result']['returncode'] == 0 and not item['error']
failed_check = json.loads((root / 'research/reviews/NEXTAI-B-324-native-intake-V1.json').read_text())
assert failed_check['result']['returncode'] == 1 and failed_check['result']['reason'] == 'exited'
for suffix in ('startup-lab', 'clone-lab-lifecycle-V1'):
    lab = json.loads((root / f'research/reviews/NEXTAI-B-324-{suffix}.stdout.txt').read_text())
    assert not lab['errors'] and not lab['warnings']
for path, count in (('research/reviews/NEXTAI-B-324-clone-conformance-V1.xml', 131),
                    ('research/reviews/NEXTAI-B-324-clone-lifecycle-V1.xml', 1)):
    groups = list(ET.parse(root / path).getroot().iter('testsuite'))
    assert sum(int(x.attrib['tests']) for x in groups) == count
    assert all(int(x.attrib[k]) == 0 for x in groups for k in ('errors', 'failures', 'skipped'))
intake_path = 'research/data_manifests/ASM01-ACQUISITION-V3.json'
intake = json.loads((root / intake_path).read_text())
assert not intake['complete'] and intake['error'] == 'ValueError: Native point grammar'
assert (intake['native_files_attempted'], intake['native_files_converted'], intake['D_samples_opened']) == (75, 74, 0)
assert intake['attempted_sample_text_sha256']['1:75'] == '3201954c4c808f8d2f63201c9af9353e1c68f6ad1d2109d94d9f97ce73913bcc'
seal_path = 'research/reviews/ASM01-V3-FAILED-INTAKE-MAINTENANCE-SEAL-V1.json'
seal = json.loads((root / seal_path).read_text())
assert seal['maintenance'] and not seal['ready'] and not seal['scoring']
assert seal['all_historical_science_bytes_unchanged'] and seal['old_schema_clauses_and_semantic_records_unchanged']
wallet = status(root)
assert wallet['stage_b_registration_attempts_used'] == 1
assert wallet['stage_b_compute_seconds_charged'] == 14185.550240200071 + cycle_seconds
assert wallet['protected_future_registration_attempts'] == 7 and wallet['protected_future_compute_seconds'] == 47000
assert not wallet['scoring_authorized'] and not wallet['ready'] and not wallet['paid_run_pending']
assert wallet['pending_fit_reservation_seconds'] == 0 and not wallet['program_terminal']
remaining = wallet['fit_seconds_remaining']
finished = utc_now()
next_step = (
    'Preregister a NEW bounded no-scoring ASM01 full-screen lexical grammar inventory before implementation '
    'or further native bytes. Use only the fixed1830 extracted screen files, disclose the75 previously attempted '
    'T1 files and their74 complete conversions; preserve all native V1/V2/V3 failures. Inventory complete row '
    'arities, lexical kinds, header/marker positions and unambiguous categorical state/stroke forms; emit no '
    'X/Y values or character names and do not convert numeric coordinates, call parsers/descriptors/models, '
    'fit, score, download or access future writers6..15/21..30. Decide whether the complete grammar permits '
    'metadata-equivalent normalization under unchanged numeric geometry. Freeze every concrete repair and '
    'synthetic accept/reject fixture before implementing it. If new numeric geometry or population filtering '
    'is necessary, preserve this original cohort as infeasible and prospectively assess a distinct licensed '
    'native family instead of weakening guards/dropping samples. Complete-cohort feasibility, new scientific '
    'identity and independent clone freeze/preflight/readiness precede any single audited EXP. Pin the '
    'remaining unprotected budget and preserve7tickets/47000seconds for replication/fresh finals/prototype.'
)
table = '\n'.join(f'| {identifier} | {amount} |' for identifier, amount in charges.items())
report = f'''# ASM01 — cykl324: nieudane przygotowanie zbioru V3

Zamknięto {finished}. Decyzja **INCONCLUSIVE** dla porównania naukowego przez
nieudaną obsługę wymaganej próbki. Nowy EXP **brak**; ostatni EXP-20261005-0007.
Cel transferu, replikacji, świeżego finału i prototypu pozostaje **ACTIVE**.

## OBSERVATION

Niezmienny plan `{study_path}`, SHA256 `{sha256_file(root / study_path)}`,
zamrożono w **a2f9fb9** przed implementacją **40c27bf** i pozostałymi danymi.
Task `{task_path}`, SHA256 `{sha256_file(root / task_path)}`. Przed native intake
commit **332ed83** wiąże **131/131 PASS** w niezależnym klonie oraz zgodność1443
plików źródłowych. Sprawdzono parsery, kanoniczne członkostwo, oba schema-cohorts,
wszystkie45 audytów, rzeczywisty Transformer/cache, klasyczne grids,144-parową
kalibrację, aktualne źródła, granicę worker przed fit oraz syntetyczne hash/scope/split
loadera. Małe fity na fiksturach są w pełnym koszcie pomocniczym, nie w wyniku naukowym.

Wszystkie modele,25 stanów źródłowych,4096 par,2048/1024 kroki,9 metod,5 stałych
par autorów,K16/32/64,updates0/1/4,nominal/adverse oraz metryki,siatki i bramki
pozostały niezmienione. Globalny worker cap8300 obejmuje45x184=8280 s przy dawnych
indywidualnych limitach120 s fit/180 s worker; auxiliary2500,razem10800,bez naruszenia
chronionej rezerwy. Deadline {study['study_deadline_at']}.

Jedyny intake zachowanego publisher RAR,bez nowego downloadu,potwierdził8235
kanonicznych próbek45x183 i jedyny wcześniej zamrożony obcy member. Wyekstrahowano
tylko1830 ustalonych plików screen; future writers i Data_Table.pdf nie otwarto.
**75 próbek autora1 odczytanych,74 poprawnie przekonwertowane; próbka75 zawiodła
Native point grammar.** Każdy z75 tekstów ma zachowany SHA; błędna próbka ma
`3201954c4c808f8d2f63201c9af9353e1c68f6ad1d2109d94d9f97ce73913bcc`.
74 nowe teksty obejmują73 nowe pełne konwersje oraz nieukończoną75; próbka1 była
już wcześniej znana. Konkretny wiersz/formę oraz liczbę częściowo przetworzonych
punktów75 nie instrumentowano; nie podajemy wymyślonej przyczyny lub zerowej ekspozycji.
Wartości X/Y i nazwy nie zostały wypisane. **D0,NPZ0,source refit0,fit badawczy0,
rejestracje0,EXP0**. Zatrzymano cały nieuruchomiony zakres,bez parser rescue lub
zastąpienia/odrzucenia próbki. Cały intake child trwał {intake['full_intake_wall_seconds']:.6f} s;
pełny nadzorowany job i allowance obciążono {failed_check['seconds_charged']} s.

Startup i końcowy doctor PASS; niezależny klon lifecycle1/1 i pełny CLI lab PASS,
errors=[],warnings=[]. Wszystkie nadzorowane drzewa bez żywych potomków.
Nowy manifest obejmuje **{seal['protected_files']} plików**. Wszystkie stare bajty
naukowe,clause schema i rekordy semantyczne zachowane; dołożono tylko nowy cohort.
Pełna regresja nie była ponawiana: dawny timeout46% z321 pozostaje niezaliczony.

## INTERPRETATION

Sprawdzona naprawa nagłówka/PEN_UP0 działa poza pojedyncząT1,ale nie wystarcza
do przyjęcia całego zadeklarowanego zbioru. Błąd75 nie rozstrzyga uczenia ani
transferu; nie wolno zastępować brakującego porównania wynikiem testów technicznych.
Nie uzyskano nowych efektów rankingu,aktualizacji,UNKNOWN lub ekonomii.

## CONFIDENCE

Wysoka dla jawnych liczników,hashy,131 fikstur oraz zatrzymania bezD/fitu/EXP.
Dokładna przyczyna wiersza75 i poprawność pozostałych1755 próbek pozostają nieznane.
Przedziały pięcioparowego efektu jakości/kosztu są **NIEOBLICZONE**,a nie zerowe.
Powtórzenia zapytań ani74 pliki jednego autora nie tworzą pięciu niezależnych jednostek.

## ALTERNATIVE EXPLANATIONS

Native point grammar obejmuje błędną arność/leksykę albo punkt poza aktywną
kreską; nie wskazuje automatycznie kolejnego legalnego metadata markera.
Możliwa jest zarówno nieuwzględniona serializacja,jak i wadliwa próbka. Nowa
całościowa inwentaryzacja powinna to rozdzielić przed następną konkretną naprawą.
Zmiana geometrii albo filtrowanie populacji wymagałoby odrębnego uzasadnienia,
nie ukrytej poprawki tego ukończonego kontraktu.

## DECISION

**INCONCLUSIVE — zatrzymać dokładny ASM01 V3 intake i nieuruchomione porównanie.**
Bez promocji,falsyfikacji rodziny,płatnego retry lub zmiany zakończonych artefaktów.
Zachować technicznie zaliczone źródła i alternatywy. Program B nadal aktywny.

| Append-only rozliczenie | Sekundy |
|---|---:|
{table}

Łącznie **{cycle_seconds}/2500 s** pomocniczych,pełne czasy testów,nadzoru oraz
awaria wliczone. Prepaid administration300 s obejmuje reads,kontrakty,archiwa,
mirrory/raport/Git; substantive checks i fity fikstur rozliczono oddzielnie.
B **1/12**, **{wallet['stage_b_compute_seconds_charged']:.9f}/72000 s**;
pozostało {remaining:.9f} s,w tym **7 rejestracji/47000 s** chronionej rezerwy.
Margines niechroniony {remaining-47000:.9f} s. A zamknięty11/17 i35649.98936010008 s;
MUC03 zamknięty3 i2655.336484700005 s; brak kredytu z niewydanegoA.
Wszystkie rezerwacje rozliczone,maintenance,ready=false,scoring=false.
Bez WT8–9,zewnętrznych modeli/API i zmian harmonogramu. Stare snapshots seal/lab
mogły zawierać ówczesną aktywną rezerwację; końcowe liczby pochodzą z ledgeru.

## NEXT DISCRIMINATING EXPERIMENT

{next_step}

Druga rodzina transferu,niezależne replikacje,świeży finał i minimalny lokalny
fact/source/update/UNKNOWN prototyp nadal pozostają niewykonane. Cały cel nieukończony.
'''
(root / analysis_path).write_bytes(report.encode())
receipt = dict(schema_version=1, id='ASM01-CYCLE324-COMPLETION-V1', created_at=finished, cycle=324,
               study_path=study_path, study_sha256=sha256_file(root / study_path),
               task_path=task_path, task_sha256=sha256_file(root / task_path),
               analysis_path=analysis_path, analysis_sha256=sha256_file(root / analysis_path),
               decision='INCONCLUSIVE native intake failure; no learning/transfer/economic result',
               new_experiment_id=None, latest_scientific_experiment_id='EXP-20261005-0007',
               new_registrations=0, new_research_fit_seconds=0, native_files_attempted=75,
               native_files_converted=74, new_native_texts_attempted=74,
               new_native_files_completely_converted=73, D_samples_opened=0,
               partial_failed_sample_point_count=None, native_NPZ_created=False,
               source_states_and_all_scientific_gates_unchanged=True, extended_goal_completed=False,
               cycle_auxiliary_seconds_charged=cycle_seconds, cycle_auxiliary_cap_seconds=2500,
               cycle_auxiliary_charges=charges, all_auxiliary_reservations_resolved=True,
               checks_and_failures_receipt_sha256=checks,
               intake_receipt_sha256=sha256_file(root / intake_path),
               maintenance_seal_sha256=sha256_file(root / seal_path),
               preintake_conformance_sha256=sha256_file(root / 'research/reviews/ASM01-V3-PREINTAKE-CONFORMANCE-V1.json'),
               conformance_junit_sha256=sha256_file(root / 'research/reviews/NEXTAI-B-324-clone-conformance-V1.xml'),
               lifecycle_junit_sha256=sha256_file(root / 'research/reviews/NEXTAI-B-324-clone-lifecycle-V1.xml'),
               passed_fixture_cases=131, passed_lifecycle_cases=1,
               full_independent_clone_lab_CLI_pass=True, original_startup_and_closing_doctor_pass=True,
               full_regression_repeated=False, protected_files=seal['protected_files'],
               protected_future_compute_seconds=47000, protected_future_registration_attempts=7,
               program_budget_before_preparation_completion_event=wallet,
               benchmark_status='maintenance', ready=False, scoring=False,
               closure_script_sha256=sha256_file(Path(__file__)), next_discriminating_experiment=next_step)
atomic_write_json(root / receipt_path, receipt)
state_path = root / 'research/state.json'
state = json.loads(state_path.read_text())
assert state['cycle_number'] == 324 and state['completed_experiments'] == 122 and state['active_experiment_id'] is None
state['updated_at'] = finished
atomic_write_json(state_path, state)
append_jsonl(root / 'research/events.jsonl', {
    'event': 'research_program_preparation_completed', 'created_at': finished, 'cycle': 324,
    'program_id': wallet['id'], 'study_path': study_path, 'study_sha256': sha256_file(root / study_path),
    'receipt_path': receipt_path, 'receipt_sha256': sha256_file(root / receipt_path),
    'no_scoring': True, 'extended_goal_completed': False,
})
append_jsonl(root / 'research/events.jsonl', {
    'event': 'bounded_research_cycle_completed', 'created_at': finished, 'cycle': 324,
    'program_id': wallet['id'], 'experiment_id': None,
    'completion_receipt_path': receipt_path, 'completion_receipt_sha256': sha256_file(root / receipt_path),
    'next_scoring_requires_new_study_freeze': True, 'whole_program_complete': False,
})
closed = status(root)
assert closed['study_terminal'] and not closed['program_terminal']
assert closed['stage_b_compute_seconds_charged'] == wallet['stage_b_compute_seconds_charged']
print(json.dumps({'receipt_path': receipt_path, 'cycle_seconds': cycle_seconds,
                  'B_compute_seconds': closed['stage_b_compute_seconds_charged'],
                  'study_terminal': True, 'goal_complete': False}), flush=True)
