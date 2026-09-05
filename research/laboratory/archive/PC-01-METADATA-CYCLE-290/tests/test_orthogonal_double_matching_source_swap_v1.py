from __future__ import annotations

import tomllib
from pathlib import Path

import numpy as np
import pytest

from nextai_autoresearch.audit import audit_relational_candidate_source
from nextai_autoresearch.benchmarks import (
    orthogonal_double_matching_source_swap_v1 as benchmark,
)
from nextai_autoresearch.relational_identifiability_contract import (
    RID_COST_FIELDS,
    AnonymousQueryBatch,
    AnonymousRelationalBatch,
)


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_contract_constants() -> None:
    assert benchmark.CONTRACT_ID == "RID-CONTRACT-001"
    assert benchmark.LATENT_DIM == 16
    assert benchmark.INPUT_DIM == 48
    assert benchmark.SCALES == (64, 256, 1024)
    assert benchmark.ROLES == ("correct", "shuffled", "random", "passive")


def test_orthogonal_mixer_and_block_exchangeability() -> None:
    audit = benchmark.mixer_audit()
    assert audit["pass"]
    fixture = benchmark.build_audit_fixture(64)
    assert benchmark.twin_world_certificate(fixture)["pass"]


def test_train_enforces_n_equals_s_and_exact_h1_h2() -> None:
    fixture = benchmark.build_audit_fixture(64)
    labeled = fixture.private_training.label_mask
    assert np.array_equal(
        fixture.private_training.first_values[labeled],
        fixture.private_training.second_values[labeled],
    )
    assert benchmark.exact_ambiguity_audit(fixture)["pass"]


def test_iid_h1_h2_are_pointwise_identical() -> None:
    fixture = benchmark.build_audit_fixture(64)
    assert np.array_equal(fixture.iid.first_targets, fixture.iid.second_targets)


def test_ood_is_independent_and_has_analytic_risks() -> None:
    audit = benchmark.ood_discriminator_audit()
    assert audit["pass"]
    assert audit["nrmse"]["h1"] <= 1e-14
    assert audit["nrmse"]["h2"] == pytest.approx(np.sqrt(2.0), abs=0.02)
    assert audit["nrmse"]["symmetric"] == pytest.approx(
        1.0 / np.sqrt(2.0), abs=0.01
    )
    assert audit["first_second_cross_moment_normalized"] <= 0.05


def test_passive_twin_world_public_transcript_is_byte_identical() -> None:
    audit = benchmark.twin_world_certificate(benchmark.build_audit_fixture(1024))
    assert audit["pass"]
    assert audit["public_world_hashes"] == audit["public_swap_hashes"]
    assert audit["train_targets_byte_identical"]
    assert audit["iid_targets_byte_identical"]


def test_matchings_are_perfect_edge_disjoint_and_collision_free() -> None:
    audit = benchmark.matching_audit(benchmark.build_audit_fixture(1024))
    assert audit["pass"]
    assert audit["first_second_edge_disjoint"]
    assert audit["passive_active_edges"] == 0
    assert audit["shuffled"]["pass"]
    assert audit["random"]["pass"]


def test_roles_are_bit_identical_outside_relation_endpoints_and_masks() -> None:
    audit = benchmark.role_bit_identity(benchmark.build_audit_fixture(256))
    assert audit["pass"]
    shared = list(audit["shared_hashes"].values())
    assert all(item == shared[0] for item in shared)


def test_correct_relation_recovers_only_the_first_subspace() -> None:
    audit = benchmark.relation_operator_audit()
    assert audit["pass"]
    final = audit["scales"]["1024"]
    assert final["first_overlap"] >= benchmark.FINAL_SUBSPACE_OVERLAP_MINIMUM
    assert final["second_overlap"] <= benchmark.FINAL_SUBSPACE_LEAKAGE_MAXIMUM
    assert final["probe_overlap"] <= benchmark.FINAL_SUBSPACE_LEAKAGE_MAXIMUM


def test_null_relations_converge_to_zero_without_hidden_collision() -> None:
    audit = benchmark.null_relation_audit()
    assert audit["pass"]
    assert audit["shuffled"]["pass"]
    assert audit["random"]["pass"]


def test_target_leakage_attackers_fail() -> None:
    audit = benchmark.target_leakage_audit(benchmark.build_audit_fixture(1024))
    assert audit["pass"]
    assert audit["paired_endpoint_target_prediction_gain"] < 0.05
    assert audit["endpoint_index_degree_position_prediction_gain"] < 0.05


def test_public_contract_and_source_firewall_hide_semantics() -> None:
    audit = benchmark.ontology_firewall_audit(ROOT)
    assert audit["pass"]
    assert set(AnonymousRelationalBatch.__dataclass_fields__) == {
        "records",
        "targets",
        "label_mask",
        "relation_edges",
        "relation_mask",
        "batch_order",
    }
    assert set(AnonymousQueryBatch.__dataclass_fields__) == {"records"}


def test_candidate_cannot_import_evaluator_or_branch_on_role_world() -> None:
    safe = """
class Candidate:
    def fit(self, batch):
        return sum(value for value, keep in zip(batch.targets, batch.label_mask) if keep)
"""
    unsafe = """
from nextai_autoresearch.benchmarks import orthogonal_double_matching_source_swap_v1
class Candidate:
    def fit(self, batch, role):
        if role == 'correct':
            return batch.stable_latent, batch.world_identity
"""
    assert audit_relational_candidate_source(safe) == ()
    problems = audit_relational_candidate_source(unsafe)
    assert any("protected evaluator" in problem for problem in problems)
    assert any("role-specific" in problem for problem in problems)
    assert sum("private" in problem for problem in problems) >= 2


def test_historical_strong_control_failure_remains_visible() -> None:
    audit = benchmark.classical_control_audit()
    assert not audit["pass"]
    assert audit["visible_boundary_only"]
    assert audit["rank_rule"] == 16


def test_passive_controls_fit_iid_without_identifying_ood_side() -> None:
    audit = benchmark.passive_identifiability_audit()
    assert audit["pass"]
    assert audit["preference_sign_flips_exactly"]
    assert audit["same_public_prediction_in_both_worlds"]


def test_three_scales_change_only_relation_sample_count() -> None:
    audit = benchmark.scale_sanity()
    assert audit["pass"]
    assert [audit["counts"][str(scale)]["relation_samples"] for scale in benchmark.SCALES] == [64, 256, 1024]
    assert len({audit["counts"][str(scale)]["labeled_train_records"] for scale in benchmark.SCALES}) == 1


def test_development_fixture_is_exact_and_no_scoring_seed_exists() -> None:
    audit = benchmark.deterministic_fixture_audit()
    assert audit["pass"]
    assert not audit["runner_random_scoring_seed_realized"]


def test_cost_schema_is_complete_and_nonnegative() -> None:
    audit = benchmark.cost_accounting_audit()
    assert audit["pass"]
    assert tuple(audit["fields"]) == RID_COST_FIELDS


def test_service_only_evaluator_hard_stops_candidate_scoring() -> None:
    with pytest.raises(RuntimeError, match="candidate scoring is forbidden"):
        benchmark.run_suite()


def test_historical_rid_cohort_remains_scoring_disabled() -> None:
    assert benchmark.BENCHMARK_ID == "orthogonal_double_matching_source_swap_v1"
    assert benchmark.CONTRACT_ID == "RID-CONTRACT-001"
    with pytest.raises(RuntimeError, match="candidate scoring is forbidden"):
        benchmark.run_suite()


def test_full_falsification_contract_preserves_k_decision() -> None:
    audit = benchmark.contract_audit()
    assert audit["decision"] == "K_CONTRACT_FAIL_OTHER"
    assert not audit["checks"]["classical_control"]["pass"]
    assert not audit["hypothesis_created"]
    assert not audit["plan_created"]
    assert not audit["candidate_created"]
    assert not audit["scoring_performed"]
    assert not audit["runner_random_scoring_seed_realized"]
    assert not audit["exp_99_created"]
