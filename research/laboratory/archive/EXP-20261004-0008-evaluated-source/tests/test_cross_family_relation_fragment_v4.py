from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.baseline_semantics import verify_required_baselines
from nextai_autoresearch.benchmarks import cross_family_relation_fragment_transfer_v4 as bench_v4
from nextai_autoresearch.benchmarks import cross_family_shared_representation_v2 as bench_v2
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


CANDIDATES = [
    "shared_relation_fragment_graph",
    "independent_relation_fragment_graph",
    "specialist_contextual_chow_liu_suite_v2",
    "specialist_empirical_joint_suite_v2",
    "specialist_autoregressive_suite_v2",
    "oracle_cross_family_suite_v2",
]
FULL_METRICS = [
    "transfer_accuracy", "minimum_family_accuracy", "near_equivalent_accuracy",
    "data_acquisition_ops", "fit_ops", "meta_fit_ops", "mean_query_ops",
    "update_ops", "state_bytes", "peak_state_bytes", "mean_bytes_touched",
    "workload_ops_r16",
]


def _v4_plan() -> dict:
    plan = copy.deepcopy(load_json(
        project_root() / "research" / "plans" / "EXP-20260830-0050.json"
    ))
    plan["benchmark"] = bench_v4.BENCHMARK_VERSION
    plan["candidates"] = CANDIDATES
    plan["primary_metrics"] = FULL_METRICS
    minimize = set(FULL_METRICS) - {
        "transfer_accuracy", "minimum_family_accuracy", "near_equivalent_accuracy"
    }
    plan["metric_directions"] = {
        value: "minimize" if value in minimize else "maximize"
        for value in FULL_METRICS
    }
    plan["transfer_protocol"].update({
        "shared_candidate": CANDIDATES[0],
        "independent_ablation": CANDIDATES[1],
        "specialist_baselines": CANDIDATES[2:],
        "learner_contract": "anonymous_relation_fragment_graph_v1",
        "test_support_adaptation": "same_frozen_fragment_extractor_charged",
        "fragment_capacity": 64,
        "composition_rule": "typed_equality_join_then_component_emit_v1",
        "permutation_equivariance": "atom_relabeling_and_anonymous_world_permutation",
    })
    return plan


def test_v4_reuses_lossless_four_family_boundary() -> None:
    public, privileged, cold, near = bench_v4._training(
        8, 1, 2, 1_500_001, (1103, 2207, 3301)
    )
    assert bench_v4.FAMILIES == bench_v2.FAMILIES
    assert len(public.training_worlds) == 12 and len(public.test_worlds) == 4
    assert all(not hasattr(world, "family") for world in public.test_worlds)
    assert {world.family for world in privileged.native_worlds} == set(bench_v4.FAMILIES)
    assert set(cold) == set(near) == set(bench_v4.FAMILIES)


def test_v4_plan_freezes_candidates_fragment_contract_and_full_costs() -> None:
    plan = _v4_plan()
    validate_document("experiment_plan", plan, project_root())
    plan["primary_metrics"].remove("workload_ops_r16")
    del plan["metric_directions"]["workload_ops_r16"]
    with pytest.raises(ValidationError, match="does not contain"):
        validate_document("experiment_plan", plan, project_root())


def test_v4_plan_rejects_wrong_fragment_contract() -> None:
    plan = _v4_plan()
    plan["transfer_protocol"]["fragment_capacity"] = 65
    with pytest.raises(ValidationError, match="64 was expected"):
        validate_document("experiment_plan", plan, project_root())


def test_v4_registered_specialists_pass_preseed_semantic_gate() -> None:
    plan = _v4_plan()
    checked = verify_required_baselines(plan, project_root(), run_tests=True)
    assert checked["required"] == CANDIDATES[2:]

