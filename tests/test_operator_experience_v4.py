from __future__ import annotations

from argparse import Namespace
from copy import deepcopy

from nextai_autoresearch import cli
from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v4 as bench
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root
from nextai_autoresearch.operator_experience_contract import Query, canonical_table
from nextai_autoresearch.operator_experience_core import (
    AntiUnificationCache, CanonicalTableCache, ExactKeyCache, StructuralResultCache,
)


def _programs():
    tables = bench._tables(1_501_103, 1103)
    first = bench._term(bench.TEST_SEQUENCE, tables, 11, 0)
    second = bench._term(bench.TEST_SEQUENCE, tables, 17, 1)
    near = bench._term((*bench.TEST_SEQUENCE[:-1], "B"), tables, 23, 1)
    return first, second, near


def test_reencoding_is_raw_distinct_semantically_equal_and_pair_breaking_is_real() -> None:
    first, second, near = _programs()
    assert first != second
    assert canonical_table(first)[0] == canonical_table(second)[0]
    assert canonical_table(first)[0] != canonical_table(near)[0]
    gate = bench.static_control_gate()
    assert gate["raw_reencoding_differs"] and gate["positive_canonical_match"]
    assert gate["pair_breaking_changes_operator"]
    assert gate["positive_pairs"] > 0 and gate["negative_pairs"] > 0


def test_exact_structural_and_canonical_caches_have_distinct_semantics() -> None:
    first, second, _ = _programs()
    state = 7
    for cls in (ExactKeyCache, StructuralResultCache, CanonicalTableCache):
        candidate = cls(0)
        candidate.query(Query(first, state), 1)
        assert not candidate.last_cache_hit
        candidate.query(Query(second, state), 1)
        if cls is CanonicalTableCache:
            assert candidate.last_cache_hit
        else:
            assert not candidate.last_cache_hit


def test_anti_unification_uses_labeled_pairs_and_never_merges_broken_pair() -> None:
    training = bench.make_training(8, 1_501_103, 1103)
    candidate = AntiUnificationCache(0)
    candidate.fit(training, 8, 16)
    assert candidate.positive and candidate.negative
    assert candidate.fit_ops > 0 and candidate.state_bytes() > 64


def test_all_mandatory_controls_complete_tiny_real_evaluator_cell() -> None:
    for name in bench.BASELINES:
        row = bench._run_cell(name, 8, 1, 2, 1_501_103, 1103, 4_194_304)
        assert row["status"] == "complete"
        assert row["data_acquisition_ops"] > 0
        assert row["workload_ops_r1"] <= row["workload_ops_r4"] <= row["workload_ops_r16"]
        if name != "operator_random":
            assert row["minimum_combination_accuracy"] == 1.0


def test_v4_plan_generator_freezes_three_exposure_counts_and_all_controls(monkeypatch) -> None:
    captured = {}
    configured = load_config()
    raw = deepcopy(configured.raw)
    raw["project"]["benchmark_version"] = "heldout_mechanism_recombination_v5"
    monkeypatch.setattr(cli, "load_config", lambda root: ResearchConfig(raw, configured.path))
    monkeypatch.setattr(cli, "ensure_layout", lambda root: None)
    monkeypatch.setattr(cli, "ensure_can_create_plan", lambda root: None)
    monkeypatch.setattr(cli, "latest_hypotheses", lambda root: {"HYP-9999": {}})
    monkeypatch.setattr(cli, "next_experiment_id", lambda root: "EXP-20990101-9999")
    monkeypatch.setattr(cli, "_git_value", lambda *args: None)
    monkeypatch.setattr(cli, "atomic_write_json", lambda path, value: captured.update(plan=value))
    monkeypatch.setattr(cli, "register_plan", lambda plan, path, root: "test-digest")
    metrics = [
        "accuracy", "warm_accuracy", "near_equivalent_accuracy",
        "minimum_combination_accuracy", "false_reuse_rate",
        "continual_new_fact_accuracy", "continual_retention", "data_acquisition_ops",
        "fit_ops", "meta_fit_ops", "mean_query_ops", "mean_warm_query_ops",
        "update_ops", "state_bytes", "peak_state_bytes", "mean_bytes_touched",
        "workload_ops_r1", "workload_ops_r4", "workload_ops_r16",
    ]
    roles = [
        "experience_operator_compiler", "experience_operator_independent",
        "experience_operator_no_pairing", *bench.BASELINES,
    ]
    cli.command_plan_new(Namespace(
        hypothesis="HYP-9999", parent=None, title="operator experience scout",
        question="Does experience compile an operator?", family="operator_experience",
        candidates=roles, budget="quick", primary_metric=metrics,
        prediction="A scout may reveal declining measured inference cost after repeated re-encodings.",
        kill_criterion=["Discard on unsafe reuse."],
        promotion_criterion=["Scout cannot promote."],
        alternative=["Classical canonicalization explains the effect."],
        confound=["Visible synthetic evaluator is screening only."],
        positive_conclusion="Permit later rigorous testing.",
        null_conclusion="Discard the direction.", negative_conclusion="Discard the direction.",
    ))
    plan = captured["plan"]
    assert plan["matrix"]["knowledge_sizes"] == [8, 32, 128]
    assert plan["matrix"]["reasoning_depths"] == [1, 4, 16]
    assert plan["matrix"]["queries_per_cell"] == 8
    assert plan["mechanism_recombination_protocol"]["classical_baselines"] == list(bench.BASELINES)
    assert "reuse_coverage" not in plan["mechanism_recombination_protocol"]["pareto_capability_metrics"]
    validate_document("experiment_plan", plan, project_root())
