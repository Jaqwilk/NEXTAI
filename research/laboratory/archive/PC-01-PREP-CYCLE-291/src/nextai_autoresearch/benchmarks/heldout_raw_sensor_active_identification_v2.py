from __future__ import annotations

from typing import Any

from . import heldout_raw_sensor_active_identification_v1 as v1


BENCHMARK_VERSION = "heldout_raw_sensor_active_identification_v2"
TRAIN_WORLD_SEEDS = v1.TRAIN_WORLD_SEEDS
DEVELOPMENT_SEED = v1.DEVELOPMENT_SEED
SENSOR_COUNT = v1.SENSOR_COUNT
SUPPORT_REPETITIONS = v1.SUPPORT_REPETITIONS
NOISE_STD = v1.NOISE_STD
KNOWLEDGE_SIZES = v1.KNOWLEDGE_SIZES
PROBE_BUDGETS = v1.PROBE_BUDGETS
BASELINES = v1.BASELINES

ROLE_IMPLEMENTATION = {
    "shared_posterior_partition_decision_dag_v1": "posterior_partition_decision_dag_core_v1",
    "source_identical_support_only_partition_dag_v1": "posterior_partition_decision_dag_core_v1",
    "source_identical_frozen_partition_dag_v1": "posterior_partition_decision_dag_core_v1",
}
ROLE_POLICY_SOURCE = {
    "shared_posterior_partition_decision_dag_v1": "meta_worlds",
    "source_identical_support_only_partition_dag_v1": "heldout_support",
    "source_identical_frozen_partition_dag_v1": "frozen",
}
SOURCE_IDENTICAL_CONTRACT = (
    "probe_boundary_constants_support_order_query_output_identical_except_"
    "meta_support_or_frozen_partition_policy_v1"
)


def verify_role_contract(protocol: dict[str, Any]) -> dict[str, str]:
    fields = {
        "shared_candidate": "shared_posterior_partition_decision_dag_v1",
        "support_only_ablation": "source_identical_support_only_partition_dag_v1",
        "frozen_representation_ablation": "source_identical_frozen_partition_dag_v1",
    }
    for field, expected in fields.items():
        if protocol.get(field) != expected:
            raise ValueError(f"raw-sensor v2 role mismatch: {field}")
    if protocol.get("source_identical_contract") != SOURCE_IDENTICAL_CONTRACT:
        raise ValueError("raw-sensor v2 source-identical contract mismatch")
    if len(set(ROLE_IMPLEMENTATION.values())) != 1:
        raise RuntimeError("raw-sensor v2 roles do not resolve to one implementation")
    return {name: ROLE_POLICY_SOURCE[name] for name in fields.values()}


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    verify_role_contract(plan["active_sensor_protocol"])
    return v1.run_suite(candidate_name, plan)


development_smoke = v1.development_smoke
