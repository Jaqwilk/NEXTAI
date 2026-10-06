"""Preserve the failed administrative assertion and reconcile existing artifacts.

Does not rerun its predecessor, edit scientific source or execute an experiment.
"""
import ast
import hashlib
import zipfile
from pathlib import Path
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[2]
assert root.name == "NEXTAI"
failure = root / "research/reviews/MUC02-REPLICATION-FINAL-METADATA-V1.failure.json"
proof = root / "research/reviews/MUC02-REPLICATION-METADATA-RECONCILIATION-V1.json"
assert not failure.exists() and not proof.exists()
atomic_write_json(failure, {"created_at": utc_now(), "operation": "administrative completed-stage header and provenance closure",
    "command": ".venv/Scripts/python.exe research/reviews/MUC02-REPLICATION-FINAL-METADATA-V1.py",
    "returncode": 1, "failed_line": 44,
    "exception": "AssertionError: ['AGENTS.md', 'program.md', 'research/LAB_PLAN.md']",
    "cause": "The assertion incorrectly expected CURRENT_STATUS.md in the protected manifest; that documentation path is not a protected entry.",
    "preserved_effects": "Four headers prepended; manifest and preflight generated before the assertion; no report or metadata proof was written by the failed helper.",
    "scientific_retry": False, "new_fit_seconds": 0, "new_scoring_seed_draws": 0,
    "resolution": "Inspect existing bytes and seal reporting through an append-only reconciliation; never rerun the failed helper.",
    "cost": "All elapsed administrative time, including this failure, is inside the 14400-second stage wall clock."})
assert verify_manifest(root)["ok"]
verify_preflight_certificate(root)
completion = load_json(root / "research/laboratory/MUC02-REPLICATION-COMPLETION-V1.receipt.json")
assert sha256_file(root / "config/research.toml") == sha256_file(root / "research/laboratory/archive/MUC02-REPLICATION-parent-V1/config/research.toml")
tree = ast.parse((root / "research/reviews/MUC02-REPLICATION-FINAL-METADATA-V1.py").read_text(encoding="utf-8"))
header = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "header" for t in node.targets))
headers = ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md")
current = load_json(root / "research/eval_manifest.json")
old_headers = {}
with zipfile.ZipFile(root / completion["controller"]["source_archive_path"]) as z:
    evaluated = __import__("json").loads(z.read("research/eval_manifest.json"))
    assert set(evaluated["files"]) == set(current["files"])
    changed = {name for name in evaluated["files"] if evaluated["files"][name] != current["files"][name]}
    allowed = ({name for name in headers if name in evaluated["files"]} | {"config/research.toml"})
    assert changed == allowed, sorted(changed)
    for name in headers:
        prior = z.read(name)
        assert (root / name).read_bytes() == header.encode("utf-8") + prior, name
        old_headers[name] = hashlib.sha256(prior).hexdigest()
write_report(root)
atomic_write_json(proof, {"created_at": utc_now(), "experiment_id": completion["experiment_id"],
    "status": "existing_metadata_reconciled", "failed_helper_was_rerun": False,
    "failure_path": failure.relative_to(root).as_posix(), "failure_sha256": sha256_file(failure),
    "scientific_source_changed": False, "new_scoring_seed_draws": 0, "new_fit_seconds": 0,
    "protected_changes_since_evaluated_source": sorted(changed), "prior_headers_preserved_as_suffixes": True,
    "old_headers_sha256": old_headers, "current_headers_sha256": {name: sha256_file(root / name) for name in headers},
    "manifest_sha256": sha256_file(root / "research/eval_manifest.json"),
    "preflight_sha256": sha256_file(root / "research/laboratory/preflight_certificate.json"),
    "config_restored_byte_for_byte": True, "scientific_incomplete_scope": []})
print("Existing completed-stage metadata reconciled; failure retained; no scientific retry.")
