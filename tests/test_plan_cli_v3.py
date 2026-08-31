from argparse import Namespace

from nextai_autoresearch import cli


def test_plan_new_emits_v4_pareto_contract(monkeypatch) -> None:
    captured = {}
    monkeypatch.setattr(cli, "ensure_layout", lambda root: None)
    monkeypatch.setattr(cli, "ensure_can_create_plan", lambda root: None)
    monkeypatch.setattr(cli, "latest_hypotheses", lambda root: {"HYP-9999": {}})
    monkeypatch.setattr(cli, "next_experiment_id", lambda root: "EXP-20990101-9999")
    monkeypatch.setattr(cli, "_git_value", lambda *args: None)
    monkeypatch.setattr(cli, "atomic_write_json", lambda path, value: captured.update(plan=value))
    monkeypatch.setattr(cli, "register_plan", lambda plan, path, root: "test-digest")

    metrics = [
        "transfer_accuracy", "minimum_family_accuracy", "stable_rollout_rate",
        "normalized_rmse", "shared_vs_independent_gain", "cross_family_transfer_gain",
        "data_acquisition_ops", "preprocessing_ops", "fit_ops", "adaptation_ops",
        "mean_query_ops", "update_ops", "state_bytes", "peak_state_bytes",
        "mean_bytes_touched", "workload_ops_r1", "workload_ops_r4", "workload_ops_r16",
    ]
    candidates = [
        "shared_predictive_index_v1", "independent_predictive_index_v1",
        "cross_family_only_predictive_index_v1", "support_only_predictive_index_v1",
        "tensor_persistence_v1", "tensor_ridge_arx_v1", "tensor_rls_arx_v1",
        "tensor_empirical_gaussian_joint_v1", "tensor_contextual_gaussian_chow_liu_v1",
        "tensor_autoregressive_v1", "tensor_raw_window_local_linear_v1",
        "tensor_random_projection_hash_v1", "privileged_tensor_support_v1",
    ]
    cli.command_plan_new(Namespace(
        hypothesis="HYP-9999", parent=None, title="v4 synthesis regression",
        question="Does v4 retain the universal Pareto contract?", family="test",
        candidates=candidates, budget="quick", primary_metric=metrics,
        prediction="No score; schema synthesis regression only.",
        kill_criterion=["Reject malformed protocol."],
        promotion_criterion=["This test cannot promote."],
        alternative=["Manual plan construction could hide the defect."],
        confound=["No runner seed is realized."],
        positive_conclusion="The generated contract validates.",
        null_conclusion="Treat as infrastructure failure.",
        negative_conclusion="Repair before preregistration.",
    ))

    protocol = captured["plan"]["continuous_transfer_protocol"]
    assert captured["plan"]["benchmark"] == "heldout_three_family_continuous_transfer_v4"
    assert protocol["causal_promotion_gates"] == [
        "shared_vs_independent_gain", "cross_family_transfer_gain"
    ]
    assert "mean_query_ops" in protocol["pareto_capability_metrics"]
