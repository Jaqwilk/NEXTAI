"""Preserve actual synthetic test evidence and immutable pre-native sources."""
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import nextai_autoresearch
from nextai_autoresearch import research_program_c as c
from nextai_autoresearch.utils import load_json, sha256_file, utc_now

STUDY = "research/plans/ASM01-C-STABILIZED-SCREEN-V1.json"
STUDY_SHA = "297357e54f271bebe8fdf8da0d6a31c6d2c7a3fea5251ad9f1008eb9b26b8c1d"
SUMMARY = "research/reviews/NEXTAI-C-CONFORMANCE-V1.json"
BINDING = "research/reviews/ASM01-C-source-binding-V1.json"


def save(root, relative, document):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main():
    root = Path(__file__).resolve().parents[1]
    if (root.name != "NEXTAI-VALIDATION-20261002"
            or not Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
            or sha256_file(root / STUDY) != STUDY_SHA):
        raise ValueError("Independent clone and exact preregistration required")
    if (root / SUMMARY).exists() or (root / BINDING).exists():
        raise ValueError("Conformance/source binding already preserved")
    study = load_json(root / STUDY)
    groups, evidence, selected_classes = [], {}, set()
    definitions = (
        ("ENGINEERING-full-V2", {"tests.test_asm01_c_intake", "tests.test_asm01_c_binding",
                                  "tests.test_c_runner_limits", "tests.test_c_scientific_driver"}, 165),
        ("ENGINEERING-readiness-V5", {"tests.test_c_prepare"}, 116),
        ("ENGINEERING-conformance-V6", {"tests.test_c_analysis", "tests.test_research_program_c",
                                       "tests.test_c_harness_admission", "tests.test_c_engineering_full_path",
                                       "tests.test_integrity_and_schemas"}, 40),
        ("ENGINEERING-legacy-semantic-V7", "passed", 36),
        ("ENGINEERING-semantic-V8", None, None),
    )
    for label, classes, expected in definitions:
        prefix = "research/reviews/NEXTAI-C-" + label
        cases = ET.parse(root / (prefix + ".xml")).getroot().findall(".//testcase")
        selected = [case for case in cases if classes is None or classes == "passed"
                    and not any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))
                    or isinstance(classes, set) and case.attrib["classname"] in classes]
        if (not selected or expected is not None and len(selected) != expected
                or any(case.find(tag) is not None for case in selected for tag in ("failure", "error", "skipped"))):
            raise ValueError("Selected conformance cases do not pass:" + label)
        job = load_json(root / (prefix + ".job.json"))["job"]
        if (job["reason"] != "exited" or job["exit_job_active_process_count"] != 0
                or job["exit_live_descendant_pids"] or classes is None and job["returncode"] != 0):
            raise ValueError("Conformance process tree did not complete and drain:" + label)
        for suffix in (".xml", ".job.json", ".stdout.txt", ".stderr.txt"):
            evidence[prefix + suffix] = sha256_file(root / (prefix + suffix))
        selected_classes.update(case.attrib["classname"] for case in selected)
        groups.append({"label": label, "selected_passed": len(selected),
            "selected_failed": 0, "selected_errors": 0, "selected_skipped": 0,
            "all_job_cases": len(cases), "whole_job_returncode": job["returncode"],
            "selection": "all" if classes is None else "passed only" if classes == "passed" else sorted(classes),
            "case_ids": [case.attrib["classname"] + "::" + case.attrib["name"] for case in selected],
            "prior_failed_cases_retained": classes is not None})
    sources = dict(study["source_hashes_preserved"])
    for relative, digest in sources.items():
        if sha256_file(c._path(root, relative)) != digest:
            raise ValueError("Preserved source bytes changed:" + relative)
    for pattern in ("src/nextai_autoresearch/**/*.py", "tests/**/*.py"):
        for path in sorted(root.glob(pattern)):
            if path.is_file() and "__pycache__" not in path.parts:
                relative = path.relative_to(root).as_posix()
                digest = sha256_file(path)
                if relative in sources and sources[relative] != digest:
                    raise ValueError("Frozen scientific source changed:" + relative)
                sources[relative] = digest
    for relative in ("schemas/experiment_plan.schema.json", "config/baseline_semantics.json",
                     "scripts/acquire_asm01_c_v1.py", "scripts/run_c_bounded.py", "scripts/run_c_science.py",
                     "scripts/prepare_c_science.py", "scripts/analyze_asm01_c_v1.py", "scripts/bind_c_conformance.py"):
        sources[relative] = sha256_file(root / relative)
    required = {"tests.test_c_analysis", "tests.test_research_program_c", "tests.test_c_harness_admission",
                "tests.test_c_engineering_full_path", "tests.test_integrity_and_schemas",
                "tests.test_preflight_contract", "tests.test_process_supervision",
                "tests.test_asm01_native_transfer", "tests.test_asm01_cohort_conformance",
                "tests.test_asm01_canonical_intake", "tests.test_asm01_v3_cohort_conformance"}
    if not required.issubset(selected_classes):
        raise ValueError("Required synthetic conformance family missing")
    all_ids = {identity for group in groups for identity in group["case_ids"]}
    registry = load_json(root / "config/baseline_semantics.json")
    for test in registry["baselines"]["asm01_source_trained_s0"]["conformance_tests"]:
        path, name = test["node_id"].split("::", 1)
        identity = path.removesuffix(".py").replace("/", ".") + "::" + name
        if not any(item == identity or item.startswith(identity + "[") for item in all_ids):
            raise ValueError("Required semantic test absent:" + identity)
    context = {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256,
        "study_path": STUDY, "study_sha256": STUDY_SHA, "cohort": study["cohort"], "stage": study["stage"]}
    save(root, SUMMARY, {**context, "created_at": utc_now(), "status": "PASS",
        "all_required_conformance_passed": True, "groups": groups,
        "selected_passed_total": sum(group["selected_passed"] for group in groups),
        "source_files": sources, "evidence_files": evidence,
        "failures_preserved_not_refunded": True, "canonical_scientific_registration_or_native_reads": 0})
    save(root, BINDING, {**context, "created_at": utc_now(),
        "task_contract_sha256": study["task_contract_sha256"], "native_intake_authorized": True,
        "synthetic_conformance_complete": True, "files": {**sources, **evidence, SUMMARY: sha256_file(root / SUMMARY)},
        "conformance_path": SUMMARY, "conformance_sha256": sha256_file(root / SUMMARY),
        "volatile_config_ledger_manifest_excluded": True})
    print(json.dumps({"summary": SUMMARY, "source_binding": BINDING,
        "selected_passed": sum(group["selected_passed"] for group in groups)}), flush=True)


if __name__ == "__main__":
    main()
