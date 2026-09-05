"""Preserve completed artifacts; validate append-only ledgers by their prefixes."""
import hashlib
import json
from pathlib import Path

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.laboratory import laboratory_problems
from nextai_autoresearch.pc01_execution import attempt_history, verify_certificate
from nextai_autoresearch.utils import load_json, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify_snapshot(root, snapshot):
    """A ledger duplicated in immutable_files is checked by its frozen prefix."""
    files = 0
    for relative, expected in snapshot["immutable_files"].items():
        if relative in snapshot["prefixes"]:
            check(expected == snapshot["prefixes"][relative]["sha256"], "Inconsistent historical prefix commitment")
            continue
        check(sha256_file(root / relative) == expected, f"Historical artifact changed: {relative}")
        files += 1
    for relative, prefix in snapshot["prefixes"].items():
        with (root / relative).open("rb") as stream:
            data = stream.read(prefix["bytes"])
        check(len(data) == prefix["bytes"] and hashlib.sha256(data).hexdigest() == prefix["sha256"],
              f"Ledger prefix changed/truncated: {relative}")
    return files


def main():
    snapshot = load_json(ROOT / "research/laboratory/PC-01-INTEGRATION-HISTORY-BEFORE.json")
    historical = verify_snapshot(ROOT, snapshot)
    manifest_path = ROOT / "research/manifests/PC-01-TELEMETRY-REPAIR-BEFORE.json"
    check(sha256_file(manifest_path) == "3b10f618b19dc42f0b33f073691a006598042f321fbe45abb7c98c5af423a4c8", "Old manifest changed")
    manifest = load_json(manifest_path)
    archive = ROOT / "research/laboratory/archive/PC-01-DEV-CYCLE-287"
    for relative, expected in manifest["files"].items():
        check(sha256_file(archive / relative) == expected, f"Old source archive changed: {relative}")
        if relative.startswith("src/nextai_autoresearch/candidates/"):
            check(sha256_file(ROOT / relative) == expected, f"Candidate changed during telemetry repair: {relative}")
    receipt_path = ROOT / "research/laboratory/PC-01-DEV-CYCLE-287-V1.receipt.json"
    check(sha256_file(receipt_path) == "71fe86d890af6b8b30107e0f24bd558aa11e69ff078bb5190d2929e46e83c77e", "Dev completion receipt changed")
    for relative, expected in load_json(receipt_path)["artifact_sha256"].items():
        check(sha256_file(ROOT / relative) == expected, f"Completed dev artifact changed: {relative}")
    attempts = attempt_history(ROOT)
    check(len(attempts) == 1 and attempts[0]["complete"] and attempts[0]["fit_seconds_charged"] == 1200,
          "Dev history or budget changed")
    check(not laboratory_problems(ROOT), "Laboratory authority invalid")
    check(laboratory_problems(ROOT, scoring=True), "Maintenance unexpectedly authorizes scoring")
    integrity = verify_manifest(ROOT)
    check(integrity["ok"], str(integrity["problems"]))
    verify_certificate(ROOT)
    print(json.dumps({"historical_nonledger_files": historical, "ledger_prefixes_preserved": True,
                      "archived_protected_files": len(manifest["files"]), "dev_artifacts_preserved": True,
                      "integrity_checked_files": integrity["checked_files"], "training_performed": False,
                      "scoring_authorized": False, "fit_seconds_charged_unchanged": 1200}))


if __name__ == "__main__":
    main()
