"""Close complete lexical evidence with settled costs; never decode native data."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
study = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.json"
study_sha = "730a9e6843eaf085970bad82e5878dc404f400634e0c8ff18ab9af0e4c46888d"
native_path = "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.receipt.json"
analysis_path = "research/analyses/ASM01-CYCLE327-COMPLETE-INVENTORY-V1.md"
completion_path = "research/laboratory/ASM01-CYCLE327-COMPLETION-V1.receipt.json"
proposal_path = "research/plans/ASM01-POINT-SERIAL-METADATA-PROSPECTIVE-V1.json"
assert not any((root / p).exists() for p in (analysis_path, completion_path, proposal_path))
assert sha256_file(root / study) == study_sha
plan = json.loads((root / study).read_text(encoding="utf-8"))
events = read_jsonl(root / "research/events.jsonl")
suffixes = ("startup-doctor", "startup-doctor-local-cache", "startup-lab",
            "administration-prepaid", "precontent-seal-V1", "inventory-fixtures-V1",
            "fixture-proof-V1", "real-metadata-V1", "native-inventory-V1",
            "clone-lab-lifecycle-V1")
charges, checks = {}, {}
for suffix in suffixes:
    identifier = "NEXTAI-B-327-" + suffix
    relative = "research/reviews/" + identifier + ".json"
    check = json.loads((root / relative).read_text(encoding="utf-8"))
    paid = [event for event in events if event.get("event") == "research_program_aux_fit_charged"
            and event.get("charge_id") == identifier]
    assert len(paid) == 1 and paid[0]["seconds"] == check["seconds_charged"]
    charges[identifier] = check["seconds_charged"]
    checks[relative] = sha256_file(root / relative)
    if suffix == "administration-prepaid":
        continue
    assert check["error"] is None
    assert check["result"]["returncode"] == (2 if suffix == "startup-doctor" else 0)
    assert not check["result"]["exit_job_active_process_count"]
    assert not check["result"]["exit_live_descendant_pids"]
    for name, digest in check["raw_outputs"].items():
        assert sha256_file(root / "research/reviews" / name) == digest
assert sum(charges.values()) <= plan["resources"]["auxiliary_test_seconds_cap"] == 1800
for relative, count in (("research/reviews/NEXTAI-B-327-inventory-fixtures-V1.xml", 70),
                        ("research/reviews/NEXTAI-B-327-clone-lifecycle-V1.xml", 1)):
    suite = ET.parse(root / relative).getroot().find("testsuite")
    assert suite.get("tests") == str(count) and len(suite.findall("testcase")) == count
    assert all(suite.get(key) == "0" for key in ("failures", "errors", "skipped"))
lab = json.loads((root / "research/reviews/NEXTAI-B-327-clone-lab-lifecycle-V1.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
native = json.loads((root / native_path).read_text(encoding="utf-8"))
assert native["complete"] and "error" not in native
assert [native[key] for key in ("payload_read_attempts", "attempted_files", "inventoried_files",
    "known_texts_reopened", "new_texts_opened", "D_texts_opened")] == [1830, 1830, 1830, 75, 1755, 915]
assert len(native["files"]) == len(native["sample_sha256"]) == 1830
assert sum(native["row_counts"].values()) == sum(native["row_form_counts"].values()) == 407424
assert native["files_with_unknown_rows"] == 0 and native["files_with_structural_anomalies"] == 55
anomalous = [key for key, value in native["files"].items() if value["structural_anomaly_counts"]]
assert sum(int(key.split(":")[0]) < 16 for key in anomalous) == 24
assert sum(int(key.split(":")[0]) >= 16 for key in anomalous) == 31
assert native["row_form_counts"]["point_shaped|4|unsigned_integer/negative_integer/unsigned_integer/unsigned_integer"] == 3
assert [key for key, value in native["files"].items() if any("negative_integer" in form for form in value["row_form_counts"])] == ["17:74"]
for key in ("coordinate_values_converted_or_emitted", "character_names_or_unknown_tokens_emitted",
            "parsers_descriptors_models_called", "new_download_extraction_or_NPZ", "scoring"):
    assert native[key] is False
assert native["numeric_native_conversions"] == native["research_fit_seconds"] == native["new_EXPs"] == 0
manifest = json.loads((root / "research/eval_manifest.json").read_text())
assert len(manifest["files"]) == 1453
integrity = {}
for label, directory in (("original", root), ("clone", clone)):
    for relative, digest in manifest["files"].items():
        assert sha256_file(directory / relative) == digest, relative
    if label == "clone":
        integrity[label] = verify_manifest(directory)
        assert integrity[label]["ok"]
    else:
        excluded = sorted(path.relative_to(root).as_posix()
                          for parent in (root / "src", root / "tests")
                          for path in parent.rglob("*.py")
                          if path.relative_to(root).as_posix() not in manifest["files"])
        integrity[label] = {"ok": True, "files_checked": 1453,
            "scope": "Exact frozen1453 checksums; separately authorized new MUC source excluded",
            "strict_current_discovery_asserted": False, "unfrozen_source_files_excluded": excluded}
    assert not any((directory / p).exists() for p in ("STOP", "PAUSE", "research/run.lock",
        "research/data/asm01_native_v1/screen-v3.npz"))
    for relative, digest in plan["parent_reference_sha256"].items():
        assert sha256_file(directory / relative) == digest
    assert sha256_file(directory / native_path) == sha256_file(root / native_path)
    old = json.loads((directory / "research/data_manifests/ASM01-ACQUISITION-V3.json").read_text())
    assert (old["native_files_attempted"], old["native_files_converted"], old["D_samples_opened"]) == (75, 74, 0)
wallet = status(root)
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000 and wallet["protected_future_registration_attempts"] == 7
assert not wallet["paid_run_pending"] and wallet["pending_fit_reservation_seconds"] == 0
now = utc_now()
next_question = ("Prospectively freeze a NEW bounded metadata-only serialization study before code or renewed native access: explicit monotonically nondecreasing positive point stroke IDs are authoritative, all X/Y/state/serial rows and order retained, declared empty strokes preserved. Only literal coordinate -0 may alias0; reject every other signed coordinate or ambiguous/nonmonotone/out-of-range ID. Require exact old accepted-array and write/nominal/adverse descriptor equality, unchanged dedup/geometry/bounds/byte caps, complete1830 hash-bound feasibility and no filtering before a separately frozen scientific cohort/readiness/one audited EXP. Negative lexical Y remains numerically unknown. Any nonzero signed value, impossible geometry, changed old array or ambiguous IDs closes this exact route without rescue; assess a distinct licensed native family prospectively. Current user-requested independent MUC stage is separate and does not rewrite ASM results. Preserve future7tickets/47000s and full transfer/replication/fresh-final/prototype goal.")
proposal = {"schema_version": 1, "id": "ASM01-POINT-SERIAL-METADATA-PROSPECTIVE-V1",
    "created_at": now, "cycle_prepared": 327, "study_kind": "proposal_only",
    "execution_authority": False, "requires_new_active_bounded_contract_before_code_or_native_access": True,
    "parent_study_path": study, "parent_study_sha256": study_sha,
    "inventory_receipt_path": native_path, "inventory_receipt_sha256": sha256_file(root / native_path),
    "negative_Y_numeric_values_known": False, "coordinate_conversions": 0, "research_fit_allocated": 0,
    "registration_attempts_allocated": 0, "repair_implemented": False,
    "question": "Can explicit point serial metadata and a literal signed-zero alias preserve the frozen global geometry without dropping any point or sample?",
    "recipe": next_question, "preserved_screen_UIDs": 1830, "prior_lexical_text_exposures": 1830,
    "prior_complete_numeric_conversions": 74, "partial_failed_conversion_points_unknown": True,
    "byte_caps": {"per_file": 262144, "aggregate": 479723520},
    "semantic_limitations": ["Serial histogram does not prove chronological monotonicity",
        "Marker changes can alter consecutive-coordinate dedup and even/odd view parity",
        "Literal -0 alias is an explicitly disclosed raw-token exception; nonzero signed Y remains unobserved",
        "Metadata repair is not evidence of physical stroke semantics, learning, transfer or economics"],
    "protected_future_compute_seconds": 47000, "protected_future_registration_attempts": 7,
    "whole_goal_completed": False}
atomic_write_json(root / proposal_path, proposal)
table = "\n".join(f"| {identifier} | {seconds} |" for identifier, seconds in charges.items())
report = f"""# ASM01 — cykl327: pełna inwentaryzacja struktury

Zamknięto {now}. Nowy EXP: **brak**; ostatni EXP-20261005-0007.
Plan `{study}`, SHA256 `{study_sha}`. Prerejestracja cfc8667; źródło fce7d49,
70-case proof05e57ed i pełny dowód metadanych8fecc22 poprzedzają jedyny odczyt.
Pełny cel pozostaje **ACTIVE**; maintenance, scoring=false.

## OBSERVATION

W niezależnym klonie zakończono **1830/1830** plików i **407424/407424** niepustych
wierszy; każdy wiersz ma kategorię i zapis formy. Nieznane wiersze: **0**.
Ponownie otwarto75 znanych tekstów, pierwszy raz1755; D:915. Wszystkie1830 SHA zachowano.
389510 wierszy ma formę punktową,5304 PEN_DOWN,5290 PEN_UP i po1830 czterech nagłówków.
Nie odczytano numerycznie X/Y; nie wykonano parsera, modelu, NPZ, fitu lub rejestracji.

**55 plików ma anomalie**: T24, D31. Liczniki wierszy/zdarzeń: incomplete lifecycle19,
pen-up-without-stroke2, repeated-down1, point-outside-stroke33, serial-mismatch345,
point-lexical-form3. Te liczniki nie oznaczają niezależnych jednostek lub błędnych współrzędnych.
W1/sample75 ma pojedynczy punkt stanu1/serial2 po adnotacji PEN_UP; zachowano pełny rekord.
Jedynie W17/sample74 zawiera3 formy Y=`negative_integer`. Konkretne tokeny i wartości są
**nieznane**: forma obejmuje także `-0`. Nie stwierdzono ujemnej wartości numerycznej.

**70/70** syntetycznych przypadków i **1/1** lifecycle PASS. Pełny końcowy Lab,
w tym Doctor: errors=[],warnings=[]. Hash wszystkich **1453 zamrożonych** plików obu kopii PASS;
pełny manifest klonu PASS. Nowe, odrębnie zatwierdzone pliki MUC w oryginale są poza cyklem327;
nie sprawdzano ich przez dawną ścisłą listę i nie użyto ich w końcowym jobie klonu.
Pierwszy startup Doctor nie uruchomił kontroli przez odmowę domyślnego cacheuv;
exit2 i pełne54s zachowano. Osobno zamrożona lokalna ścieżka cache przeszła kontrolę.
Wszystkie nadzorowane drzewa zakończone bez żywych potomków. Pełnej regresji nie powtarzano;
timeout46% z cyklu321 pozostaje niezaliczony. Dawny intake75prób/74konwersje/D0 niezmieniony.

## INTERPRETATION

Alias końcowego `.txt`/`.TXT` zachował wszystkie UID i umożliwił pełną strukturę.
Niektóre adnotacje pióra są niespójne z jawnym polem stroke. Jest to diagnoza serializacji,
nie wynik uczenia, UNKNOWN lub kosztu inferencji. Nie ma nowego wyniku naukowego ani CI.

## CONFIDENCE

Wysoka dla kompletności tej skończonej inwentaryzacji i form leksykalnych. Nieustalona
dla wartości podpisanych Y, monotoniczności wszystkich seriali, geometrii i skutków transferu.
Histogram seriali nie zachowuje kolejności. Przyszła korekta granic może zmienić deduplikację,
liczbę punktów i parzystość widoków; nie wolno nazywać jej równoważną bez testu zgodności.

## DECISION

**KEEP** kompletną strukturę i walidację techniczną; **INCONCLUSIVE** porównanie naukowe.
Zapisano wyłącznie przyszłą propozycję `{proposal_path}`; bez implementacji lub retry.
Tylko literalne `-0→0` może być jawnie dopuszczoną reprezentacją tego samego zera.
Nie wolno akceptować innych znaków, clamp/abs/offset ani usuwać próbek/punktów.
Niewykonalność konkretnych bramek zamyka ten przepis i uzasadnia odrębną licencjonowaną rodzinę.

| Pełny koszt pomocniczy, w tym nieudany startup | Sekundy |
|---|---:|
{table}

Łącznie **{sum(charges.values())}/1800s**; rezerwacje rozliczone. B: **1/12**, **{wallet['stage_b_compute_seconds_charged']:.12f}/72000s**.
Chronione **7rejestracji/47000s**; margines niechroniony **{wallet['fit_seconds_remaining']-47000:.12f}s**.
A i MUC pozostają zamknięte i zużyte. Bez WT8–9, zewnętrznych modeli/API i zmiany harmonogramu.

## NEXT DISCRIMINATING EXPERIMENT

{next_question}

Druga rodzina, niezależne replikacje, świeże finały i lokalny prototyp nadal wymagają dowodów.
"""
(root / analysis_path).write_text(report, encoding="utf-8", newline="\n")
receipt = {"created_at": now, "id": "ASM01-CYCLE327-COMPLETION-V1", "cycle": 327,
    "study_path": study, "study_sha256": study_sha, "analysis_path": analysis_path,
    "analysis_sha256": sha256_file(root / analysis_path), "closure_script_sha256": sha256_file(Path(__file__)),
    "checks_receipt_sha256": checks, "cycle_auxiliary_charges": charges,
    "cycle_auxiliary_seconds_charged": sum(charges.values()), "cycle_auxiliary_cap_seconds": 1800,
    "all_auxiliary_reservations_resolved": True, "native_receipt_sha256": sha256_file(root / native_path),
    "synthetic_passed_cases": 70, "lifecycle_passed_cases": 1, "full_clone_Lab_including_Doctor_pass": True,
    "native_attempt_consumed": True, "native_inventory_complete": True, "inventoried_texts": 1830,
    "new_lexical_text_exposures": 1755, "known_lexical_texts_reopened": 75, "D_lexical_texts": 915,
    "inventoried_nonempty_rows": 407424, "files_with_anomalies": 55, "anomalous_T_files": 24,
    "anomalous_D_files": 31, "negative_Y_lexical_forms": 3, "negative_Y_numeric_values_known": False,
    "new_numeric_conversions": 0, "new_research_fit_seconds": 0, "new_registrations": 0,
    "new_experiment_id": None, "latest_scientific_experiment_id": "EXP-20261005-0007",
    "repair_implemented": False, "full_regression_repeated": False, "protected_files": 1453,
    "manifest_verification": integrity, "ready": False, "scoring": False,
    "program_before_completion_event": wallet, "extended_goal_completed": False,
    "prospective_recipe_path": proposal_path, "prospective_recipe_sha256": sha256_file(root / proposal_path),
    "decision": "KEEP complete lexical inventory and technical conformance; INCONCLUSIVE science",
    "next_discriminating_experiment": next_question}
atomic_write_json(root / completion_path, receipt)
append_jsonl(root / "research/events.jsonl", {"event": "research_program_preparation_completed", "created_at": now,
    "program_id": wallet["id"], "cycle": 327, "study_path": study, "study_sha256": study_sha,
    "receipt_path": completion_path, "receipt_sha256": sha256_file(root / completion_path),
    "decision": receipt["decision"], "next_discriminating_experiment": next_question,
    "extended_goal_completed": False})
state = json.loads((root / "research/state.json").read_text())
assert state["cycle_number"] == 327 and state["completed_experiments"] == 122 and state["active_experiment_id"] is None
state["updated_at"] = now
atomic_write_json(root / "research/state.json", state)
final = status(root)
assert final["study_terminal"] and not final["program_terminal"] and not final["scoring_authorized"]
print(json.dumps({"receipt_path": completion_path, "cycle_seconds": sum(charges.values()),
    "B_seconds": final["stage_b_compute_seconds_charged"], "study_terminal": True, "goal_complete": False}), flush=True)
