from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

import numpy as np

from .successor_graph_v1 import load_candidate, percentile
from ..adaptive_transition_core import OracleQuery, TransitionDataset, TransitionPair


BENCHMARK_VERSION = "shared_transition_adaptive_compute_v2"
TRAIN_MAX_DEPTH = 4
REUSE_SCHEDULE = (1, 4, 16)


@dataclass(frozen=True)
class Task:
    state: np.ndarray
    target: np.ndarray
    near_state: np.ndarray
    near_target: np.ndarray
    required_depth: int


def direction(dimensions: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed ^ dimensions * 65537)
    vector = rng.normal(size=dimensions)
    return vector / np.linalg.norm(vector)


def anchor(dimensions: int, seed: int, vector: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(seed)
    value = rng.normal(size=dimensions)
    return value - vector * float(value @ vector)


def make_dataset(dimensions: int, seed: int, offset: int = 0) -> TransitionDataset:
    vector, pairs = direction(dimensions, seed), []
    for index in range(8):
        base = anchor(dimensions, seed ^ 0xA5A5 ^ (offset + index) * 8191, vector)
        pairs.append(TransitionPair(base, base.copy()))
        for depth in range(1, TRAIN_MAX_DEPTH + 1):
            pairs.append(TransitionPair(base + depth * vector, base + (depth - 1) * vector))
    return TransitionDataset(tuple(pairs), 8, 6)


def make_tasks(dimensions: int, depth: int, count: int, seed: int, offset: int = 0) -> tuple[Task, ...]:
    vector, tasks = direction(dimensions, seed), []
    for index in range(count):
        base = anchor(dimensions, seed ^ 0x5A5A ^ (offset + index) * 104729, vector)
        tasks.append(Task(base + depth * vector, base,
                          base + (depth + 0.49) * vector, base + 0.49 * vector, depth))
    return tuple(tasks)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    data = make_dataset(knowledge_size, seed)
    tasks = make_tasks(knowledge_size, reasoning_depth, queries_per_cell, seed)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    initial_fit_ops, peak_state = float(candidate.fit_ops), candidate.state_bytes()

    def measure(near: bool = False):
        nonlocal peak_state
        rows = []
        for task in tasks:
            state = task.near_state if near else task.state
            target = task.near_target if near else task.target
            query = OracleQuery(state, task.required_depth) if candidate_name == "oracle_shared_halt" else state
            tick = time.perf_counter_ns()
            answer = candidate.query(query, 0)
            latency = (time.perf_counter_ns() - tick) / 1000
            calls = float(candidate.last_transition_calls)
            rows.append({"correct": np.allclose(answer, target, atol=1e-7),
                         "latency": latency, "ops": candidate.last_ops + knowledge_size,
                         "input": float(knowledge_size), "controller": candidate.last_controller_ops,
                         "calls": calls, "premature": calls < task.required_depth,
                         "late": max(0.0, calls - task.required_depth)})
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold, warm, near = measure(), measure(), measure(True)
    update_data = make_dataset(knowledge_size, seed, 100)
    tick = time.perf_counter_ns()
    candidate.update(update_data, None)
    update_latency = (time.perf_counter_ns() - tick) / 1000
    update_ops = float(candidate.update_ops)
    new_task = make_tasks(knowledge_size, reasoning_depth, 1, seed, 100)[0]
    new_query = OracleQuery(new_task.state, reasoning_depth) if candidate_name == "oracle_shared_halt" else new_task.state
    new_answer = candidate.query(new_query, 0)
    new_correct, after_ops = np.allclose(new_answer, new_task.target, atol=1e-7), candidate.last_ops + knowledge_size
    old_task = tasks[0]
    old_query = OracleQuery(old_task.state, reasoning_depth) if candidate_name == "oracle_shared_halt" else old_task.state
    retained = np.allclose(candidate.query(old_query, 0), old_task.target, atol=1e-7)
    workloads = {reuse: update_ops + reuse * after_ops for reuse in REUSE_SCHEDULE}
    peak_state = max(peak_state, candidate.state_bytes())

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    accuracy = lambda rows: statistics.fmean(float(row["correct"]) for row in rows)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "reuse_precision": 0.0, "reuse_coverage": 0.0, "false_reuse_rate": 0.0,
        "continual_new_fact_accuracy": float(new_correct), "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": initial_fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_input_ops": mean(cold, "input"), "mean_controller_ops": mean(cold, "controller"),
        "mean_transition_calls": mean(cold, "calls"), "near_transition_calls": mean(near, "calls"),
        "premature_halt_rate": mean(cold, "premature"), "mean_late_steps": mean(cold, "late"),
        "near_mean_late_steps": mean(near, "late"),
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.5),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.5),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(peak_state, fit_peak)),
        "update_ops": update_ops, "cumulative_update_ops": update_ops,
        "update_latency_us": update_latency, "workload_ops_r1": workloads[1],
        "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
        "workload_ops": initial_fit_ops + sum(row["ops"] for row in cold + near) + workloads[16],
        "transition_signature": float(candidate.transition_signature),
        "shared_transition_width": 8.0, "train_max_depth": float(TRAIN_MAX_DEPTH),
        "ood_depth": float(reasoning_depth > TRAIN_MAX_DEPTH),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
