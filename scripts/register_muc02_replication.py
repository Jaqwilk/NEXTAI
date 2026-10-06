"""Register exactly one canonical experiment under the new sidecar authority."""
import copy
import json
from pathlib import Path
from nextai_autoresearch.config import load_config
from nextai_autoresearch.gates import ensure_can_create_plan
from nextai_autoresearch.integrity import manifest_path
from nextai_autoresearch.ledger import append_jsonl, next_experiment_id
from nextai_autoresearch.muc02_replication_stage import protocol, status
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.runner import environment_fingerprint
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_json, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
ensure_can_create_plan(root)
stage = status(root)
assert stage["scoring_authorized"] and stage["registrations_used"] == 0
identity = next_experiment_id(root)
parent = load_json(root / "research/plans/EXP-20261004-0001.json")
plan = copy.deepcopy(parent)
config = load_config(root)
environment = environment_fingerprint(root)
plan.update(experiment_id=identity, created_at=utc_now(), benchmark=config.benchmark_version,
            evaluator_sha256=load_json(manifest_path(root))["evaluator_sha256"],
            title="Independent MUC02 random versus hard negatives replication, fixed4096/192",
            parent_experiment_id="EXP-20261004-0001", status="planned",
            git_before={"commit": environment["git_commit"], "branch": environment["git_branch"], "dirty": environment["git_dirty"]},
            muc02_negatives_protocol=protocol(root),
            confounds=["Visible synthetic development replication; five units jointly vary initialization and fresh train/dev. Old failed results are disclosed and never pooled. Fixed bounded graph construction conditions on query-stratum feasibility."],
            alternative_explanations=["Effect may depend on byte grammar, entity prefixes, conditional graph generation or absence distribution; no natural-language/transfer claim."])
validate_document("experiment_plan", plan, root)
relative = f"research/plans/{identity}.json"
assert not (root / relative).exists()
atomic_write_json(root / relative, plan)
append_jsonl(root / "research/plan_registry.jsonl", {"experiment_id": identity, "plan_sha256": sha256_json(plan), "plan_path": relative, "created_at": utc_now()})
append_jsonl(root / "research/events.jsonl", {"event": "muc02_replication_registered", "stage_id": stage["id"], "created_at": utc_now(),
    "experiment_id": identity, "plan_path": relative, "plan_sha256": sha256_json(plan)})
print(json.dumps({"experiment_id": identity, "plan_path": relative, "scoring_seed_draws": 0, "fit": 0}))
