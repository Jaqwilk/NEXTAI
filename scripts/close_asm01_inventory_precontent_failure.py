"""Close stopped inventory and synthetic-only correction; preserve every outcome."""
import ast
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
study = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.json"
correction = "research/plans/ASM01-INVENTORY-FIXTURE-ID-CONFORMANCE-V1.json"
receipt_path = "research/laboratory/ASM01-CYCLE325-COMPLETION-V1.receipt.json"
analysis_path = "research/analyses/ASM01-CYCLE325-PRECONTENT-FAILURE-V1.md"
assert not (root / receipt_path).exists() and not (root / analysis_path).exists()
assert sha256_file(root / study) == "2f01c210d0e1ea1d067106188a39660246e59e71d56a2528dfaa52b35bb9c683"
assert sha256_file(root / correction) == "bc5c5ffc63fb97291e844dec915ef1a2fa918839bc3955e73f19bfeb970340c7"
identifiers = ["startup-doctor", "startup-lab", "administration-prepaid", "precontent-seal-V1",
               "inventory-fixtures-V1", "fixture-ID-seal-V1", "inventory-fixtures-V2",
               "clone-lab-lifecycle-V1"]
records, charges = {}, {}
events = read_jsonl(root / "research/events.jsonl")
for suffix in identifiers:
    identifier = "NEXTAI-B-325-" + suffix
    relative = "research/reviews/" + identifier + ".json"
    check = json.loads((root / relative).read_text())
    charge = [e for e in events if e.get("event") == "research_program_aux_fit_charged"
              and e.get("charge_id") == identifier]
    assert len(charge) == 1 and charge[0]["seconds"] == check["seconds_charged"]
    charges[identifier] = check["seconds_charged"]
    records[relative] = sha256_file(root / relative)
    if suffix == "administration-prepaid":
        continue
    assert not check["error"] and not check["result"]["exit_job_active_process_count"]
    assert not check["result"]["exit_live_descendant_pids"]
    assert check["result"]["returncode"] == (1 if suffix == "inventory-fixtures-V1" else 0)
    for name, digest in check["raw_outputs"].items():
        assert sha256_file(root / "research/reviews" / name) == digest
assert sum(charges.values()) <= 1800
original = ET.parse(root / "research/reviews/NEXTAI-B-325-inventory-fixtures-V1.xml").getroot().find("testsuite")
cases = original.findall("testcase")
assert len(cases) == 36 and original.get("failures") == "0" and original.get("errors") == "2"
assert sum(not x.findall("failure") and not x.findall("error") for x in cases) == 35
for relative, count in (("research/reviews/NEXTAI-B-325-inventory-fixtures-V2.xml", 36),
                        ("research/reviews/NEXTAI-B-325-clone-lifecycle-V1.xml", 1)):
    suite = ET.parse(root / relative).getroot().find("testsuite")
    assert suite.get("tests") == str(count) and all(suite.get(k) == "0" for k in ("failures", "errors", "skipped"))
lab = json.loads((root / "research/reviews/NEXTAI-B-325-clone-lab-lifecycle-V1.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
plan = json.loads((root / correction).read_text())
scanner = "src/nextai_autoresearch/asm01_grammar_inventory.py"
fixtures = "tests/test_asm01_grammar_inventory.py"
assert sha256_file(root / scanner) == plan["source_and_failed_records_sha256"][scanner]
old = ast.parse((root / plan["archive_path"] / fixtures).read_text(encoding="utf-8"))
new = ast.parse((root / fixtures).read_text(encoding="utf-8"))
node = next(x for x in new.body if isinstance(x, ast.FunctionDef) and x.name == "test_input_type_bytes_and_encoding_guard")
assert ast.literal_eval(node.decorator_list[0].keywords[0].value) == ["none", "text", "over-byte-cap", "non-ascii"]
node.decorator_list[0].keywords = []
assert ast.dump(old) == ast.dump(new)
for directory in (root, clone):
    assert not any((directory / p).exists() for p in ("STOP", "PAUSE", "research/run.lock",
        "research/reviews/ASM01-INVENTORY-PRECONTENT-CONFORMANCE-V1.json",
        "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.receipt.json",
        "research/data/asm01_native_v1/screen-v3.npz"))
    previous = json.loads((directory / "research/data_manifests/ASM01-ACQUISITION-V3.json").read_text())
    assert (previous["native_files_attempted"], previous["native_files_converted"], previous["D_samples_opened"]) == (75, 74, 0)
    assert verify_manifest(directory)["ok"]
wallet = status(root)
assert not wallet["paid_run_pending"] and wallet["pending_fit_reservation_seconds"] == 0
assert wallet["protected_future_compute_seconds"] == 47000 and wallet["protected_future_registration_attempts"] == 7
assert wallet["stage_b_registration_attempts_used"] == 1 and not wallet["scoring_authorized"]
now = utc_now()
next_question = ("Preregister a NEW bounded full-screen grammar inventory binding to the unchanged conformed scanner and 36 short-ID fixtures before new native bytes. Use exactly 1830 fixed extracted screen files, T1-5/D16-20; disclose 75 prior raw exposures, 74 complete conversions and the unknown partial count for failed file 75. Preserve all V1/V2/V3 native failures and this fixture/framework failure. Inventory every row, form and lifecycle once using only redacted lexical/categorical evidence; no coordinate conversion, name emission, parser, descriptor, model, fit, scoring, download, extraction, NPZ or future writers 6-15/21-30. Freeze any concrete metadata-only repair and its synthetic accept/reject rules before code; numeric geometry or population changes require a distinct justified licensed family, not sample filtering. Then separately freeze the scientific cohort and validate native feasibility, clone freeze, preflight and readiness before exactly one audited five-pair, three-scale EXP. Keep all gates and the protected future 7 tickets/47000 s; independent replications, fresh finals and an evidence-selected prototype remain required.")
table = "\n".join(f"| {identifier} | {seconds} |" for identifier, seconds in charges.items())
report = f"""# ASM01 — cykl 325: zatrzymana inwentaryzacja przed nowymi danymi

Zamknięto {now}. Nowy EXP **brak**; ostatni EXP-20261005-0007.
**INCONCLUSIVE** dla inwentaryzacji i nauki; **KEEP** wyłącznie korektę ID i syntetyczną zgodność.
Cały cel pozostaje **ACTIVE**.

## OBSERVATION

Niezmienny plan `{study}` (SHA256 `2f01c210d0e1ea1d067106188a39660246e59e71d56a2528dfaa52b35bb9c683`)
zamrożono w 8f827f5 przed implementacją 9306352 i odczytem pozostałych 1755 tekstów.
Skaner jest czysto strukturalny; ukrywa nazwy, X/Y i niejednoznaczne argumenty markerów.
Przed testami zachowano wszystkie stare bajty naukowe i odnowiono integralność 1448 plików.

Pierwszy syntetyczny zestaw: **35/36 przypadków PASS**, jeden oversized-input z
**2 błędami setup/teardown**. Automatyczny ID zawierał payload długości 262145 znaków;
pytest próbował zapisać go w PYTEST_CURRENT_TEST, ponad limit 32767 znaków Windows.
Test limitu bajtów nie doszedł do wywołania skanera; to nie jego wynik negatywny.
XML, surowe stdout/stderr, źródło i pełny koszt 56 s zachowano bez zmian.
Zgodnie z pierwotnym failure_policy zatrzymano cały nieuruchomiony native scope.

Nowy syntetyczny kontrakt `{correction}` (SHA256 `bc5c5ffc63fb97291e844dec915ef1a2fa918839bc3955e73f19bfeb970340c7`)
zamrożono w 05bb15b przed korektą 6f61d1d. Zmieniono tylko cztery krótkie ID;
AST danych, asercji i 36 przypadków pozostał identyczny, podobnie wszystkie bajty skanera.
**36/36 PASS**, bez skip/xfail, error/failure. To odrębny test zgodności na fiksturach,
nie retry native intake/EXP i nie ponowne otwarcie zatrzymanych danych.
Klon: lifecycle **1/1 PASS** oraz pełny CLI Lab z Doctor PASS, errors=[], warnings=[].
Wszystkie nadzorowane drzewa procesów zakończono, bez żywych potomków.

**Nowe teksty ASM01: 0; konwersje: 0; NPZ: 0; fit badawczy: 0; rejestracje: 0; EXP: 0**.
Stan wcześniejszego odczytu: nadal 75 prób / 74 konwersje autora 1, D: 0.
Pozostałych 1755 tekstów, w tym 915 tekstów D, nie otwarto w tym cyklu.
Nie powtarzano pełnej regresji; historyczny timeout przy 46% w cyklu 321 pozostaje niezaliczony.

## INTERPRETATION

Zgodność skanera na jawnych fiksturach jest wsparta pełnym zestawem 36 przypadków,
redakcją wartości i ścisłym członkostwem 1830 plików. Sam zbiór ASM nadal nie jest
sprawdzony w całości. Nie znamy formy błędnego wiersza pliku 75 i nie wnioskujemy o
uczeniu, rankingu, aktualizacjach, UNKNOWN lub ekonomii z zielonych testów.

## CONFIDENCE

Wysoka dla lokalnej przyczyny błędu Windows, identyczności skanera/AST i 36 zaliczonych
fikstur. Brak dowodów o pozostałych formach ASM01, geometrii lub pięcioparowych
efektach jakości/kosztu; przedziały są **NIEOBLICZONE**, nie zerowe.

## ALTERNATIVE EXPLANATIONS

Wymagana próbka 75 może zawierać inną serializację albo błąd danych. Ten cykl tego
nie rozdzielił. Nie wolno zwężać populacji, domyślać brakujących współrzędnych lub
traktować poprawki nazw testów jako naprawy gramatyki danych ASM01.

## DECISION

**KEEP** korektę krótkich ID i techniczną zgodność 36 przypadków.
**INCONCLUSIVE** pierwotną inwentaryzację, która pozostała niewykonana po awarii frameworka.
Maintenance, scoring=false, ready=false; pełny program aktywny, bez promocji.

| Pełny koszt pomocniczy i awarie | Sekundy |
|---|---:|
{table}

Łącznie **{sum(charges.values())}/1800 s**. Wszystkie rezerwacje rozliczone.
B **1/12**, **{wallet['stage_b_compute_seconds_charged']:.12f}/72000 s**;
chronione 7 rejestracji / 47000 s, margines niechroniony
{wallet['fit_seconds_remaining']-47000:.12f} s. A i MUC zamknięte, bez resetu/kredytu.
Opisowe budget_at_freeze w planie pobrano przed kosztem 300 s administracji;
append-only ASM01-INVENTORY-BUDGET-SNAPSHOT-NOTE-V1 wyjaśnia etykietę.
Wiążące rozliczenie pochodzi z ledgeru i receipt, nie ze starego snapshotu.
Bez WT 8–9, zewnętrznych modeli/API lub zmian harmonogramu.

## NEXT DISCRIMINATING EXPERIMENT

{next_question}

Druga rodzina transferu, niezależne replikacje, świeży finał i lokalny prototyp
fact/source/update/UNKNOWN pozostają niewykonane. Cały cel nieukończony.
"""
(root / analysis_path).write_text(report, encoding="utf-8", newline="\n")
receipt = {"created_at": now, "id": "ASM01-CYCLE325-COMPLETION-V1", "cycle": 325,
    "study_path": study, "study_sha256": sha256_file(root / study),
    "correction_path": correction, "correction_sha256": sha256_file(root / correction),
    "analysis_path": analysis_path, "analysis_sha256": sha256_file(root / analysis_path),
    "closure_script_sha256": sha256_file(Path(__file__)), "checks_receipt_sha256": records,
    "junit_sha256": {f"research/reviews/{name}.xml": sha256_file(root / f"research/reviews/{name}.xml")
        for name in ("NEXTAI-B-325-inventory-fixtures-V1", "NEXTAI-B-325-inventory-fixtures-V2", "NEXTAI-B-325-clone-lifecycle-V1")},
    "cycle_auxiliary_charges": charges, "cycle_auxiliary_seconds_charged": sum(charges.values()),
    "cycle_auxiliary_cap_seconds": 1800, "all_auxiliary_reservations_resolved": True,
    "original_passed_cases": 35, "original_framework_errors": 2, "corrected_passed_cases": 36,
    "lifecycle_passed_cases": 1, "full_clone_Lab_including_Doctor_pass": True,
    "scanner_byte_identical": True, "fixture_AST_equal_except_short_IDs": True,
    "native_scope_stopped": True, "native_inventory_executed": False,
    "new_native_texts": 0, "new_numeric_conversions": 0, "D_texts_opened": 0,
    "new_research_fit_seconds": 0, "new_registrations": 0, "new_experiment_id": None,
    "latest_scientific_experiment_id": "EXP-20261005-0007", "full_regression_repeated": False,
    "protected_files": len(json.loads((root / "research/eval_manifest.json").read_text())["files"]),
    "ready": False, "scoring": False, "extended_goal_completed": False,
    "program_before_completion_event": wallet, "decision": "KEEP fixture-ID correction; INCONCLUSIVE unexecuted native inventory and science",
    "next_discriminating_experiment": next_question}
atomic_write_json(root / receipt_path, receipt)
append_jsonl(root / "research/events.jsonl", {"event": "research_program_preparation_completed", "created_at": now,
    "program_id": wallet["id"], "cycle": 325, "study_path": study, "study_sha256": sha256_file(root / study),
    "receipt_path": receipt_path, "receipt_sha256": sha256_file(root / receipt_path), "decision": receipt["decision"],
    "next_discriminating_experiment": next_question, "extended_goal_completed": False})
state = json.loads((root / "research/state.json").read_text())
assert state["cycle_number"] == 325 and state["completed_experiments"] == 122 and state["active_experiment_id"] is None
state["updated_at"] = now
atomic_write_json(root / "research/state.json", state)
final = status(root)
assert final["study_terminal"] and not final["program_terminal"] and not final["scoring_authorized"]
print(json.dumps({"receipt_path": receipt_path, "cycle_seconds": sum(charges.values()),
    "B_seconds": final["stage_b_compute_seconds_charged"], "study_terminal": True, "goal_complete": False}), flush=True)
