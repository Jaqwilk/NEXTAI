"""New clone conformance/intake seal for the independently frozen replication."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import nextai_autoresearch
from nextai_autoresearch.baseline_semantics import verify_required_baselines, write_preflight_certificate, verify_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import read_jsonl, append_jsonl
from nextai_autoresearch.research_program import status, _study_scope
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

STUDY_PATH = "research/plans/HAR01-INDEPENDENT-REPLICATION-V3.json"
STUDY_SHA = "9cf2153945a322e9c0e47c6d20287a9286e544a62ca0f711b64c797bcb493400"


def main(args):
    root = Path(__file__).resolve().parents[1]
    assert root.name == "NEXTAI-VALIDATION-20261002", "Independent clone required"
    assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
    assert sha256_file(root / STUDY_PATH) == STUDY_SHA
    study = json.loads((root / STUDY_PATH).read_text(encoding="utf-8"))
    prep_deadline = datetime.fromisoformat(study["preparation_deadline_at"].replace("Z", "+00:00"))
    assert datetime.now(timezone.utc) < prep_deadline, "Frozen preparation deadline exhausted"
    study = json.loads((root / STUDY_PATH).read_text(encoding="utf-8"))
    current = status(root)
    assert current["study_path"] == STUDY_PATH and not current["study_terminal"] and not current["study_expired"]
    assert not current["ready"] and not current["paid_run_pending"]
    assert not any(e.get("event") == "research_program_registration_started" and e.get("study_path") == STUDY_PATH for e in read_jsonl(root / "research/events.jsonl"))
    assert study["task_contract_sha256"] == sha256_file(root / study["task_contract_path"])
    for path, digest in study["parent_bindings"].items():
        assert sha256_file(root / path) == digest, path
    intake_path = root / "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V3.json"
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    assert intake["complete"] is True and intake["converted_subjects"] == list(range(6, 11)) + list(range(21, 26))
    assert intake["no_unselected_subject_signal_arrays"] is True
    assert intake["study_sha256"] == STUDY_SHA and intake["task_contract_sha256"] == study["task_contract_sha256"]
    payload = {intake["dataset_path"]: intake["dataset_sha256"], "research/data/har01_native_v1/publisher.zip": intake["publisher_sha256"]}
    for path, digest in payload.items():
        assert sha256_file(root / path) == digest, path
    full = (root / args.conformance).resolve()
    assert full.is_relative_to(root / "research/reviews")
    record = json.loads(full.read_text(encoding="utf-8"))
    assert record["study_sha256"] == STUDY_SHA
    assert Path(record["package_origin"]).resolve().is_relative_to(root / "src")
    assert record["tested_source_files_sha256"], "Tested source bindings required"
    for relative, digest in record["tested_source_files_sha256"].items():
        path = (root / relative).resolve()
        assert path.is_relative_to(root) and sha256_file(path) == digest, relative
    assert record["error"] is None and record["result"]["returncode"] == 0
    assert record["result"]["exit_job_active_process_count"] == 0
    assert not record["result"]["exit_live_descendant_pids"]
    cases = ET.parse(full.with_suffix(".xml")).findall(".//testcase")
    assert len(cases) == args.expected_cases and len(cases) > 0
    assert not any(any(row.find(k) is not None for k in ("failure", "error", "skipped")) for row in cases)
    nodes = {row.get("classname", "") + "::" + row.get("name", "") for row in cases}
    for node in args.required_node:
        assert node in nodes, f"Missing required fresh conformance node {node}"
    assert len([row for row in cases if row.get("classname") == "tests.test_har01_replication_analysis_v4"]) == 7
    assert any(row.get("classname") == "tests.test_har01_replication_integration_v4" for row in cases)
    if args.ready:
        config = root / "config/research.toml"
        text = config.read_text(encoding="utf-8")
        assert text.count('benchmark_status = "maintenance"') == 1
        config.write_text(text.replace('benchmark_status = "maintenance"', 'benchmark_status = "active"', 1), encoding="utf-8", newline="\n")
    freeze_manifest(root, overwrite=True)
    bound = {"candidates": study["candidates"], "research_program_protocol": _study_scope(study)}
    semantics = verify_required_baselines(bound, root, run_tests=True)
    write_preflight_certificate(root)
    certificate = verify_preflight_certificate(root)
    integrity = verify_manifest(root)
    assert integrity["ok"]
    assert datetime.now(timezone.utc) < prep_deadline, "Preparation deadline reached before readiness"
    receipt = {"created_at": utc_now(), "study_path": STUDY_PATH, "study_sha256": STUDY_SHA,
        "native_payload_sha256": payload, "intake_receipt_sha256": sha256_file(intake_path),
        "independent_clone": str(root), "package_origin": nextai_autoresearch.__file__,
        "before_paid_seed_fit_or_registration": True, "integrity": integrity,
        "preflight_sha256": certificate["certificate_sha256"], "baseline_conformance_nodes": semantics["tests"],
        "historical_A_closed_and_B_reserves": current, "ready": args.ready,
        "full_regression_receipt_sha256": sha256_file(full), "full_regression_XML_sha256": sha256_file(full.with_suffix(".xml")),
        "tested_source_files_sha256": record["tested_source_files_sha256"],
        "fresh_conformance_case_count": len(cases), "required_conformance_nodes": args.required_node,
        "no_metric_recipe_or_threshold_change": True, "old_receipts_reused_as_new_proof": False}
    path = root / ("research/checks/HAR01-replication-readiness-V3.json" if args.ready else "research/checks/HAR01-replication-maintenance-seal-V3.json")
    assert not path.exists()
    atomic_write_json(path, receipt)
    if args.ready:
        append_jsonl(root / "research/events.jsonl", {"event": "research_program_study_ready", "created_at": utc_now(),
            "program_id": current["id"], "study_path": STUDY_PATH, "study_sha256": STUDY_SHA,
            "receipt_path": str(path.relative_to(root)).replace("\\", "/"), "receipt_sha256": sha256_file(path)})
        assert status(root)["scoring_authorized"] is True
    print(json.dumps({"ready": args.ready, "integrity_ok": integrity["ok"], "semantic_nodes": len(semantics["tests"])}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready", action="store_true")
    parser.add_argument("--conformance", default="research/reviews/HAR01-REPLICATION-conformance-V3.json")
    parser.add_argument("--expected-cases", type=int, required=True)
    parser.add_argument("--required-node", action="append", default=[])
    main(parser.parse_args())
