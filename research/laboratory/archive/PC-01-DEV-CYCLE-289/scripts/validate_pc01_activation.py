"""Read-only prospective activation and preserved integration history checks."""
import hashlib
import json
from pathlib import Path

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.laboratory import activation_authority, laboratory_problems
from nextai_autoresearch.pc01_execution import verify_certificate
from nextai_autoresearch.utils import load_json, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    snapshot = load_json(ROOT / "research/laboratory/PC-01-INTEGRATION-HISTORY-BEFORE.json")
    for relative, expected in snapshot["immutable_files"].items():
        check(sha256_file(ROOT / relative) == expected, f"Historical artifact changed: {relative}")
    for relative, prefix in snapshot["prefixes"].items():
        raw = (ROOT / relative).read_bytes()[:prefix["bytes"]]
        check(hashlib.sha256(raw).hexdigest() == prefix["sha256"], f"Ledger prefix changed: {relative}")
    archived = 0
    for stage in ("PC-01-HARNESS-V1", "PC-01-INTEGRATION-V1"):
        seal = load_json(ROOT / "research/laboratory" / f"{stage}.json")
        for relative, expected in seal["artifact_sha256"].items():
            check(sha256_file(ROOT / "research/laboratory/archive" / stage / relative) == expected,
                  f"Sealed source archive changed: {stage}/{relative}")
            archived += 1
    check(sha256_file(ROOT / "research/manifests/PC-01-ACTIVATION-BEFORE.json") ==
          "0db7cdb17cbf9d1b072c66cf7f45da740251001d35af41ff3558c2af278f0a9d", "Prior manifest changed")
    check(sha256_file(ROOT / "research/laboratory/PC-01-INTEGRATION-V1.json") ==
          "a36368373a79f2ea6e9658415199ffe573d9218db8b218e89e277db53aa304b9", "Integration seal changed")
    check(not laboratory_problems(ROOT), "Laboratory authority invalid")
    authority = activation_authority(ROOT)
    check(authority is not None and not authority["final_access_authorized"], "Wrong execution scope")
    check(not (ROOT / "research/laboratory/PC-01-FINAL-SERIES-V1.json").exists(), "Unauthorized final series")
    integrity = verify_manifest(ROOT)
    check(integrity["ok"], str(integrity["problems"]))
    verify_certificate(ROOT)
    print(json.dumps({"historical_files_unchanged": len(snapshot["immutable_files"]),
                      "ledger_prefixes_preserved": True, "archived_sources": archived,
                      "integrity_checked_files": integrity["checked_files"],
                      "evaluator_sha256": integrity["evaluator_sha256"],
                      "activation": authority["id"], "final_access_authorized": False}))


if __name__ == "__main__":
    main()
