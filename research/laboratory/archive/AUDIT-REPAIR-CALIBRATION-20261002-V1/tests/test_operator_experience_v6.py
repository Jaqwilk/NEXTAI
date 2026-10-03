from __future__ import annotations

from argparse import Namespace
from copy import deepcopy

from nextai_autoresearch import cli
from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v4 as v4
from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v6 as v6
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


def test_v4_default_sequence_is_unchanged_by_additive_depth_parameter() -> None:
    args = ("operator_interpreter", 8, 1, 2, 1_501_103, 1103, 4_194_304)
    implicit = v4._run_cell(*args)
    explicit = v4._run_cell(*args, v4.TEST_SEQUENCE)
    nondeterministic = {"fit_seconds", "fit_peak_bytes", "peak_state_bytes", "p50_latency_us", "p95_latency_us"}
    assert {k: v for k, v in implicit.items() if k not in nondeterministic} == {
        k: v for k, v in explicit.items() if k not in nondeterministic
    }


def test_v6_freezes_three_unseen_depths_and_real_control_cells() -> None:
    gate = v6.static_control_gate()
    assert gate["test_composition_lengths"] == [4, 8, 16]
    assert gate["all_tests_exceed_training_depth"]
    plan = {
        "matrix": {"seeds": [1_501_103], "knowledge_sizes": [8],
                   "reasoning_depths": [4, 8, 16], "queries_per_cell": 2},
        "mechanism_recombination_protocol": {
            "mechanism_source_seed": 1103, "state_budget_bytes": 4_194_304,
        },
    }
    rows = v6.run_suite("operator_interpreter", plan)
    assert [row["reasoning_depth"] for row in rows] == [4, 8, 16]
    assert all(row["exposure_count"] == 16 for row in rows)
    assert all(row["minimum_combination_accuracy"] == 1.0 for row in rows)
    assert rows[0]["mean_input_ops"] < rows[1]["mean_input_ops"] < rows[2]["mean_input_ops"]


def test_v6_plan_freezes_depth_axis_roles_and_source_contract(monkeypatch) -> None:
    captured = {}
    configured = load_config()
    raw = deepcopy(configured.raw)
    raw["project"]["benchmark_version"] = v6.BENCHMARK_VERSION
    monkeypatch.setattr(cli, "load_config", lambda root: ResearchConfig(raw, configured.path))
    monkeypatch.setattr(cli, "ensure_layout", lambda root: None)
    monkeypatch.setattr(cli, "ensure_can_create_plan", lambda root: None)
    monkeypatch.setattr(cli, "latest_hypotheses", lambda root: {"HYP-9999": {}})
    monkeypatch.setattr(cli, "next_experiment_id", lambda root: "EXP-20990101-9999")
    monkeypatch.setattr(cli, "_git_value", lambda *args: None)
    monkeypatch.setattr(cli, "atomic_write_json", lambda path, value: captured.update(plan=value))
    monkeypatch.setattr(cli, "register_plan", lambda plan, path, root: "test-digest")
    protocol = raw["recombination"]
    roles = [
        protocol["shared_candidate_v6"], protocol["independent_ablation_v6"],
        protocol["no_cross_mechanism_ablation_v6"], *v6.BASELINES,
    ]
    metrics = list(protocol["pareto_capability_metrics"])
    cli.command_plan_new(Namespace(
        hypothesis="HYP-9999", parent=None, title="macro DAG scout",
        question="Can learned macro reuse reduce total work with depth?",
        family="learned_macro_operator_dag", candidates=roles, budget="quick",
        primary_metric=metrics, prediction="Depth scaling may separate reusable macros from interpretation.",
        kill_criterion=["Discard without exact quality and a total-work advantage."],
        promotion_criterion=["A one-seed scout cannot promote."],
        alternative=["Exact interpretation remains cheaper."],
        confound=["Visible synthetic evaluator is scout-only."],
        positive_conclusion="Permit unchanged replication.",
        null_conclusion="Discard this exact rule.", negative_conclusion="Discard this exact rule.",
    ))
    plan = captured["plan"]
    assert plan["matrix"]["reasoning_depths"] == [4, 8, 16]
    frozen = plan["mechanism_recombination_protocol"]
    assert frozen["heldout_compositions"] == ["CBAC", "CBACABAC", "CBACABACBCABCBAC"]
    assert frozen["exposure_count"] == 16
    assert frozen["source_identical_contract"] == protocol["source_identical_contract_v6"]
    validate_document("experiment_plan", plan, project_root())
