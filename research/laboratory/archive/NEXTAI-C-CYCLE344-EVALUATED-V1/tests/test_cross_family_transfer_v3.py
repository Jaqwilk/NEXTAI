from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.baseline_semantics import verify_required_baselines
from nextai_autoresearch.benchmarks import cross_family_shared_representation_v2 as bench_v2
from nextai_autoresearch.benchmarks import cross_family_shared_representation_v3 as bench_v3
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


def test_v3_reuses_frozen_world_boundary_without_family_leakage() -> None:
    public, privileged, cold, near = bench_v3._training(
        8, 1, 2, 1_500_001, (1103, 2207, 3301)
    )
    assert bench_v3.FAMILIES == bench_v2.FAMILIES
    assert len(public.training_worlds) == 12 and len(public.test_worlds) == 4
    assert all(not hasattr(world, "family") for world in public.test_worlds)
    assert {world.family for world in privileged.native_worlds} == set(bench_v3.FAMILIES)
    assert set(cold) == set(near) == set(bench_v3.FAMILIES)


def _v3_plan() -> dict:
    plan = copy.deepcopy(load_json(
        project_root() / "research" / "plans" / "EXP-20260830-0046.json"
    ))
    plan["benchmark"] = bench_v3.BENCHMARK_VERSION
    plan["candidates"] = [
        "shared_recurrent_predictive_state",
        "independent_recurrent_predictive_state",
        "specialist_contextual_chow_liu_suite_v2",
        "specialist_empirical_joint_suite_v2",
        "specialist_autoregressive_suite_v2",
        "oracle_cross_family_suite_v2",
    ]
    plan["transfer_protocol"].update({
        "shared_candidate": "shared_recurrent_predictive_state",
        "independent_ablation": "independent_recurrent_predictive_state",
        "specialist_baselines": plan["candidates"][2:],
        "learner_contract": "tied_recurrent_predictive_state_width32_v1",
        "shared_slow_fit_scope": "pooled_training_worlds_only",
        "test_support_adaptation": "same_frozen_rule_charged",
    })
    return plan


def test_v3_plan_requires_shared_and_source_identical_independent_candidates() -> None:
    plan = _v3_plan()
    validate_document("experiment_plan", plan, project_root())
    plan["candidates"].remove("independent_recurrent_predictive_state")
    with pytest.raises(ValidationError, match="does not contain"):
        validate_document("experiment_plan", plan, project_root())


def test_v3_registered_specialists_pass_preseed_semantic_gate() -> None:
    plan = _v3_plan()
    checked = verify_required_baselines(plan, project_root(), run_tests=True)
    assert checked["required"] == plan["transfer_protocol"]["specialist_baselines"]
