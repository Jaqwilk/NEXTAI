"""Close cycle323 only after all owned checks and charges are settled."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI"
study_path = "research/plans/ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1.json"
repair_path = "research/plans/ASM01-SERIALIZER-METADATA-REPAIR-V1.json"
task_path = "research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json"
analysis_path = "research/analyses/ASM01-CYCLE323-SERIALIZER-CONFORMANCE-V1.md"
receipt_path = "research/laboratory/ASM01-CYCLE323-COMPLETION-V1.receipt.json"
assert not (root / analysis_path).exists() and not (root / receipt_path).exists()
assert sha256_file(root / study_path) == "8db10c6c2bd714994b86f4b83e88593ef7e90a3ab15014c258cb2e8e88a2f8ae"
assert sha256_file(root / repair_path) == "9b4d91cd42c681bf89c5dc42420a7d4f723a0de5f798674ce06825df92d04a86"
assert sha256_file(root / task_path) == "d34bf101fe22ad5fbe739d6ff05a24b96ce4939eca57720f76b8eb89063c4dd1"
study = json.loads((root / study_path).read_text())
assert datetime.now(timezone.utc) < datetime.fromisoformat(study["study_deadline_at"].replace("Z", "+00:00"))
events = [e for e in read_jsonl(root / "research/events.jsonl")
          if str(e.get("charge_id", "")).startswith("NEXTAI-B-323-")]
reserves = {e["charge_id"] for e in events if e["event"] == "research_program_aux_fit_reserved"}
charges = {e["charge_id"]: e["seconds"] for e in events if e["event"] == "research_program_aux_fit_charged"}
assert reserves == set(charges)
cycle_seconds = sum(charges.values())
assert cycle_seconds <= study["resources"]["auxiliary_test_seconds_cap"] == 2200
checks = {}
for identifier, amount in charges.items():
    relative = f"research/reviews/{identifier}.json"
    item = json.loads((root / relative).read_text())
    assert item["seconds_charged"] == amount
    for filename, digest in item.get("raw_outputs", {}).items():
        assert sha256_file(root / "research/reviews" / filename) == digest
    if item.get("result"):
        assert item["result"]["exit_job_active_process_count"] == 0
        assert not item["result"]["exit_live_descendant_pids"]
    checks[relative] = sha256_file(root / relative)
for suffix in ("startup-doctor", "startup-lab", "T1-structural-diagnosis-V1", "serializer-fixtures-V1",
               "T1-serializer-conformance-V2", "maintenance-seal-V1", "closing-doctor-V1", "clone-lab-lifecycle-V1"):
    check = json.loads((root / f"research/reviews/NEXTAI-B-323-{suffix}.json").read_text())
    assert check["result"]["returncode"] == 0 and not check["error"]
for suffix in ("startup-lab", "clone-lab-lifecycle-V1"):
    lab = json.loads((root / f"research/reviews/NEXTAI-B-323-{suffix}.stdout.txt").read_text())
    assert not lab["errors"] and not lab["warnings"] and not lab["current_scope"]["scoring_authorized"]
for suffix, count in (("serializer-fixtures-V1", 80), ("clone-lifecycle-V1", 1)):
    suite = ET.parse(root / f"research/reviews/NEXTAI-B-323-{suffix}.xml").getroot().find("testsuite")
    assert int(suite.attrib["tests"]) == count
    assert all(int(suite.attrib[k]) == 0 for k in ("errors", "failures", "skipped"))
failed = json.loads((root / "research/reviews/NEXTAI-B-323-T1-serializer-conformance-V1.json").read_text())
assert failed["result"] is None and failed["raw_outputs"] == {}
assert "Timeout must be finite and positive" in failed["error"] and failed["seconds_charged"] == 73
bound_path = "research/reviews/ASM01-STRUCTURE-PREEXEC-CONFORMANCE-BOUND-V1.json"
assert json.loads((root / bound_path).read_text())["native_parse_started_count_before_correction"] == 0
native_path = "research/reviews/ASM01-EXPOSED-T1-SERIALIZER-CONFORMANCE-V1.json"
native = json.loads((root / native_path).read_text())
assert native["complete"] and native["independent_point_reference_equal"] and native["all3_descriptors_equal"]
assert native["raw_numeric_point_rows"] == 290 and native["point_shape"] == [290, 2]
assert native["new_samples_opened"] == native["D_samples_opened"] == native["fit"] == 0
seal_path = "research/reviews/ASM01-SERIALIZER-MAINTENANCE-SEAL-V1.json"
seal = json.loads((root / seal_path).read_text())
assert seal["parent_protected_files"] == 1434 and seal["old_headers_preserved_exactly"]
assert seal["all_parent_scientific_bytes_unchanged_except_permitted_metadata"]
assert sha256_file(root / "research/eval_manifest.json") == seal["manifest_sha256"]
assert sha256_file(root / "research/laboratory/preflight_certificate.json") == seal["preflight_sha256"]
wallet = status(root)
assert wallet["pending_fit_reservation_seconds"] == 0 and not wallet["paid_run_pending"]
assert not wallet["scoring_authorized"] and not wallet["program_terminal"]
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000 and wallet["protected_future_registration_attempts"] == 7
finished = utc_now()
remaining = 72000 - wallet["stage_b_compute_seconds_charged"]
next_step = (
    "Freeze ASM01-FROZEN-SOURCE-SCREEN-V3 in a NEW bounded cycle using the prospective "
    "verified-serializer taskV3: exact existing source states/models,4096pairs/2048alignment/1024decoder, "
    "all9arms,five predefined disjoint writer pairs,K16/32/64,updates0/1/4,nominal/adverse and unchanged "
    "metrics/grids/quality/UNKNOWN/FA/economic gates. Pin remaining budget/future reserve and original "
    "intake failures/exposed-T1. Implement only delegated new-cohort/loader/acquisition wrappers, validate "
    "in independent clone before remaining native T/D content; complete all1830 screen samples without "
    "dropping/replacing failures;freeze/preflight/readiness before exactly one audited EXP. No paid retry."
)
table = "\n".join(f"| {identifier} | {amount} |" for identifier, amount in charges.items())
report = f"""# ASM01 — cykl323: kompletna diagnoza i zgodność znanejT1

Zamknięto {finished}; decyzja **KEEP wyłącznie techniczną naprawę serializera**.
Nowy EXP: **brak**. Niezmienny plan `{study_path}`, SHA256 `{sha256_file(root / study_path)}`,
oraz naprawa `{repair_path}`, SHA256 `{sha256_file(root / repair_path)}`.
120 minut, deadline{study['study_deadline_at']},2200 s pomocniczych obliczeń;
zero rejestracji, fitu badawczego i scoringu. Cel rozszerzony pozostaje **ACTIVE**.

## OBSERVATION

Plan diagnozy zamrożono w512ffc3 przed implementacjąbebd502 i ponownym otwarciemT1.
Inwentaryzacja obejmuje wszystkie300 niepuste wiersze:290 wierszy punktów,
3PEN_DOWN,3PEN_UP oraz cztery wiersze nagłówka/count/kolumn/end. Wszystkie punkty
mają cztery pola całkowite i state1; trzy dodatnie numery kresek. PEN_DOWN ma
zero dodatkowych pól; każdy PEN_UP ma tylko **0**. X/Y nie konwertowano ani
nie wypisywano w diagnozie, nazwy znaków nie stały się kluczami. D/future/new0.

ParserV1 uznawał singleton w PEN_UP za bieżący dodatni numer kreski; dlatego0
powodowało poprzedni błąd. `categorical_serial_consistent=false` w niezmienionej
diagnozie obejmuje właśnie tę starą interpretację markera; nie jest osobnym
dowodem błędnego porządku punktów. Nowy kontrakt po diagnozie zamrożono w **e7f272e**
przed implementacją **d470518**. Minimalny adapterV4 usuwa tylko singleton0 z
PEN_UP w próbce z jednym poprawnie położonym dokładnym publicznym nagłówkiem.
Bez nagłówka i dla pozostałych form zachowujeV3. Całą walidację punktów, aktywnej
kreski, liczby kresek, caps, deduplikację i geometrię nadal wykonuje niezmienionyV1.

W niezależnym klonie **80/80 PASS**:49 nowych przypadków i31 niezmienionychV3.
Obejmują legacy, singleton0, nagłówki, numery/stan/współrzędne, pen lifecycle,
caps/ASCII i degenerację, dokładne punkty i wszystkie trzy deskryptory. Bez fitu.

Pierwsze uruchomienie native conformance zatrzymało się **PRZED utworzeniem Job,
otwarciem stdout/stderr lub procesu potomnego**: rezerwacja trwała32.47 s i dla
checkcap90/overhead65 pozostał niedodatni timeout. Zachowano pełny błąd i73 s.
Prospektywny append-only addendum zwiększył tylko cap pojedynczego nadzorowanego
uruchomienia do160/timeout90 w tych samych2200 s i deadline; kod, dane, nauka,
fikstury i wszystkie stare capy/gates nie zostały zmienione. Nie było pierwszej
próby native parsera ani retry płatnego EXP. KontrolaV2 jest pierwszym uruchomionym
procesem conformance po tej naprawie administracyjnej.

Dokładnie jedna już ujawnionaT1,10644 B, SHA256
`4c3e65ac49ff5ad55f521ab9f86b47dbaa55cfb5cd341d6d1d234ad1d4e9dfff`:
**PASS**,290x2 float32,290 surowych wierszy punktów. Cała tablica równa niezależnemu
odczytowi punktów z oryginalnych wierszy z resetem na granicy kreski; trzy64D
deskryptory write/nominal/adverse identyczne bitowo i skończone. W jednym procesie
wywołano takżeV3 jako kontrolę odtworzonej awarii i niezależny odczyt referencyjny;
nie oznacza to tylko jednej operacji konwersji każdej liczby. Częściowy odczyt
punktów kontrolnegoV3 nie był instrumentowany. Wypisano tylko counts/shapes/hashes,
bez współrzędnych lub nazw. Nowe próbki0,D0,ekstrakcja0,NPZ0,fit0,scoring=false.

Oryginalny startup/closing doctor i startup lab: PASS. Klon: lifecycle **1/1 PASS**,
pełny CLI lab errors=[],warnings=[]. Wszystkie wykonane Job trees zamknięte bez
żywych potomków. Aktualny manifest **{seal['protected_files']} plików**; wszystkie
1434 wcześniejsze chronione bajty poza pięcioma uprawnionymi metadanymi zachowane.
Stare nagłówki, plany, wyniki, parseryV1/V2/V3 i źródła/model/generator pozostają
niezmienione. Pełna regresja nie była powtórzona; timeout46% z321 nadal niezaliczony.

## INTERPRETATION

Usunięto konkretną pomyłkę serializacji bez zmiany numerycznej reprezentacji.
Nie uzyskano nowego wyniku naukowego: brak nowych efektów jakości,rankingu,
aktualizacji,UNKNOWN,transferu albo ekonomii. Żadne testy techniczne nie zastępują
kompetentnej kontroli Transformer ani niezależnych pięcioparowych wyników.
EXP-20261005-0007 pozostaje DISCARD dla dokładnej receptury source-transfer HAR,
z ekonomią INCONCLUSIVE przy niekompetentnej kontroli dense.

## CONFIDENCE

Wysoka dla tej dokładnejT1 i deklarowanych syntetycznych reguł. Niepewność dotyczy
formatu i degeneracji pozostałych autorów; jedna już znana próbka nie potwierdza
całego zbioru. Nie ma nowych naukowych przedziałów ufności ani twierdzenia o transferze.

## ALTERNATIVE EXPLANATIONS

PEN_UP0 to jawny marker zamknięcia, a nie punkt z zerowym numerem kreski. Sposób
kodowania innych markerów pozostaje objęty dawną ścisłą walidacją; nowe nieznane
formy powinny zatrzymać osobny intake. Zmiana geometrii, wybór łatwiejszych autorów
lub pomijanie próbek nie są naprawą metadanych i nie zostały wykonane.

## DECISION

**KEEP wyłącznie techniczną naprawęV4**, bez promocji i bez gotowości do scoringu.
Prospektywny task `{task_path}`, SHA256 `{sha256_file(root / task_path)}`,
wiąże naprawę iT1, z `execution_authority=false`. Comparison/metrics/training/views/
independent_units są identyczne z taskV2; jawnie ujawniono znanąT1 i zachowano
nieudane intakeV1/V2. Osobny naukowy kontrakt i nowy cohort są nadal konieczne.

| Rozliczenie append-only | Sekundy |
|---|---:|
{table}

Łącznie **{cycle_seconds}/2200 s**, w tym awaria przed Job, wszystkie testy,
pełne czasy kontroli i konserwatywne allowance. Administration300 s obejmuje
prereads, kontrakty/skrypty administracyjne, archiwum, mirror/raport/Git; nie ukrywa
diagnozy, parsera lub testów. B **1/12**, **{wallet['stage_b_compute_seconds_charged']:.9f}/72000 s**;
pozostało {remaining:.9f} s, w tym chronione **7 rejestracji/47000 s**.
Swobodny margines {remaining-47000:.9f} s. A zamknięty11/17,35649.98936010008 s;
MUC03 zamknięty3/2655.336484700005 s; niewydaneA nie powiększaB. Wszystkie rezerwacje
rozliczone, maintenance, ready=false, scoring=false; snapshots seal/CLI mogły
obejmować bieżącą wtedy rezerwację, końcowe liczby pochodzą z rozliczonego ledgeru.
Bez WT8–9, zewnętrznych modeli/API, zmiany harmonogramu i płatnego retry.

## NEXT DISCRIMINATING EXPERIMENT

{next_step}

Transfer drugiej rodziny, niezależne replikacje, świeży finał i lokalny prototyp
fact/source/update/UNKNOWN nadal wymagają wykonania. Cel nie jest ukończony.
"""
(root / analysis_path).write_bytes(report.encode())
receipt = {
    "schema_version": 1, "id": "ASM01-CYCLE323-COMPLETION-V1", "created_at": finished, "cycle": 323,
    "study_path": study_path, "study_sha256": sha256_file(root / study_path),
    "repair_path": repair_path, "repair_sha256": sha256_file(root / repair_path),
    "prospective_task_path": task_path, "prospective_task_sha256": sha256_file(root / task_path),
    "analysis_path": analysis_path, "analysis_sha256": sha256_file(root / analysis_path),
    "decision": "KEEP exact technical serializer conformance; no learning/transfer/economic result",
    "new_experiment_id": None, "latest_scientific_experiment_id": "EXP-20261005-0007",
    "new_registrations": 0, "new_research_fit_seconds": 0, "scoring": False,
    "native_T1_conformance_path": native_path, "native_T1_conformance_sha256": sha256_file(root / native_path),
    "preexecution_failure_preserved": True, "preexecution_correction_sha256": sha256_file(root / bound_path),
    "executed_known_T1_conformance_jobs": 1, "new_native_samples_opened": 0, "D_samples_opened": 0,
    "native_point_shape": [290, 2], "all3_descriptor_references_equal": True,
    "old_V3_control_partial_conversion_count": "unknown, not instrumented; same T1 only",
    "passed_grammar_fixture_cases": 80, "passed_lifecycle_cases": 1,
    "full_regression_repeated": False, "full_independent_clone_lab_CLI_pass": True,
    "original_startup_and_closing_doctor_pass": True,
    "cycle_auxiliary_seconds_charged": cycle_seconds, "cycle_auxiliary_cap_seconds": 2200,
    "cycle_auxiliary_charges": charges, "all_auxiliary_reservations_resolved": True,
    "checks_and_failures_receipt_sha256": checks,
    "maintenance_seal_path": seal_path, "maintenance_seal_sha256": sha256_file(root / seal_path),
    "protected_files": seal["protected_files"], "program_budget_before_preparation_completion_event": wallet,
    "protected_future_compute_seconds": 47000, "protected_future_registration_attempts": 7,
    "disk_free_bytes": shutil.disk_usage(root).free, "extended_goal_completed": False,
    "closure_script_sha256": sha256_file(Path(__file__)), "next_discriminating_experiment": next_step,
}
atomic_write_json(root / receipt_path, receipt)
state_path = root / "research/state.json"
state = json.loads(state_path.read_text())
assert state["cycle_number"] == 323 and state["completed_experiments"] == 122 and state["active_experiment_id"] is None
state["updated_at"] = finished
atomic_write_json(state_path, state)
append_jsonl(root / "research/events.jsonl", {
    "event": "research_program_preparation_completed", "created_at": finished, "cycle": 323,
    "program_id": wallet["id"], "study_path": study_path, "study_sha256": sha256_file(root / study_path),
    "receipt_path": receipt_path, "receipt_sha256": sha256_file(root / receipt_path),
    "no_scoring": True, "extended_goal_completed": False,
})
append_jsonl(root / "research/events.jsonl", {
    "event": "bounded_research_cycle_completed", "created_at": finished, "cycle": 323,
    "program_id": wallet["id"], "experiment_id": None,
    "completion_receipt_path": receipt_path, "completion_receipt_sha256": sha256_file(root / receipt_path),
    "next_scoring_requires_new_study_freeze": True, "whole_program_complete": False,
})
closed = status(root)
assert closed["study_terminal"] and not closed["program_terminal"]
assert closed["stage_b_compute_seconds_charged"] == wallet["stage_b_compute_seconds_charged"]
assert not closed["scoring_authorized"] and closed["pending_fit_reservation_seconds"] == 0
print(json.dumps({"receipt_path": receipt_path, "cycle_seconds": cycle_seconds,
                  "B_seconds": closed["stage_b_compute_seconds_charged"], "B_attempts": 1,
                  "future_protected_seconds": 47000, "study_terminal": True, "goal_complete": False}), flush=True)
