"""Append-only cycle321 closure after every bounded execution is settled."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI"
study_path = "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json"
task_path = "research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json"
analysis_path = "research/analyses/ASM01-CYCLE321-INTAKE-INVALIDITY-V1.md"
receipt_path = "research/laboratory/ASM01-CYCLE321-COMPLETION-V1.receipt.json"
assert not (root / analysis_path).exists() and not (root / receipt_path).exists()
study = json.loads((root / study_path).read_text(encoding="utf-8"))
assert sha256_file(root / study_path) == "ff35bd63a84ce510fc13e67f5d1f5314620607a634899aa321d74c2d39411925"
assert sha256_file(root / task_path) == "debdeea304bec803b482c421b6d7d54dfc398a8563f7312f7a84fdbe226063a9"
assert datetime.now(timezone.utc) < datetime.fromisoformat(study["study_deadline_at"].replace("Z", "+00:00"))
events = read_jsonl(root / "research/events.jsonl")
cycle_events = [e for e in events if str(e.get("charge_id", "")).startswith("NEXTAI-B-321-")]
reserves = {e["charge_id"] for e in cycle_events if e["event"] == "research_program_aux_fit_reserved"}
charges = {e["charge_id"]: e["seconds"] for e in cycle_events if e["event"] == "research_program_aux_fit_charged"}
assert reserves == set(charges)
cycle_seconds = sum(charges.values())
assert cycle_seconds <= study["resources"]["auxiliary_test_seconds_cap"] == 3600
wallet = status(root)
assert wallet["pending_fit_reservation_seconds"] == 0 and not wallet["paid_run_pending"]
assert not wallet["scoring_authorized"] and not wallet["program_terminal"]
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000
assert wallet["protected_future_registration_attempts"] == 7
checks = {}
for identifier, amount in charges.items():
    relative = f"research/reviews/{identifier}.json"
    item = json.loads((root / relative).read_text(encoding="utf-8"))
    assert item["seconds_charged"] == amount
    for filename, digest in item.get("raw_outputs", {}).items():
        assert sha256_file(root / "research/reviews" / filename) == digest
    checks[relative] = sha256_file(root / relative)

clone_lab_check = json.loads((root / "research/reviews/NEXTAI-B-321-clone-lab-lifecycle-V2.json").read_text())
assert clone_lab_check["result"]["returncode"] == 0 and not clone_lab_check["error"]
assert not clone_lab_check["result"]["exit_live_descendant_pids"]
lab = json.loads((root / "research/reviews/NEXTAI-B-321-clone-lab-lifecycle-V2.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
assert not lab["current_scope"]["scoring_authorized"]
affected_xml = root / "research/reviews/NEXTAI-B-321-affected-conformance-V1.xml"
affected = ET.parse(affected_xml).getroot().find("testsuite")
assert int(affected.attrib["tests"]) == 29 and int(affected.attrib["failures"]) == 1
assert int(affected.attrib["errors"]) == 0 and int(affected.attrib["skipped"]) == 0
failures = affected.findall("testcase/failure")
assert len(failures) == 1 and "research/REPORT.md is stale" in (failures[0].text or "")
lifecycle_xml = root / "research/reviews/NEXTAI-B-321-clone-lifecycle-V2.xml"
lifecycle = ET.parse(lifecycle_xml).getroot().find("testsuite")
assert int(lifecycle.attrib["tests"]) == 1
assert all(int(lifecycle.attrib[k]) == 0 for k in ("errors", "failures", "skipped"))
full = json.loads((root / "research/reviews/NEXTAI-B-321-clone-full-regression-V1.json").read_text())
assert full["result"]["returncode"] == 124
percentages = re.findall(r"\[\s*(\d+)%\]", (root / "research/reviews/NEXTAI-B-321-clone-full-regression-V1.stdout.txt").read_text())
assert percentages and int(percentages[-1]) == 46
process_exit_path = "research/reviews/ASM01-FULL-REGRESSION-PROCESS-EXIT-V1.json"
mirror_path = "research/reviews/ASM01-CLOSED-ORIGINAL-CLONE-MIRROR-V1.json"
mirror = json.loads((root / mirror_path).read_text())
assert mirror["both_current_manifests_ok"] and mirror["protected_files"] == 1432
intake_v1 = "research/data_manifests/ASM01-ACQUISITION-V1.json"
intake_v2 = "research/data_manifests/ASM01-ACQUISITION-V2.json"
acquisition = json.loads((root / intake_v2).read_text())
assert acquisition["complete"] is False and acquisition["no_model_fit_or_scoring"] is True
assert acquisition["native_legal_files"] == 8235 and acquisition["new_download_bytes"] == 0
diagnosis_path = "research/reviews/ASM01-NATIVE-GRAMMAR-DIAGNOSIS-V1.json"
diagnosis = json.loads((root / diagnosis_path).read_text())
assert diagnosis["development_files_numerically_read"] == 0
compression_path = "research/reviews/ASM01-CLOSED-ARCHIVE-COMPRESSION-V1.receipt.json"
compression = json.loads((root / compression_path).read_text())
assert compression["all_paths_and_content_bytes_preserved"] and compression["files_deleted"] == 0
finished = utc_now()
free = shutil.disk_usage(root).free
remaining = 72000 - wallet["stage_b_compute_seconds_charged"]
discretionary = remaining - 47000
table = "\n".join(f"| {identifier} | {seconds} |" for identifier, seconds in charges.items())
next_step = (
    "Separate prospective preparation-only grammar conformance: allow exactly the publisher's public "
    "X/Y/STYLUS_STATE/STROKE header before PENDOWN, reject malformed/duplicate/misplaced headers, "
    "test synthetic fixtures and only the already-exposed T1 sample in the clone before any new coordinate access. "
    "Preserve failed V1/V2, models, descriptors, gates and costs. Then freeze a new intake/cohort study, "
    "verify native feasibility and clone integrity/preflight/readiness before exactly one audited five-pair "
    "three-scale nominal/adverse transfer comparison; no retry of a paid experiment."
)
report = f"""# ASM01 — cykl 321: nieważne przygotowanie native intake

Zamknięto {finished}. **INCONCLUSIVE**: intake zatrzymano przed fit badawczym,
realizacją prywatnych jednostek/seedów, rejestracją płatną i scoringiem. Nie uzyskano
nowego wyniku jakości, transferu ani ekonomii. Szerszy cel pozostaje **ACTIVE**.

## Identyfikator, kontrakty i proweniencja

Nowy EXP: **brak**; ostatni wynik nadal EXP-20261005-0007. Niezmienny plan V2:
`{study_path}`, SHA256 `{sha256_file(root / study_path)}`; task:
`{task_path}`, SHA256 `{sha256_file(root / task_path)}`. Plan V1 pozostaje
`research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json`, SHA256
`eeed8e364291320100eaf10d54788cbb29b1407b92fdf95aa0f85f257c08fa4e`.
Wspólny początek {study['study_started_at']}, deadline {study['study_deadline_at']},
180 minut, 3600 s pomocniczych obliczeń, 9000 s łącznego pełnego kosztu workerów
i najwyżej jedna rejestracja. W tym cyklu **0/1** nowych rejestracji i **0 s** fitu badawczego.

V1 zamrożono w 05ba675 przed implementacją i odczytem współrzędnych; publiczne
syntetyczne testy i przygotowany kod w 3d21ffa poprzedziły archiwum. V2 zmieniła
jedynie kanoniczne członkostwo zbioru na podstawie nazw/rozmiarów archiwum,
przed otwarciem próbki. Cały przygotowany cohort i testy zamrożono w 3cfae7f przed
intake V2. Formalny późniejszy event study_frozen wiąże status terminalnego intake
z tą wcześniejszą prerejestracją; nie jest dowodem nowego prospektywnego freeze po wyniku.
Modele, 4096 par, receptury, metryki, progi, siatki i wspólne capy nie zostały zmienione.

## OBSERVATION

Publiczny [zbiór UCI Assamese](https://archive.ics.uci.edu/dataset/208/online+handwritten+assamese+characters+dataset),
Baruah/Hazarika2015, DOI10.24432/C50C8Q, CC BY4.0, stanowi niezależną rodzinę
natywnych pomiarów pióra wobec HAR. Jedyny download: **8 067 448 B**, publisher
SHA256 `d6ad543e65269d53e38fdac6a32dd20bcd942e7616891a6cf95986894b454a4d`.
Całe archiwum: 8237 plików, w tym 8236 TXT i nieotwarty Data_Table.pdf,
66 920 184 B deklarowanej zawartości po rozpakowaniu.

V1 wykryła dodatkową obcą ścieżkę W6/15.5.TXT, 9459 B, dotyczącą autora5,
obok właściwego W5/15.5.TXT, 5572 B. Zatrzymała się na indeksie archiwum przed
ekstrakcją/liczbami. Przerejestrowana korekta V2 wyklucza wyłącznie tę obcą ścieżkę:
**45 autorów ×183 kanoniczne pliki =8235**, zero brakujących natywnych próbek,
bez zastępowania lub usuwania kanonicznych autorów. Nie pobrano archiwum ponownie.

V2 wyodrębniła tylko screen T1–5/D16–20. Pierwsza próbka T1/sample1 zatrzymała
ścisły parser na linii3: tekstowy nagłówek **X Y STYLUS_STATE STROKE** został
potraktowany jak wiersz punktu liczbowego. Bajty tej próbki **zostały otwarte**;
nie wolno opisywać tego jako braku dostępu do zawartości natywnej. Pierwszy błąd
wystąpił przed konwersją punktów liczbowych i zwróceniem deskryptorów; numerycznych
plików D nie przetworzono. Dodatkowa diagnoza czytała wyłącznie już ujawnioną
pierwszą próbkę, zapisała nazwy pól i zredagowała wartości liczbowe. Nie zmieniono
parsera ani naukowej receptury po tym odczycie. Przyszli autorzy replikacji/finału
nie byli wyodrębniani ani przetwarzani numerycznie. Brak NPZ gotowego screeningu.

Przygotowano minimalny parser, deterministyczne dwa widoki 32-punktowe/64D,
aktualizowalną pamięć z bieżącą wartością i źródłem, scoring UNKNOWN z kalibracją
tylko na T, import rzeczywistych stanów trained/untrained/shuffled/ridge ze źródła,
niezmienny dense i mocne ridge/PCA/kernel/raw/DTW. Pięć par, K16/32/64,
aktualizacje0/1/4, nominal/adverse. To przygotowany kod zweryfikowany na fiksturach,
**nie wykonany eksperyment natywny**. Stare modele HAR/PVM są niezmienione.

Przed zawartością przeszły16 przypadków V1,5 kanonicznych i28 pełnego cohortu.
Końcowe testy objęte zmianą: **28 PASS**, jedyny błąd w przebiegu29 przypadków
dotyczył starego wygenerowanego research/REPORT.md w klonie. Po odświeżeniu
tego raportu pojedynczy test lifecycle zakończył się **1/1 PASS**.
Pełny CLI `uv run --no-sync nextai lab status` w niezależnym klonie: **PASS**,
errors=[], warnings=[], bez potomków pozostających po zakończeniu procesu.
Doctor w oryginale na początku cyklu: PASS. Początkowy lab status FAIL wykrył
brak jeszcze niezamrożonych nowych ASM plików w starym manifeście; zachowano ten wynik.

Pełny zestaw regresji: **TIMEOUT**, ostatni zapisany postęp46%, brak kompletnego
JUnit. Nie jest to zaliczony przebieg. Utrwalono stdout/stderr, nadzorowane drzewo
procesów i oddzielny dowód, że po zamknięciu Job nie pozostały wskazane procesy.
Nie powtórzono pełnego zestawu, płatnego eksperymentu ani realizacji seedów.

## INTERPRETATION i CONFIDENCE

**INCONCLUSIVE** dla skuteczności i kosztów: brak porównań natywnych, brak
przedziałów ufności jakości/transferu i brak mierzalnej przewagi end-to-end.
Wysoka pewność dotyczy konkretnego błędu zgodności parsera z publicznym nagłówkiem,
kanonicznego indeksu oraz zachowania historii. Awaria nie falsyfikuje rodziny
architektur ani transferu. Zamrożona reguła zatrzymania intake pozostaje spełniona;
V1/V2 nie wolno ratować zmianą parsera i kontynuacją scoringu pod starym planem.

Wcześniejszy EXP-20261005-0007 nadal stanowi ujemny wynik tej dokładnej receptury
source-transfer HAR, z nierozstrzygniętą ekonomią przy niekompetentnej kontroli dense;
nie zamieniono go w wynik dodatni przez wybór innego zbioru. Nowe przygotowanie
ASM nie dostarcza nowego dowodu. Replikacje, świeży finał i prototyp użytkowy
fact/source/update/UNKNOWN nadal wymagają wykonania.

## Integralność, koszty i awarie

| Rozliczenie append-only | Sekundy |
|---|---:|
{table}

Łącznie **{cycle_seconds}/3600 s**, w tym wszystkie nieudane testy, intake,
ewaluacje fikstur, nadzór i konserwatywne allowance. Fikstury zawierają małe
syntetyczne fit/readout/optimizer checks, obciążone powyżej; **0 s fitu badawczego**
nie oznacza braku każdej operacji treningowej w testach. Rezerwa administracyjna
300 s obejmuje sporządzanie dokumentów, diag już ujawnionego T1, mirror i Git;
nie pomija pracy naukowej ani obliczeń zakończonych błędem.

B: **1/12 rejestracji**, **{wallet['stage_b_compute_seconds_charged']:.9f}/72000 s**;
pozostaje {remaining:.9f} s, w tym chronione **7 rejestracji/47000 s** na niezależne
replikacje, świeży finał i prototyp. Swobodny margines: {discretionary:.9f} s.
A zamknięty11/17 i35649.98936010008 s; wcześniejszy MUC03 zamknięty3 rejestracje/
2655.336484700005 s. Nie przeniesiono niewydanego A do B. Snapshot CLI klonu
obejmował nierozliczoną wtedy rezerwację450 s; końcowe liczby tutaj pochodzą z
rozliczonego append-only ledgeru. Wszystkie rezerwacje cyklu są rozliczone;
paid pending=false, maintenance, scoring=false, ready=false.

Porównano **{mirror['files_compared']} plików** w obu checkoutach; aktualne manifesty
1432 plików PASS. Poprzednie plany, wyniki, analizy, source-state ZIP i rejestry
zachowują bajty. Uprawnione zmiany harnessu i metadanych mają archiwum rodzica;
historyczne wpisy baseline i klauzule schematu pozostały identyczne. Nie ma nowego
EXP. Nie zmieniano WT8–9, harmonogramu, modeli zewnętrznych ani progów ekonomicznych.

Zachowane awarie: startup lab, V1 duplicate-member intake, pierwsza kanoniczna
fikstura z błędem importu podczas kolekcji, V2 native point grammar, pełna regresja
timeout i nieaktualny raport w29-case check. Żaden wynik nie został usunięty.

Kompresja zamkniętych własnych archiwów NTFS LZX zachowała4725 ścieżek i hashe
zawartości, zero usunięć, odzyskała **{compression['space_reclaimed_bytes']} B**.
Narzut odczytu/dekompresji nadal należy do pełnej granicy pomiaru; nie zmieniono
historycznych czasów. Wolne miejsce przy zamknięciu: **{free} B ({free/1024**3:.3f} GiB)**.
Brama10 GiB po przyszłym maksymalnym footprint320 MiB: **{'PASS' if free-320*1024**2 >= 10*1024**3 else 'BLOCKED'}**;
to migawka, wymagająca ponownego pomiaru przed instalacją/download.

## DECISION i NEXT DISCRIMINATING EXPERIMENT

**INCONCLUSIVE; zamknięcie nieudanego intake V1/V2, bez promocji i bez zamknięcia
całego celu.** Zachować recepturę i alternatywy; parser wymaga odrębnej prospektywnej
naprawy technicznej z nową wersją cohortu przed kolejnymi danymi.

Następny cykl: prerejestrowana naprawa wyłącznie publicznego nagłówka czterech
kolumn; odrzucanie błędnych/powtórzonych/przesuniętych nagłówków, syntetyczne
fikstury i tylko już ujawniony T1 w klonie, bez scoringu lub nowych próbek.
Następnie osobny freeze nowego intake/receptury, walidacja natywnej wykonalności,
integrity/preflight/readiness i dokładnie jeden audytowany EXP z pięcioma parami,
trzema skalami oraz pełnymi kontrolami. Wszystkie dotychczasowe capy i koszty
pozostają zużyte. Nie jest to retry płatnego EXP ani zmiana V1/V2 po wyniku.
"""
(root / analysis_path).write_bytes(report.encode("utf-8"))
receipt = {
    "schema_version": 1, "id": "ASM01-CYCLE321-COMPLETION-V1", "created_at": finished,
    "cycle": 321, "study_path": study_path, "study_sha256": sha256_file(root / study_path),
    "task_path": task_path, "task_sha256": sha256_file(root / task_path),
    "analysis_path": analysis_path, "analysis_sha256": sha256_file(root / analysis_path),
    "decision": "INCONCLUSIVE native intake implementation failure; no learning/transfer/economic result",
    "new_experiment_id": None, "latest_scientific_experiment_id": "EXP-20261005-0007",
    "new_registrations": 0, "new_research_fit_seconds": 0,
    "first_training_sample_bytes_opened": True, "coordinate_points_numerically_parsed": 0,
    "development_files_numerically_read": 0, "future_replication_final_files_extracted": False,
    "synthetic_fit_checks_included_in_auxiliary_charges": True, "extended_goal_completed": False,
    "cycle_auxiliary_seconds_charged": cycle_seconds, "cycle_auxiliary_cap_seconds": 3600,
    "cycle_auxiliary_charges": charges, "all_auxiliary_reservations_resolved": True,
    "program_budget_before_preparation_completion_event": wallet,
    "protected_future_compute_seconds": 47000, "protected_future_registration_attempts": 7,
    "checks_and_failures_receipt_sha256": checks,
    "intake_receipt_sha256": {p: sha256_file(root / p) for p in (intake_v1, intake_v2)},
    "grammar_diagnosis_sha256": sha256_file(root / diagnosis_path),
    "passed_changed_scope_pytest_cases": 28, "passed_refreshed_lifecycle_cases": 1,
    "affected_junit_sha256": sha256_file(affected_xml), "lifecycle_junit_sha256": sha256_file(lifecycle_xml),
    "full_regression_complete": False, "full_regression_exit_code": 124,
    "full_regression_last_recorded_percent": 46, "process_exit_proof_sha256": sha256_file(root / process_exit_path),
    "full_independent_clone_lab_CLI_pass": True, "original_startup_doctor_pass": True,
    "original_startup_lab_CLI_pass": False, "scoring": False, "benchmark_status": "maintenance",
    "mirror_proof_path": mirror_path, "mirror_proof_sha256": sha256_file(root / mirror_path),
    "compression_receipt_sha256": sha256_file(root / compression_path), "disk_free_bytes": free,
    "future320MiB_disk_snapshot_gate_pass": free-320*1024**2 >= 10*1024**3,
    "closure_script_sha256": sha256_file(Path(__file__)), "next_discriminating_experiment": next_step,
}
atomic_write_json(root / receipt_path, receipt)
state_path = root / "research/state.json"
state = json.loads(state_path.read_text())
assert state["cycle_number"] == 321 and state["completed_experiments"] == 122
state["updated_at"] = finished
atomic_write_json(state_path, state)
append_jsonl(root / "research/events.jsonl", {
    "event": "research_program_preparation_completed", "created_at": finished, "cycle": 321,
    "program_id": wallet["id"], "study_path": study_path, "study_sha256": sha256_file(root / study_path),
    "receipt_path": receipt_path, "receipt_sha256": sha256_file(root / receipt_path),
    "no_scoring": True, "extended_goal_completed": False,
})
append_jsonl(root / "research/events.jsonl", {
    "event": "bounded_research_cycle_completed", "created_at": finished, "cycle": 321,
    "program_id": wallet["id"], "experiment_id": None,
    "completion_receipt_path": receipt_path, "completion_receipt_sha256": sha256_file(root / receipt_path),
    "next_scoring_requires_new_study_freeze": True, "whole_program_complete": False,
})
closed = status(root)
assert closed["study_terminal"] and not closed["program_terminal"]
assert closed["stage_b_compute_seconds_charged"] == wallet["stage_b_compute_seconds_charged"]
assert not closed["scoring_authorized"] and closed["pending_fit_reservation_seconds"] == 0
print(json.dumps({"receipt_path": receipt_path, "cycle_seconds": cycle_seconds,
                  "B_compute_seconds": closed["stage_b_compute_seconds_charged"],
                  "B_attempts": closed["stage_b_registration_attempts_used"],
                  "future_protected_seconds": 47000, "study_terminal": True,
                  "goal_complete": False}), flush=True)
