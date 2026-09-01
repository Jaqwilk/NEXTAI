from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _max(values: list[float]) -> float | None:
    return max(values) if values else None


def log_log_slope(points: list[tuple[float, float]]) -> float | None:
    filtered = [(x, y) for x, y in points if x > 0 and y > 0]
    if len(filtered) < 2:
        return None
    xs = [math.log(x) for x, _ in filtered]
    ys = [math.log(y) for _, y in filtered]
    x_mean = statistics.fmean(xs)
    y_mean = statistics.fmean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return None
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator


def log_log_regression(points: list[tuple[float, float]]) -> dict[str, float | int | None]:
    filtered = [(x, y) for x, y in points if x > 0 and y > 0]
    slope = log_log_slope(filtered)
    count = len(filtered)
    if slope is None:
        return {"slope": None, "standard_error": None, "r_squared": None, "points": count}
    xs = [math.log(x) for x, _ in filtered]
    ys = [math.log(y) for _, y in filtered]
    x_mean = statistics.fmean(xs)
    y_mean = statistics.fmean(ys)
    intercept = y_mean - slope * x_mean
    residual_sum = sum(
        (y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys)
    )
    total_sum = sum((y - y_mean) ** 2 for y in ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    standard_error = None
    if count >= 3 and denominator > 0:
        standard_error = math.sqrt((residual_sum / (count - 2)) / denominator)
    r_squared = 1.0 - residual_sum / total_sum if total_sum > 0 else 1.0
    return {
        "slope": slope,
        "standard_error": standard_error,
        "r_squared": r_squared,
        "points": count,
    }


def aggregate_trials(trials: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [trial for trial in trials if trial.get("status") == "complete"]
    if not complete:
        return {
            "status": "failed",
            "completed_trials": 0,
            "total_trials": len(trials),
        }

    by_knowledge: dict[int, list[float]] = defaultdict(list)
    by_depth: dict[int, list[float]] = defaultdict(list)
    for trial in complete:
        by_knowledge[int(trial["knowledge_size"])].append(float(trial["mean_query_ops"]))
        by_depth[int(trial["reasoning_depth"])].append(float(trial["mean_query_ops"]))

    knowledge_points = [
        (float(k), statistics.fmean(values)) for k, values in sorted(by_knowledge.items())
    ]
    depth_points = [
        (float(depth), statistics.fmean(values)) for depth, values in sorted(by_depth.items())
    ]
    cold_ops = [float(trial["mean_query_ops"]) for trial in complete]
    warm_ops = [float(trial["mean_warm_query_ops"]) for trial in complete]
    mean_cold = statistics.fmean(cold_ops)
    mean_warm = statistics.fmean(warm_ops)
    optional_mean = lambda name: _mean(
        [float(trial[name]) for trial in complete if trial.get(name) is not None]
    )
    optional_max = lambda name: _max(
        [float(trial[name]) for trial in complete if trial.get(name) is not None]
    )
    optional_min = lambda name: min(
        [float(trial[name]) for trial in complete if trial.get(name) is not None],
        default=None,
    )
    knowledge_regression = log_log_regression(knowledge_points)
    depth_regression = log_log_regression(depth_points)
    by_seed: dict[int, list[float]] = defaultdict(list)
    by_family: dict[str, list[float]] = defaultdict(list)
    for trial in complete:
        by_seed[int(trial.get("seed", 0))].append(float(trial["accuracy"]))
        if trial.get("world_family") is not None:
            by_family[str(trial["world_family"])].append(float(trial["accuracy"]))
    seed_means = [statistics.fmean(values) for values in by_seed.values()]
    mean_seed_accuracy = statistics.fmean(seed_means)
    seed_accuracy_cv = (
        statistics.pstdev(seed_means) / mean_seed_accuracy
        if len(seed_means) >= 2 and mean_seed_accuracy
        else None
    )
    minimum_scaling_points = 3
    return {
        "status": "complete" if len(complete) == len(trials) else "partial",
        "completed_trials": len(complete),
        "total_trials": len(trials),
        "accuracy": _mean([float(trial["accuracy"]) for trial in complete]),
        "minimum_cell_accuracy": min(float(trial["accuracy"]) for trial in complete),
        "seed_count": len(seed_means),
        "seed_accuracy_cv": seed_accuracy_cv,
        "warm_accuracy": _mean([float(trial["warm_accuracy"]) for trial in complete]),
        "near_equivalent_accuracy": optional_mean("near_equivalent_accuracy"),
        "transfer_accuracy": (
            _mean([float(trial["accuracy"]) for trial in complete]) if by_family else None
        ),
        "minimum_family_accuracy": (
            min(statistics.fmean(values) for values in by_family.values())
            if by_family else None
        ),
        "family_router_accuracy": optional_mean("family_router_accuracy"),
        "minimum_combination_accuracy": optional_min("minimum_combination_accuracy"),
        "family_count": len(by_family),
        "reuse_precision": optional_mean("reuse_precision"),
        "reuse_coverage": optional_mean("reuse_coverage"),
        "false_reuse_rate": optional_mean("false_reuse_rate"),
        "continual_new_fact_accuracy": optional_mean("continual_new_fact_accuracy"),
        "continual_retention": _mean(
            [float(trial["continual_retention"]) for trial in complete]
        ),
        "conditional_probability_mae": optional_mean("conditional_probability_mae"),
        "conditional_log_loss": optional_mean("conditional_log_loss"),
        "normalized_rmse": optional_mean("normalized_rmse"),
        "worst_file_normalized_rmse": optional_max("worst_file_normalized_rmse"),
        "worst_transition_normalized_rmse": optional_max("worst_transition_normalized_rmse"),
        "worst_flight_normalized_rmse": optional_max("worst_flight_normalized_rmse"),
        "worst_condition_normalized_rmse": optional_max("worst_condition_normalized_rmse"),
        "teacher_forced_nrmse": optional_mean("teacher_forced_nrmse"),
        "rollout_10_nrmse": optional_mean("rollout_10_nrmse"),
        "rollout_50_nrmse": optional_mean("rollout_50_nrmse"),
        "rollout_16_nrmse": optional_mean("rollout_16_nrmse"),
        "rollout_32_nrmse": optional_mean("rollout_32_nrmse"),
        "rollout_96_nrmse": optional_mean("rollout_96_nrmse"),
        "stable_rollout_rate": optional_mean("stable_rollout_rate"),
        "oracle_gap_closed": optional_mean("oracle_gap_closed"),
        "privileged_support_gain": optional_mean("privileged_support_gain"),
        "minimum_condition_transfer_gain": optional_min("minimum_condition_transfer_gain"),
        "minimum_trajectory_transfer_gain": optional_min("minimum_trajectory_transfer_gain"),
        "shared_vs_independent_gain": optional_min("shared_vs_independent_gain"),
        "cross_family_transfer_gain": optional_min("cross_family_transfer_gain"),
        "calibration_error": optional_mean("calibration_error"),
        "prequential_loss": optional_mean("prequential_loss"),
        "bits_per_byte": optional_mean("bits_per_byte"),
        "worst_span_bits_per_byte": optional_max("bits_per_byte"),
        "exact_span_accuracy": optional_mean("exact_span_accuracy"),
        "critical_path_steps": optional_max("critical_path_steps"),
        "total_position_probabilities": optional_mean("total_position_probabilities"),
        "cold_bits_per_byte": optional_mean("cold_bits_per_byte"),
        "worst_file_bits_per_byte": optional_max("worst_file_bits_per_byte"),
        "compression_ratio": optional_mean("compression_ratio"),
        "worst_phase_accuracy": optional_min("worst_phase_accuracy"),
        "post_switch_recovery": optional_mean("post_switch_recovery"),
        "recurrence_retention": optional_mean("recurrence_retention"),
        "distractor_interference": optional_mean("distractor_interference"),
        "circuit_nodes": optional_max("circuit_nodes"),
        "mean_query_ops": mean_cold,
        "mean_warm_query_ops": mean_warm,
        "warm_op_ratio": mean_warm / mean_cold if mean_cold else None,
        "p50_latency_us": _mean(
            [float(trial["p50_latency_us"]) for trial in complete]
        ),
        "p95_latency_us": _mean(
            [float(trial["p95_latency_us"]) for trial in complete]
        ),
        "fit_seconds": _max([float(trial["fit_seconds"]) for trial in complete]),
        "fit_ops": optional_max("fit_ops"),
        "meta_fit_ops": optional_max("meta_fit_ops"),
        "data_acquisition_ops": optional_mean("data_acquisition_ops"),
        "preprocessing_ops": optional_max("preprocessing_ops"),
        "adaptation_ops": optional_max("adaptation_ops"),
        "fit_peak_bytes": optional_max("fit_peak_bytes"),
        "state_bytes": _max([float(trial["state_bytes"]) for trial in complete]),
        "peak_state_bytes": optional_max("peak_state_bytes"),
        "mean_input_ops": optional_mean("mean_input_ops"),
        "mean_comparisons": optional_mean("mean_comparisons"),
        "mean_probe_count": optional_mean("mean_probe_count"),
        "mean_bytes_touched": optional_mean("mean_bytes_touched"),
        "update_ops": _mean([float(trial["update_ops"]) for trial in complete]),
        "workload_ops": optional_mean("workload_ops"),
        "workload_ops_r1": optional_mean("workload_ops_r1"),
        "workload_ops_r4": optional_mean("workload_ops_r4"),
        "workload_ops_r16": optional_mean("workload_ops_r16"),
        "update_latency_us": _mean(
            [float(trial["update_latency_us"]) for trial in complete]
        ),
        "knowledge_compute_slope": (
            knowledge_regression["slope"]
            if int(knowledge_regression["points"]) >= minimum_scaling_points
            else None
        ),
        "knowledge_compute_slope_screening": knowledge_regression["slope"],
        "knowledge_compute_slope_points": knowledge_regression["points"],
        "knowledge_compute_slope_se": knowledge_regression["standard_error"],
        "knowledge_compute_slope_r2": knowledge_regression["r_squared"],
        "depth_compute_slope": (
            depth_regression["slope"]
            if int(depth_regression["points"]) >= minimum_scaling_points
            else None
        ),
        "depth_compute_slope_screening": depth_regression["slope"],
        "depth_compute_slope_points": depth_regression["points"],
        "depth_compute_slope_se": depth_regression["standard_error"],
        "depth_compute_slope_r2": depth_regression["r_squared"],
    }
