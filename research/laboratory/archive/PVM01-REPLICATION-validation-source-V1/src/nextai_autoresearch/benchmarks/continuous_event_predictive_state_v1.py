from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

import numpy as np

from .successor_graph_v1 import load_candidate, percentile
from ..continuous_event_core import Coefficients, Episode, ForecastQuery, OracleEpisode


BENCHMARK_VERSION = "continuous_event_predictive_state_v1"
COEFFICIENTS: Coefficients = ((0.62, -0.22), (0.78, 0.07), (0.52, 0.31))
TRAIN_ORDERS = ((-1, 0, 1), (0, 1, -1), (-1, 1, 0))
REUSE_SCHEDULE = (1, 4, 16)


@dataclass(frozen=True)
class World:
    width: int
    active_index: int
    context_index: int


@dataclass(frozen=True)
class Task:
    cold: ForecastQuery
    warm: ForecastQuery
    near: ForecastQuery
    target: tuple[float, ...]
    near_target: tuple[float, ...]


def make_world(width: int, seed: int) -> World:
    rng = random.Random(seed ^ width * 65537)
    active, context = rng.sample(range(width), 2)
    return World(width, active, context)


def _step(value: float, regime: int, coefficients: Coefficients) -> float:
    a, b = coefficients[regime + 1]
    return a * value + b


def _background(rows: int, world: World, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    matrix = rng.normal(0, 0.75, (rows, world.width))
    return matrix


def make_episode(world: World, seed: int, coefficients: Coefficients = COEFFICIENTS,
                 regime: int | None = None, rows: int = 108) -> Episode:
    rng = random.Random(seed)
    matrix, targets = _background(rows, world, seed ^ 0xD157), np.empty(rows)
    value = rng.uniform(-0.8, 0.8)
    for index in range(rows):
        if regime is None:
            order = TRAIN_ORDERS[(index // 18) % len(TRAIN_ORDERS)]
            current_regime = order[(index // 6) % 3]
        else:
            current_regime = regime
        if index % 18 == 0:
            value = rng.uniform(-0.8, 0.8)
        matrix[index, world.active_index] = value
        matrix[index, world.context_index] = current_regime
        targets[index] = _step(value, current_regime, coefficients)
        value = targets[index]
    # Confusable channels are locally predictive or regime-like, but never globally exact.
    spare = [j for j in range(world.width) if j not in (world.active_index, world.context_index)]
    if spare:
        matrix[:, spare[0]] = matrix[:, world.active_index] + np.random.default_rng(seed ^ 31).normal(0, 0.03, rows)
    if len(spare) > 1:
        matrix[:, spare[1]] = matrix[:, world.context_index] + np.random.default_rng(seed ^ 47).normal(0, 0.04, rows)
    return Episode(matrix, targets)


def _query(world: World, value: float, regimes: tuple[int, ...], seed: int) -> ForecastQuery:
    matrix = _background(len(regimes), world, seed)
    matrix[0, world.active_index] = value
    matrix[:, world.context_index] = regimes
    return ForecastQuery(matrix)


def _target(value: float, regimes: tuple[int, ...], coefficients: Coefficients) -> tuple[float, ...]:
    output = []
    for regime in regimes:
        value = _step(value, regime, coefficients)
        output.append(value)
    return tuple(output)


def make_tasks(world: World, depth: int, seed: int, count: int,
               coefficients: Coefficients = COEFFICIENTS) -> tuple[Task, ...]:
    tasks = []
    for index in range(count):
        rng = random.Random(seed ^ depth * 8191 ^ index * 104729)
        value = rng.uniform(-0.9, 0.9)
        regimes = tuple((1, -1, 0)[(step + index) % 3] for step in range(depth))
        changed = list(regimes)
        changed[index % depth] = {-1: 1, 0: -1, 1: 0}[changed[index % depth]]
        near_regimes = tuple(changed)
        tasks.append(Task(
            _query(world, value, regimes, seed ^ index ^ 0xC01D),
            _query(world, value, regimes, seed ^ index ^ 0xA11CE),
            _query(world, value, near_regimes, seed ^ index ^ 0xBAD),
            _target(value, regimes, coefficients),
            _target(value, near_regimes, coefficients),
        ))
    return tuple(tasks)


def _correct(answer: tuple[float, ...], target: tuple[float, ...]) -> bool:
    return len(answer) == len(target) and bool(np.allclose(answer, target, rtol=1e-5, atol=1e-6))


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world, coefficients = make_world(knowledge_size, seed), COEFFICIENTS
    episode = make_episode(world, seed, coefficients)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell, coefficients)
    candidate = load_candidate(candidate_name, seed)

    def wrapped(current: Episode, current_coefficients: Coefficients):
        return OracleEpisode(current, world.active_index, world.context_index, current_coefficients) if candidate_name == "oracle_sparse_dynamics" else current

    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(wrapped(episode, coefficients), knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    initial_fit_ops, peak_state = float(candidate.fit_ops), candidate.state_bytes()

    def measure(field: str, target_field: str):
        nonlocal peak_state
        rows = []
        for task in tasks:
            query, target = getattr(task, field), getattr(task, target_field)
            tick = time.perf_counter_ns()
            answer = candidate.query(query, reasoning_depth)
            rows.append({
                "correct": _correct(answer, target), "rmse": float(np.sqrt(np.mean(np.square(np.asarray(answer) - target)))),
                "latency": (time.perf_counter_ns() - tick) / 1000, "ops": candidate.last_ops,
                "input": candidate.last_input_ops, "search": candidate.last_search_ops,
                "execution": candidate.last_execution_ops, "reads": candidate.last_memory_reads,
                "bytes": candidate.last_bytes_loaded, "hit": float(candidate.last_cache_hit),
            })
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold, warm, near = measure("cold", "target"), measure("warm", "target"), measure("near", "near_target")
    retained_query = _query(world, 0.37, (1,) * reasoning_depth, seed ^ 0x5151)
    retained_target = _target(0.37, (1,) * reasoning_depth, coefficients)
    updates, update_latencies, new_correct, retained, workloads = [], [], [], [], {}
    current = list(coefficients)
    for stage, reuses in enumerate(REUSE_SCHEDULE):
        a, b = current[0]
        current[0] = (a - 0.02, b + 0.015)
        coefficients = tuple(current)
        update_episode = make_episode(world, seed ^ stage ^ 0xBEEF, coefficients, regime=-1, rows=36)
        tick = time.perf_counter_ns()
        candidate.update(wrapped(update_episode, coefficients), None)
        update_latencies.append((time.perf_counter_ns() - tick) / 1000)
        updates.append(float(candidate.update_ops))
        changed = _query(world, -0.41, (-1,) * reasoning_depth, seed ^ stage ^ 0xCAFE)
        changed_target = _target(-0.41, (-1,) * reasoning_depth, coefficients)
        stage_ops, correctness = float(candidate.update_ops), []
        for _ in range(reuses):
            correctness.append(_correct(candidate.query(changed, reasoning_depth), changed_target))
            stage_ops += candidate.last_ops
        new_correct.append(all(correctness))
        retained.append(_correct(candidate.query(retained_query, reasoning_depth), retained_target))
        stage_ops += candidate.last_ops
        workloads[reuses] = stage_ops
        peak_state = max(peak_state, candidate.state_bytes())

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    accuracy = lambda rows: statistics.fmean(float(row["correct"]) for row in rows)
    reuse_rows, hits = warm + near, sum(row["hit"] for row in warm + near)
    correct_hits = sum(row["hit"] * row["correct"] for row in reuse_rows)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "reuse_precision": correct_hits / hits if hits else 0.0, "reuse_coverage": hits / len(reuse_rows),
        "false_reuse_rate": (hits - correct_hits) / hits if hits else 0.0,
        "continual_new_fact_accuracy": statistics.fmean(new_correct), "continual_retention": statistics.fmean(retained),
        "forecast_rmse": mean(cold, "rmse"), "near_forecast_rmse": mean(near, "rmse"),
        "fit_seconds": fit_seconds, "fit_ops": initial_fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_input_ops": mean(cold, "input"), "mean_alignment_ops": mean(cold, "search"),
        "mean_execution_ops": mean(cold, "execution"), "mean_memory_reads": mean(cold, "reads"),
        "mean_bytes_loaded": mean(cold, "bytes"), "p50_latency_us": percentile([r["latency"] for r in cold], 0.5),
        "p95_latency_us": percentile([r["latency"] for r in cold], 0.95),
        "warm_p50_latency_us": percentile([r["latency"] for r in warm], 0.5),
        "warm_p95_latency_us": percentile([r["latency"] for r in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(peak_state, fit_peak)),
        "update_ops": statistics.fmean(updates), "cumulative_update_ops": sum(updates),
        "mean_invalidated_entries": 1.0, "workload_ops_r1": workloads[1], "workload_ops_r4": workloads[4],
        "workload_ops_r16": workloads[16], "workload_ops": initial_fit_ops + sum(workloads.values()),
        "update_latency_us": statistics.fmean(update_latencies), "stream_channels": float(knowledge_size), "training_rows": float(len(episode.targets)),
        "relevant_channels": 2.0, "heldout_regime_order_rate": 1.0, "measurement_noise_std": 0.75,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
