from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from typing import Any

from . import heldout_parallel_masked_infilling_v9 as v9
from . import heldout_parallel_masked_infilling_v12 as v12
from .heldout_parallel_masked_infilling_v8 import _CLOSE, _OPEN, _PAIRS
from .heldout_parallel_masked_infilling_v11 import _run_case
from ..masked_refinement_contract import MASK


BENCHMARK_VERSION = "heldout_parallel_masked_infilling_v13"
make_stack_training = v12.make_stack_training


def recoverable_push_chain_case(raw: bytes, depth: int, slot: int,
                                permutation: tuple[int, ...]):
    stack, chain, closes = [], None, {}
    for offset, symbol in enumerate(raw.decode("ascii")):
        if symbol in _OPEN:
            stack.append((symbol, offset))
            if len(stack) == depth and chain is None:
                chain = tuple(stack)
        elif symbol in _CLOSE:
            if not stack:
                raise ValueError("unbalanced immutable trace")
            opener, position = stack.pop()
            if _PAIRS[symbol] != opener:
                raise ValueError("unbalanced immutable trace")
            closes[position] = offset
    if stack or chain is None:
        raise ValueError(f"trace does not reach balanced depth {depth}")
    positions = tuple(position for _, position in chain[1:])
    if not any(symbol != chain[0][0] for symbol, _ in chain[1:]):
        raise ValueError("missing pushes are copyable from the visible outer opener")
    if any(position not in closes for position in positions):
        raise ValueError("missing push has no intact matching return")
    encoded = list(v9._permute(raw, permutation))
    target = tuple(encoded[position] for position in positions)
    for position in positions:
        encoded[position] = MASK
    return slot, tuple(encoded), positions, target


def _repair_cases(tests, depth: int, count: int, seed: int,
                  permutation: tuple[int, ...]):
    identity = tuple(range(256))
    eligible = []
    for trace, maximum in tests:
        if maximum != depth:
            continue
        try:
            recoverable_push_chain_case(trace, depth, 0, identity)
        except ValueError:
            continue
        eligible.append(trace)
    if not eligible:
        raise ValueError(f"no identifiable depth-{depth} repair cases")
    rng = random.Random(seed ^ (depth << 12) ^ 0x13)
    rng.shuffle(eligible)
    slots = rng.sample(range(100, 9_999), len(eligible))
    return [recoverable_push_chain_case(
        eligible[index % len(eligible)], depth,
        slots[index % len(slots)], permutation,
    ) for index in range(count)]


def _run_cell(candidate_name: str, size: int, depth: int, count: int,
              seed: int, maximum_depth: int, protocol: dict[str, Any]):
    training, tests, permutation = make_stack_training(size, seed)
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
            for case in _repair_cases(tests, depth, count, seed, permutation)]
    masked = count * (depth - 1)
    query_ops = sum(row["query_ops"] for row in rows)
    fit_ops = v9._number(candidate, "fit_ops")
    base = training.acquisition_ops + fit_ops
    workloads = {h: base + h * query_ops for h in (1, 4, 16)}
    latencies = [value for row in rows for value in row["latency"]]
    return {
        "status": "complete", "world_family": f"recoverable_push_depth_{depth}",
        "span_length": depth - 1, "knowledge_size": size,
        "reasoning_depth": depth, "refinement_rounds": 1, "seed": seed,
        "query_count": masked,
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
        "mean_query_ops": query_ops / masked,
        "mean_warm_query_ops": query_ops / masked,
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
    matrix, protocol = plan["matrix"], plan["masked_refinement_protocol"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [_run_cell(candidate_name, int(size), int(depth),
                      int(matrix["queries_per_cell"]), int(seed), maximum, protocol)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"]]
