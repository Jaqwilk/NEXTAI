from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass, replace
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..local_state_core import OracleSpec, feature, local_rule


BENCHMARK_VERSION = "nonlinear_local_state_transfer_v1"


@dataclass(frozen=True)
class World:
    descriptor_by_kind: tuple[int, ...]
    training_cases: tuple[tuple[tuple[int, ...], tuple[int, int]], ...]


@dataclass(frozen=True)
class Task:
    descriptors: tuple[int, ...]
    states: tuple[int, ...]
    edges: tuple[tuple[int, int], ...]
    source: int
    pulse: int
    signature: int


def make_world(seed: int) -> World:
    descriptors = list(range(8))
    random.Random(seed ^ 0xCA11).shuffle(descriptors)
    descriptors = tuple(descriptors[:5])
    cases = tuple((feature(descriptors[kind], state, pulse), local_rule(kind, state, pulse))
                  for kind in range(4) for state in range(8) for pulse in range(4))
    return World(descriptors, cases)


def make_task(world: World, size: int, seed: int, index: int) -> Task:
    rng = random.Random(seed ^ (index * 104729) ^ (size << 11))
    active = rng.sample(range(size), 3)
    descriptors = [world.descriptor_by_kind[rng.randrange(4)] for _ in range(size)]
    states = [7 * rng.randrange(2) for _ in range(size)]
    edges = [(rng.randrange(size), rng.randrange(size)) for _ in range(size)]
    for position, node in enumerate(active):
        edges[node] = (active[(position + 1) % 3], active[(position - 1) % 3])
    return Task(tuple(descriptors), tuple(states), tuple(edges), active[0], rng.randrange(4), index + 1)


def oracle_answer(task: Task, world: World, steps: int) -> tuple[int, int, int]:
    kinds = {descriptor: kind for kind, descriptor in enumerate(world.descriptor_by_kind)}
    node, pulse, states = task.source, task.pulse, list(task.states)
    for _ in range(steps):
        states[node], pulse = local_rule(kinds[task.descriptors[node]], states[node], pulse)
        node = task.edges[node][pulse & 1]
    return node, pulse, states[node]


def damaged(task: Task) -> Task:
    states = list(task.states)
    states[task.source] ^= 1
    return replace(task, states=tuple(states), signature=task.signature ^ 0xD00D)


def update_case(world: World, size: int) -> tuple[tuple[int, ...], tuple[int, int], Task]:
    raw = feature(world.descriptor_by_kind[4], 1, 3)
    target = local_rule(4, 1, 3)
    descriptors = (world.descriptor_by_kind[4],) + (world.descriptor_by_kind[0],) * (size - 1)
    task = Task(descriptors, (1,) + (0,) * (size - 1), tuple((1 % size, 1 % size) for _ in range(size)), 0, 3, 0xADD)
    return raw, target, task


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world, candidate = make_world(seed), load_candidate(candidate_name, seed)
    tasks = tuple(make_task(world, knowledge_size, seed ^ reasoning_depth, index)
                  for index in range(queries_per_cell))
    expected = tuple(oracle_answer(task, world, reasoning_depth) for task in tasks)
    fit_data = (OracleSpec({descriptor: kind for kind, descriptor in enumerate(world.descriptor_by_kind)}),) \
        if candidate_name == "oracle_local_state_rule" else world.training_cases
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    fit_ops = float(candidate.fit_ops)

    def measure(items: tuple[Task, ...]):
        rows = []
        for task in items:
            tick = time.perf_counter_ns()
            answer = candidate.query(task, reasoning_depth)
            rows.append((answer, float(candidate.last_ops), float(candidate.last_rule_evaluations),
                         float(candidate.last_active_cells), float(candidate.last_irregular_bytes),
                         (time.perf_counter_ns() - tick) / 1000.0))
        return rows

    cold, warm, near = measure(tasks), measure(tasks), measure(tuple(map(damaged, tasks)))
    raw, target, new_task = update_case(world, knowledge_size)
    tick = time.perf_counter_ns()
    candidate.update(raw, target)
    update_latency = (time.perf_counter_ns() - tick) / 1000.0
    new_correct = candidate.query(new_task, 1) == oracle_answer(new_task, world, 1)
    after_ops = float(candidate.last_ops)
    retained = candidate.query(tasks[0], reasoning_depth) == expected[0]
    mean = lambda rows, index: statistics.fmean(row[index] for row in rows)
    accuracy = lambda rows: statistics.fmean(row[0] == answer for row, answer in zip(rows, expected))
    input_bytes = float(48 * knowledge_size)
    workload = fit_ops + sum(row[1] for row in cold + near) + candidate.update_ops + 16 * after_ops
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "heldout_composition_accuracy": accuracy(cold), "damage_recovery_accuracy": accuracy(near),
        "continual_new_fact_accuracy": float(new_correct), "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, 1), "mean_warm_query_ops": mean(warm, 1),
        "mean_input_ops": float(6 * knowledge_size), "mean_rule_evaluations": mean(cold, 2),
        "mean_active_cells": mean(cold, 3), "mean_irregular_bytes": mean(cold, 4),
        "p50_latency_us": percentile([row[5] for row in cold], 0.5),
        "p95_latency_us": percentile([row[5] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row[5] for row in warm], 0.5),
        "warm_p95_latency_us": percentile([row[5] for row in warm], 0.95),
        "input_state_bytes": input_bytes, "state_bytes": float(candidate.state_bytes() + input_bytes),
        "peak_state_bytes": float(max(candidate.state_bytes() + input_bytes, fit_peak)),
        "update_ops": float(candidate.update_ops), "update_latency_us": update_latency,
        "workload_ops": float(workload), "recurrent_visit_required": float(reasoning_depth >= 4),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
