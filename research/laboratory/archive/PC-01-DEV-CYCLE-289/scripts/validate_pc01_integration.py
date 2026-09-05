"""Read-only history/source/certificate checks for the third authorized service.

Prior validators and their assertions are preserved unchanged. When a former
source path legitimately evolved, verify its exact sealed bytes in the archive.
"""
import hashlib
import json
from pathlib import Path

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.pc01 import verify_corpus
from nextai_autoresearch.pc01_execution import verify_certificate
from nextai_autoresearch.utils import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    snapshot = json.loads((ROOT / "research/laboratory/PC-01-INTEGRATION-HISTORY-BEFORE.json").read_text())
    for relative, expected in snapshot["immutable_files"].items():
        check(sha256_file(ROOT / relative) == expected, f"Historical artifact changed: {relative}")
    for relative, prefix in snapshot["prefixes"].items():
        raw = (ROOT / relative).read_bytes()[:prefix["bytes"]]
        check(hashlib.sha256(raw).hexdigest() == prefix["sha256"], f"Ledger prefix changed: {relative}")
    old = json.loads((ROOT / "research/laboratory/PC-01-HARNESS-V1.json").read_text())
    archive = ROOT / "research/laboratory/archive/PC-01-HARNESS-V1"
    for relative, expected in old["artifact_sha256"].items():
        check(sha256_file(archive / relative) == expected, f"Old sealed source not preserved: {relative}")
    check(sha256_file(ROOT / "research/manifests/PC-01-INTEGRATION-BEFORE.json") == snapshot["prior_manifest_sha256"],
          "Former evaluator manifest changed")
    seal = json.loads((ROOT / "research/laboratory/PC-01-INTEGRATION-V1.json").read_text())
    for relative, expected in seal["artifact_sha256"].items():
        path = (ROOT / relative).resolve()
        check(path.is_relative_to(ROOT) and sha256_file(path) == expected, f"Integration source changed: {relative}")
    corpus, manifest = verify_corpus(ROOT)
    check(len(corpus) == 1115394, "Corpus size changed")
    integrity = verify_manifest(ROOT)
    check(integrity["ok"], str(integrity["problems"]))
    certificate = verify_certificate(ROOT)
    print(json.dumps({"historical_files_unchanged": len(snapshot["immutable_files"]),
        "ledger_prefixes_preserved": True, "old_sealed_sources_archived": len(old["artifact_sha256"]),
        "new_sealed_sources": len(seal["artifact_sha256"]), "integrity_checked_files": integrity["checked_files"],
        "conformance_certificate_verified": certificate["all_required_checks_passed"],
        "corpus_sha256": manifest["sha256"], "training_performed": False, "scoring_authorized": False,
        "real_model_recipe_executed": False, "activation_review_still_required": True}))


if __name__ == "__main__":
    main()
