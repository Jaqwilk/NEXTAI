"""Read-only preparation verification; does not certify a runnable PC-01 cohort."""
import hashlib
import json
from pathlib import Path

from nextai_autoresearch.pc01 import verify_corpus


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    snapshot = json.loads((ROOT / "research/laboratory/PC-01-HARNESS-HISTORY-BEFORE.json").read_text())
    for relative, expected in snapshot["immutable_files"].items():
        check(digest(ROOT / relative) == expected, f"Historical artifact changed: {relative}")
    for relative, prefix in snapshot["prefixes"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()[:prefix["bytes"]]).hexdigest()
        check(actual == prefix["sha256"], f"Ledger prefix changed: {relative}")
    prior = ROOT / "research/manifests/PC-01-HARNESS-BEFORE-a0c945af93aa.json"
    check(digest(prior) == snapshot["manifest_sha256"], "Prior evaluator manifest not preserved")
    seal = json.loads((ROOT / "research/laboratory/PC-01-HARNESS-V1.json").read_text())
    for relative, expected in seal["artifact_sha256"].items():
        path = (ROOT / relative).resolve()
        check(path.is_relative_to(ROOT) and path.is_file(), f"Invalid artifact path: {relative}")
        check(digest(path) == expected, f"Harness artifact changed after sealing: {relative}")
    payload, manifest = verify_corpus(ROOT)
    check(len(payload) == 1115394, "Corpus size changed")
    print(json.dumps({"historical_files_unchanged": len(snapshot["immutable_files"]),
                      "ledger_prefixes_preserved": True, "prior_manifest_archived_exactly": True,
                      "harness_artifacts_verified": len(seal["artifact_sha256"]),
                      "corpus_sha256": manifest["sha256"], "candidate_training_performed": False,
                      "executable_cohort_ready": False,
                      "missing_requirements": [row["id"] for row in seal["missing_components"]]}))


if __name__ == "__main__":
    main()
