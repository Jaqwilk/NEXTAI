from __future__ import annotations

import importlib
import tomllib
from dataclasses import fields

import numpy as np
from scipy.sparse import diags

from nextai_autoresearch.baseline_semantics import required_baseline_names
from nextai_autoresearch.benchmarks import heldout_suitesparse_cross_matrix_prolongation_v1 as bench
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


def test_frozen_payload_hashes_and_split_are_disjoint() -> None:
    assert bench.verify_static_contract() == {
        "train": 12, "test": 3, "targets": [9801, 10605, 81920],
    }


def test_candidate_boundary_contains_only_anonymous_csr_numerics() -> None:
    assert tuple(item.name for item in fields(bench.AnonymousSparseOperator)) == (
        "shape", "indptr", "indices", "data",
    )


def test_four_roles_share_one_implementation_and_only_scope_changes() -> None:
    assert len(set(bench.BASE_IMPLEMENTATION.values())) == 1
    _, pairs = bench._records()
    for pair in pairs:
        support = bench._training_names("support_only", pair)
        independent = bench._training_names("independent", pair)
        cross = bench._training_names("cross_family_only", pair)
        shared = bench._training_names("shared", pair)
        assert support == independent == (pair["source"],)
        assert set(cross).isdisjoint(support)
        assert set(shared) == set(cross) | set(support)


def test_contract_preserves_complete_low_quality_recycling_outcome() -> None:
    audit = bench.contract_audit()
    assert audit["pass"]
    assert audit["checks"]["generic_reuse_is_complete_low_quality"]
    assert audit["controls"] == list(bench.CONTROL_NAMES)
    assert not audit["runner_random_scoring_seed_realized"]
    assert not audit["scoring_performed"]


def test_real_file_standard_sa_smoke_meets_frozen_residual() -> None:
    smoke = bench.development_smoke()
    assert smoke["pass"]
    assert smoke["relative_residual"] <= bench.RTOL


def test_five_controls_execute_their_declared_hierarchy_semantics() -> None:
    _, pairs = bench._records()
    pair = next(item for item in pairs if item["size"] == 10605)
    source, target = bench._load_matrix(pair["source"]), bench._load_matrix(pair["target"])
    standard, _, _, _ = bench._control("target_standard_sa_v1", source, target)
    adaptive, _, _, _ = bench._control("target_adaptive_sa_v1", source, target)
    frozen, _, frozen_update, _ = bench._control("source_frozen_hierarchy_v1", source, target)
    refreshed, _, refresh_update, _ = bench._control("fixed_pr_numeric_refresh_v1", source, target)
    none, setup, update, _ = bench._control("unpreconditioned_cg_v1", source, target)
    assert standard.levels[0].A is target and adaptive.levels[0].A is target
    assert frozen.levels[0].A is target and frozen_update == target.nnz
    assert refreshed.levels[0].A is target and refresh_update > target.nnz
    assert none is None and setup == update == 0.0


def test_retained_config_and_preseed_baseline_discovery_match_contract() -> None:
    with (project_root() / "config/research.toml").open("rb") as handle:
        config = tomllib.load(handle)
    historical = load_json(project_root() / "research/manifests/PC-01-ACTIVATION-BEFORE.json")
    assert historical["benchmark_version"] == bench.BENCHMARK_VERSION
    # New diagnostic activation does not change the retained SuiteSparse contract.
    assert config["project"]["benchmark_version"] == "pc01_byte_lm_learning_measurement_v2"
    assert config["project"]["protocol_version"] == 3
    assert config["project"]["benchmark_status"] == "active"
    protocol = config["suitesparse_cross_matrix"]
    assert protocol["source_identical_contract"] == bench.SOURCE_IDENTICAL_CONTRACT
    plan = {"suitesparse_transfer_protocol": {
        "classical_baselines": list(bench.CONTROL_NAMES),
    }}
    assert required_baseline_names(plan) == list(bench.CONTROL_NAMES)


def test_future_preregistration_schema_freezes_the_entire_contract() -> None:
    root = project_root()
    plan = load_json(root / "research/plans/EXP-20260901-0062.json")
    for key in list(plan):
        if key.endswith("_protocol"):
            plan.pop(key)
    protocol = tomllib.loads((root / "config/research.toml").read_text(encoding="utf-8"))[
        "suitesparse_cross_matrix"
    ]
    metrics = list(protocol["pareto_capability_metrics"])
    plan.update({
        "benchmark": bench.BENCHMARK_VERSION,
        "candidates": [*bench.ROLE, *bench.CONTROL_NAMES],
        "matrix": {"knowledge_sizes": list(bench.TARGET_SIZES), "reasoning_depths": [1],
                   "queries_per_cell": 1, "seed_policy": {"method": "runner_random_v1",
                   "count": 1, "minimum": 1000000, "maximum": 2147483647}},
        "primary_metrics": [*metrics, "shared_vs_independent_gain", "cross_family_transfer_gain"],
        "metric_directions": {name: "maximize" if name in {"accuracy", "transfer_accuracy",
            "minimum_family_accuracy", "shared_vs_independent_gain", "cross_family_transfer_gain"}
            else "minimize" for name in [*metrics, "shared_vs_independent_gain", "cross_family_transfer_gain"]},
        "suitesparse_transfer_protocol": {
            "dataset_id": protocol["dataset_id"],
            "candidate_boundary": "anonymous_csr_shape_indptr_indices_data_only",
            "target_metadata": "evaluator_private", "target_result_access_during_fit": "forbidden",
            "shared_candidate": protocol["shared_candidate"],
            "independent_ablation": protocol["independent_ablation"],
            "cross_family_only_ablation": protocol["cross_family_only_ablation"],
            "support_only_ablation": protocol["support_only_ablation"],
            "classical_baselines": list(protocol["classical_baselines"]),
            "source_identical_contract": protocol["source_identical_contract"],
            "relative_residual_maximum": protocol["relative_residual_maximum"],
            "maximum_iterations": protocol["maximum_iterations"],
            "declared_horizons": list(protocol["declared_horizons"]),
            "state_budget_bytes": protocol["state_budget_bytes"],
            "pareto_capability_metrics": metrics,
            "invalidation_rules": list(protocol["invalidation_rules"]),
        },
    })
    validate_document("experiment_plan", plan, root)


def test_prospective_learned_role_bundle_lifecycle_and_semantics() -> None:
    root = project_root()
    names = tuple(bench.ROLE)
    paths = tuple(
        root / "src" / "nextai_autoresearch" / "candidates" / f"{name}.py"
        for name in names
    )
    present = tuple(path.is_file() for path in paths)
    assert not any(present) or all(present)
    if not all(present):
        return

    modules = tuple(importlib.import_module(
        f"nextai_autoresearch.candidates.{name}"
    ) for name in names)
    core = modules[0]
    assert all(module.Candidate is core.Candidate for module in modules)
    assert (core.RELAXATION_STEPS, core.RELAXATION_WEIGHT, core.RIDGE) == (
        8, 2.0 / 3.0, 1e-3,
    )

    matrix = diags(
        [-np.ones(11), np.linspace(2.2, 3.0, 12), -np.ones(11)],
        [-1, 0, 1], format="csr",
    )
    permutation = np.array([4, 0, 9, 2, 11, 6, 1, 8, 5, 10, 3, 7])
    permuted = matrix[permutation][:, permutation].tocsr()
    features = core.local_features(bench.anonymous(matrix))
    permuted_features = core.local_features(bench.anonymous(permuted))
    np.testing.assert_allclose(permuted_features, features[permutation], atol=1e-11)

    learner = core.Candidate(seed=7)
    learner.fit((bench.anonymous(matrix),))
    vectors = learner.candidate_vectors(bench.anonymous(matrix))
    permuted_vectors = learner.candidate_vectors(bench.anonymous(permuted))
    assert vectors.shape == (12, 2)
    np.testing.assert_allclose(vectors[:, 0], 1.0)
    np.testing.assert_allclose(permuted_vectors, vectors[permutation], atol=1e-10)
    assert abs(float(np.mean(vectors[:, 1]))) < 1e-11
    assert learner.fit_ops > 0 and learner.state_bytes() > 0

    contrasting = diags(
        [-0.2 * np.ones(11), np.linspace(1.0, 4.0, 12), -1.4 * np.ones(11)],
        [-1, 0, 1], format="csr",
    )
    other = core.Candidate(seed=7)
    other.fit((bench.anonymous(contrasting),))
    assert np.linalg.norm(learner.coefficients - other.coefficients) > 1e-7
