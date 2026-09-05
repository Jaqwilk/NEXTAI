from argparse import Namespace
from copy import deepcopy

import pytest

from nextai_autoresearch import cli
from nextai_autoresearch.benchmarks import heldout_raw_sensor_active_identification_v1 as v1
from nextai_autoresearch.benchmarks import heldout_raw_sensor_active_identification_v2 as v2
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.utils import project_root


def _protocol() -> dict:
    configured = load_config(project_root())
    return cli._active_sensor_protocol(configured)


def test_v2_preserves_v1_data_task_controls_and_cost_matrix() -> None:
    assert v2.TRAIN_WORLD_SEEDS == v1.TRAIN_WORLD_SEEDS
    assert v2.DEVELOPMENT_SEED == v1.DEVELOPMENT_SEED
    assert v2.KNOWLEDGE_SIZES == v1.KNOWLEDGE_SIZES
    assert v2.PROBE_BUDGETS == v1.PROBE_BUDGETS
    assert v2.BASELINES == v1.BASELINES
    assert v2.development_smoke is v1.development_smoke


def test_v2_roles_share_one_core_and_only_policy_source_differs() -> None:
    scopes = v2.verify_role_contract(_protocol())
    assert len(set(v2.ROLE_IMPLEMENTATION.values())) == 1
    assert set(scopes.values()) == {"meta_worlds", "heldout_support", "frozen"}
    protocol = _protocol()
    assert v1._uses_meta_worlds(protocol["shared_candidate"], protocol)
    assert v1._uses_meta_worlds(protocol["frozen_representation_ablation"], protocol)
    assert not v1._uses_meta_worlds(protocol["support_only_ablation"], protocol)


def test_v2_rejects_mixed_historical_role_contract() -> None:
    protocol = _protocol()
    protocol["shared_candidate"] = "shared_raw_sensor_probe_learner_v1"
    with pytest.raises(ValueError, match="role mismatch"):
        v2.verify_role_contract(protocol)


def test_plan_new_emits_schema_valid_v2_role_contract(monkeypatch) -> None:
    captured = {}
    configured = load_config(project_root())
    raw = deepcopy(configured.raw)
    raw["project"]["benchmark_version"] = "heldout_raw_sensor_active_identification_v2"
    monkeypatch.setattr(cli, "load_config", lambda root: ResearchConfig(raw, configured.path))
    monkeypatch.setattr(cli, "ensure_layout", lambda root: None)
    monkeypatch.setattr(cli, "ensure_can_create_plan", lambda root: None)
    monkeypatch.setattr(cli, "latest_hypotheses", lambda root: {"HYP-9999": {}})
    monkeypatch.setattr(cli, "next_experiment_id", lambda root: "EXP-20990101-9999")
    monkeypatch.setattr(cli, "_git_value", lambda *args: None)
    monkeypatch.setattr(cli, "atomic_write_json", lambda path, value: captured.update(plan=value))
    monkeypatch.setattr(cli, "register_plan", lambda plan, path, root: "test-digest")

    roles = list(v2.ROLE_IMPLEMENTATION)
    cli.command_plan_new(Namespace(
        hypothesis="HYP-9999", parent=None, title="Decision DAG v2 synthesis regression",
        question="Does the v2 generator freeze one coherent source-identical role contract?",
        family="test", candidates=[*roles, *v2.BASELINES], budget="quick",
        primary_metric=None, prediction="No score; schema synthesis regression only.",
        kill_criterion=["Reject a malformed or mixed role contract."],
        promotion_criterion=["This service fixture cannot promote."],
        alternative=["Manual plan construction could hide a wiring defect."],
        confound=["No runner seed is realized by this fixture."],
        positive_conclusion="The generated prospective contract validates.",
        null_conclusion="Treat as an infrastructure failure.",
        negative_conclusion="Repair before preregistration.",
    ))

    plan = captured["plan"]
    assert plan["benchmark"] == v2.BENCHMARK_VERSION
    assert plan["matrix"]["knowledge_sizes"] == [8, 32, 128]
    assert plan["matrix"]["reasoning_depths"] == [4, 8, 16]
    assert v2.verify_role_contract(plan["active_sensor_protocol"])
