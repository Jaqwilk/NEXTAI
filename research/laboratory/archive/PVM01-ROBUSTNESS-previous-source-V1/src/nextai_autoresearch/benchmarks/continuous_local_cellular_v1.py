from __future__ import annotations

import math
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile


BENCHMARK_VERSION = "continuous_local_cellular_v1"
CHANNELS = 4
TRAINING_TRANSITIONS = 384
REUSES = (1, 4, 16)
ERROR_THRESHOLD = 0.10
MINIMUM_NRMSE_GAIN = 0.01

Vector = tuple[float, float, float, float]
Latent = tuple[float, float]


@dataclass(frozen=True)
class Transition:
    left: Vector
    center: Vector
    right: Vector
    target: Vector


@dataclass(frozen=True)
class Task:
    size: int
    source: int
    target: int
    initial: tuple[tuple[int, Vector], ...]


@dataclass(frozen=True)
class World:
    permutation: tuple[int, ...]
    signs: tuple[int, ...]
    training: tuple[Transition, ...]


@dataclass(frozen=True)
class PrivilegedWorld:
    world: World


def _step(left: Latent, center: Latent, right: Latent) -> Latent:
    x, y = center
    return (
        math.tanh(0.62 * x + 0.28 * (left[0] + right[0]) + 0.14 * math.tanh(y) + 0.06 * x * y),
        math.tanh(0.65 * y + 0.24 * (left[1] + right[1]) - 0.12 * math.tanh(x) + 0.05 * (left[0] - right[0])),
    )


def encode(world: World, latent: Latent) -> Vector:
    x, y = latent
    raw = (x, y, 0.5 * x + 0.25 * y + 0.1 * x * y, math.tanh(x - y))
    return tuple(world.signs[index] * raw[source] for index, source in enumerate(world.permutation))  # type: ignore[return-value]


def decode(world: World, vector: Vector) -> Latent:
    raw = [0.0] * CHANNELS
    for index, source in enumerate(world.permutation):
        raw[source] = world.signs[index] * vector[index]
    return raw[0], raw[1]


def make_world(seed: int) -> World:
    rng = random.Random(seed ^ 0xC311)
    permutation = list(range(CHANNELS))
    rng.shuffle(permutation)
    signs = tuple(rng.choice((-1, 1)) for _ in range(CHANNELS))
    shell = World(tuple(permutation), signs, ())
    rows = []
    for _ in range(TRAINING_TRANSITIONS):
        latent = tuple((rng.uniform(-0.65, 0.65), rng.uniform(-0.65, 0.65)) for _ in range(3))
        rows.append(Transition(
            encode(shell, latent[0]), encode(shell, latent[1]), encode(shell, latent[2]),
            encode(shell, _step(latent[0], latent[1], latent[2])),
        ))
    return World(shell.permutation, shell.signs, tuple(rows))


def make_task(world: World, size: int, depth: int, seed: int, index: int, *, damaged: bool = False) -> Task:
    rng = random.Random(seed ^ size * 65537 ^ depth * 8191 ^ index * 104729)
    source = rng.randrange(size)
    target = (source + rng.randrange(-min(2, depth), min(2, depth) + 1)) % size
    amplitude = rng.uniform(0.85, 1.10) * rng.choice((-1.0, 1.0))
    vector = list(encode(world, (amplitude, -0.55 * amplitude)))
    if damaged:
        vector[index % CHANNELS] += 0.75 * (1.0 if vector[index % CHANNELS] <= 0 else -1.0)
    return Task(size, source, target, ((source, tuple(vector)),))  # type: ignore[arg-type]


def oracle_target(world: World, task: Task, depth: int) -> Vector:
    state = {position: decode(world, vector) for position, vector in task.initial}
    for _ in range(depth):
        active = set(state)
        positions = active | {(position - 1) % task.size for position in active} | {(position + 1) % task.size for position in active}
        state = {
            position: _step(
                state.get((position - 1) % task.size, (0.0, 0.0)),
                state.get(position, (0.0, 0.0)),
                state.get((position + 1) % task.size, (0.0, 0.0)),
            )
            for position in positions
        }
    return encode(world, state.get(task.target, (0.0, 0.0)))


def _error(answer: Any, target: Vector) -> float:
    try:
        values = tuple(float(value) for value in answer)
    except (TypeError, ValueError):
        return 1_000_000.0
    if len(values) != CHANNELS or not all(math.isfinite(value) for value in values):
        return 1_000_000.0
    rmse = math.sqrt(statistics.fmean((value - expected) ** 2 for value, expected in zip(values, target)))
    scale = max(0.10, math.sqrt(statistics.fmean(value * value for value in target)))
    return rmse / scale


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world = make_world(seed)
    candidate = load_candidate(candidate_name, seed)
    fit_data: Any = PrivilegedWorld(world) if candidate_name == "privileged_continuous_local_support" else world.training
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_state = max(candidate.state_bytes(), fit_peak)
    tasks = tuple(make_task(world, knowledge_size, reasoning_depth, seed, index) for index in range(queries_per_cell))
    damaged = tuple(make_task(world, knowledge_size, reasoning_depth, seed, index, damaged=True) for index in range(queries_per_cell))

    def measure(items: tuple[Task, ...], clean_items: tuple[Task, ...]):
        nonlocal peak_state
        rows = []
        for task, clean in zip(items, clean_items):
            target = oracle_target(world, clean, reasoning_depth)
            tick = time.perf_counter_ns()
            answer = candidate.query(task, reasoning_depth)
            error = _error(answer, target)
            valid = float(error < 1_000_000.0)
            rows.append((error, float(candidate.last_ops), float(getattr(candidate, "last_bytes_touched", candidate.last_ops * 8)),
                         (time.perf_counter_ns() - tick) / 1000.0, valid))
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold = measure(tasks, tasks)
    warm = measure(tasks, tasks)
    repaired = measure(damaged, tasks)
    update_row = world.training[-1]
    tick = time.perf_counter_ns()
    candidate.update(update_row, None)
    update_latency = (time.perf_counter_ns() - tick) / 1000.0
    new_task = make_task(world, knowledge_size, min(4, reasoning_depth), seed ^ 0xADD, 0)
    new_error = _error(candidate.query(new_task, min(4, reasoning_depth)), oracle_target(world, new_task, min(4, reasoning_depth)))
    retained_error = _error(candidate.query(tasks[0], reasoning_depth), oracle_target(world, tasks[0], reasoning_depth))
    mean = lambda rows, index: statistics.fmean(row[index] for row in rows)
    rate = lambda rows: statistics.fmean(float(row[0] <= ERROR_THRESHOLD) for row in rows)
    acquisition = float(TRAINING_TRANSITIONS * CHANNELS * 4)
    base = acquisition + float(candidate.fit_ops) + sum(row[1] for row in cold + repaired) + float(candidate.update_ops)
    warm_total = sum(row[1] for row in warm)
    workloads = {reuse: base + reuse * warm_total for reuse in REUSES}
    finite_rate = statistics.fmean(row[4] for row in cold + repaired)
    return {
        "status": "complete", "world_family": "continuous_local_cellular", "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth, "seed": seed, "query_count": queries_per_cell,
        "accuracy": rate(cold), "warm_accuracy": rate(warm), "near_equivalent_accuracy": rate(repaired),
        "normalized_rmse": mean(cold, 0), "stable_rollout_rate": finite_rate,
        "continual_new_fact_accuracy": float(new_error <= ERROR_THRESHOLD),
        "continual_retention": float(retained_error <= ERROR_THRESHOLD),
        "data_acquisition_ops": acquisition, "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops),
        "fit_peak_bytes": float(fit_peak), "mean_query_ops": mean(cold, 1),
        "mean_warm_query_ops": mean(warm, 1), "mean_input_ops": float(CHANNELS + 3),
        "mean_bytes_touched": mean(cold, 2), "p50_latency_us": percentile([row[3] for row in cold], 0.5),
        "p95_latency_us": percentile([row[3] for row in cold], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(peak_state),
        "update_ops": float(candidate.update_ops), "update_latency_us": update_latency,
        "workload_ops": workloads[16], "workload_ops_r1": workloads[1],
        "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
