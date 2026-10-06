"""Reproduce frozen analysis, preserve runtime and restore the unchanged B wallet."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import zipfile
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.muc02_replication_stage import status, ID, PLAN, PLAN_SHA256
from nextai_autoresearch.research_program import status as program_status
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
archive = root / "research/laboratory/archive/MUC02-REPLICATION-parent-V1"
completion_path = root / "research/laboratory/MUC02-REPLICATION-COMPLETION-V1.receipt.json"
assert not completion_path.exists()
controller = load_json(root / "research/reviews/MUC02-REPLICATION-EXPERIMENT-CONTROLLER-V1.json")
identity = controller["experiment_id"]
assert identity
assert (clone / f"research/results/{identity}.json").is_file()
parent = load_json(archive / "parent-bindings.json")
ledger_names = ("events.jsonl", "experiments.tsv", "plan_registry.jsonl", "plan_status_events.jsonl")
for name in ledger_names:
    source = clone / "research" / name
    original = root / "research" / name
    old = parent["ledger_prefixes"][name]
    import hashlib
    assert hashlib.sha256(source.read_bytes()[:old["bytes"]]).hexdigest() == old["sha256"], name
    assert hashlib.sha256(original.read_bytes()[:old["bytes"]]).hexdigest() == old["sha256"], name
    assert source.read_bytes().startswith(original.read_bytes()), name
    shutil.copyfile(source, original)
for relative in (f"research/plans/{identity}.json", f"research/results/{identity}.json", "research/state.json"):
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists() or relative == "research/state.json"
    shutil.copyfile(clone / relative, destination)
result_path = root / f"research/results/{identity}.json"
result = load_json(result_path)
assert verify_manifest(root)["ok"] and verify_manifest(clone)["ok"]
stage = status(root)
assert stage["terminal"] and stage["registrations_used"] == stage["executions_started"] == 1
module_path = root / "scripts/analyze_muc02_hard_negatives.py"
spec = importlib.util.spec_from_file_location("muc02_frozen_analysis", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
evidence = module.analyze(root, identity)
analysis_relative = f"research/reviews/{identity}-paired-analysis.json"
assert not (root / analysis_relative).exists()
atomic_write_json(root / analysis_relative, evidence)
runtime_path = root / "research/laboratory/archive/MUC02-REPLICATION-RUNTIME-V1.zip"
assert not runtime_path.exists()
with zipfile.ZipFile(runtime_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted((clone / "research/tmp" / identity).glob("*")):
        if p.is_file():
            z.write(p, p.relative_to(clone).as_posix())
    for p in sorted((clone / "research/logs").glob(identity + "-*")):
        z.write(p, p.relative_to(clone).as_posix())
proposals = []
for p in (clone / "research/tmp" / identity).glob("*.data.jsonl"):
    proposals += read_jsonl(p)
checks = [load_json(p) for p in (root / "research/reviews").glob("MUC02-REPL-*.json") if not p.name.endswith(".started.json")]
old_wallet = parent["B_wallet"]
decision = evidence["decision"]["decision"]
means = evidence["arm_means"]
contrasts = evidence["paired_contrasts"]
completed_roles = sum(o["status"] == "complete" for o in result["candidates"])
unstarted = [o["candidate"] for o in result["candidates"] if o["status"] != "complete"]
report = [f"# {identity}: niezależna replikacja MUC v2, losowe i trudne negatywy", "",
    f"Decyzja zamrożonego porównania: **{decision}**. Ukończone role: {completed_roles}/11. Pełne pięć sparowanych jednostek: {evidence['complete_five_pair_comparison']}.", "",
    "To jawna replikacja na syntetycznych train/dev. Model,4096 par,192 kroki,próg0,5,metryki i bramki są identyczne z wcześniejszą próbą. Wyniki wcześniejszej porażki pozostają oddzielne; nie połączono jednostek ani nie dobierano checkpointu.", "",
    "| Metryka | Losowe | Trudne | Różnica (pp) | Przedział różnicy (pp) | Dodatnie pary |",
    "|---|---:|---:|---:|---:|---:|"]
for metric in ("fact_top1_accuracy", "dense_unknown_rejection", "accepted_fact_accuracy", "known_false_abstention", "e2e_known_accuracy", "e2e_unknown_rejection", "continual_new_fact_accuracy", "continual_retention"):
    if metric in contrasts:
        c = contrasts[metric]
        report.append(f"| {metric} | {100*means['random'][metric]:.3f}% | {100*means['hard'][metric]:.3f}% | {100*c['mean']:+.3f} | [{100*c['lower']:+.3f}; {100*c['upper']:+.3f}] | {c['positive_pairs']}/5 |")
report += ["", "Dwa główne przedziały mają poziom97,5% każdy (rodzinna pewność95%,Bonferroni,t z4 stopniami swobody). Pozostałe95% są opisowe. Jednostką jest sparowany seed i jego świeże dane; zapytania nie są niezależnymi replikacjami.", "",
    "Ranking liczy wybór najnowszego właściwego rekordu przed odrzucaniem. UNKNOWN wymaga maksimum wszystkich ocen poniżej0,5. accepted_fact_accuracy ma mianownik wszystkich znanych prób: wybór musi być poprawny i zaakceptowany. Znana abstencja oraz odpowiedzi po aktualizacjach i zachowanie wcześniejszych faktów są raportowane osobno.", "",
    "Bramki: top1≥+5pp,UNKNOWN≥+10pp,obie dolne granice głównych CI>0,co najmniej4/5 dodatnich par w każdym; zaakceptowane i końcowe znane odpowiedzi≥−2pp,znana abstencja≤+2pp,kompetentna kontrola symboliczna≥99,5%.", "",
    "| Bramka | Wynik |", "|---|---|"]
report += [f"| {name} | {value} |" for name, value in evidence["decision"].get("gates", {}).items()]
report += ["", "| Rola | Pełny worker (s) | Nadzorowany fit (s) | RSS (MiB) | CUDA reserved (MiB) | p95 E2E (µs) |", "|---|---:|---:|---:|---:|---:|"]
for role, c in evidence["costs_by_role"].items():
    report.append(f"| {role} | {c['worker_seconds']:.3f} | {c['supervised_fit_seconds']:.3f} | {c['peak_rss_bytes']/2**20:.1f} | {c['peak_cuda_reserved_bytes']/2**20:.1f} | {c['e2e_b1_p95_us']:.1f} |")
now = datetime.now(timezone.utc)
stage_wall = (now - datetime.fromisoformat(load_json(root / PLAN)["stage_started_at"].replace("Z", "+00:00"))).total_seconds()
report += ["", f"Łączny nadzorowany fit: {evidence['total_supervised_fit_seconds']:.6f}/3600s; pełni workerzy: {evidence['experiment_seconds']:.6f}s; kontroler z rejestracją: {controller['parent_wall_seconds']:.6f}s. Czas etapu do raportu: {stage_wall:.1f}/14400s. Wszystkie testy/administracja i awarie mieszczą się w zegarze etapu.", "",
    "Koszty obejmują generację danych, inicjalizację, przygotowanie par,fit,indeksowanie i aktualizacje,warmup,odpowiedzi oraz osobne pełne diagnostyki. FLOPs i logiczna pamięć są oszacowaniami; RSS i CUDA reserved są pomiarami. Energii,pieniędzy i całej pamięci sterownika GPU nie mierzono; brak wniosku o przewadze ekonomicznej.", "",
    f"Dzienniki konstrukcji: {len(proposals)} zapisów,{sum(not p['accepted'] for p in proposals)} odrzuconych propozycji strukturalnych. Stała reguła najwyżej64 propozycji kondycjonuje rozkład na wykonalności wymaganych typów pytań; nie używa jakości modelu. Brak powtórzenia eksperymentu lub zastępowania seedów.", "",
    "Kontrole par zachowują identyczną inicjalizację,train/dev,pozytywy oraz kolejność dokumentów i etykiet. Hard ma1024 negatywy tego samego podmiotu i1024 tej samej relacji. Pozostałe pola,próg i mechanika odczytu są wspólne.", "",
    "Niepewność: tylko pięć jednostek i jeden widoczny syntetyczny rozkład. Wynik nie rozstrzyga transferu,naturalnego języka ani całej rodziny architektur. Nie dostosowano progów po wynikach.", "",
    f"Niedokończony zakres: {unstarted if unstarted else 'brak w tym etapie'}. Szerszy cel B (druga rodzina,replikacje,świeże finały,prototyp) pozostaje aktywny. Jego historia i rezerwa7 biletów/47000s są nienaruszone.", "",
    f"Źródła: `{PLAN}` SHA256 `{PLAN_SHA256}`; wynik `{result_path.relative_to(root).as_posix()}` SHA256 `{sha256_file(result_path)}`; maszyna `{analysis_relative}`; pełne źródła i runtime są zarchiwizowane. Reprodukcja analizy: `.venv/Scripts/python.exe scripts/analyze_muc02_hard_negatives.py --experiment {identity}` w osobnej kopii (plik wyjściowy jest jednokrotny).", ""]
report_path = root / f"research/analyses/{identity}.md"
assert not report_path.exists()
report_path.write_text("\n".join(report), encoding="utf-8", newline="\n")
receipt = {"created_at": utc_now(), "stage_id": ID, "plan_sha256": PLAN_SHA256, "experiment_id": identity,
    "status": "validated_complete" if evidence["complete_five_pair_comparison"] else "inconclusive_partial_or_invalid",
    "decision": evidence["decision"], "result_sha256": sha256_file(result_path),
    "analysis_path": analysis_relative, "analysis_sha256": sha256_file(root / analysis_relative),
    "report_sha256": sha256_file(report_path), "controller": controller,
    "stage_wall_seconds_at_report": stage_wall, "auxiliary_checks_wall_seconds": sum(c["wall_seconds"] for c in checks),
    "fit_seconds_charged": evidence["total_supervised_fit_seconds"], "fit_seconds_cap": 3600,
    "full_workers_seconds": evidence["experiment_seconds"], "pairing_checks": evidence["pairing_checks"],
    "runtime_archive_path": runtime_path.relative_to(root).as_posix(), "runtime_archive_sha256": sha256_file(runtime_path),
    "data_proposal_records": len(proposals), "rejected_structural_proposals": sum(not p["accepted"] for p in proposals),
    "retry": False, "WT8_9": False, "new_architecture": False, "new_external_model_API": False,
    "calibration_or_final_access": False, "schedule_change": False, "incomplete_scope": unstarted,
    "protected_B_wallet": {k: old_wallet[k] for k in ("stage_b_compute_seconds_charged", "stage_b_registration_attempts_used", "protected_future_registration_attempts", "protected_future_compute_seconds")}}
atomic_write_json(completion_path, receipt)
append_jsonl(root / "research/events.jsonl", {"event": "muc02_replication_completed", "created_at": utc_now(), "stage_id": ID,
    "plan_sha256": PLAN_SHA256, "experiment_id": identity, "receipt_path": completion_path.relative_to(root).as_posix(), "receipt_sha256": sha256_file(completion_path)})
shutil.copyfile(archive / "config/research.toml", root / "config/research.toml")
freeze_manifest(root, overwrite=True)
write_preflight_certificate(root)
write_report(root)
wallet = program_status(root)
for key in ("fit_seconds_charged", "registration_attempts_used", "protected_future_registration_attempts", "protected_future_compute_seconds", "stage_b_compute_seconds_charged", "stage_b_registration_attempts_used"):
    assert wallet[key] == old_wallet[key], key
assert verify_manifest(root)["ok"]
assert not wallet["program_terminal"] and not wallet["scoring_authorized"]
print(json.dumps({"experiment": identity, "decision": decision, "fit_seconds": evidence["total_supervised_fit_seconds"],
    "B_wallet_preserved": True, "incomplete_scope": unstarted, "report": str(report_path)}))
