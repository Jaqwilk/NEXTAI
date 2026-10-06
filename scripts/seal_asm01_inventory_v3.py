"""Preserve every old scientific byte before the prospective metadata-only adapter."""
import json
from pathlib import Path
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
archive = root / "research/laboratory/archive/ASM01-cycle327-parent-V1"
parent = json.loads((archive / "research/eval_manifest.json").read_text())
changed = {"config/research.toml", "AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"}
for relative, digest in parent["files"].items():
    if relative not in changed:
        assert sha256_file(root / relative) == digest, relative
for relative in changed - {"config/research.toml"}:
    assert (root / relative).read_bytes().endswith((archive / relative).read_bytes())
manifest = freeze_manifest(root, overwrite=True)
write_preflight_certificate(root)
write_report(root)
assert verify_manifest(root)["ok"]
path = "research/reviews/ASM01-INVENTORY-V3-PRECONTENT-SEAL-V1.json"
assert not (root / path).exists()
atomic_write_json(root / path, dict(created_at=utc_now(), cycle=327,
    study_sha256=sha256_file(root / "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.json"),
    parent_protected_files=len(parent["files"]), protected_files=len(manifest["files"]),
    all_old_scientific_bytes_unchanged=True, old_headers_preserved_exactly=True,
    permitted_metadata_changes=sorted(changed), manifest_sha256=sha256_file(root / "research/eval_manifest.json"),
    preflight_sha256=sha256_file(root / "research/laboratory/preflight_certificate.json"),
    new_native_content=False, research_fit=0, new_EXPs=0, scoring=False))
append_jsonl(root / "research/events.jsonl", dict(event="maintenance_source_frozen", created_at=utc_now(),
    cycle=327, receipt_path=path, receipt_sha256=sha256_file(root / path),
    purpose="Extension-only alias metadata adapter; all old scanner/scientific bytes preserved before native content"))
print(json.dumps(dict(protected_files=len(manifest["files"]), old_science_preserved=True, native_content=False)))
