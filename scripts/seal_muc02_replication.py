"""Commit exact new protocol schema and independent source/preflight before any seeds."""
import copy
import json
from pathlib import Path
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.integrity import freeze_manifest, verify_manifest
from nextai_autoresearch.muc02_replication_stage import protocol, PLAN_SHA256, COHORT
from nextai_autoresearch.report import write_report
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
archive = root / "research/laboratory/archive/MUC02-REPLICATION-parent-V1"
assert archive.is_dir()
receipt_path = root / "research/reviews/MUC02-REPLICATION-PRESEED-SEAL-V1.json"
assert not receipt_path.exists()
parent = json.loads((archive / "parent-bindings.json").read_text())
allowed = {"AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md", "config/research.toml",
           "src/nextai_autoresearch/laboratory.py", "src/nextai_autoresearch/audit.py", "src/nextai_autoresearch/integrity.py",
           "schemas/experiment_plan.schema.json"}
for relative, digest in parent["protected_scientific_files"].items():
    if relative not in allowed:
        assert sha256_file(root / relative) == digest, relative
for relative in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md"):
    assert (root / relative).read_bytes().endswith((archive / relative).read_bytes())
new_protocol = protocol(root)
p = root / "schemas/experiment_plan.schema.json"
schema = json.loads(p.read_text(encoding="utf-8"))
assert len(schema["properties"]["muc02_negatives_protocol"]["oneOf"]) == 2
schema["properties"]["muc02_negatives_protocol"]["oneOf"].append({"const": new_protocol})
schema["allOf"].append({
    "if": {"properties": {"benchmark": {"const": COHORT}}, "required": ["benchmark"]},
    "then": {"properties": {"muc02_negatives_protocol": {"const": new_protocol},
                            "candidates": {"const": new_protocol["classical_baselines"]},
                            "matrix": {"const": {"knowledge_sizes": [32,128,512], "reasoning_depths": [1,2,4],
                                "queries_per_cell": 16, "seed_policy": {"method": "runner_random_v1", "count": 5,
                                    "minimum": 1000000, "maximum": 2147483647}}}},
             "required": ["muc02_negatives_protocol"]}})
atomic_write_json(p, schema)
manifest = freeze_manifest(root, overwrite=True)
write_preflight_certificate(root)
write_report(root)
assert verify_manifest(root)["ok"]
atomic_write_json(receipt_path, {"created_at": utc_now(), "status": "source_frozen_preseed",
    "plan_sha256": PLAN_SHA256, "cohort": COHORT, "parent_protected_files": len(parent["protected_scientific_files"]),
    "all_old_model_sampler_task_and_evaluator_bytes_unchanged": True,
    "changed_infrastructure_or_scope_files": sorted(allowed), "new_protected_files": len(manifest["files"]),
    "manifest_sha256": sha256_file(root / "research/eval_manifest.json"),
    "preflight_sha256": sha256_file(root / "research/laboratory/preflight_certificate.json"),
    "protocol": new_protocol, "fit_seconds": 0, "scoring_seed_draws": 0, "B_wallet_preserved": True})
print(json.dumps({"source_frozen": True, "protected_files": len(manifest["files"]), "scoring_seeds": 0, "fit": 0}))
