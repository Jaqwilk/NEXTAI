from __future__ import annotations

import inspect

import numpy as np
import pytest

from nextai_autoresearch.audit import audit_relational_candidate_source
from nextai_autoresearch.benchmarks import anonymous_repeated_measurement_ood_v1 as benchmark
from nextai_autoresearch.relational_ood_contract import (
    COST_FIELDS,
    RelationalQueryBatch,
    RelationalTrainingBatch,
)


def test_exact_frozen_contract_constants() -> None:
    assert benchmark.SOURCE_DIM == 16
    assert benchmark.INPUT_DIM == 32
    assert benchmark.SCALES == (64, 256, 1024)
    assert benchmark.MEASUREMENTS_PER_SOURCE == 2
    assert benchmark.QUERIES_PER_CONDITION == 256
    assert benchmark.TRAIN_NUISANCE == (
        (1 / 16, 0.0),
        (1 / 8, 0.0),
        (0.0, 1 / 16),
        (0.0, 1 / 8),
    )
    assert benchmark.QUERY_NUISANCE["s1"] == (3 / 16, 3 / 16)
    assert benchmark.QUERY_NUISANCE["s2"] == (1 / 4, 1 / 4)
    assert benchmark.QUERY_NUISANCE["s3"] == (3 / 8, 3 / 8)


def test_relation_is_constructed_before_probe_target_and_nuisance() -> None:
    trace = benchmark.CONSTRUCTION_TRACE
    assert trace.index("relation graph") < trace.index("public probes")
    assert trace.index("relation graph") < trace.index("targets")
    assert trace.index("relation graph") < trace.index("nuisance realization")
    source = inspect.getsource(benchmark._build_training)
    assert source.index("pre_edges =") < source.index("probes =")
    assert source.index("pre_edges =") < source.index("targets =")
    assert source.index("pre_edges =") < source.index("nuisance_index =")
    assert source.index("shuffled_pre =") < source.index("batch_permutation =")
    assert source.index("random_pre =") < source.index("batch_permutation =")


def test_roles_are_bit_identical_except_relations() -> None:
    audit = benchmark.role_bit_identity(benchmark.build_audit_fixture(256))
    assert audit["pass"]
    hashes = list(audit["hashes"].values())
    assert all(item == hashes[0] for item in hashes)
    assert audit["relation_hashes"]["correct"] != audit["relation_hashes"]["shuffled"]


def test_relation_roles_have_the_declared_matching_semantics() -> None:
    audit = benchmark.relation_construction_audit(benchmark.build_audit_fixture(1024))
    assert audit["pass"]
    assert audit["correct"]["true_pair_count"] == 1024
    assert audit["shuffled"]["true_pair_count"] == 0
    assert audit["random"]["true_pair_count"] == 0
    assert audit["passive"]["active_count"] == 0
    assert all(audit[name]["degree_min"] == audit[name]["degree_max"] == 1 for name in ("correct", "shuffled", "random"))


def test_target_leakage_attackers_fail() -> None:
    audit = benchmark.target_leakage_audit(benchmark.build_audit_fixture(1024))
    assert audit["pass"]
    assert audit["edge_truth_target_pair_mi_bits"] < 0.08
    assert audit["edge_truth_absolute_target_gap_correlation"] < 0.10
    assert audit["correct_pair_target_correlation"] < 0.10
    assert audit["source_conditional_target_distribution_exact_tv"] == 0.0
    assert audit["record_index_target_prediction_relative_gain"] < 0.05


def test_source_identity_metadata_attackers_fail() -> None:
    audit = benchmark.source_identity_leakage_audit(benchmark.build_audit_fixture(1024))
    assert audit["pass"]
    assert not audit["public_source_labels"]
    assert not audit["public_nuisance_labels"]
    assert not audit["public_filenames"]


def test_public_contract_does_not_expose_evaluation_targets_or_private_state() -> None:
    fixture = benchmark.build_audit_fixture(64)
    query = fixture.queries["s1"].public
    assert isinstance(query, RelationalQueryBatch)
    assert not hasattr(query, "targets")
    assert set(RelationalTrainingBatch.__dataclass_fields__) == {
        "records",
        "targets",
        "relation_edges",
        "relation_mask",
        "batch_order",
    }
    assert set(RelationalQueryBatch.__dataclass_fields__) == {"records"}


def test_both_permutations_are_bijections_and_preserve_oracle_targets() -> None:
    audit = benchmark.permutation_audit()
    assert audit["pass"]
    assert sorted(audit["main_permutation"]) == list(range(32))
    assert sorted(audit["adversarial_permutation"]) == list(range(32))


@pytest.mark.parametrize("variant", ["main", "adversarial"])
@pytest.mark.parametrize("scale", benchmark.SCALES)
def test_oracle_is_exact_at_every_scale_and_condition(scale: int, variant: str) -> None:
    audit = benchmark.oracle_sanity(benchmark.build_audit_fixture(scale, variant))
    assert audit["pass"]
    assert all(error == 0.0 for error in audit["max_absolute_error"].values())


def test_strong_classical_controls_are_numerically_feasible() -> None:
    audit = benchmark.classical_control_feasibility(benchmark.build_audit_fixture(64))
    assert audit["pass"]
    assert audit["regularization"] == benchmark.CCA_REGULARIZATION
    assert audit["rank"] == benchmark.CCA_RANK
    assert audit["tolerance"] == benchmark.NUMERICAL_TOLERANCE
    assert len(audit["controls"]) == 3


def test_passive_degree2_control_falsifies_relational_discrimination() -> None:
    audit = benchmark.contract_audit()
    assert audit["decision"] == "E"
    assert not audit["scoring_authorized"]
    assert audit["passive_polynomial_ridge"]["1024"][
        "all_ood_at_or_below_frozen_ceiling"
    ]


def test_nuisance_difficulty_is_monotone_on_ood_conditions() -> None:
    audit = benchmark.nuisance_sanity()
    assert audit["pass"]
    assert audit["analytic_rms_corruption"][-3] < audit["analytic_rms_corruption"][-2] < audit["analytic_rms_corruption"][-1]
    assert audit["empirical_rms_corruption"][-3] < audit["empirical_rms_corruption"][-2] < audit["empirical_rms_corruption"][-1]


def test_scale_and_query_counts_are_exact() -> None:
    audit = benchmark.scale_sanity()
    assert audit["pass"]
    for scale in benchmark.SCALES:
        item = audit["counts"][str(scale)]
        assert item["training_records"] == 2 * scale
        assert item["correct_relations"] == scale
        assert item["queries_per_condition"] == [256, 256, 256, 256]


def test_fixture_rerun_is_exact_and_uses_no_runner_scoring_seed() -> None:
    first = benchmark.build_audit_fixture(256, "main", benchmark.DEVELOPMENT_FIXTURE_SEED)
    second = benchmark._build_training(256, "main", benchmark.DEVELOPMENT_FIXTURE_SEED + 256)
    assert np.array_equal(first.private_training.public_records, second.public_records)
    assert np.array_equal(first.private_training.targets, second.targets)
    assert benchmark.DEVELOPMENT_FIXTURE_SEED < 1_000_000


def test_relational_candidate_boundary_rejects_private_state_rng_and_roles() -> None:
    safe = """
class Candidate:
    def fit(self, batch):
        self.mean = sum(batch.targets) / len(batch.targets)
"""
    unsafe = """
import random
class Candidate:
    def fit(self, batch, role):
        if role == 'correct':
            return batch.latent_records, random.random()
"""
    assert audit_relational_candidate_source(safe) == ()
    problems = audit_relational_candidate_source(unsafe)
    assert any("role-specific" in problem for problem in problems)
    assert any("private" in problem for problem in problems)
    assert any("random" in problem for problem in problems)


def test_cost_schema_is_complete_and_nonnegative() -> None:
    audit = benchmark.cost_accounting_audit()
    assert audit["pass"]
    assert tuple(audit["fields"]) == COST_FIELDS
    assert "diagnostic" in audit["wall_time_status"]


def test_service_only_evaluator_hard_stops_scoring() -> None:
    with pytest.raises(RuntimeError, match="service-audit only"):
        benchmark.run_suite()
