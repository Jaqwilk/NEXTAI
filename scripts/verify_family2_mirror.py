"""Byte-only preparation mirror proof; does not decode or fit target samples."""
import json
from pathlib import Path
import subprocess

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
assert clone.resolve() != root.resolve() and (clone / ".git").is_dir()
parent = "24ad3a51ad1960b58229bb5559c358b62815805e"
# The wrapper's current reservation is append-only and is mirrored before the
# byte proof. Its later settled charge and completion events are mirrored again.
ledger = root / "research/events.jsonl"
clone_ledger = clone / "research/events.jsonl"
assert ledger.read_bytes().startswith(clone_ledger.read_bytes())
clone_ledger.write_bytes(ledger.read_bytes())
assert verify_manifest(root)["ok"] and verify_manifest(clone)["ok"]
manifest = json.loads((root / "research/eval_manifest.json").read_text())
paths = set(manifest["files"]) | {
    "research/eval_manifest.json", "research/laboratory/preflight_certificate.json",
    "research/REPORT.md", "research/REPORT.provenance.json", "research/events.jsonl",
    "research/sources.jsonl", "research/state.json", "research/experiments.tsv",
    "research/plans/NEXTAI-FAMILY2-INTAKE-PREPARATION-V1.json",
    "research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json",
    "research/laboratory/FAMILY2-CYCLE320-METADATA-RECOVERY-V1.json",
    "research/reviews/FAMILY2-CLONE-CONFORMANCE-V1.json",
    "scripts/verify_family2_preparation.py", "scripts/verify_family2_mirror.py",
}
paths.update(subprocess.check_output(["git", "diff", "--name-only", parent, "HEAD"], cwd=root).decode().splitlines())
paths.update(p.relative_to(root).as_posix() for p in (root / "research/reviews").glob("NEXTAI-B-320-*") if p.is_file())
paths.update(p.relative_to(root).as_posix() for p in
             (root / "research/laboratory/archive/FAMILY2-cycle320-metadata-V1").iterdir() if p.is_file())
digests = {}
for relative in sorted(paths):
    assert (root / relative).is_file() and (clone / relative).is_file(), relative
    digest = sha256_file(root / relative)
    assert sha256_file(clone / relative) == digest, relative
    digests[relative] = digest

expected_result = "78380a19ffacf4a58af0bd8586425fbacee44b2e5a92c6e056f3699f769ed255"
expected_source = "3576935b401f6c9324f2f4ed426de104b632a22ba74fb04da55757421f7632a8"
for directory in (root, clone):
    assert sha256_file(directory / "research/results/EXP-20261005-0007.json") == expected_result
    assert sha256_file(directory / "research/results/EXP-20261005-0006.fitted-state.zip") == expected_source
    assert not (directory / "STOP").exists() and not (directory / "PAUSE").exists()
    state = json.loads((directory / "research/state.json").read_text())
    assert state["active_experiment_id"] is None and state["completed_experiments"] == 122
    assert state["last_experiment_id"] == "EXP-20261005-0007" and state["cycle_number"] == 320

atomic_write_json(root / "research/reviews/FAMILY2-ORIGINAL-CLONE-MIRROR-V1.json", {
    "created_at": utc_now(), "original_root": str(root), "independent_clone_root": str(clone),
    "source_validation_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
    "files_compared": len(digests), "both_current_manifests_ok": True, "file_sha256": digests,
    "latest_native_result_sha256": expected_result, "actual_fitted_source_archive_sha256": expected_source,
    "completed_experiments_unchanged": 122, "new_EXP": 0, "new_research_fit_seconds": 0,
    "target_content_opened": False, "numeric_payloads_only_hashed_not_decoded": True,
})
print(json.dumps({"mirror_ok": True, "files_compared": len(digests), "research_fit": 0, "new_EXP": 0}), flush=True)
