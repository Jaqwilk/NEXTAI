from __future__ import annotations

import math
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

import numpy as np

from .successor_graph_v1 import load_candidate, percentile
from ..entity_addressing_contract import (
    DEPTHS, KNOWLEDGE_SIZES, OBSERVATION_DIMENSION, PrivateQuery, PrivateSpec,
    RawQuery, ROLE_CONTRACT, TransitionBurst,
)


BENCHMARK_VERSION = "latent_entity_binding_retrieval_v2"
PRIVILEGED = "privileged_exact_entity_key_v1"


@dataclass(frozen=True)
class World:
    records: tuple[TransitionBurst, ...]
    transitions: dict[int, int]
    values: dict[int, int]
    latent: tuple[tuple[float, float, float], ...]
    encoder_a: tuple[tuple[float, float, float], ...]
    encoder_b: tuple[tuple[float, float, float], ...]
    phase: tuple[float, ...]
    seed: int


@dataclass(frozen=True)
class Task:
    public: RawQuery
    private: PrivateQuery
    expected: int


def _observation(world: World, entity: int, view: int, noise: float = 0.015) -> tuple[float, ...]:
    z = np.asarray(world.latent[entity])
    a, b, phase = np.asarray(world.encoder_a), np.asarray(world.encoder_b), np.asarray(world.phase)
    rng = np.random.default_rng(world.seed ^ (entity * 104729) ^ (view * 130363))
    raw = np.tanh(a @ z + 0.35 * np.sin(b @ z + phase))
    return tuple(float(value) for value in raw + rng.normal(0.0, noise, OBSERVATION_DIMENSION))


def make_world(size: int, seed: int) -> World:
    if size not in KNOWLEDGE_SIZES:
        raise ValueError(f"v2 requires K in {KNOWLEDGE_SIZES}")
    rng = random.Random(seed ^ 0xADDE55)
    side = math.ceil(size ** (1 / 3))
    latent = []
    for index in range(size + 1):
        x, rem = divmod(index, side * side)
        y, z = divmod(rem, side)
        latent.append(tuple(2.0 * coordinate / max(side - 1, 1) - 1.0 for coordinate in (x, y, z)))
    rng.shuffle(latent)
    encoder_a = tuple(tuple(rng.uniform(-1.7, 1.7) for _ in range(3)) for _ in range(OBSERVATION_DIMENSION))
    encoder_b = tuple(tuple(rng.uniform(-2.3, 2.3) for _ in range(3)) for _ in range(OBSERVATION_DIMENSION))
    phase = tuple(rng.uniform(-math.pi, math.pi) for _ in range(OBSERVATION_DIMENSION))
    order = list(range(size))
    rng.shuffle(order)
    transitions = {order[i]: order[(i + 1) % size] for i in range(size)}
    values = {entity: 1_000_000 + rng.randrange(1_000_000_000) for entity in range(size + 1)}
    shell = World((), transitions, values, tuple(latent), encoder_a, encoder_b, phase, seed)
    records = []
    for slot, (source, target) in enumerate(transitions.items()):
        cut = 2 + rng.randrange(4)
        observations = tuple(_observation(shell, source, 10_000 + 16 * slot + i) for i in range(cut))
        observations += tuple(_observation(shell, target, 20_000 + 16 * slot + i) for i in range(7 - cut))
        records.append(TransitionBurst(observations, values[target]))
    rng.shuffle(records)
    return World(tuple(records), transitions, values, tuple(latent), encoder_a, encoder_b, phase, seed)


def make_tasks(world: World, depth: int, seed: int, count: int) -> tuple[Task, ...]:
    rng = random.Random(seed ^ depth * 65537)
    tasks = []
    for index in range(count):
        source = rng.randrange(len(world.transitions))
        target = source
        for _ in range(depth):
            target = world.transitions[target]
        observation = _observation(world, source, 50_000 + index)
        public = RawQuery(observation, index + 1)
        tasks.append(Task(public, PrivateQuery(observation, index + 1, source), world.values[target]))
    return tuple(tasks)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world, candidate = make_world(knowledge_size, seed), load_candidate(candidate_name, seed)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell)
    fit_data = (PrivateSpec(world.transitions, world.values),) if candidate_name == PRIVILEGED else world.records
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rows = []
    for task in tasks:
        query = task.private if candidate_name == PRIVILEGED else task.public
        tick = time.perf_counter_ns()
        answer = candidate.query(query, reasoning_depth)
        rows.append((answer, candidate.last_ops, candidate.last_comparisons, candidate.last_bytes_touched,
                     (time.perf_counter_ns() - tick) / 1000.0))
    warm = []
    for task in tasks:
        query = task.private if candidate_name == PRIVILEGED else task.public
        answer = candidate.query(query, reasoning_depth)
        warm.append((answer, candidate.last_ops))

    new_entity = knowledge_size
    target = next(iter(world.transitions))
    update_record = TransitionBurst(
        tuple(_observation(world, new_entity, 80_000 + i) for i in range(3))
        + tuple(_observation(world, target, 90_000 + i) for i in range(4)),
        world.values[target],
    )
    update_source = (new_entity, target) if candidate_name == PRIVILEGED else update_record
    tick = time.perf_counter_ns()
    candidate.update(update_source, world.values[target])
    update_latency = (time.perf_counter_ns() - tick) / 1000.0
    query_observation = _observation(world, new_entity, 100_000)
    update_query = PrivateQuery(query_observation, 0xADD, new_entity) if candidate_name == PRIVILEGED else RawQuery(query_observation, 0xADD)
    new_correct = candidate.query(update_query, 1) == world.values[target]
    after_ops = float(candidate.last_ops)
    accuracy = statistics.fmean(row[0] == task.expected for row, task in zip(rows, tasks))
    warm_accuracy = statistics.fmean(row[0] == task.expected for row, task in zip(warm, tasks))
    mean_query = statistics.fmean(float(row[1]) for row in rows)
    acquisition = knowledge_size * 7 * OBSERVATION_DIMENSION
    base = acquisition + float(candidate.fit_ops) + float(candidate.update_ops)
    workloads = {reuse: base + reuse * (queries_per_cell * mean_query + after_ops) for reuse in (1, 4, 16, 256, 4096)}
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy,
        "warm_accuracy": warm_accuracy, "near_equivalent_accuracy": accuracy,
        "continual_new_fact_accuracy": float(new_correct), "continual_retention": accuracy,
        "data_acquisition_ops": float(acquisition), "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops), "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean_query, "mean_warm_query_ops": statistics.fmean(float(row[1]) for row in warm),
        "mean_input_ops": float(OBSERVATION_DIMENSION),
        "mean_comparisons": statistics.fmean(float(row[2]) for row in rows),
        "mean_bytes_touched": statistics.fmean(float(row[3]) for row in rows),
        "p50_latency_us": percentile([float(row[4]) for row in rows], 0.5),
        "p95_latency_us": percentile([float(row[4]) for row in rows], 0.95),
        "state_bytes": float(candidate.state_bytes()),
        "peak_state_bytes": float(max(candidate.state_bytes(), fit_peak)),
        "update_ops": float(candidate.update_ops), "update_latency_us": update_latency,
        "workload_ops": workloads[16], "workload_ops_r1": workloads[1],
        "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
        "workload_ops_r256": workloads[256], "workload_ops_r4096": workloads[4096],
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max(DEPTHS))
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
