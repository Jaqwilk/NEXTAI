"""Close one replication or preparation failure; preserve evidence before maintenance."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from nextai_autoresearch.integrity import manifest_path, freeze_manifest, verify_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.ledger import append_jsonl, read_jsonl
from nextai_autoresearch.research_program import auxiliary_reserve, auxiliary_charge, status, _execution_fit
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now

STUDY = "research/plans/HAR01-INDEPENDENT-REPLICATION-V3.json"
SHA = "9cf2153945a322e9c0e47c6d20287a9286e544a62ca0f711b64c797bcb493400"
BINDING = "research/reviews/HAR01-REPLICATION-SOURCE-BINDING-V3.json"
COMPLETE = "research/laboratory/HAR01-REPLICATION-COMPLETION-V3.receipt.json"
ARCHIVE = "research/laboratory/archive/HAR01-REPLICATION-EVIDENCE-V3.zip"


def copy_preserved(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == source.read_bytes(), f"Preserved bytes differ: {target}"
    else:
        shutil.copyfile(source, target)


def copy_ledger(source, target):
    incoming = source.read_bytes()
    prior = target.read_bytes() if target.exists() else b""
    assert incoming.startswith(prior), f"Ledger prefix differs: {target}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(incoming)


def main():
    root = Path.cwd().resolve()
    clone = root.parent / "NEXTAI-VALIDATION-20261002"
    assert root.name == "NEXTAI" and clone.name == "NEXTAI-VALIDATION-20261002"
    assert not (root / COMPLETE).exists() and not (clone / COMPLETE).exists()
    assert sha256_file(root / STUDY) == sha256_file(clone / STUDY) == SHA
    study = load_json(clone / STUDY)
    deadline = datetime.fromisoformat(study["study_deadline_at"].replace("Z", "+00:00"))
    events = read_jsonl(clone / "research/events.jsonl")
    registrations = [e for e in events if e.get("event") == "research_program_registered" and e.get("study_path") == STUDY]
    assert len(registrations) <= 1
    identity = registrations[0]["experiment_id"] if registrations else None
    charge_id = "HAR01-REPLICATION-controller-V3"
    reserved = [e for e in events if e.get("event") == "research_program_aux_fit_reserved" and e.get("charge_id") == charge_id]
    charged = [e for e in events if e.get("event") == "research_program_aux_fit_charged" and e.get("charge_id") == charge_id]
    if not reserved:
        auxiliary_reserve(clone, charge_id, 250)
    if not charged:
        auxiliary_charge(clone, charge_id, 250)
    binding = load_json(root / BINDING)
    paths = set(binding["files"]) | {BINDING, STUDY, "config/research.toml", "research/events.jsonl"}
    paths.add(str(manifest_path(clone).relative_to(clone)).replace("\\", "/"))
    for relative in ("research/laboratory/preflight_certificate.json", "research/checks/preflight_certificate.json",
                     "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V3.json",
                     "research/checks/HAR01-replication-readiness-V3.json"):
        if (clone / relative).exists():
            paths.add(relative)
    for folder in (clone / "research/reviews", root / "research/reviews"):
        paths.update(str(p.relative_to(folder.parent.parent)).replace("\\", "/")
                     for p in folder.glob("HAR01-REPLICATION-*-V3.*") if p.is_file())
    prep = root / "research/laboratory/HAR01-REPLICATION-PREPARATION-COMPLETION-V3.receipt.json"
    if prep.exists():
        paths.add(str(prep.relative_to(root)).replace("\\", "/"))
    result = None
    if identity:
        for prefix in ("research/plans", "research/results", "research/analyses"):
            paths.update(str(p.relative_to(clone)).replace("\\", "/") for p in (clone / prefix).glob(identity + "*") if p.is_file() and p.suffix not in {".npz", ".zip"})
        runtime = clone / "research/tmp" / identity
        if runtime.exists():
            paths.update(str(p.relative_to(clone)).replace("\\", "/") for p in runtime.rglob("*") if p.is_file() and p.suffix not in {".npz", ".zip"})
        result_path = clone / f"research/results/{identity}.json"
        if result_path.exists():
            result = load_json(result_path)
    selected = {p: (clone / p if (clone / p).exists() else root / p) for p in sorted(paths)}
    assert all(p.is_file() for p in selected.values())
    hashes = {p: sha256_file(source) for p, source in selected.items()}
    archive_path = root / ARCHIVE
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for relative, source in selected.items():
            archive.write(source, relative)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert all(hashlib.sha256(archive.read(p)).hexdigest() == digest for p, digest in hashes.items())
    workers = _execution_fit(result["candidates"]) if result else _execution_fit(
        load_json(p) for p in (clone / "research/tmp" / identity).glob("*.supervisor.json")) if identity else 0.
    recoveries = [e for e in read_jsonl(clone / "research/events.jsonl") if e.get("event") == "research_program_worker_charge_recovery" and e.get("experiment_id") == identity]
    full_worker_charge = max([workers, *(e["worker_charge_total"] for e in recoveries)])
    analysis_path = clone / f"research/analyses/{identity}-har01.json" if identity else None
    analysis = load_json(analysis_path) if analysis_path and analysis_path.exists() else None
    decision = analysis["source_information_transfer"] if analysis else "INCONCLUSIVE"
    accounted = status(clone)
    receipt = {"id": "HAR01-REPLICATION-COMPLETION-V3", "created_at": utc_now(),
        "study_path": STUDY, "study_sha256": SHA, "experiment_id": identity,
        "decision": decision, "measurement_invalidity_is_not_a_scientific_null": analysis is None or not analysis.get("valid"),
        "prior_consumed_stage_seconds": 4950, "new_auxiliary_seconds": 550,
        "observed_full_workers_seconds": workers, "full_worker_charge_including_conservative_recovery": full_worker_charge,
        "whole_stage_charged_seconds": 5500 + full_worker_charge, "whole_stage_cap_seconds": 6000,
        "whole_stage_cap_pass": 5500 + full_worker_charge <= 6000,
        "hard_deadline_at": study["study_deadline_at"], "deadline_overrun_seconds": max(0., (datetime.now(timezone.utc) - deadline).total_seconds()),
        "archive_path": ARCHIVE, "archive_sha256": sha256_file(archive_path), "archived_files_sha256": hashes,
        "workers_present": len(result["candidates"]) if result else len(list((clone / "research/tmp" / identity).glob("*.supervisor.json"))) if identity else 0,
        "trials_present": sum(len(r.get("trials", [])) for r in result["candidates"]) if result else 0,
        "paid_retry": False, "whole_goal_complete": False, "remaining_protected_other_registrations": 6,
        "remaining_protected_other_seconds": 41000, "native_raw_publisher_or_NPZ_published": False}
    receipt.update(B_registrations_used=accounted["stage_b_registration_attempts_used"],
        B_seconds_charged=accounted["stage_b_compute_seconds_charged"], B_seconds_remaining=accounted["fit_seconds_remaining"])
    atomic_write_json(clone / COMPLETE, receipt)
    # This event closes only the current study, including a failure before EXP.
    append_jsonl(clone / "research/events.jsonl", {"event": "research_program_preparation_completed", "created_at": utc_now(),
        "program_id": "NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1", "study_path": STUDY,
        "study_sha256": SHA, "receipt_path": COMPLETE, "receipt_sha256": sha256_file(clone / COMPLETE)})
    config = clone / "config/research.toml"
    text = config.read_text(encoding="utf-8")
    if 'benchmark_status = "active"' in text:
        config.write_text(text.replace('benchmark_status = "active"', 'benchmark_status = "maintenance"', 1), encoding="utf-8", newline="\n")
    freeze_manifest(clone, overwrite=True)
    write_preflight_certificate(clone)
    integrity = verify_manifest(clone)
    assert integrity["ok"]
    wallet = status(clone)
    assert wallet["study_terminal"] and not wallet["scoring_authorized"] and wallet["fit_seconds_remaining"] >= 41000
    # Mutable lifecycle files are copied only after immutable evaluated bytes are archived.
    lifecycle = {"config/research.toml", "research/state.json", "research/eval_manifest.json", "research/laboratory/preflight_certificate.json"}
    for relative in selected:
        if relative.startswith(("research/tmp/", "research/plans/EXP-", "research/results/EXP-", "research/analyses/EXP-", "research/checks/HAR01-", "research/data_manifests/HAR01-", "research/reviews/HAR01-REPLICATION-")) or relative.endswith(".worker-recovery.json"):
            copy_preserved(selected[relative], root / relative)
    copy_preserved(clone / COMPLETE, root / COMPLETE)
    for relative in lifecycle:
        if (clone / relative).exists():
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(clone / relative, root / relative)
    for name in ("events.jsonl", "plan_registry.jsonl", "plan_status_events.jsonl", "hypothesis_events.jsonl", "experiments.tsv"):
        if (clone / "research" / name).exists():
            copy_ledger(clone / "research" / name, root / "research" / name)
    atomic_write_json(root / "research/laboratory/HAR01-REPLICATION-CLOSURE-STATUS-V3.json",
        {"created_at": utc_now(), "wallet": wallet, "integrity_ok": integrity["ok"], "complete_receipt_sha256": sha256_file(root / COMPLETE),
         "archive_sha256": sha256_file(archive_path), "whole_goal_complete": False})
    if analysis is None:
        prep_record = load_json(prep) if prep.exists() else {}
        report = root / "research/analyses/HAR01-CYCLE342-INDEPENDENT-REPLICATION-V3.md"
        assert not report.exists()
        report.write_text(
            "# HAR independent replication V2 — incomplete\n\n"
            "Decision: **INCONCLUSIVE through technical failure or missing scientific analysis**. "
            "This does not establish a learning, transfer or economic null. Earlier HAR results remain unchanged.\n\n"
            f"Recorded conformance: {prep_record.get('passed', 'unknown')} passed, "
            f"{prep_record.get('failed', 'unknown')} failed. Recorded EXP: {identity}. "
            f"Workers/trials preserved: {receipt['workers_present']}/{receipt['trials_present']}.\n\n"
            f"First-slot charge: {receipt['whole_stage_charged_seconds']:.6f}/6000 s; "
            f"4950 prior plus550 new auxiliary and {full_worker_charge:.6f} worker charge. "
            "Conservative recovery is distinguished from measured supervised fit. "
            f"B usage: {wallet['stage_b_registration_attempts_used']}/12 registrations and "
            f"{wallet['stage_b_compute_seconds_charged']:.6f}/72000 s. Other6/41000 s protected.\n\n"
            "Unperformed scope includes every missing worker/trial, the full five-pair scientific "
            "comparison and decision, second transfer family, target fresh finals and prototype. "
            "No retry or outcome-based repair was performed; future subjects remain closed. "
            f"Lossless evidence: {ARCHIVE}; completion receipt: {COMPLETE}. "
            f"Hard-deadline overrun at receipt: {receipt['deadline_overrun_seconds']:.6f} s.\n",
            encoding="utf-8", newline="\n")
    print(json.dumps({"receipt": COMPLETE, "decision": decision, "stage_charge": receipt["whole_stage_charged_seconds"],
        "B_registrations": wallet["stage_b_registration_attempts_used"], "B_charge": wallet["stage_b_compute_seconds_charged"], "scoring": wallet["scoring_authorized"]}), flush=True)


if __name__ == "__main__":
    main()
