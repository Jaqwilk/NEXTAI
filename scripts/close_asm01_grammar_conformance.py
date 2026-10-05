"""Close failed cycle322 without modifying any completed scientific record."""
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
study_path = "research/plans/ASM01-NATIVE-GRAMMAR-CONFORMANCE-V1.json"
analysis_path = "research/analyses/ASM01-CYCLE322-GRAMMAR-CONFORMANCE-V1.md"
receipt_path = "research/laboratory/ASM01-CYCLE322-COMPLETION-V1.receipt.json"
assert not (root / analysis_path).exists() and not (root / receipt_path).exists()
assert sha256_file(root / study_path) == "2e33af01acf0fee203275a84f434279de6c5f098a6ee2178bc87fd994b7ea217"
study = json.loads((root / study_path).read_text(encoding="utf-8"))
assert datetime.now(timezone.utc) < datetime.fromisoformat(study["study_deadline_at"].replace("Z", "+00:00"))
events = [e for e in read_jsonl(root / "research/events.jsonl")
          if str(e.get("charge_id", "")).startswith("NEXTAI-B-322-")]
reserves = {e["charge_id"] for e in events if e["event"] == "research_program_aux_fit_reserved"}
charges = {e["charge_id"]: e["seconds"] for e in events if e["event"] == "research_program_aux_fit_charged"}
assert reserves == set(charges)
cycle_seconds = sum(charges.values())
assert cycle_seconds <= study["resources"]["auxiliary_test_seconds_cap"] == 1800
wallet = status(root)
assert not wallet["paid_run_pending"] and wallet["pending_fit_reservation_seconds"] == 0
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
    if item.get("result"):
        assert item["result"]["exit_job_active_process_count"] == 0
        assert not item["result"]["exit_live_descendant_pids"]
    checks[relative] = sha256_file(root / relative)
for identifier in ("startup-doctor", "startup-lab", "maintenance-seal-V1",
                   "closing-doctor-V1", "clone-grammar-fixtures-V2", "clone-lab-lifecycle-V1"):
    item = json.loads((root / f"research/reviews/NEXTAI-B-322-{identifier}.json").read_text())
    assert item["result"]["returncode"] == 0 and not item["error"]
for identifier in ("startup-lab", "clone-lab-lifecycle-V1"):
    lab = json.loads((root / f"research/reviews/NEXTAI-B-322-{identifier}.stdout.txt").read_text())
    assert not lab["errors"] and not lab["warnings"]
    assert not lab["current_scope"]["scoring_authorized"]
for filename, tests, errors in (("clone-grammar-fixtures-V1", 31, 2),
                               ("clone-grammar-fixtures-V2", 31, 0), ("clone-lifecycle-V1", 1, 0)):
    suite = ET.parse(root / f"research/reviews/NEXTAI-B-322-{filename}.xml").getroot().find("testsuite")
    assert int(suite.attrib["tests"]) == tests and int(suite.attrib["errors"]) == errors
    assert int(suite.attrib["failures"]) == 0 and int(suite.attrib["skipped"]) == 0
native_path = "research/reviews/ASM01-EXPOSED-T1-GRAMMAR-CONFORMANCE-V1.json"
native = json.loads((root / native_path).read_text())
assert native["error"] == "ValueError: Pen-up supplied state/stroke"
assert native["preserved_original_parser_error"] == "Native point grammar"
assert not native["complete"] and not native["native_array_returned"]
assert native["fit"] == 0 and not native["scoring"]
assert native["new_samples_opened"] == native["D_samples_opened"] == 0
assert native["partial_numeric_conversion_count"] == "not instrumented; authorized T1 only"
seal_path = "research/reviews/ASM01-GRAMMAR-MAINTENANCE-SEAL-V1.json"
seal = json.loads((root / seal_path).read_text())
assert seal["protected_files"] == 1434 and seal["old_headers_preserved_exactly"]
assert seal["all1432_parent_scientific_bytes_unchanged_except_permitted_metadata"]
assert sha256_file(root / "research/eval_manifest.json") == seal["manifest_sha256"]
assert sha256_file(root / "research/laboratory/preflight_certificate.json") == seal["preflight_sha256"]
finished = utc_now()
remaining = 72000 - wallet["stage_b_compute_seconds_charged"]
next_step = (
    "Preregister a bounded structural serializer diagnosis of ONLY the already-exposed T1: "
    "inventory all header/pen/numeric-row token counts and categorical marker conventions without "
    "coordinate values, new files or fit. Then prospectively freeze the complete justified grammar "
    "repair before implementation, preserve numeric bounds/geometry/models/gates, validate synthetic "
    "fixtures and T1 in the clone. Only after success freeze a NEW scientific intake/cohort before "
    "fresh native feasibility, independent clone/preflight/readiness and one audited five-pair "
    "three-scale nominal/adverse experiment. No paid retry or one-field rescue in closed cycle322."
)
table = "\n".join(f"| {identifier} | {amount} |" for identifier, amount in charges.items())
report = f"""# ASM01 — cykl322: zgodność nagłówka i nieudana próbka natywna

Zamknięto {finished}. Nowy EXP: **brak**; niezmienny plan `{study_path}`,
SHA256 `{sha256_file(root / study_path)}`. 90 minut, deadline {study['study_deadline_at']},
1800 s pomocniczych obliczeń, zero rejestracji, fitu badawczego i scoringu.
Szerszy cel pozostaje **ACTIVE**; ostatni wynik naukowy to EXP-20261005-0007.

## OBSERVATION

Prospektywny commit263c817 poprzedził implementację8993bca oraz każdy nowy test
i konwersję T1. Adapter21 linii usuwa wyłącznie jeden dokładny publiczny nagłówek
`X Y STYLUS_STATE STROKE` w zadeklarowanym miejscu, a następnie deleguje do
niezmienionego parseraV1. Zachowuje byte cap przed usunięciem, numeric/stroke rules,
deskryptory, modele, metryki, progi, siatki klasyczne i stare plany/wyniki.

Pierwszy przebieg31 przypadków miał **2 błędy infrastruktury setup/teardown**,
zero failures: pytest umieścił ponad256KiB parametru bytes w identyfikatorze testu
i przekroczył limit zmiennej środowiskowej Windows. Pozostałe30 przypadków przeszło.
Zachowano surowe logi/JUnit i dokładne źródło testu. Commit834f3fc zmienił tylko
krótkie jawne identyfikatory, bez payloadów, asercji lub parsera; skorygowany
przebieg w niezależnym klonie: **31/31 PASS**. To testy syntetyczne bez fitu.

Dokładnie jedna już ujawniona próbkaT1,10644 B, SHA256
`4c3e65ac49ff5ad55f521ab9f86b47dbaa55cfb5cd341d6d1d234ad1d4e9dfff`,
pozostała jedynym legalnym plikiem natywnym. V1 nadal odrzuca nagłówek jako
`Native point grammar`. Adapter przeszedł nagłówek, lecz ścisła walidacjaV1
zatrzymała się na **`ValueError: Pen-up supplied state/stroke`**. Nie zwrócono
tablicy ścieżki ani żadnego z trzech deskryptorów. W tym cyklu podjęto autoryzowaną
konwersję liczbT1; liczba częściowo przekonwertowanych punktów **nie była
instrumentowana i jest nieznana**. Nie wolno raportować jej jako zero.
Nowe próbki0, numeryczny dostępD0, nowa ekstrakcja0, NPZ0, fit0, scoring=false.
Nie wykonano naprawy ani ponownej próby natywnej po tym błędzie.

Startup doctor i lab oraz końcowy doctor: PASS. Końcowa kontrola niezależnego
klonu: test lifecycle **1/1 PASS**, pełny CLI lab status errors=[],warnings=[].
Wszystkie drzewa procesów zamknięte, brak żywych potomków. Bieżący manifest
**1434 pliki**; wszystkie1432 wcześniejsze chronione bajty poza pięcioma jawnie
uprawnionymi metadanymi zachowane; stare nagłówki zachowane dosłownie w archiwum.
Pełny zestaw regresji nie został wykonany ponownie; timeout46% z cyklu321 pozostaje
niezaliczonym historycznym przebiegiem, a nie dowodem pełnego pokrycia.

## INTERPRETATION

Potwierdzono wąską obsługę nagłówka w syntetycznych fiksturach. Nie potwierdzono
zgodności całego serializera wydawcy: następny warunekPEN_UP różni się od przyjętej
gramatyki. Nie uzyskano nowego wyniku jakości, UNKNOWN, aktualizacji, transferu
ani kosztu end-to-end; brak nowych estymacji i przedziałów ufności naukowych.
Awaria techniczna nie falsyfikuje architektonicznej rodziny. Ujemny wynik dokładnej
recepturyHAR w EXP-20261005-0007 oraz niekompetentna kontrola dense pozostają bez zmian.

## CONFIDENCE

Wysoka dla konkretnego odtworzonego błędu i zachowania historii. Zgodność pełnej
natywnej gramatyki pozostaje niepotwierdzona; jedna widoczna próbka nie gwarantuje
formatu innych autorów. Nie ma podstaw do ilościowej pewności transferu lub ekonomii.

## ALTERNATIVE EXPLANATIONS

Dotychczasowe fikstury odzwierciedlały założoną semantykęPEN_UP, a nie pełny
serializer wydawcy. Należy jednocześnie zinwentaryzować wszystkie rodzaje wierszy
już znanejT1 przed kolejną implementacją. Możliwe są dalsze różnice serializacji;
nie należy zgadywać kolejnego pola ani otwierać świeżych danych w zamkniętym etapie.

## DECISION

**INCONCLUSIVE** dla natywnej zgodności i wszystkich twierdzeń naukowych.
Nie spełniono prerejestrowanej reguły KEEP adaptera jako kompletnej naprawy.
Zachować wąską obsługę nagłówka i wszystkie niepowodzenia jako historię techniczną;
bez promocji, gotowości do scoringu lub ratowania starego intake po wyniku.

| Rozliczenie append-only | Sekundy |
|---|---:|
{table}

Łącznie **{cycle_seconds}/1800 s**, w tym nieudane testy i native conformance,
pełne czasy nadzoru/CLI oraz konserwatywne allowance. Administration300 s obejmuje
prereads, prerejestrację, zachowanie archiwum, mirror, raport końcowy i Git;
substantywne kontrole są dodatkowo rozliczone. Zero fitu badawczego i płatnych prób.
B: **1/12**, **{wallet['stage_b_compute_seconds_charged']:.9f}/72000 s**;
pozostało {remaining:.9f} s, w tym chronione **7 rejestracji/47000 s**. Swobodny
margines {remaining-47000:.9f} s. A pozostaje zamknięty11/17,35649.98936010008 s;
MUC03 zamknięty3 prób,2655.336484700005 s. NiewydaneA nie powiększaB.
Wszystkie rezerwacje cyklu rozliczone, maintenance, ready=false, scoring=false.
Snapshot CLI/seal mógł obejmować wtedy bieżącą rezerwację; liczby końcowe wyżej
pochodzą z rozliczonego ledgeru. WT8–9, harmonogram i modele/API zewnętrzne bez zmian.

## NEXT DISCRIMINATING EXPERIMENT

{next_step}

Przyszłe replikacje, świeży finał i minimalny prototyp fact/source/update/UNKNOWN
pozostają niewykonane. Zamknięcie tego przygotowania nie zamyka całego celu.
"""
(root / analysis_path).write_bytes(report.encode("utf-8"))
receipt = {
    "schema_version": 1, "id": "ASM01-CYCLE322-COMPLETION-V1", "created_at": finished,
    "cycle": 322, "study_path": study_path, "study_sha256": sha256_file(root / study_path),
    "analysis_path": analysis_path, "analysis_sha256": sha256_file(root / analysis_path),
    "decision": "INCONCLUSIVE native grammar; declared KEEP rule not met; no scientific result",
    "new_experiment_id": None, "latest_scientific_experiment_id": "EXP-20261005-0007",
    "new_registrations": 0, "new_research_fit_seconds": 0, "scoring": False,
    "cycle_auxiliary_seconds_charged": cycle_seconds, "cycle_auxiliary_cap_seconds": 1800,
    "cycle_auxiliary_charges": charges, "all_auxiliary_reservations_resolved": True,
    "checks_and_failures_receipt_sha256": checks,
    "native_conformance_path": native_path, "native_conformance_sha256": sha256_file(root / native_path),
    "partial_numeric_conversion_count": "unknown, not instrumented; already-exposed T1 only",
    "new_native_samples_opened": 0, "development_samples_opened": 0,
    "new_native_extraction": False, "passed_grammar_fixture_cases": 31, "passed_lifecycle_cases": 1,
    "fixture_failure_preserved": True, "full_regression_repeated": False,
    "full_independent_clone_lab_CLI_pass": True, "original_closing_doctor_pass": True,
    "maintenance_seal_path": seal_path, "maintenance_seal_sha256": sha256_file(root / seal_path),
    "protected_files": 1434, "program_budget_before_preparation_completion_event": wallet,
    "protected_future_compute_seconds": 47000, "protected_future_registration_attempts": 7,
    "extended_goal_completed": False, "next_discriminating_experiment": next_step,
    "disk_free_bytes": shutil.disk_usage(root).free,
    "closure_script_sha256": sha256_file(Path(__file__)),
}
atomic_write_json(root / receipt_path, receipt)
state_path = root / "research/state.json"
state = json.loads(state_path.read_text())
assert state["cycle_number"] == 322 and state["completed_experiments"] == 122
assert state["last_experiment_id"] == "EXP-20261005-0007" and state["active_experiment_id"] is None
state["updated_at"] = finished
atomic_write_json(state_path, state)
append_jsonl(root / "research/events.jsonl", {
    "event": "research_program_preparation_completed", "created_at": finished, "cycle": 322,
    "program_id": wallet["id"], "study_path": study_path, "study_sha256": sha256_file(root / study_path),
    "receipt_path": receipt_path, "receipt_sha256": sha256_file(root / receipt_path),
    "no_scoring": True, "extended_goal_completed": False,
})
append_jsonl(root / "research/events.jsonl", {
    "event": "bounded_research_cycle_completed", "created_at": finished, "cycle": 322,
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
                  "B_attempts": 1, "future_protected_seconds": 47000,
                  "study_terminal": True, "goal_complete": False}), flush=True)
