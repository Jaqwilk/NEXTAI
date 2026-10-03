from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from typing import Any

from .heldout_parallel_masked_infilling_v8 import (
    TEST_DEPTHS, _CLOSE, _OPEN, _PAIRS, _number, _permute, _run_case,
    load_candidate, make_stack_training, percentile,
)
from ..masked_refinement_contract import MASK


BENCHMARK_VERSION = "heldout_parallel_masked_infilling_v9"


def closure_chain_case(raw: bytes, depth: int, slot: int,
                       permutation: tuple[int, ...]):
    stack, chain, closes = [], None, {}
    for offset, symbol in enumerate(raw.decode("ascii")):
        if symbol in _OPEN:
            stack.append((symbol, offset))
            if len(stack) == depth and chain is None:
                chain = tuple(position for _, position in stack)
        elif symbol in _CLOSE:
            opener, position = stack.pop()
            if _PAIRS[symbol] != opener:
                raise ValueError("unbalanced immutable trace")
            closes[position] = offset
    if chain is None:
        raise ValueError(f"trace does not reach depth {depth}")
    positions = tuple(sorted(closes[position] for position in chain))
    encoded = list(_permute(raw, permutation))
    target = tuple(encoded[position] for position in positions)
    for position in positions:
        encoded[position] = MASK
    return slot, tuple(encoded), positions, target


def _stack_cases(tests, depth: int, count: int, seed: int,
                 permutation: tuple[int, ...]):
    eligible = [trace for trace, maximum in tests if maximum == depth]
    if not eligible:
        raise ValueError(f"no immutable depth-{depth} stack cases")
    rng = random.Random(seed ^ (depth << 12))
    rng.shuffle(eligible)
    slots = rng.sample(range(100, 9_999), len(eligible))
    return [closure_chain_case(eligible[index % len(eligible)], depth,
                               slots[index % len(slots)], permutation)
            for index in range(count)]


def _run_cell(candidate_name: str, size: int, depth: int, count: int,
              seed: int, maximum_depth: int, protocol: dict[str, Any]):
    training, tests, permutation = make_stack_training(size, seed)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, size, maximum_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    state = _number(candidate, "state_bytes")
    if state > int(protocol["state_budget_bytes"]):
        raise ValueError("state budget exceeded")
    rows = [_run_case(candidate, candidate_name, case, 1)
            for case in _stack_cases(tests, depth, count, seed, permutation)]
    query_ops = sum(row["query_ops"] for row in rows)
    fit_ops = _number(candidate, "fit_ops")
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
        "meta_fit_ops": _number(candidate, "meta_fit_ops", fit_ops),
        "data_acquisition_ops": float(training.acquisition_ops),
        "fit_peak_bytes": float(fit_peak), "mean_query_ops": query_ops / (count * depth),
        "mean_warm_query_ops": query_ops / (count * depth),
        "mean_input_ops": statistics.fmean(row["input_ops"] for row in rows),
        "mean_bytes_touched": statistics.fmean(row["bytes"] for row in rows),
        "p50_latency_us": percentile(latencies, 0.5),
        "p95_latency_us": percentile(latencies, 0.95),
        "state_bytes": state, "peak_state_bytes": max(state, float(fit_peak)),
        "update_ops": 0.0, "update_latency_us": 0.0,
        "workload_ops": workloads[1], "workload_ops_r1": workloads[1],
        "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
    }


def run_suite(candidate_name: str, plan: dict[str, Any]):
    matrix, protocol = plan["matrix"], plan["masked_refinement_protocol"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [_run_cell(candidate_name, int(size), int(depth),
                      int(matrix["queries_per_cell"]), int(seed), maximum, protocol)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"]]
