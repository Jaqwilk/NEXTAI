"""Close the consumed V2 scope failure; never reopen native content."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
study = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.json"
proposal = "research/plans/ASM01-EXTENSION-CASE-REPAIR-PROSPECTIVE-V1.json"
native = "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.receipt.json"
diagnosis = "research/reviews/ASM01-INVENTORY-V2-EXTENSION-CASE-DIAGNOSIS-V1.json"
receipt_path = "research/laboratory/ASM01-CYCLE326-COMPLETION-V1.receipt.json"
analysis_path = "research/analyses/ASM01-CYCLE326-MEMBERSHIP-FAILURE-V1.md"
assert not (root / receipt_path).exists() and not (root / analysis_path).exists()
assert sha256_file(root / study) == "6351509210dc6ad6f4247665db14ea50aba70e79a6f9dc46b2b0c654e6254726"
assert sha256_file(root / proposal) == "6ec1001b6ea667dcc9e6b3582516cfb39483d71dff5cee48dc0f11373ee483f8"
suffixes = ("startup-doctor", "startup-lab", "administration-prepaid", "precontent-seal-V1",
            "inventory-fixtures-V1", "native-inventory-V1", "extension-case-diagnosis-V1",
            "clone-lab-lifecycle-V1")
events = read_jsonl(root / "research/events.jsonl")
charges, checks = {}, {}
for suffix in suffixes:
    identifier = "NEXTAI-B-326-" + suffix
    relative = "research/reviews/" + identifier + ".json"
    check = json.loads((root / relative).read_text())
    paid = [e for e in events if e.get("event") == "research_program_aux_fit_charged"
            and e.get("charge_id") == identifier]
    assert len(paid) == 1 and paid[0]["seconds"] == check["seconds_charged"]
    charges[identifier] = check["seconds_charged"]
    checks[relative] = sha256_file(root / relative)
    if suffix == "administration-prepaid":
        continue
    assert not check["error"] and not check["result"]["exit_job_active_process_count"]
    assert not check["result"]["exit_live_descendant_pids"]
    assert check["result"]["returncode"] == (1 if suffix == "native-inventory-V1" else 0)
    for name, digest in check["raw_outputs"].items():
        assert sha256_file(root / "research/reviews" / name) == digest
assert sum(charges.values()) <= 1800
for relative, count in (("research/reviews/NEXTAI-B-326-inventory-fixtures-V1.xml", 42),
                        ("research/reviews/NEXTAI-B-326-clone-lifecycle-V1.xml", 1)):
    suite = ET.parse(root / relative).getroot().find("testsuite")
    assert suite.get("tests") == str(count) and len(suite.findall("testcase")) == count
    assert all(suite.get(k) == "0" for k in ("failures", "errors", "skipped"))
lab = json.loads((root / "research/reviews/NEXTAI-B-326-clone-lab-lifecycle-V1.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
failed = json.loads((root / native).read_text())
assert failed["error"] == "ValueError: Exactly the frozen1830 canonical members required"
assert not failed["complete"]
assert all(failed[k] == 0 for k in ("attempted_files", "inventoried_files", "known_texts_reopened",
                                  "new_texts_opened", "D_texts_opened", "numeric_native_conversions"))
diag = json.loads((root / diagnosis).read_text())
assert diag["listed_names"] == diag["disk_files"] == 1830
assert diag["uppercase_extension_by_writer"] == {"W5": 153}
assert diag["listing_and_disk_raw_names_identical"] and diag["extension_only_bijection_preserves_all_UIDs"]
assert diag["normalized_name_collisions"] == 0 and not diag["repair_implemented"]
plan = json.loads((root / study).read_text())
for directory in (root, clone):
    assert verify_manifest(directory)["ok"]
    assert not any((directory / p).exists() for p in ("STOP", "PAUSE", "research/run.lock",
        "research/reviews/ASM01-INVENTORY-PRECONTENT-CONFORMANCE-V1.json",
        "research/data/asm01_native_v1/screen-v3.npz"))
    for relative, digest in plan["parent_reference_sha256"].items():
        assert sha256_file(directory / relative) == digest
    old = json.loads((directory / "research/data_manifests/ASM01-ACQUISITION-V3.json").read_text())
    assert (old["native_files_attempted"], old["native_files_converted"], old["D_samples_opened"]) == (75, 74, 0)
wallet = status(root)
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000 and wallet["protected_future_registration_attempts"] == 7
assert not wallet["paid_run_pending"] and wallet["pending_fit_reservation_seconds"] == 0
next_question = ("Activate a NEW bounded full-screen inventory contract before code or native bytes, using the frozen recipe ASM01-EXTENSION-CASE-REPAIR-PROSPECTIVE-V1. Accept only final .txt/.TXT aliases in BOTH pinned listing and actual extracted metadata; preserve all1830 UID/actual-path bijections, fixed order, links/outside/duplicate/foreign/byte guards and unchanged scanner. Validate the complete real1830-name metadata before payload, in addition to synthetic cases. Then at most one full lexical inventory; no coordinates, numerical parser, model, fit, filtering or native retry. Preserve the consumed V1 fixture and V2 membership failures and75 prior raw/74 numerical exposures. Use the complete grammar evidence to freeze any concrete metadata-equivalent serializer repair and a separate five-pair, three-scale scientific cohort before code/data/one audited EXP. Keep all scientific gates and protected7tickets/47000s; whole transfer, replication, fresh-final and prototype goal remains active.")
now = utc_now()
table = "\n".join(f"| {identifier} | {seconds} |" for identifier, seconds in charges.items())
report = f"""# ASM01 — cykl 326: błąd członkostwa przed odczytem danych

Zamknięto {now}. Nowy EXP: **brak**; ostatni EXP-20261005-0007.
Plan `{study}`, SHA256 `6351509210dc6ad6f4247665db14ea50aba70e79a6f9dc46b2b0c654e6254726`.
Zamrożony w b3c0071 przed implementacją 20f0c31; dowód zgodności w 7a650c2 przed odczytem.
Cały cel pozostaje **ACTIVE**.

## OBSERVATION

**42/42 testy syntetyczne PASS**, bez skip/error/failure; 36 dawnych przypadków i 6 nowych
kontroli powiązań. Funkcje skanera nie zmieniły się; AST uruchomienia różni się wyłącznie
zadeklarowanymi powiązaniami i polami hash. Syntetyczne nazwy miały rozszerzenie `.txt`.

Pojedyncze uruchomienie inwentaryzacji zakończyło się błędem
`Exactly the frozen1830 canonical members required`, **przed odczytem pierwszego payloadu**.
Attempted/inventoried/known-reopened/new/D: **0/0/0/0/0**. Pełne stdout/stderr,
niekompletny receipt, commit i koszt **54 s** zachowano. Nie powtórzono odczytu.

Pełna diagnoza samych nazw potwierdziła **1830 pozycji listy = 1830 plików na dysku**.
Ich surowe zestawy są identyczne; 153 pliki autora **W5** mają `.TXT`, pozostałe `.txt`.
Zmiana wyłącznie końcowego rozszerzenia daje dokładnie wszystkie 1830 zamrożonych UID,
bez kolizji, braków, obcych członków albo linków. Pierwotna lista nie została zmieniona.
Metadane `stat`: maksimum **25086 B**, suma **14394085 B**; oba dotychczasowe limity spełnione.

Klon lifecycle **1/1 PASS**, pełny CLI Lab z Doctor: errors=[], warnings=[].
Integralność **1450** chronionych plików potwierdzona w obu kopiach.
Wszystkie nadzorowane drzewa procesów zakończone, bez żywych potomków.
Nowe teksty/współrzędne/konwersje/NPZ/fit badawczy/rejestracje/EXP: **0**.
Wcześniejszy intake nadal 75 prób / 74 konwersje autora 1, D: 0; forma błędnego pliku 75 nieznana.
Pełnej regresji nie powtarzano; timeout przy 46% w cyklu 321 pozostaje niezaliczony.

## INTERPRETATION

To niedopasowanie walidatora nazw do zachowanej pisowni wydania. Wszystkie zadeklarowane
UID są obecne. Zielone fikstury z samym `.txt` nie dowodziły zgodności z realną listą.
Nie ma wyników o gramatyce pozostałych tekstów, uczeniu, rankingu, aktualizacjach,
UNKNOWN lub ekonomii. Nie jest to negatywny wynik transferu albo architektury.

## CONFIDENCE

Wysoka dla dokładnej przyczyny gate failure i bijekcji 153 aliasów rozszerzenia,
potwierdzonej na całej liście i wszystkich nazwach na dysku. Brak nowych pomiarów jakości;
sparowane przedziały naukowe są **NIEOBLICZONE**, a nie zerowe.

## ALTERNATIVE EXPLANATIONS

Po poprawce nazw nadal mogą istnieć niezgodne wiersze, stany, geometria albo inne błędy
danych. Metadane nazw i bajtów tego nie rozstrzygają. Nie wolno usuwać próbek lub
poszerzać reguł współrzędnych na podstawie tego wyniku.

## DECISION

**KEEP** 42-case zgodność syntetyczną i pełną diagnozę nazw.
**INCONCLUSIVE** inwentaryzację tekstów i porównanie naukowe; scope zatrzymany bez retry.
Konkretny przyszły przepis: `{proposal}`, SHA256
`6ec1001b6ea667dcc9e6b3582516cfb39483d71dff5cee48dc0f11373ee483f8`.
To propozycja wymagająca nowego aktywnego, ograniczonego kontraktu; nie wykonano poprawki
ani nie otwarto ponownie V2. Maintenance, scoring=false, ready=false.

| Pełny koszt pomocniczy, w tym awaria | Sekundy |
|---|---:|
{table}

Łącznie **{sum(charges.values())}/1800 s**; wszystkie rezerwacje rozliczone.
B: **1/12**, **{wallet['stage_b_compute_seconds_charged']:.12f}/72000 s**.
Chronione **7 rejestracji / 47000 s**; margines niechroniony
**{wallet['fit_seconds_remaining']-47000:.12f} s**. A i MUC zamknięte, bez resetu lub kredytu.
Bez WT 8–9, zewnętrznych modeli/API i zmian harmonogramu.

## NEXT DISCRIMINATING EXPERIMENT

{next_question}

Druga rodzina transferu, niezależne replikacje, świeży finał i lokalny prototyp
fact/source/update/UNKNOWN pozostają niewykonane. Cały cel jest nieukończony.
"""
(root / analysis_path).write_text(report, encoding="utf-8", newline="\n")
receipt = {"created_at": now, "id": "ASM01-CYCLE326-COMPLETION-V1", "cycle": 326,
    "study_path": study, "study_sha256": sha256_file(root / study),
    "analysis_path": analysis_path, "analysis_sha256": sha256_file(root / analysis_path),
    "closure_script_sha256": sha256_file(Path(__file__)), "checks_receipt_sha256": checks,
    "native_receipt_sha256": sha256_file(root / native), "diagnosis_sha256": sha256_file(root / diagnosis),
    "prospective_recipe_path": proposal, "prospective_recipe_sha256": sha256_file(root / proposal),
    "cycle_auxiliary_charges": charges, "cycle_auxiliary_seconds_charged": sum(charges.values()),
    "cycle_auxiliary_cap_seconds": 1800, "all_auxiliary_reservations_resolved": True,
    "synthetic_passed_cases": 42, "lifecycle_passed_cases": 1, "full_clone_Lab_including_Doctor_pass": True,
    "native_attempt_consumed": True, "native_inventory_complete": False, "native_scope_stopped": True,
    "new_native_texts": 0, "new_numeric_conversions": 0, "D_texts_opened": 0,
    "uppercase_extension_files": 153, "fixed_UIDs_preserved_by_proposed_alias": 1830,
    "repair_implemented": False, "new_research_fit_seconds": 0, "new_registrations": 0,
    "new_experiment_id": None, "latest_scientific_experiment_id": "EXP-20261005-0007",
    "full_regression_repeated": False, "protected_files": 1450, "ready": False, "scoring": False,
    "program_before_completion_event": wallet, "extended_goal_completed": False,
    "decision": "KEEP metadata diagnosis and synthetic conformance; INCONCLUSIVE stopped native inventory and science",
    "next_discriminating_experiment": next_question}
atomic_write_json(root / receipt_path, receipt)
append_jsonl(root / "research/events.jsonl", {"event": "research_program_preparation_completed", "created_at": now,
    "program_id": wallet["id"], "cycle": 326, "study_path": study, "study_sha256": sha256_file(root / study),
    "receipt_path": receipt_path, "receipt_sha256": sha256_file(root / receipt_path),
    "decision": receipt["decision"], "next_discriminating_experiment": next_question,
    "extended_goal_completed": False})
state = json.loads((root / "research/state.json").read_text())
assert state["cycle_number"] == 326 and state["completed_experiments"] == 122 and state["active_experiment_id"] is None
state["updated_at"] = now
atomic_write_json(root / "research/state.json", state)
final = status(root)
assert final["study_terminal"] and not final["program_terminal"] and not final["scoring_authorized"]
print(json.dumps({"receipt_path": receipt_path, "cycle_seconds": sum(charges.values()),
    "B_seconds": final["stage_b_compute_seconds_charged"], "study_terminal": True, "goal_complete": False}), flush=True)
