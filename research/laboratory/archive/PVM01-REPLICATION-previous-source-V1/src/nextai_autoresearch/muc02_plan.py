"""Small cohort adapter; the prospective repair contract fixes every parameter."""
from .audit_repair import AUTHORITY, PLAN, ROLES
from .utils import load_json, sha256_file

METRICS = ["accuracy", "continual_new_fact_accuracy", "continual_retention", "exact_span_accuracy",
           "near_equivalent_accuracy", "stable_rollout_rate", "preprocessing_ops", "fit_ops", "mean_query_ops",
           "mean_search_ops", "update_ops", "p95_latency_us", "state_bytes", "peak_state_bytes",
           "mean_bytes_touched", "workload_ops_r1", "workload_ops_r4", "workload_ops_r16"]


def protocol(base):
    contract = load_json(base / PLAN)
    return {"authority_path": AUTHORITY, "contract_path": PLAN, "contract_sha256": sha256_file(base / PLAN),
            "classical_baselines": list(ROLES), "fit_steps_cap": contract["recipe"]["updates"],
            "fit_seconds_cap": contract["resources"]["fit_seconds_per_role"],
            "worker_seconds_cap": contract["resources"]["worker_seconds_per_role"],
            "max_rss_bytes": contract["resources"]["max_rss_bytes"],
            "max_cuda_reserved_bytes": contract["resources"]["max_cuda_reserved_bytes"],
            "train_worlds_per_cell": 45, "development_worlds_per_cell": 15, "calibration_worlds_per_cell": 15,
            "declared_reuses": [1, 4, 16], "control_thresholds": contract["quality_gates"],
            "recipe": contract["recipe"], "cost_contract": contract["measurement"],
            "invalidation_rules": ["Missing answers, world/cell coverage or costs invalidate the comparison",
                                   "Any terminal outcome consumes the one registration; no automatic retry",
                                   "No private generator, answers or strata may reach a candidate before prediction",
                                   "No post-calibration recipe, threshold, selection or seed change"]}


def configure_plan(plan, args, base, directions):
    if tuple(args.candidates) != ROLES or args.budget != "quick":
        raise ValueError("MUC v2 requires the exact four frozen roles and quick budget")
    plan["matrix"] = {"knowledge_sizes": [32, 128, 512], "reasoning_depths": [1, 2, 4], "queries_per_cell": 16,
                      "seed_policy": {"method": "runner_random_v1", "count": 1, "minimum": 1_000_000, "maximum": 2_147_483_647}}
    plan["primary_metrics"] = METRICS
    plan["metric_directions"] = {name: directions[name] for name in METRICS}
    plan["muc02_protocol"] = protocol(base)
    plan["eligibility_contract"] = {"metric": "accuracy", "minimum": 0.85}
