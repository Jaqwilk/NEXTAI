from __future__ import annotations

import pytest

from nextai_autoresearch.metrics import aggregate_trials, log_log_regression, log_log_slope
from nextai_autoresearch.pareto import (
    complete_metric_axes,
    dominates,
    is_oracle_candidate,
    is_privileged_candidate,
    pareto_front,
)


def test_log_log_slope_recovers_constant_linear_and_quadratic() -> None:
    assert log_log_slope([(1, 7), (10, 7), (100, 7)]) == pytest.approx(0.0)
    assert log_log_slope([(1, 3), (10, 30), (100, 300)]) == pytest.approx(1.0)
    assert log_log_slope([(1, 2), (10, 200), (100, 20000)]) == pytest.approx(2.0)


def test_aggregate_trials_keeps_knowledge_and_depth_axes_separate() -> None:
    trials = []
    for knowledge in (10, 100):
        for depth in (1, 10):
            trials.append(
                {
                    "status": "complete",
                    "knowledge_size": knowledge,
                    "reasoning_depth": depth,
                    "accuracy": 1.0,
                    "warm_accuracy": 1.0,
                    "continual_retention": 1.0,
                    "conditional_probability_mae": 0.02,
                    "conditional_log_loss": 0.4,
                    "calibration_error": 0.01,
                    "circuit_nodes": float(knowledge // 10),
                    "mean_query_ops": float(knowledge * depth),
                    "mean_warm_query_ops": 1.0,
                    "p50_latency_us": 1.0,
                    "p95_latency_us": 2.0,
                    "fit_seconds": 0.1,
                    "state_bytes": float(knowledge),
                    "update_ops": 1.0,
                    "update_latency_us": 1.0,
                }
            )
    summary = aggregate_trials(trials)
    assert summary["status"] == "complete"
    assert summary["knowledge_compute_slope"] is None
    assert summary["knowledge_compute_slope_screening"] == pytest.approx(1.0)
    assert summary["knowledge_compute_slope_points"] == 2
    assert summary["depth_compute_slope"] is None
    assert summary["depth_compute_slope_screening"] == pytest.approx(1.0)
    assert summary["warm_op_ratio"] < 1.0
    assert summary["conditional_probability_mae"] == pytest.approx(0.02)
    assert summary["conditional_log_loss"] == pytest.approx(0.4)
    assert summary["calibration_error"] == pytest.approx(0.01)
    assert summary["circuit_nodes"] == 10.0


def test_three_point_scaling_reports_slope_and_uncertainty_metadata() -> None:
    regression = log_log_regression([(1, 2), (10, 20), (100, 200)])
    assert regression["slope"] == pytest.approx(1.0)
    assert regression["standard_error"] == pytest.approx(0.0)
    assert regression["r_squared"] == pytest.approx(1.0)
    assert regression["points"] == 3


def test_accuracy_cost_tradeoff_retains_non_dominated_rows() -> None:
    rows = [
        {"candidate": "cheap", "accuracy": 0.96, "ops": 1.0},
        {"candidate": "balanced", "accuracy": 0.99, "ops": 2.0},
        {"candidate": "dominated", "accuracy": 0.95, "ops": 3.0},
    ]
    assert dominates(rows[0], rows[2], ["accuracy"], ["ops"])
    front = pareto_front(rows, maximize=["accuracy"], minimize=["ops"])
    assert {row["candidate"] for row in front} == {"cheap", "balanced"}


def test_missing_metric_does_not_create_false_dominance() -> None:
    left = {"accuracy": 1.0, "ops": None}
    right = {"accuracy": 1.0, "ops": 2.0}
    assert not dominates(left, right, ["accuracy"], ["ops"])
    assert not dominates(right, left, ["accuracy"], ["ops"])


def test_frontier_axes_are_complete_and_oracles_are_classified() -> None:
    rows = [
        {"accuracy": 1.0, "ops": 2.0, "optional": None},
        {"accuracy": 0.99, "ops": 1.0, "optional": 3.0},
    ]
    maximize, minimize = complete_metric_axes(
        rows, ["accuracy", "optional"], ["ops"]
    )
    assert maximize == ["accuracy"]
    assert minimize == ["ops"]
    assert is_oracle_candidate("oracle_identity_index")
    assert is_oracle_candidate("mapping_oracle_dependency_trace")
    assert not is_oracle_candidate("exact_tuple_store_vsa")
    assert is_privileged_candidate("privileged_same_condition_support_arx_v3")
