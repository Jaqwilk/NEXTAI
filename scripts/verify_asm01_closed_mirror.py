"""Compare sealed science in both checkouts; mirror only settled owned records."""
import json
from pathlib import Path
import subprocess

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
assert root.name == "NEXTAI" and (clone / ".git").is_dir()
assert root.resolve() != clone.resolve()
ledger = root / "research/events.jsonl"
clone_ledger = clone / "research/events.jsonl"
assert ledger.read_bytes().startswith(clone_ledger.read_bytes())
clone_ledger.write_bytes(ledger.read_bytes())

live_id = "NEXTAI-B-321-closed-mirror-V1"
owned = [root / "research/REPORT.md", root / "research/REPORT.provenance.json",
         root / "scripts/verify_asm01_closed_mirror.py",
         root / "scripts/verify_asm01_clone_maintenance.py"]
owned.extend(p for p in (root / "research/reviews").glob("NEXTAI-B-321-*")
             if p.is_file() and not p.name.startswith(live_id))
owned.extend(p for p in (root / "research/reviews").glob("ASM01-*") if p.is_file())
for path in owned:
    destination = clone / path.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if path.name not in {"REPORT.md", "REPORT.provenance.json"} and destination.exists():
        assert destination.read_bytes() == path.read_bytes(), path
    destination.write_bytes(path.read_bytes())

checks = {"original": verify_manifest(root), "clone": verify_manifest(clone)}
assert all(item["ok"] for item in checks.values()), checks
manifest = json.loads((root / "research/eval_manifest.json").read_text(encoding="utf-8"))
paths = set(manifest["files"]) | {
    "research/eval_manifest.json", "research/laboratory/preflight_certificate.json",
    "research/events.jsonl", "research/REPORT.md", "research/REPORT.provenance.json",
    "research/state.json", "research/experiments.tsv", "research/sources.jsonl",
}
paths.update(subprocess.check_output(
    ["git", "diff", "--name-only", "cb6b7daf19ceb390bcc029bf6974e033da5a904b", "HEAD"],
    cwd=root).decode().splitlines())
paths.update(path.relative_to(root).as_posix() for path in owned)
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
    state = json.loads((directory / "research/state.json").read_text(encoding="utf-8"))
    assert state["active_experiment_id"] is None and state["completed_experiments"] == 122
    assert state["last_experiment_id"] == "EXP-20261005-0007" and state["cycle_number"] == 321

receipt = {
    "created_at": utc_now(), "original_root": str(root), "independent_clone_root": str(clone),
    "files_compared": len(digests), "protected_files": len(manifest["files"]),
    "both_current_manifests_ok": True, "manifest_verification": checks, "file_sha256": digests,
    "latest_native_result_sha256": expected_result, "actual_fitted_source_archive_sha256": expected_source,
    "completed_experiments_unchanged": 122, "new_EXP": 0, "new_research_fit_seconds": 0,
    "native_payloads_only_hashed_not_decoded_by_this_check": True,
    "live_wrapper_outputs_excluded_until_settled": live_id,
}
atomic_write_json(root / "research/reviews/ASM01-CLOSED-ORIGINAL-CLONE-MIRROR-V1.json", receipt)
print(json.dumps({"mirror_ok": True, "files_compared": len(digests),
                  "protected_files": len(manifest["files"]), "new_EXP": 0}), flush=True)
