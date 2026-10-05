"""No-seed native conformance seal; activate once only after clone regression."""
import argparse
import json
from pathlib import Path

from nextai_autoresearch.baseline_semantics import verify_required_baselines, write_preflight_certificate, verify_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import read_jsonl, append_jsonl
from nextai_autoresearch.research_program import status, _study_scope
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


def main(ready):
    root = Path(__file__).resolve().parents[1]
    assert root.name == "NEXTAI-VALIDATION-20261002", "Independent clone required"
    study_path = "research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json"
    study = json.loads((root / study_path).read_text(encoding="utf-8"))
    current = status(root)
    assert current["study_path"] == study_path and not current["study_terminal"] and not current["study_expired"]
    assert not current["ready"] and not current["paid_run_pending"]
    intake = json.loads((root / "research/data_manifests/HAR01-ACQUISITION-V1.json").read_text(encoding="utf-8"))
    payload = {intake["dataset_path"]: intake["dataset_sha256"],
               "research/data/har01_native_v1/publisher.zip": intake["publisher_sha256"]}
    for path, digest in payload.items():
        assert sha256_file(root / path) == digest, path
    assert study["task_contract_sha256"] == sha256_file(root / study["task_contract_path"])
    bound = {"candidates": study["candidates"], "research_program_protocol": _study_scope(study)}
    if ready:
        full = root / "research/reviews/NEXTAI-B-319-full-regression-V1.json"
        record = json.loads(full.read_text(encoding="utf-8"))
        assert record["result"]["returncode"] == 0 and record["error"] is None
        assert record["result"]["exit_job_active_process_count"] == 0
        config = root / "config/research.toml"
        text = config.read_text(encoding="utf-8")
        assert text.count('benchmark_status = "maintenance"') == 1
        config.write_text(text.replace('benchmark_status = "maintenance"', 'benchmark_status = "active"', 1), encoding="utf-8", newline="\n")
    freeze_manifest(root, overwrite=True)
    semantics = verify_required_baselines(bound, root, run_tests=True)
    write_preflight_certificate(root)
    certificate = verify_preflight_certificate(root)
    integrity = verify_manifest(root)
    assert integrity["ok"]
    receipt = {"created_at": utc_now(), "study_path": study_path, "study_sha256": sha256_file(root / study_path),
        "native_payload_sha256": payload, "independent_clone": str(root), "before_paid_seed_fit_or_registration": True,
        "integrity": integrity, "preflight_sha256": certificate["certificate_sha256"],
        "baseline_conformance_nodes": semantics["tests"], "historical_A_closed_and_B_reserves": current,
        "ready": ready, "no_metric_recipe_or_threshold_change": True}
    if ready:
        receipt["full_regression_receipt_sha256"] = sha256_file(full)
        receipt["full_regression_stdout_sha256"] = sha256_file(full.with_suffix(".stdout.txt"))
    path = root / ("research/checks/HAR01-readiness-V1.json" if ready else "research/checks/HAR01-maintenance-seal-V1.json")
    assert not path.exists()
    atomic_write_json(path, receipt)
    if ready:
        append_jsonl(root / "research/events.jsonl", {"event": "research_program_study_ready", "created_at": utc_now(),
            "program_id": current["id"], "study_path": study_path, "study_sha256": receipt["study_sha256"],
            "receipt_path": str(path.relative_to(root)).replace("\\", "/"), "receipt_sha256": sha256_file(path)})
        assert status(root)["scoring_authorized"] is True
    print(json.dumps({"ready": ready, "integrity_ok": integrity["ok"], "semantic_nodes": len(semantics["tests"])}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready", action="store_true")
    main(parser.parse_args().ready)
