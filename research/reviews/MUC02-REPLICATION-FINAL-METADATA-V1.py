"""Record the completed stage without changing the frozen scientific recipe."""
from pathlib import Path
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[2]
assert root.name == "NEXTAI"
destination = root / "research/reviews/MUC02-REPLICATION-FINAL-METADATA-V1.json"
assert not destination.exists()
completion = load_json(root / "research/laboratory/MUC02-REPLICATION-COMPLETION-V1.receipt.json")
assert completion["status"] == "validated_complete" and completion["incomplete_scope"] == []
assert completion["decision"]["decision"] == "discard_proposed_recipe"
assert verify_manifest(root)["ok"]
before = load_json(root / "research/eval_manifest.json")
headers = ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md")
header = (
    "# Completed cycle328: independent MUC v2 negatives replication (2026-10-06)\n\n"
    "The separately authorized MUC02-NEGATIVES-REPLICATION-20261006-V1 stage is complete.\n"
    "One canonical clone execution EXP-20261006-0001: 11/11 roles,135 trials,5 fresh paired seeds.\n"
    "Same model,4096 pairs,192 steps; frozen metrics,threshold0.5 and gates unchanged.\n"
    "Decision DISCARD exact recipe: ranking +8.000pp,97.5% CI[-3.869,+19.869];\n"
    "dense UNKNOWN -14.148pp,CI[-55.633,+27.336]; known false abstention +9.481pp.\n"
    "Symbolic control100%; fit115.4139476/3600s; full workers626.9652242s.\n"
    "All prior failures,source bytes,registrations,results and costs remain consumed and preserved.\n"
    "Report research/analyses/EXP-20261006-0001.md; separate interpretation and final accounting.\n"
    "Current config restored exactly to parent ASM01 maintenance,scoring=false; no further MUC execution.\n"
    "B remains active,its wallet unchanged: 1/12 registrations,20098.55024020007/72000s;\n"
    "protected7 registrations/47000s unchanged. Separate MUC authority grants no extra B credit.\n"
    "Broader transfer/prototype goal remains open. Any further scientific scope needs separately frozen authority.\n"
    "No retry,WT8-9,future ASM/HAR writers,external models/API,new architecture or schedule change.\n"
    "Earlier stage-specific sections below remain preserved history.\n\n"
)
old_headers = {name: sha256_file(root / name) for name in headers}
for name in headers:
    path = root / name
    path.write_bytes(header.encode("utf-8") + path.read_bytes())
freeze_manifest(root, overwrite=True)
write_preflight_certificate(root)
after = load_json(root / "research/eval_manifest.json")
assert set(before["files"]) == set(after["files"])
changed = sorted(name for name in before["files"] if before["files"][name] != after["files"][name])
assert changed == sorted(headers), changed
assert verify_manifest(root)["ok"]
write_report(root)
atomic_write_json(destination, {"created_at": utc_now(), "experiment_id": completion["experiment_id"], "metadata_only": True,
    "new_scoring_seed_draws": 0, "new_fit_seconds": 0, "scientific_source_changed": False,
    "protected_files_changed": changed, "old_headers_sha256": old_headers,
    "new_headers_sha256": {name: sha256_file(root / name) for name in headers},
    "evaluated_source_preserved": completion["controller"]["source_archive_path"],
    "manifest_sha256": sha256_file(root / "research/eval_manifest.json"),
    "preflight_sha256": sha256_file(root / "research/laboratory/preflight_certificate.json")})
print("Completed-stage metadata frozen; scientific code unchanged; no new fit or scoring.")
