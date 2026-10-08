"""Hash-bound C prerequisites, pure dry-run proof and final release readiness."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import nextai_autoresearch
from nextai_autoresearch import research_program_c as c
from nextai_autoresearch.baseline_semantics import _certificate_path, verify_preflight_certificate, verify_required_baselines
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.research_program import dry_run_plan
from nextai_autoresearch.utils import load_json, sha256_file, utc_now

STUDY = "research/plans/ASM01-C-STABILIZED-SCREEN-V1.json"
STUDY_SHA = "297357e54f271bebe8fdf8da0d6a31c6d2c7a3fea5251ad9f1008eb9b26b8c1d"
TASK_SHA = "66cb7521a72e3485c8738d0f46cfe64bad3d773755fcc15c5db23a4cde9afa85"
DATASET = "research/data/asm01_c_v1/screen.npz"
PUBLISHER_SHA = "d6ad543e65269d53e38fdac6a32dd20bcd942e7616891a6cf95986894b454a4d"
SOURCE_BINDING = "research/reviews/ASM01-C-source-binding-V1.json"
INPUTS = "research/reviews/NEXTAI-C-PROSPECTIVE-INPUTS-V1.json"
DRY = "research/reviews/NEXTAI-C-ACTUAL-DRY-RUN-V1.json"
READY_CHECK = "research/reviews/NEXTAI-C-READINESS-CHECK-V1.json"
READY = "research/reviews/NEXTAI-C-READY-V1.json"
LEDGERS = ("research/events.jsonl", "research/c_events.jsonl", "research/plan_registry.jsonl",
           "research/plan_status_events.jsonl", "research/hypothesis_events.jsonl",
           "research/experiments.tsv", "research/state.json")


def exclusive(root, relative, document):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def evidence(root, relative):
    return {"path": relative, "sha256": sha256_file(root / relative)}


def preflight_evidence(root):
    return evidence(root, _certificate_path(root).relative_to(root).as_posix())


def conformance_verified(root, relative, context):
    document = load_json(root / relative)
    if (document.get("status") != "PASS" or document.get("all_required_conformance_passed") is not True
            or any(document.get(key) != value for key, value in context.items())
            or not isinstance(document.get("source_files"), dict) or not document["source_files"]
            or not isinstance(document.get("evidence_files"), dict) or not document["evidence_files"]):
        raise ValueError("All preregistered conformance paths and exact source binding are required")
    for mapping in (document["source_files"], document["evidence_files"]):
        for name, digest in mapping.items():
            if sha256_file(c._path(root, name)) != digest:
                raise ValueError("Conformance sources or raw evidence changed")
    return document


def binding(root):
    value = c.status(root)
    if (not value or value["study_path"] != STUDY or value["study_sha256"] != STUDY_SHA
            or value["cohort"] != "asm01_native_memory_v4"
            or value["stage"] != load_json(root / STUDY)["stage"]
            or value["program_terminal"] or value["study_terminal"] or value["study_expired"]
            or value["registration_attempts_used"]):
        raise ValueError("C readiness requires the exact frozen, unused scientific scope")
    return {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256,
            "study_path": STUDY, "study_sha256": STUDY_SHA,
            "cohort": value["cohort"], "stage": load_json(root / STUDY)["stage"]}


def input_receipt(root, conformance):
    context = binding(root)
    native = "research/data_manifests/ASM01-C-ACQUISITION-V1.json"
    intake = load_json(root / native)
    counters = ("native_files_attempted", "native_files_converted", "validated_files",
                "old74_compared", "previous1171_compared", "D_samples_opened")
    if (intake.get("complete") is not True or tuple(intake.get(k) for k in counters) != (1830,1830,1830,74,1171,915)
            or intake.get("study_sha256") != STUDY_SHA or intake.get("no_future_writer_coordinates_read") is not True
            or intake.get("task_contract_sha256") != TASK_SHA
            or intake.get("dataset_path") != DATASET or intake.get("publisher_sha256") != PUBLISHER_SHA
            or intake.get("C_program_id") != c.PROGRAM_ID
            or intake.get("source_binding_sha256") != sha256_file(root / SOURCE_BINDING)
            or sha256_file(root / intake["dataset_path"]) != intake["dataset_sha256"]):
        raise ValueError("Complete C native intake was not proven")
    conformance_verified(root, conformance, context)
    verified = verify_manifest(root)
    if not verified["ok"]:
        raise ValueError("C source/data integrity does not pass")
    verify_preflight_certificate(root)
    freeze = "research/reviews/NEXTAI-C-SOURCE-DATA-FREEZE-V1.json"
    exclusive(root, freeze, {**context, "created_at": utc_now(), "integrity": verified,
        "evaluator_manifest": evidence(root, "research/eval_manifest.json"),
        "source_binding": evidence(root, "research/reviews/ASM01-C-source-binding-V1.json"),
        "native_manifest": evidence(root, native), "dataset_sha256": intake["dataset_sha256"]})
    gates = {"complete1830_native_intake": evidence(root, native),
             "all_conformance": evidence(root, conformance),
             "source_and_data_hash_freeze": evidence(root, freeze),
             "preflight": preflight_evidence(root)}
    exclusive(root, INPUTS, {**context, "created_at": utc_now(),
        "status": "validated_prospective_inputs", "release_checks": {key: True for key in gates},
        "gate_evidence": gates})
    c.mark_inputs_ready(root, INPUTS)


def dry_receipt(root):
    context = binding(root)
    before = {name: sha256_file(root / name) if (root / name).is_file() else None for name in LEDGERS}
    names_before = sorted(p.relative_to(root).as_posix() for folder in ("research/plans", "research/tmp")
                          for p in (root / folder).rglob("*") if p.is_file())
    plan = dry_run_plan(root)
    after = {name: sha256_file(root / name) if (root / name).is_file() else None for name in LEDGERS}
    names_after = sorted(p.relative_to(root).as_posix() for folder in ("research/plans", "research/tmp")
                         for p in (root / folder).rglob("*") if p.is_file())
    if before != after or names_before != names_after or "seeds" in plan["matrix"]:
        raise ValueError("Prospective validation mutated a plan, ledger or private realization")
    exclusive(root, DRY, {**context, "created_at": utc_now(), "status": "PASS", "plan": plan,
        "ledger_sha256_before": before, "ledger_sha256_after": after,
        "plan_and_runtime_file_names_before": names_before,
        "plan_and_runtime_file_names_after": names_after,
        "plan_and_runtime_file_names_unchanged": True, "private_entropy_realized": False,
        "scientific_registration_attempts_used": c.status(root)["registration_attempts_used"]})


def ready_receipt(root):
    context = binding(root)
    dry = load_json(root / DRY)
    before = dry.get("ledger_sha256_before")
    after = dry.get("ledger_sha256_after")
    current = {name: sha256_file(root / name) if (root / name).is_file() else None for name in LEDGERS}
    names_before = dry.get("plan_and_runtime_file_names_before")
    names_after = dry.get("plan_and_runtime_file_names_after")
    plan = dry.get("plan", {})
    if not isinstance(plan, dict) or not isinstance(plan.get("matrix"), dict) or not isinstance(plan.get("research_program_protocol"), dict):
        raise ValueError("The actual no-ticket dry-run plan is malformed")
    matrix = plan.get("matrix", {})
    protocol = plan.get("research_program_protocol", {})
    if (dry.get("status") != "PASS" or type(dry.get("scientific_registration_attempts_used")) is not int
            or dry["scientific_registration_attempts_used"] != 0
            or any(dry.get(key) != value for key, value in context.items())
            or dry.get("private_entropy_realized") is not False
            or dry.get("plan_and_runtime_file_names_unchanged") is not True
            or not isinstance(before, dict) or set(before) != set(LEDGERS)
            or before != after or after != current
            or not isinstance(names_before, list) or names_before != names_after
            or names_before != sorted(p.relative_to(root).as_posix()
                for folder in ("research/plans", "research/tmp")
                for p in (root / folder).rglob("*") if p.is_file())
            or plan.get("benchmark") != context["cohort"]
            or "seeds" in matrix or matrix != load_json(root / STUDY)["matrix"]
            or protocol.get("program_id") != context["program_id"]
            or protocol.get("program_contract_sha256") != context["contract_sha256"]
            or protocol.get("study_path") != context["study_path"]
            or protocol.get("study_sha256") != context["study_sha256"]):
        raise ValueError("The actual no-ticket dry-run proof is missing")
    verified = verify_manifest(root)
    if not verified["ok"]:
        raise ValueError("C final readiness integrity changed")
    verify_required_baselines(dry["plan"], root, run_tests=False)
    verify_preflight_certificate(root)
    if c.prospective_admission_problems(root):
        raise ValueError("C prospective prerequisites are no longer valid")
    exclusive(root, READY_CHECK, {**context, "created_at": utc_now(), "status": "PASS",
        "integrity": verified, "dry_run": evidence(root, DRY),
        "preflight": preflight_evidence(root),
        "complete_intake_and_conformance_and_source_freeze_verified": True,
        "scientific_registration_attempts_used": 0})
    gates = load_json(root / INPUTS)["gate_evidence"]
    gates.update(same_builder_dry_run=evidence(root, DRY), readiness=evidence(root, READY_CHECK))
    exclusive(root, READY, {**context, "created_at": utc_now(), "status": "validated_ready",
        "release_checks": {key: True for key in c.RELEASE_CHECKS}, "gate_evidence": gates})
    c.mark_ready(root, READY)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("inputs", "dry-run", "ready"))
    parser.add_argument("--conformance")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if root.name != "NEXTAI-VALIDATION-20261002" or not Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src"):
        raise ValueError("Independent clone imports are required")
    if args.phase == "inputs":
        if not args.conformance:
            raise ValueError("A saved conformance receipt is required")
        input_receipt(root, args.conformance)
    elif args.phase == "dry-run":
        dry_receipt(root)
    else:
        ready_receipt(root)
    print(json.dumps({"phase": args.phase, "status": "PASS", "scientific_ticket_used": False}), flush=True)


if __name__ == "__main__":
    main()
