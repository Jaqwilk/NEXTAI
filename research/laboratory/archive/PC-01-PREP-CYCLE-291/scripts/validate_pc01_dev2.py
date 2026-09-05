"""Prospective stage proof; old maintenance-only validators remain immutable."""
import importlib.util
import json

from nextai_autoresearch.laboratory import dev2_authority, _dev2_plans
from nextai_autoresearch.pc01_execution import attempt_history, verify_certificate, recipe_digest
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.utils import project_root, load_json, sha256_file


def main():
    root = project_root()
    authority = dev2_authority(root)
    assert authority is not None
    plans = _dev2_plans(root, authority)
    snapshot = load_json(root / "research/manifests/PC-01-DEV2-BEFORE.json")
    archive = root / authority["archive"]
    for relative, digest in snapshot["files"].items():
        assert sha256_file(archive / relative) == digest, relative
        if relative.startswith("src/nextai_autoresearch/candidates/") or relative in (
            "src/nextai_autoresearch/pc01_worker.py", "src/nextai_autoresearch/pc01_telemetry.py",
            "schemas/pc01_plan.schema.json", "schemas/pc01_result.schema.json", "schemas/pc01_replica.schema.json"):
            assert sha256_file(root / relative) == digest, relative
    # Reuse only the pure prefix validator; never invoke its obsolete stage gate.
    spec = importlib.util.spec_from_file_location("old_history", root / "scripts/validate_pc01_telemetry_repair.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    old = load_json(root / "research/laboratory/PC-01-INTEGRATION-HISTORY-BEFORE.json")
    fixed = module.verify_snapshot(root, old)
    for name in ("PC-01-TELEMETRY-REPAIR-V1.receipt.json", "PC-01-DEV-CYCLE-287-V1.receipt.json"):
        receipt = load_json(root / "research/laboratory" / name)
        for relative, digest in receipt.get("artifact_sha256", {}).items():
            source = archive / relative if relative in snapshot["files"] else root / relative
            assert sha256_file(source) == digest, relative
    history = attempt_history(root)
    assert 1 <= len(history) <= 2 and history[0]["complete"]
    assert history[0]["fit_seconds_charged"] == 1200
    assert all(row["phase"] == "dev" for row in history)
    assert not (root / "research/laboratory/PC-01-FINAL-SERIES-V1.json").exists()
    assert recipe_digest(root) == authority["recipe_sha256"]
    integrity = verify_manifest(root)
    assert integrity["ok"], integrity
    verify_certificate(root)
    print(json.dumps({"historical_nonledger_files": fixed, "archived_files": len(snapshot["files"]),
                      "historical_prefixes_preserved": True, "candidate_and_worker_unchanged": True,
                      "registered_dev_attempts": len(plans), "started_dev_attempts": len(history),
                      "total_fit_seconds_charged": sum(row["fit_seconds_charged"] for row in history),
                      "all_attempts_terminal": all(row["complete"] for row in history),
                      "integrity_checked_files": integrity["checked_files"], "final_access": False}))


if __name__ == "__main__":
    main()
