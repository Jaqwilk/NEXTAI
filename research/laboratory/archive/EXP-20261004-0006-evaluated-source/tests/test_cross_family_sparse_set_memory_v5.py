from __future__ import annotations

import copy
import importlib
from dataclasses import dataclass
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.baseline_semantics import verify_required_baselines
from nextai_autoresearch.benchmarks import cross_family_relation_fragment_transfer_v4 as v4
from nextai_autoresearch.benchmarks import cross_family_shared_representation_v2 as v2
from nextai_autoresearch.benchmarks import cross_family_shared_representation_v3 as v3
from nextai_autoresearch.benchmarks import cross_family_sparse_set_memory_v5 as v5
from nextai_autoresearch.cross_family_transfer_v2_contract import encode
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root, sha256_file


CONTROLS = [
    "specialist_contextual_chow_liu_suite_v2",
    "specialist_empirical_joint_suite_v2",
    "specialist_autoregressive_suite_v2",
    "oracle_cross_family_suite_v2",
]
CANDIDATES = [*v5.CAUSAL_ROLES, *CONTROLS]
FULL_METRICS = [
    "transfer_accuracy", "minimum_family_accuracy", "near_equivalent_accuracy",
    "data_acquisition_ops", "fit_ops", "meta_fit_ops", "mean_query_ops",
    "update_ops", "state_bytes", "peak_state_bytes", "mean_bytes_touched",
    "workload_ops_r16",
]
LEGACY_SHA256 = {
    "src/nextai_autoresearch/benchmarks/cross_family_shared_representation_v1.py":
        "891c143fcbcf8847cb183fb0c5dba0a64afbc227a3d3c4a3e896490f03d2ad4f",
    "src/nextai_autoresearch/benchmarks/cross_family_shared_representation_v2.py":
        "ce8e2f488e917e06d5149c78719f12df7b07a6d68ccd6c4898b2a3f15835fcba",
    "src/nextai_autoresearch/benchmarks/cross_family_shared_representation_v3.py":
        "f8f5f69e66927bee1da8ef947f5611a8f59108cabd21e692061c50bbb4fa2fb7",
    "src/nextai_autoresearch/benchmarks/cross_family_relation_fragment_transfer_v4.py":
        "bafd6654ad3f257a9066406d5660eb3a53af63720e5a241f77f91b5e2ef5e766",
    "src/nextai_autoresearch/candidates/shared_recurrent_predictive_state.py":
        "6801d67e02457d27b194c5f0d9a8bb3dddd8032daab50d8a12479ca4ad6ca268",
    "src/nextai_autoresearch/candidates/independent_recurrent_predictive_state.py":
        "0d9e6326bd4cb8bc57cd85cb203af17ac0f510b69d6ead8ba68d30d3f3ae196c",
    "src/nextai_autoresearch/candidates/shared_relation_fragment_graph.py":
        "ee06565cb9d205216e20aaf6c58097d1e9250f9f6e62492a93ce17ac83ebbcd3",
    "src/nextai_autoresearch/candidates/independent_relation_fragment_graph.py":
        "459d9ef516de8a099a7090c3e6666694762ce26d623dc34b56d6dd6256bded07",
}


def _plan() -> dict:
    plan = copy.deepcopy(load_json(
        project_root() / "research" / "plans" / "EXP-20260830-0050.json"
    ))
    plan["benchmark"] = v5.BENCHMARK_VERSION
    plan["candidates"] = CANDIDATES
    plan["matrix"].update({
        "knowledge_sizes": [8, 32],
        "reasoning_depths": [1, 4, 6],
        "queries_per_cell": 8,
    })
    plan["primary_metrics"] = FULL_METRICS
    maximize = {"transfer_accuracy", "minimum_family_accuracy", "near_equivalent_accuracy"}
    plan["metric_directions"] = {
        metric: "maximize" if metric in maximize else "minimize"
        for metric in FULL_METRICS
    }
    plan["transfer_protocol"].update({
        "shared_candidate": CANDIDATES[0],
        "independent_ablation": CANDIDATES[1],
        "source_identical_dense_ablation": CANDIDATES[2],
        "source_identical_frozen_router_ablation": CANDIDATES[3],
        "specialist_baselines": CONTROLS,
        "learner_contract": "permutation_equivariant_induced_sparse_set_memory_v1",
        "shared_slow_fit_scope": "pooled_training_worlds_only",
        "test_support_adaptation": "same_frozen_set_encoder_and_memory_rule_charged",
        "role_implementation": "sparse_set_memory_core_v1",
        "source_identical_contract": "tokenization_embedding_set_encoder_memory_initialization_fit_order_query_update_output_constants_and_accounting_identical_except_pooled_independent_sparse_dense_or_frozen_routing_v1",
        "embedding_width": 32,
        "memory_slots": 32,
        "sparse_top_k": 4,
        "attention_heads": 1,
        "fit_epochs": 24,
        "batch_size": 32,
        "optimizer": "adam",
        "learning_rate": 0.001,
        "routing_distance": "squared_euclidean",
        "permutation_equivariance": "consistent_anonymous_token_and_world_permutation",
    })
    plan["transfer_protocol"].pop("fragment_capacity", None)
    plan["transfer_protocol"].pop("composition_rule", None)
    return plan


def test_v5_is_a_thin_byte_identical_v2_evaluator_wrapper() -> None:
    assert v5.FAMILIES == v2.FAMILIES
    assert v5._training is v2._training
    assert v5._run_cell is v2._run_cell
    assert v5.run_suite is v2.run_suite
    assert v3._training is v4._training is v5._training
    assert v3.run_suite is v4.run_suite is v5.run_suite


def test_v1_through_v4_evaluators_and_roles_remain_byte_identical() -> None:
    root = project_root()
    assert {
        path: sha256_file(root / path) for path in LEGACY_SHA256
    } == LEGACY_SHA256


def test_v5_public_boundary_is_family_blind_and_field_name_blind() -> None:
    public, privileged, cold, near = v5._training(
        8, 1, 2, 1_500_001, (1103, 2207, 3301)
    )
    assert len(public.training_worlds) == 12 and len(public.test_worlds) == 4
    assert all(not hasattr(world, "family") for world in public.test_worlds)
    assert {world.family for world in privileged.native_worlds} == set(v5.FAMILIES)
    assert set(cold) == set(near) == set(v5.FAMILIES)

    @dataclass(frozen=True)
    class Left:
        secret_name: int
        another_name: tuple[int, ...]

    @dataclass(frozen=True)
    class Right:
        renamed: int
        also_renamed: tuple[int, ...]

    assert encode(Left(7, (8, 9))) == encode(Right(7, (8, 9)))


def test_v5_role_contract_is_disjoint_and_source_identical() -> None:
    assert tuple(v5.ROLE_IMPLEMENTATION) == v5.CAUSAL_ROLES
    assert set(v5.ROLE_IMPLEMENTATION.values()) == {"sparse_set_memory_core_v1"}
    assert tuple(v5.ROLE_INTERVENTION) == v5.CAUSAL_ROLES
    assert len(set(v5.ROLE_INTERVENTION.values())) == 4
    validate_document("experiment_plan", _plan(), project_root())


def test_v5_rejects_mixed_v3_v4_or_partial_v5_contracts() -> None:
    mixed_role = _plan()
    mixed_role["candidates"][1] = "independent_recurrent_predictive_state"
    with pytest.raises(ValidationError, match="was expected"):
        validate_document("experiment_plan", mixed_role, project_root())

    mixed_protocol = _plan()
    mixed_protocol["transfer_protocol"]["fragment_capacity"] = 64
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", mixed_protocol, project_root())

    wrong_constant = _plan()
    wrong_constant["transfer_protocol"]["sparse_top_k"] = 5
    with pytest.raises(ValidationError, match="4 was expected"):
        validate_document("experiment_plan", wrong_constant, project_root())


def test_v5_registered_specialists_pass_preseed_semantic_gate() -> None:
    checked = verify_required_baselines(_plan(), project_root(), run_tests=True)
    assert checked["required"] == CONTROLS


def test_v5_prospective_candidate_bundle_is_absent_or_one_common_core() -> None:
    directory = project_root() / "src" / "nextai_autoresearch" / "candidates"
    wrappers = tuple(directory / f"{role}.py" for role in v5.CAUSAL_ROLES)
    core = directory / "sparse_set_memory_core_v1.py"
    present = tuple(path.is_file() for path in (*wrappers, core))
    if not any(present):
        pytest.skip("v5 candidates are intentionally absent before preregistration")
    assert all(present), "partial prospective v5 candidate bundle"

    classes = [
        importlib.import_module(f"nextai_autoresearch.candidates.{role}").Candidate
        for role in v5.CAUSAL_ROLES
    ]
    assert len({candidate.__bases__ for candidate in classes}) == 1
    assert classes[0].__bases__[0].__module__.endswith("sparse_set_memory_core_v1")
    instances = [candidate(7) for candidate in classes]
    assert [instance.mode for instance in instances] == list(v5.ROLE_INTERVENTION.values())
    for instance in instances:
        assert (
            instance.embedding_width,
            instance.memory_slots,
            instance.sparse_top_k,
            instance.attention_heads,
            instance.fit_epochs,
            instance.batch_size,
            instance.learning_rate,
            instance.routing_distance,
        ) == (32, 32, 4, 1, 24, 32, 0.001, "squared_euclidean")
