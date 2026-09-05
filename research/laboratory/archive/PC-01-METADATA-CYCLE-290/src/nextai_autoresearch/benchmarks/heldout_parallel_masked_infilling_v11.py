from __future__ import annotations

import statistics
import time
import tracemalloc
from typing import Any

from . import heldout_parallel_masked_infilling_v9 as v9
from .heldout_parallel_masked_infilling_v1 import _run_case as _historical_run_case


BENCHMARK_VERSION = "heldout_parallel_masked_infilling_v11"
PRIVILEGED = frozenset({
    "oracle_conditional_masked_byte",
    "privileged_conditional_masked_byte_v2",
})


def _run_case(candidate: Any, candidate_name: str, case, rounds: int):
    routed_name = (
        "oracle_conditional_masked_byte"
        if candidate_name in PRIVILEGED
        else candidate_name
    )
    return _historical_run_case(candidate, routed_name, case, rounds)


def _run_privileged_cell(candidate_name: str, size: int, depth: int, count: int,
                         seed: int, maximum_depth: int,
                         protocol: dict[str, Any]):
    training, tests, permutation = v9.make_stack_training(size, seed)
    candidate = v9.load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, size, maximum_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    state = v9._number(candidate, "state_bytes")
    if state > int(protocol["state_budget_bytes"]):
        raise ValueError("state budget exceeded")
    rows = [_run_case(candidate, candidate_name, case, 1)
            for case in v9._stack_cases(tests, depth, count, seed, permutation)]
    query_ops = sum(row["query_ops"] for row in rows)
    fit_ops = v9._number(candidate, "fit_ops")
    base = training.acquisition_ops + fit_ops
    workloads = {h: base + h * query_ops for h in (1, 4, 16)}
    latencies = [value for row in rows for value in row["latency"]]
    return {
        "status": "complete", "world_family": f"stack_depth_{depth}",
        "span_length": depth, "knowledge_size": size, "reasoning_depth": depth,
        "refinement_rounds": 1, "seed": seed, "query_count": count * depth,
        "accuracy": statistics.fmean(row["accuracy"] for row in rows),
        "warm_accuracy": statistics.fmean(row["accuracy"] for row in rows),
        "continual_retention": statistics.fmean(row["exact"] for row in rows),
        "exact_span_accuracy": statistics.fmean(row["exact"] for row in rows),
        "bits_per_byte": statistics.fmean(row["bits"] for row in rows),
        "critical_path_steps": max(row["critical"] for row in rows),
        "total_position_probabilities": sum(row["probabilities"] for row in rows),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops,
        "meta_fit_ops": v9._number(candidate, "meta_fit_ops", fit_ops),
        "data_acquisition_ops": float(training.acquisition_ops),
        "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": query_ops / (count * depth),
        "mean_warm_query_ops": query_ops / (count * depth),
        "mean_input_ops": statistics.fmean(row["input_ops"] for row in rows),
        "mean_bytes_touched": statistics.fmean(row["bytes"] for row in rows),
        "p50_latency_us": v9.percentile(latencies, 0.5),
        "p95_latency_us": v9.percentile(latencies, 0.95),
        "state_bytes": state, "peak_state_bytes": max(state, float(fit_peak)),
        "update_ops": 0.0, "update_latency_us": 0.0,
        "workload_ops": workloads[1], "workload_ops_r1": workloads[1],
        "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
    }


def run_suite(candidate_name: str, plan: dict[str, Any]):
    if candidate_name != "privileged_conditional_masked_byte_v2":
        return v9.run_suite(candidate_name, plan)
    matrix, protocol = plan["matrix"], plan["masked_refinement_protocol"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [_run_privileged_cell(candidate_name, int(size), int(depth),
                                 int(matrix["queries_per_cell"]), int(seed),
                                 maximum, protocol)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"]]
