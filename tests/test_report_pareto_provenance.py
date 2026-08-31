from types import SimpleNamespace

from nextai_autoresearch import report


UNIVERSAL = {
    "maximize": ["transfer_accuracy", "minimum_family_accuracy", "stable_rollout_rate"],
    "minimize": ["normalized_rmse", "mean_query_ops"],
}
CAUSAL_GATES = ("shared_vs_independent_gain", "cross_family_transfer_gain")


def _row(experiment_id: str, contract=UNIVERSAL) -> dict:
    return {
        "experiment_id": experiment_id,
        "hypothesis_id": "HYP-test",
        "benchmark": "heldout_three_family_continuous_transfer_v5",
        "budget": "quick",
        "candidate": "shared_predictive_index_v1",
        "candidate_status": "complete",
        "status": "complete",
        "is_privileged": False,
        "integrity_ok": True,
        "scientifically_valid": True,
        "pareto_metrics": contract,
        "promotion_gates": CAUSAL_GATES,
        "accuracy": 0.96,
        "transfer_accuracy": 0.96,
        "minimum_family_accuracy": 0.95,
        "stable_rollout_rate": 1.0,
        "normalized_rmse": 0.5,
        "mean_query_ops": 10.0,
        "matrix_seed_count": 1,
        "matrix_knowledge_points": 3,
        "matrix_depth_points": 1,
        "knowledge_compute_slope": 0.0,
        "knowledge_compute_slope_points": 3,
        "mean_input_ops": 1.0,
        "mean_bytes_touched": 2.0,
        "workload_ops_r16": 3.0,
        "state_bytes": 4.0,
    }


def test_report_separates_authoritative_pareto_axes_from_causal_gates(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / "research").mkdir()
    monkeypatch.setattr(report, "collect_rows", lambda root: [_row("EXP-test")])
    monkeypatch.setattr(report, "invalid_experiment_ids", lambda root: set())
    monkeypatch.setattr(
        report,
        "load_config",
        lambda root: SimpleNamespace(raw={"decision": {
            "minimum_screen_accuracy": 0.95, "minimum_scaling_points": 3,
        }}),
    )
    rendered = report.write_report(tmp_path).read_text(encoding="utf-8")
    axes_line = next(line for line in rendered.splitlines() if line.startswith("Pareto axes:"))
    assert "transfer_accuracy" in axes_line
    assert all(gate not in axes_line for gate in CAUSAL_GATES)
    assert "Promotion-only gates (not Pareto axes)" in rendered
    assert all(gate in rendered for gate in CAUSAL_GATES)


def test_report_refuses_missing_or_inconsistent_immutable_contracts() -> None:
    assert report._cohort_pareto_contract([_row("EXP-old", None)])[2].startswith(
        "immutable result lacks"
    )
    different = {"maximize": ["accuracy"], "minimize": []}
    maximize, minimize, problem = report._cohort_pareto_contract([
        _row("EXP-a"), _row("EXP-b", different),
    ])
    assert (maximize, minimize) == ([], [])
    assert problem == "inconsistent immutable pareto_metrics across experiments"
