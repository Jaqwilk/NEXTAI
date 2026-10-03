from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from typing import Any

from .successor_graph_v1 import load_candidate, make_world, oracle_answer, percentile
from ..vsa_capacity_core import OracleVSAQuery, VSAQuery


BENCHMARK_VERSION = "routed_vsa_capacity_scaling_v2"
NOISE_RATE = 0.05


def path(oracle: dict[int, int], source: int, steps: int) -> tuple[int, ...]:
    values, current = [], source
    for _ in range(steps):
        current = oracle[current]
        values.append(current)
    return tuple(values)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world, candidate = make_world(knowledge_size, seed), load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(world.facts, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    fit_ops, peak_state = float(candidate.fit_ops), candidate.state_bytes()
    rng = random.Random(seed ^ knowledge_size ^ (reasoning_depth << 16))
    sources = [rng.randrange(knowledge_size) for _ in range(queries_per_cell)]

    def measure(noisy: bool = False) -> list[dict[str, float]]:
        nonlocal peak_state
        rows = []
        for index, source in enumerate(sources):
            query = (OracleVSAQuery(source, seed ^ index, NOISE_RATE if noisy else 0.0,
                                    path(world.oracle, source, reasoning_depth))
                     if candidate_name == "oracle_routed_vsa_r32" else
                     VSAQuery(source, seed ^ index, NOISE_RATE if noisy else 0.0))
            tick = time.perf_counter_ns()
            answer = candidate.query(query, reasoning_depth)
            rows.append({"correct": float(answer == oracle_answer(world.oracle, source, reasoning_depth)),
                         "ops": float(candidate.last_ops),
                         "comparisons": float(getattr(candidate, "last_comparisons", 0)),
                         "bytes": float(getattr(candidate, "last_bytes_touched", 0)),
                         "latency": (time.perf_counter_ns() - tick) / 1000.0})
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold, warm, near = measure(), measure(), measure(True)
    update_source = sources[0]
    old_target = world.oracle[update_source]
    new_target = (old_target + 1) % knowledge_size
    if new_target == old_target:
        new_target = (new_target + 1) % knowledge_size
    tick = time.perf_counter_ns()
    candidate.update(update_source, new_target)
    update_latency = (time.perf_counter_ns() - tick) / 1000.0
    update_ops = float(candidate.update_ops)
    new_query = (OracleVSAQuery(update_source, path=(new_target,))
                 if candidate_name == "oracle_routed_vsa_r32" else VSAQuery(update_source))
    new_correct = candidate.query(new_query, 1) == new_target
    after_ops = float(candidate.last_ops)
    retained_source = next(source for source in range(knowledge_size) if source != update_source)
    retained_query = (OracleVSAQuery(retained_source, path=(world.oracle[retained_source],))
                      if candidate_name == "oracle_routed_vsa_r32" else VSAQuery(retained_source))
    retained = candidate.query(retained_query, 1) == world.oracle[retained_source]
    mean = lambda rows, key: statistics.fmean(row[key] for row in rows)
    accuracy = lambda rows: mean(rows, "correct")
    workload = fit_ops + sum(row["ops"] for row in cold + near) + update_ops + 16 * after_ops
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "reuse_precision": 0.0, "reuse_coverage": 0.0, "false_reuse_rate": 1.0 - accuracy(cold),
        "continual_new_fact_accuracy": float(new_correct), "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_cleanup_comparisons": mean(cold, "comparisons"),
        "mean_bytes_touched": mean(cold, "bytes"), "mean_noisy_bytes_touched": mean(near, "bytes"),
        "mean_input_ops": 1.0, "mean_controller_ops": mean(cold, "comparisons"),
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.5),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.5),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(peak_state, fit_peak)),
        "update_ops": update_ops, "update_latency_us": update_latency, "workload_ops": workload,
        "dimension": float(getattr(candidate, "dimension", 0)),
        "capacity_ratio": float(getattr(candidate, "ratio", 0)),
        "representation_signature": float(getattr(candidate, "representation_signature", 0)),
        "memory_signature": float(getattr(candidate, "memory_signature", 0)),
        "noise_rate": NOISE_RATE,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
