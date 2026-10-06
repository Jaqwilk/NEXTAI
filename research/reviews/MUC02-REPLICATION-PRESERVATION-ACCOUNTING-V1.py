"""Preserve a completed experiment and incomplete final validation; no retries."""
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path
import zipfile
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[2]
assert root.name == "NEXTAI"
relative = "research/laboratory/MUC02-REPLICATION-FINAL-ACCOUNTING-V1.receipt.json"
destination = root / relative
assert not destination.exists()
completion = load_json(root / "research/laboratory/MUC02-REPLICATION-COMPLETION-V1.receipt.json")
pre = load_json(root / "research/reviews/MUC02-REPL-preseed-conformance-V1.json")
post = load_json(root / "research/reviews/MUC02-REPL-postrun-validation-V1.json")
proof = load_json(root / "research/reviews/MUC02-REPLICATION-CLONE-POSTRUN-V1.json")
assert completion["status"] == "validated_complete"
assert pre["result"]["returncode"] == 0 and post["result"]["returncode"] == 1
assert not proof["complete"] and proof["checks"][0]["name"] == "lifecycle"
assert all(proof[k] for k in ("analysis_reproduced", "B_wallet_preserved", "ledger_prefixes_preserved", "evaluated_archive_hashes_verified"))
failure_text = (root / "research/reviews/MUC02-REPL-postrun-validation-V1.stdout.txt").read_text(encoding="utf-8")
assert "literature review is due: 6 completed experiments since the last review (cadence 6)" in failure_text
state = load_json(root / "research/state.json")
assert state["completed_experiments"] == 123 and state["last_literature_review_completed_experiments"] == 117
assert state["active_experiment_id"] is None
observed_trace = (
    "Traceback (most recent call last):\r\n"
    '  File "C:\\Users\\NATAN\\Documents\\ChatGPT\\NEXTAI\\research\\reviews\\MUC02-REPLICATION-FINAL-METADATA-V1.py", line 44, in <module>\r\n'
    "    assert changed == sorted(headers), changed\r\n"
    "           ^^^^^^^^^^^^^^^^^^^^^^^^^^\r\n"
    "AssertionError: ['AGENTS.md', 'program.md', 'research/LAB_PLAN.md']\r\n"
)
trace = root / "research/reviews/MUC02-REPLICATION-FINAL-METADATA-V1.observed-command-output.txt"
assert not trace.exists()
trace.write_bytes(observed_trace.encode("utf-8"))
evidence_files = sorted(p for p in (root / "research/reviews").glob("MUC02-REPL*") if p.is_file())
archive_path = root / "research/laboratory/archive/MUC02-REPLICATION-DIAGNOSTIC-EVIDENCE-V1.zip"
assert not archive_path.exists()
bindings = {p.relative_to(root).as_posix(): sha256_file(p) for p in evidence_files}
with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in evidence_files:
        z.write(p, p.relative_to(root).as_posix())
    import json
    z.writestr("native-byte-bindings.json", json.dumps(bindings, indent=2, sort_keys=True))
now = datetime.now(timezone.utc)
plan = load_json(root / "research/plans/MUC02-NEGATIVES-REPLICATION-20261006-V1.json")
wall = (now - datetime.fromisoformat(plan["stage_started_at"].replace("Z", "+00:00"))).total_seconds()
reserve = 300
charged = math.ceil(wall) + reserve
assert charged < 14400
incomplete = ["Postrun Doctor: not started after lifecycle failure", "Postrun Lab: not started after lifecycle failure", "Due literature review: not performed in this stopped stage"]
report_path = root / "research/analyses/EXP-20261006-0001-final-status-V1.md"
assert not report_path.exists()
report = (
    "# MUC v2: końcowy wynik i stan etapu\n\n"
    "**Decyzja naukowa: DISCARD tej zamrożonej receptury. Eksperyment jest kompletny; końcowa weryfikacja operacyjna pozostała niedokończona po awarii.**\n\n"
    "Na pięciu świeżych sparowanych seedach ranking wzrósł z 9,333% do 17,333% (+8,000 pp; CI 97,5% [−3,869; +19,869] pp). Główne dense UNKNOWN spadło z 30,000% do 15,852% (−14,148 pp; CI 97,5% [−55,633; +27,336] pp). Oba CI obejmują zero. Znana abstencja wzrosła z 0% do 9,481%, przekraczając zamrożoną bramkę +2 pp. Nie potwierdzono łącznej poprawy wyboru faktów i rozpoznawania braku odpowiedzi.\n\n"
    "Model,4096 par,192 kroki i próg0,5 pozostały niezmienione. Wszystkie 11 ról/135 prób zakończyły się poprawnie. Kontrola symboliczna uzyskała100%. Nie połączono starych wyników lub seedów,nie zastąpiono żadnej pary i nie wykonano retry. Pełna analiza oraz interpretacja zachowują również niekorzystne jednostki i różnicę między dense UNKNOWN a opisowym E2E UNKNOWN.\n\n"
    "| Koszt | Wartość |\n|---|---:|\n"
    f"| Nadzorowany fit wszystkich ról | {completion['fit_seconds_charged']:.6f}/3600 s |\n"
    f"| Pełna praca workerów | {completion['full_workers_seconds']:.6f} s |\n"
    f"| Kontroler z rejestracją | {completion['controller']['parent_wall_seconds']:.6f} s |\n"
    f"| Przed- i poeksperymentalne kontrole | {pre['wall_seconds'] + post['wall_seconds']:.6f}/1800 s |\n"
    f"| Pełny zegar etapu do rozliczenia | {wall:.3f} s ({wall/60:.2f} min) |\n"
    f"| Konserwatywnie rozliczony cały etap | {charged}/14400 s ({charged/60:.2f} min) |\n\n"
    f"Pomiar zegara obejmuje wszystkie testy,analizę,dokumentację,administrację i zachowane błędy. Rozliczenie dodaje {reserve}s na końcowy zapis,synchronizację Git i przekazanie raportu. Nie sumujemy ponownie fitu,workerów i kontrolera: to zagnieżdżone granice kosztu. Energia i pieniądze nie były mierzone.\n\n"
    "Przed treningiem przeszło67/67 testów zgodności oraz Doctor i Lab. Niezależny przegląd wyników nie wykazał błędów metryk,CI,parowania,świeżości lub kosztów. Po wykonaniu w klonie ponownie odtworzono analizę,potwierdzono hashe archiwum,prefiksy rejestrów i niezmieniony portfel B.\n\n"
    "Końcowy test cyklu życia zakończył się FAIL: `literature review is due: 6 completed experiments since the last review (cadence 6)`. Nowy wynik zwiększył licznik zakończonych eksperymentów do123; ostatni przegląd pozostaje przy117. Nie zmieniono licznika ani rytmu przeglądów. Po tym pierwszym błędzie zatrzymano dalszą sekwencję; nie uruchomiono postrun Doctor/Lab i nie powtórzono testu. Ta bramka dotyczy obowiązków utrzymania projektu po eksperymencie; źródła i wyniki naukowe zostały wcześniej poprawnie zamrożone i sprawdzone.\n\n"
    "Zachowano również administracyjny AssertionError dotyczący manifestu dokumentacji: helper błędnie oczekiwał CURRENT_STATUS.md w chronionych wpisach. Nie powtórzono helpera; osobny zapis uzgodnił istniejące bajty i potwierdził brak zmian kodu naukowego. Pełne dane obu awarii oraz oryginalne bajty diagnostyczne są w archiwum.\n\n"
    "Niedokończony zakres: końcowe Doctor/Lab oraz należny przegląd literatury. Dalsze prace wymagają osobnego zakresu; nie ma upoważnienia do ponowienia tego eksperymentu. W tej sesji nie otwierano WT8–9,przyszłych writerów ASM/HAR,nie dodawano architektur,nie używano zewnętrznych modeli/API i nie zmieniano harmonogramu.\n\n"
    "Historia i portfel B są nienaruszone:1/12 rejestracji,20098,55024020007/72000s; rezerwa7 rejestracji/47000s. Szerszy cel transferu i prototypu pozostaje aktywny. Obecna konfiguracja jest przywrócona do parent ASM01 maintenance,scoring=false.\n\n"
    f"Końcowy zapis kosztów: `{relative}`. Oryginalny raport: `research/analyses/EXP-20261006-0001.md`; interpretacja: `research/analyses/EXP-20261006-0001-interpretation-V1.md`.\n"
)
report_path.write_text(report, encoding="utf-8", newline="\n")
atomic_write_json(destination, {"created_at": utc_now(), "stage_id": completion["stage_id"], "experiment_id": completion["experiment_id"],
    "status": "scientific_complete_final_validation_incomplete", "decision": completion["decision"],
    "scientific_incomplete_scope": [], "operational_incomplete_scope": incomplete,
    "stage_started_at": plan["stage_started_at"], "accounting_cutoff_at": now.isoformat(),
    "stage_wall_seconds_measured_at_cutoff": wall, "closing_administration_reserve_seconds": reserve,
    "stage_seconds_charged_conservatively": charged, "stage_work_seconds_cap": 14400,
    "fit_seconds_charged": completion["fit_seconds_charged"], "fit_seconds_cap": 3600,
    "workers_seconds": completion["full_workers_seconds"], "controller_seconds": completion["controller"]["parent_wall_seconds"],
    "auxiliary_checks_seconds": pre["wall_seconds"] + post["wall_seconds"], "auxiliary_cap": 1800,
    "preseed_conformance_tests": {"passed": 67, "failed": 0, "Doctor": "PASS", "Lab": "PASS"},
    "postrun": {"analysis_reproduced": True, "archive_hashes_verified": True, "ledger_prefixes_preserved": True,
        "B_wallet_preserved": True, "lifecycle": "FAIL", "Doctor": "not_started", "Lab": "not_started", "failure": "literature_review_due_cadence_6", "retry": False},
    "state_counters": {"completed_experiments": 123, "last_literature_review_completed_experiments": 117, "cadence_unchanged": True},
    "prior_completion_sha256": sha256_file(root / "research/laboratory/MUC02-REPLICATION-COMPLETION-V1.receipt.json"),
    "result_sha256": completion["result_sha256"], "source_archive_sha256": completion["controller"]["source_archive_sha256"],
    "runtime_archive_sha256": completion["runtime_archive_sha256"],
    "diagnostic_archive_path": archive_path.relative_to(root).as_posix(), "diagnostic_archive_sha256": sha256_file(archive_path),
    "diagnostic_files": bindings, "raw_text_authority": "ZIP-native bytes; ordinary Git text copies may be line-ending normalized",
    "metadata_failure_trace_source": "observed exec_command output copied verbatim; failure preserved without rerunning its helper",
    "report_path": report_path.relative_to(root).as_posix(), "report_sha256": sha256_file(report_path),
    "independent_review_sha256": sha256_file(root / "research/reviews/MUC02-REPLICATION-INDEPENDENT-REVIEW-V1.json"),
    "protected_B_wallet": completion["protected_B_wallet"], "new_experiment_retry": False,
    "new_architecture": False, "WT8_9": False, "external_model_API": False, "schedule_change": False})
print(f"Preserved incomplete final validation; science DISCARD; charged stage {charged}/14400s; no retries.")
