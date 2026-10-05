"""Append-only cycle320 closure, after all bounded checks have been settled."""
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
plan_path = "research/plans/NEXTAI-FAMILY2-INTAKE-PREPARATION-V1.json"
task_path = "research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json"
analysis_path = "research/analyses/FAMILY2-CYCLE320-PREPARATION-V1.md"
receipt_path = "research/laboratory/FAMILY2-CYCLE320-COMPLETION-V1.receipt.json"
assert not (root / analysis_path).exists() and not (root / receipt_path).exists()
events = read_jsonl(root / "research/events.jsonl")
cycle_events = [e for e in events if str(e.get("charge_id", "")).startswith("NEXTAI-B-320-")]
reserved = {e["charge_id"] for e in cycle_events if e["event"] == "research_program_aux_fit_reserved"}
charges = {e["charge_id"]: e["seconds"] for e in cycle_events if e["event"] == "research_program_aux_fit_charged"}
assert reserved == set(charges)
plan = json.loads((root / plan_path).read_text())
assert sum(charges.values()) <= plan["resources"]["auxiliary_test_seconds_cap"]
wallet = status(root)
assert wallet["pending_fit_reservation_seconds"] == 0 and not wallet["paid_run_pending"]
assert not wallet["scoring_authorized"] and not wallet["program_closed"]
assert wallet["protected_future_compute_seconds"] == 47000
assert wallet["protected_future_registration_attempts"] == 7
assert wallet["stage_b_registration_attempts_used"] == 1
checks = {}
for name in charges:
    path = root / f"research/reviews/{name}.json"
    assert path.is_file(), name
    item = json.loads(path.read_text())
    assert item["seconds_charged"] == charges[name], name
    checks[path.relative_to(root).as_posix()] = sha256_file(path)
for name in ("startup-doctor", "startup-lab-cli", "clone-conformance-V3", "clone-lab-cli"):
    check = json.loads((root / f"research/reviews/NEXTAI-B-320-{name}.json").read_text())
    assert check["result"]["returncode"] == 0 and not check["error"], name
    assert not check["result"]["exit_live_descendant_pids"], name
lab = json.loads((root / "research/reviews/NEXTAI-B-320-clone-lab-cli.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
assert lab["current_scope"]["stage_b_registration_attempts_used"] == 1
assert not lab["current_scope"]["scoring_authorized"]
admin_path = "research/reviews/FAMILY2-ADMIN-MIRROR-V2.json"
admin = json.loads((root / admin_path).read_text())
assert admin["result"]["returncode"] == 0 and not admin["result"]["exit_live_descendant_pids"]
assert admin["charged_to_prepaid_id"] == "NEXTAI-B-320-metadata-administration"
checks[admin_path] = sha256_file(root / admin_path)
junit_path = root / "research/reviews/NEXTAI-B-320-clone-conformance-V3.xml"
suite = ET.parse(junit_path).getroot().find("testsuite")
assert suite is not None and int(suite.attrib["tests"]) == 39
assert all(int(suite.attrib[k]) == 0 for k in ("errors", "failures", "skipped"))
mirror_path = "research/reviews/FAMILY2-ORIGINAL-CLONE-MIRROR-V1.json"
mirror = json.loads((root / mirror_path).read_text())
assert mirror["both_current_manifests_ok"] and mirror["new_EXP"] == 0
compression = json.loads((root / "research/reviews/FAMILY2-NTFS-COMPRESSION-V1.json").read_text())
free = shutil.disk_usage(root).free
intake_footprint = 320 * 1024**2
disk_ready = free - intake_footprint >= 10 * 1024**3
finished = utc_now()
failures = ["NEXTAI-B-320-publisher-metadata", "NEXTAI-B-320-publisher-metadata-V2",
            "NEXTAI-B-320-clone-conformance", "NEXTAI-B-320-clone-conformance-V2",
            "NEXTAI-B-320-mirror-proof"]
table = "\n".join(f"| {key} | {value} |" for key, value in charges.items())
remaining = 72000 - wallet["stage_b_compute_seconds_charged"]
discretionary = remaining - 47000
report = f"""# FAMILY2 — przygotowanie cyklu 320

Zamknięto {finished}. Decyzja: **KEEP warunkową propozycję niezależnej rodziny ASM01**;
nie uzyskano nowego wyniku uczenia, transferu ani ekonomii. Szerszy cel pozostaje aktywny.

## Identyfikator i niezmienny plan

Nowy EXP: **brak**; zero rejestracji i zero fitu badawczego. Ostatni ukończony wynik
pozostaje EXP-20261005-0007. Plan przygotowania: `{plan_path}`,
SHA256 `{sha256_file(root / plan_path)}`; zamrożenie w Git 554a76c przed odczytem metadanych.
Początek {plan['study_started_at']}, deadline {plan['study_deadline_at']}, cap 120 minut/1800 s
testów i pomocniczych obliczeń. Zamknięte plany, wyniki, progi i historyczne awarie zachowano.

## OBSERVATION — co sprawdzono

Porównano wyłącznie metadane trzech publicznych źródeł. Przetworzone optdigits mają
64 wejścia i klasę, bez identyfikatora autora w wierszu: odrzucamy ten sposób intake dla
protokołu wymagającego 15 niezależnych par. Oryginalne nagłówki pozostają niezbadane;
nie dowodzimy niemożliwości całego zbioru. [Dokumentacja UCI](https://archive.ics.uci.edu/ml/machine-learning-databases/optdigits/optdigits-orig.names).

NIST SD19 `by_write` dokumentuje autorów, ale zapisany prefiks katalogu ZIP jest częściowy:
13 038 wpisów z 830 019; nie potwierdza liczności wszystkich wybranych autorów. Pozostaje
też niewyjaśniona stosowalność konkretnych warunków licencyjnych SD19. To zachowana
alternatywa, nie aktualna rodzina. [NIST](https://www.nist.gov/srd/nist-special-database-19),
[przewodnik](https://s3.amazonaws.com/nist-srd/SD19/sd19_users_guide_edition_2.pdf).

UCI Online Handwritten Assamese Characters dokumentuje **45 autorów po 183 natywne
trajektorie**, jawne numery autorów w katalogach i nazwach oraz **CC BY4.0**. Jest to
inna rodzina fizycznych pomiarów niż inercyjne HAR. [Oficjalne metadane i licencja](https://archive.ics.uci.edu/dataset/208/online+handwritten+assamese+characters+dataset).
W bieżącym cyklu nie pobrano ani nie odczytano współrzędnych, obrazów ani etykiet próbek.
Zapisano 1 643 227 B nazw/opisów/katalogu ZIP, poniżej 4 MiB capu. Dokładna długość RAR
pozostaje nieznana: HEAD nie podał Content-Length; 7.7 MB to oszacowanie wydawcy.
Surowe bajty i odzyskany opis mają osobne hashe; odzysk nie wykonywał nowych requestów.

Prospektywny dokument `{task_path}` ma SHA256 `{sha256_file(root / task_path)}`.
Przypisuje T1–5/D16–20 do screeningu, T6–10/D21–25 do niezależnej replikacji,
T11–15/D26–30 do świeżego finału; 31–45 pozostają niewykorzystani. Pięć par,
K16/32/64, aktualizacje0/1/4, warunki nominal/adverse. To pamięć konkretnych instancji,
nie OCR ani dowód transferu semantycznego. Dwa widoki są zależnymi podpróbkami jednej
trajektorii, nie niezależnymi akwizycjami. Przewidziano rzeczywiste zamrożone stany źródła
oraz kontrole untrained/shuffled z identyczną dozwoloną adaptacją, kompetentny dense,
ridge/PCA, kernel, raw i band4 DTW na tych samych publicznych widokach. Kalibracja score
plus margin będzie używać wyłącznie treningu, bez ratowania zamkniętego HAR dev.

Pełny doctor i CLI lab status w oryginale **PASS**; pełny CLI lab status w niezależnym
klonie **PASS**, bez błędów i ostrzeżeń. Końcowe 39/39 przypadków pytest **PASS**, proces
zakończył się kodem0. Oddzielnie przeszły dwa syntetyczne przypadki HEAD: długość brakująca
oraz jawna1234; nie użyto sieci ani danych docelowych. Zweryfikowano 1370 wcześniejszych
plików chronionych, zachowanie prefiksów ledgerów i dosłownych historycznych dokumentów.
Dowód końcowego lustrzanego zapisu porównał {mirror['files_compared']} plików; oryginał i
klon mają też niezmienny natywny wynik EXP-20261005-0007 i archiwum faktycznych stanów źródła.
Kod src, kandydaci, testy i schematy nie zostały zmienione w tym cyklu.

## INTERPRETATION i CONFIDENCE

KEEP dotyczy wyłącznie udokumentowanej, ograniczonej propozycji zadania. Pewność co do
publikowanych liczności/licencji/proweniencji jest duża; faktyczna zgodność archiwum,
niedegeneracja widoków i identyfikowalność instancji **nie zostały jeszcze sprawdzone**.
Wniosek o uczeniu, transferze i przewadze kosztowej pozostaje niedostępny bez eksperymentu.
Dokument tasku ma execution_authority=false. Nie implementowano generatora ani modelu
ASM01 i nie otwarto nowych danych. Ekonomiczne i naukowe bramki nie zostały osłabione.

## Koszty, awarie i integralność

| Obciążenie append-only | Sekundy |
|---|---:|
{table}

Łącznie **{sum(charges.values())}/1800 s** w cyklu, z fit badawczym **0 s**. B ma
**1/12** zużytych rejestracji i **{wallet['stage_b_compute_seconds_charged']:.9f}/72000 s**
pełnego rozliczenia; pozostaje {remaining:.9f} s, w tym chronione **7 rejestracji/47000 s**.
Niechroniony margines to {discretionary:.9f} s. A pozostaje11/17 i35649.98936010008 s;
wcześniejszy MUC03 pozostaje3 rejestracje/2655.336484700005 s. Nie przeniesiono niewydanego A do B.
Wszystkie rezerwacje pomocnicze są rozliczone. Maintenance, scoring=false, brak paid pending.

Zachowane porażki: pierwszy intake zatrzymała bramka dysku przed odczytem bajtów; drugi
zapisał surowe metadane, po czym serializer nie obsłużył brakującej długości HEAD.
Oryginalny helper i traceback zachowano; poprawka nie wymyśla długości. Pierwsza fikstura
clone-conformance miała błędny syntetyczny zakres ZIP; poprawiono ją. V2 zapisała JUnit
39/39 bez błędów, lecz proces przekroczył limit podczas końcowego sprzątania; timeout i126 s
pozostają porażką wykonania, nie PASS całego procesu. V3 z nowym lokalnym basetemp
zakończyła się poprawnie. Nie powtórzono żadnego płatnego EXP, seedów ani fitu źródła.
Pierwszy dowód mirroru zatrzymał się na swoim aktualnie powstającym pliku stderr, którego
klon jeszcze nie miał; porażka i57 s pozostają w ledgerze. Po rozliczeniu wykonania wszystkie
zamknięte pliki zostały skopiowane, a powtórna administracyjna kontrola bajtów przeszła.
Jej zmierzony czas drzewa procesu wyniósł {admin['result']['elapsed_seconds']:.6f} s i jest
objęty wcześniej opłaconym300 s allowance na mirroring/administrację, bez dodatkowego
fitu ani nowej rejestracji. To porównanie zamkniętych plików, nie nowy test naukowy.

Próba rekurencyjnego usuwania zweryfikowanych kopii tymczasowych została zablokowana przez
automatyczną politykę i niczego nie usunęła. Bezpieczna alternatywa, przezroczysta kompresja
NTFS LZX, zachowała wszystkie ścieżki i bajty 26 wyników/kopii, odzyskując3 249 840 128 B.
Koszt przyszłego odczytu/dekompresji pozostaje w pełnej granicy pomiaru; historyczne
czasy i wyniki nie zostały zmienione. Nie zmieniano pagefile ani innych ustawień systemu.
Wolne miejsce na zakończeniu: **{free} B ({free / 1024**3:.3f} GiB)**.
Po hipotetycznym capie320 MiB pozostałoby {free - intake_footprint} B;
bieżąca bramka≥10 GiB po operacji: **{'PASS' if disk_ready else 'BLOCKED'}**.
Jest to migawka; przed przyszłym pobraniem/instalacją trzeba ponownie zmierzyć wolne miejsce.
RAR jest ograniczony strumieniem10 MiB i listą/extraction128 MiB; przekroczenie lub
niebezpieczna ścieżka zatrzyma intake przed fit; żaden większy download nie jest zatwierdzony.

## DECISION i NEXT DISCRIMINATING EXPERIMENT

**KEEP warunkową propozycję ASM01**, DISCARD processed-optdigits intake w tym protokole,
NIST pozostawiony jako nieprzetestowana alternatywa. Cały cel **ACTIVE**, bez promocji
architektury i bez twierdzenia, że naprawiono wszystkie możliwe problemy projektu.

Następny odrębny, ograniczony cykl: zamrozić kompletną recepturę ASM01 przed implementacją
i współrzędnymi (parser, normalizacja, DTW, score/margin, wszystkie siatki, metryki, progi,
capy i decyzja), testować minimalne publiczne fikstury w klonie, zweryfikować jedno legalne
ograniczone intake oraz natywne liczności, następnie freeze/preflight/readiness i dokładnie
jeden audytowany EXP z pięcioma świeżymi parami, trzema skalami i mocnymi kontrolami.
Nie zastępować brakującego/degenerowanego autora po odczycie. Przyszłe numeryczne HAR,
WT8–9, zewnętrzne modele/API, source replay i zmiany harmonogramu pozostają wykluczone.
Replikacje, świeże finały, drugi rzeczywisty test transferu i prototyp fact/source/update/UNKNOWN
pozostają niezrealizowanym zakresem programu, a nie osiągniętym wynikiem tego przygotowania.
"""
(root / analysis_path).write_bytes(report.encode("utf-8"))
receipt = {
    "schema_version": 1, "id": "FAMILY2-CYCLE320-COMPLETION-V1", "created_at": finished,
    "cycle": 320, "study_path": plan_path, "study_sha256": sha256_file(root / plan_path),
    "task_path": task_path, "task_sha256": sha256_file(root / task_path),
    "analysis_path": analysis_path, "analysis_sha256": sha256_file(root / analysis_path),
    "decision": "KEEP conditional metadata-grounded ASM01 task proposal; no scientific transfer claim",
    "new_experiment_id": None, "latest_scientific_experiment_id": "EXP-20261005-0007",
    "new_registrations": 0, "new_research_fit_seconds": 0, "new_target_content_opened": False,
    "metadata_download_bytes": 1643227, "extended_goal_completed": False,
    "cycle_auxiliary_seconds_charged": sum(charges.values()), "cycle_auxiliary_cap_seconds": 1800,
    "cycle_auxiliary_charges": charges, "all_auxiliary_reservations_resolved": True,
    "program_budget_before_preparation_completion_event": wallet,
    "protected_future_compute_seconds": 47000, "protected_future_registration_attempts": 7,
    "checks_and_failures_receipt_sha256": checks, "failed_checks_preserved": failures,
    "passed_pytest_cases": 39, "pytest_complete_process_exit_code": 0,
    "junit_sha256": sha256_file(junit_path), "full_original_doctor_and_lab_CLI_pass": True,
    "full_independent_clone_lab_CLI_pass": True, "scoring": False, "benchmark_status": "maintenance",
    "mirror_proof_path": mirror_path, "mirror_proof_sha256": sha256_file(root / mirror_path),
    "metadata_only_recovery_sha256": sha256_file(root / "research/laboratory/FAMILY2-CYCLE320-METADATA-RECOVERY-V1.json"),
    "compression_receipt_sha256": sha256_file(root / "research/reviews/FAMILY2-NTFS-COMPRESSION-V1.json"),
    "disk_free_bytes": free, "future320MiB_disk_snapshot_gate_pass": disk_ready,
    "closure_script_sha256": sha256_file(Path(__file__)),
    "next_discriminating_experiment": plan["next_discriminating_experiment"],
}
atomic_write_json(root / receipt_path, receipt)
state_path = root / "research/state.json"
state = json.loads(state_path.read_text())
assert state["cycle_number"] == 320 and state["completed_experiments"] == 122
state["updated_at"] = finished
atomic_write_json(state_path, state)
append_jsonl(root / "research/events.jsonl", {
    "event": "research_program_preparation_completed", "created_at": finished, "cycle": 320,
    "program_id": wallet["id"], "study_path": plan_path, "study_sha256": sha256_file(root / plan_path),
    "receipt_path": receipt_path, "receipt_sha256": sha256_file(root / receipt_path),
    "no_scoring": True, "extended_goal_completed": False,
})
append_jsonl(root / "research/events.jsonl", {
    "event": "bounded_research_cycle_completed", "created_at": finished, "cycle": 320,
    "program_id": wallet["id"], "experiment_id": None,
    "completion_receipt_path": receipt_path, "completion_receipt_sha256": sha256_file(root / receipt_path),
    "next_scoring_requires_new_study_freeze": True, "whole_program_complete": False,
})
closed = status(root)
assert closed["study_terminal"] and not closed["program_terminal"]
assert closed["stage_b_compute_seconds_charged"] == wallet["stage_b_compute_seconds_charged"]
assert not closed["scoring_authorized"] and closed["pending_fit_reservation_seconds"] == 0
print(json.dumps({"receipt_path": receipt_path, "cycle_seconds": sum(charges.values()),
                  "B_compute_seconds": closed["stage_b_compute_seconds_charged"],
                  "B_attempts": closed["stage_b_registration_attempts_used"],
                  "future_protected_seconds": 47000, "study_terminal": True,
                  "goal_complete": False, "disk_snapshot_gate": disk_ready}), flush=True)
