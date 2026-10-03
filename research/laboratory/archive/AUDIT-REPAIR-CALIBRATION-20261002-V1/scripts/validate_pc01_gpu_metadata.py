"""No-training maintenance proof. Preserve old validators and completed evidence."""
import importlib.util
import json

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.laboratory import gpu_metadata_status, laboratory_problems
from nextai_autoresearch.pc01_execution import attempt_history, registered_plans, verify_certificate
from nextai_autoresearch.utils import project_root, load_json, sha256_file


def main():
    root = project_root()
    assert gpu_metadata_status(root) is not None
    receipt_path = root / "research/laboratory/PC-01-DEV-CYCLE-289-V1.receipt.json"
    assert sha256_file(receipt_path) == "c014a41e79fd94e85ac6b599f901d8cbbe061f2cde84c16f633d9293f279f6e1"
    for relative, digest in load_json(receipt_path)["artifact_sha256"].items():
        assert sha256_file(root / relative) == digest, relative
    manifest_path = root / "research/manifests/PC-01-GPU-METADATA-BEFORE.json"
    assert sha256_file(manifest_path) == "1671535a2d03a4d7bd3467ab241b4d2f9ceb0bb25898ce193d559bc75e40a118"
    old = load_json(manifest_path)
    archive = root / "research/laboratory/archive/PC-01-DEV-CYCLE-289"
    for relative, digest in old["files"].items():
        assert sha256_file(archive / relative) == digest, relative
        if relative.startswith("src/nextai_autoresearch/candidates/") or relative in (
            "src/nextai_autoresearch/runner.py", "src/nextai_autoresearch/pc01_telemetry.py",
            "schemas/pc01_plan.schema.json", "schemas/pc01_result.schema.json", "schemas/pc01_replica.schema.json"):
            assert sha256_file(root / relative) == digest, relative
    spec = importlib.util.spec_from_file_location("prefix_history", root / "scripts/validate_pc01_telemetry_repair.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixed = module.verify_snapshot(root, load_json(root / "research/laboratory/PC-01-INTEGRATION-HISTORY-BEFORE.json"))
    attempts = attempt_history(root)
    assert len(attempts) == len(registered_plans(root)) == 2 and all(a["complete"] for a in attempts)
    assert all(a["phase"] == "dev" for a in attempts)
    charge = sum(a["fit_seconds_charged"] for a in attempts)
    assert charge == 1500.4259332000001
    assert len(list((root / "research/results").glob("EXP-*.json"))) == 101
    assert not laboratory_problems(root)
    assert laboratory_problems(root, scoring=True)
    integrity = verify_manifest(root)
    assert integrity["ok"], integrity
    verify_certificate(root)
    print(json.dumps(dict(archived_protected_files=len(old["files"]), historical_nonledger_files=fixed,
                          historical_prefixes_preserved=True, integrity_checked_files=integrity["checked_files"],
                          completed_results=101, dev_attempts=2, total_fit_seconds_charged=charge,
                          training_performed=False, scoring_authorized=False, candidate_environment_unchanged=True)))


if __name__ == "__main__":
    main()
