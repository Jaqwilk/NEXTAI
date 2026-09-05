"""Read-only, exact v2 selection to v3 measurement bridge; never authority."""
import ast
import hashlib
from pathlib import Path

from .config import load_config
from .integrity import manifest_path
from .pc01 import METADATA_COHORT, CONTRACT_PATH, require
from .utils import load_json, sha256_file, sha256_json

PLAN_PATH = "research/plans/PC-01-FINAL-PREP-V1.json"
PLAN_SHA256 = "a6e38d7c0afda28ef6e899f09ee0f7055ac0079236ce99ba05e0ff868e8a041f"


def selected_transition(root: Path, selected_dev_id: str) -> dict:
    from .pc01_execution import audit_bundle, recipe_digest
    require(sha256_file(root / PLAN_PATH) == PLAN_SHA256, "transition contract changed")
    policy = load_json(root / PLAN_PATH)
    require(selected_dev_id == policy["selected_dev_id"], "transition selected dev changed")
    plan = load_json(root / "research/plans" / f"{selected_dev_id}.json")
    result_path = root / "research/results" / f"{selected_dev_id}.json"
    require(sha256_json(plan) == policy["selected_plan_sha256"], "selected plan changed")
    require(sha256_file(result_path) == policy["selected_result_sha256"], "selected result changed")
    require(load_json(result_path)["status"] == "complete", "selected dev incomplete")
    require(plan["phase"] == "dev" and plan["benchmark"] == policy["selected_cohort"], "selected cohort changed")
    require(plan["evaluator_sha256"] == policy["selected_evaluator_sha256"], "selected evaluator changed")
    require(plan["candidate"] == policy["candidate"], "selected candidate changed")
    require(plan["data_sha256"] == policy["data_sha256"], "selected data changed")
    require(sha256_file(root / CONTRACT_PATH) == policy["design_sha256"], "design changed")
    require(recipe_digest(root) == plan["recipe_sha256"] == policy["recipe_sha256"], "recipe changed")
    require(audit_bundle(plan["candidate"], root)["sha256"] == policy["candidate_audit_sha256"], "candidate audit changed")
    require(sha256_file(root / policy["metadata_receipt"]) == policy["metadata_receipt_sha256"], "metadata receipt changed")
    for relative, digest in policy["source_constraints"].items():
        require(sha256_file(root / relative) == digest, f"trusted source changed: {relative}")
    tree = ast.parse((root / "src/nextai_autoresearch/pc01.py").read_text(encoding="utf-8"))
    tree.body = [node for node in tree.body if not (isinstance(node, ast.FunctionDef) and node.name == "series_decision")]
    require(hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest() == policy["nonseries_ast_sha256"],
            "non-series measurement semantics changed")
    require(load_config(root).benchmark_version == METADATA_COHORT == policy["target_cohort"], "target cohort changed")
    return {"contract_path": PLAN_PATH, "contract_sha256": PLAN_SHA256,
            "selected_dev_id": selected_dev_id, "selected_plan_sha256": policy["selected_plan_sha256"],
            "selected_result_sha256": policy["selected_result_sha256"],
            "selected_evaluator_sha256": policy["selected_evaluator_sha256"],
            "target_cohort": METADATA_COHORT,
            "target_evaluator_sha256": load_json(manifest_path(root))["evaluator_sha256"]}
