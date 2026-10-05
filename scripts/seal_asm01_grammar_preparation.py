"""Seal preparation only; keep every old scientific source byte and failure."""
import json
from pathlib import Path

from nextai_autoresearch.baseline_semantics import write_preflight_certificate, verify_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
archive = root / "research/laboratory/archive/ASM01-grammar-cycle322-parent-V1"
parent = json.loads((archive / "research/eval_manifest.json").read_text())
changed = {"config/research.toml", "AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"}
for relative, digest in parent["files"].items():
    if relative not in changed:
        assert sha256_file(root / relative) == digest, relative
for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"):
    assert (root / relative).read_bytes().endswith((archive / relative).read_bytes())
native = json.loads((root / "research/reviews/ASM01-EXPOSED-T1-GRAMMAR-CONFORMANCE-V1.json").read_text())
assert native["complete"] is False and native["error"] == "ValueError: Pen-up supplied state/stroke"
assert native["new_samples_opened"] == 0 and native["D_samples_opened"] == 0 and native["fit"] == 0
manifest = freeze_manifest(root, overwrite=True)
write_preflight_certificate(root)
write_report(root)
assert verify_manifest(root)["ok"]
verify_preflight_certificate(root)
wallet = status(root)
assert not wallet["scoring_authorized"] and not wallet["paid_run_pending"]
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000 and wallet["protected_future_registration_attempts"] == 7
receipt_path = "research/reviews/ASM01-GRAMMAR-MAINTENANCE-SEAL-V1.json"
assert not (root / receipt_path).exists()
receipt = {"created_at": utc_now(), "all1432_parent_scientific_bytes_unchanged_except_permitted_metadata": True,
           "permitted_metadata_changes": sorted(changed), "old_headers_preserved_exactly": True,
           "manifest_sha256": sha256_file(root / "research/eval_manifest.json"),
           "preflight_sha256": sha256_file(root / "research/laboratory/preflight_certificate.json"),
           "protected_files": len(manifest["files"]), "native_failure_preserved": True,
           "maintenance": True, "scoring": False, "ready": False, "new_EXP": 0, "fit": 0,
           "program": wallet}
atomic_write_json(root / receipt_path, receipt)
append_jsonl(root / "research/events.jsonl", {
    "event": "maintenance_source_frozen", "created_at": utc_now(), "cycle": 322,
    "program_id": wallet["id"], "purpose": "Separate no-scoring versioned grammar conformance; preserve native failure and all old science",
    "receipt_path": receipt_path, "receipt_sha256": sha256_file(root / receipt_path),
})
print(json.dumps({k: v for k, v in receipt.items() if k != "program"}), flush=True)
