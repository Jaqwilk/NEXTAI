from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..entity_binding_contract import (
    BindingFact, DIMENSION, OracleQuery, OracleSpec, OracleUpdate, View, ViewQuery,
)


BENCHMARK_VERSION = "latent_entity_binding_retrieval_v1"


@dataclass(frozen=True)
class World:
    codes: tuple[int, ...]
    stable: tuple[int, ...]
    polarity: tuple[int, ...]
    transitions: dict[int, int]
    values: dict[int, int]
    facts: tuple[BindingFact, ...]
    seed: int


@dataclass(frozen=True)
class Task:
    query: ViewQuery
    near: ViewQuery
    oracle: OracleQuery
    expected: int


def _view(world: World, entity: int, view_id: int, nuisance: float = 3.0) -> View:
    rng = random.Random(world.seed ^ (entity * 104729) ^ (view_id * 130363))
    values = [rng.uniform(-nuisance, nuisance) for _ in range(DIMENSION)]
    code = world.codes[entity]
    for bit, position in enumerate(world.stable):
        sign = 1.0 if (code >> bit) & 1 else -1.0
        values[position] = world.polarity[bit] * sign + rng.uniform(-0.12, 0.12)
    return tuple(values)


def _pair(world: World, entity: int, offset: int) -> tuple[View, View]:
    return _view(world, entity, offset), _view(world, entity, offset + 1)


def make_world(size: int, seed: int) -> World:
    if size not in (8, 32):
        raise ValueError("v1 quick supports K=8 or K=32")
    rng = random.Random(seed ^ 0xE171)
    codes = rng.sample(range(64), size + 1)
    stable = tuple(rng.sample(range(DIMENSION), 6))
    polarity = tuple(rng.choice((-1, 1)) for _ in range(6))
    order = list(range(size))
    rng.shuffle(order)
    transitions = {order[i]: order[(i + 1) % size] for i in range(size)}
    values = {entity: 10000 + rng.randrange(1_000_000) for entity in range(size + 1)}
    shell = World(tuple(codes), stable, polarity, transitions, values, (), seed)
    facts = tuple(BindingFact(_pair(shell, source, 10 + 8 * source),
                              _pair(shell, target, 1000 + 8 * source), values[target])
                  for source, target in transitions.items())
    return World(tuple(codes), stable, polarity, transitions, values, facts, seed)


def make_tasks(world: World, depth: int, seed: int, count: int) -> tuple[Task, ...]:
    rng = random.Random(seed ^ (depth * 65537))
    tasks = []
    for index in range(count):
        source = rng.randrange(len(world.transitions))
        target = source
        for _ in range(depth):
            target = world.transitions[target]
        query = ViewQuery(_view(world, source, 5000 + index), index + 1)
        near = ViewQuery(_view(world, source, 7000 + index, 5.0), index + 1001)
        tasks.append(Task(query, near, OracleQuery(query.view, query.signature, source), world.values[target]))
    return tuple(tasks)


def update_items(world: World, size: int):
    entity = size
    fact = BindingFact(_pair(world, entity, 9000), _pair(world, entity, 9100), world.values[entity])
    query = ViewQuery(_view(world, entity, 9200), 0xADD)
    return fact, query, OracleQuery(query.view, query.signature, entity), OracleUpdate(entity, entity, world.values[entity])


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world, candidate = make_world(knowledge_size, seed), load_candidate(candidate_name, seed)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell)
    fit_data = (OracleSpec(world.transitions, world.values),) if candidate_name == "oracle_identity_index" else world.facts
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    fit_ops = float(candidate.fit_ops)

    def measure(near: bool = False):
        rows = []
        for task in tasks:
            source = task.oracle if candidate_name == "oracle_identity_index" else (task.near if near else task.query)
            tick = time.perf_counter_ns()
            answer = candidate.query(source, reasoning_depth)
            rows.append((answer, float(candidate.last_ops), float(candidate.last_comparisons),
                         float(candidate.last_bytes_touched), (time.perf_counter_ns() - tick) / 1000.0))
        return rows

    cold, warm, near = measure(), measure(), measure(True)
    fact, query, oracle_query, oracle_update = update_items(world, knowledge_size)
    update_source = oracle_update if candidate_name == "oracle_identity_index" else fact
    tick = time.perf_counter_ns()
    candidate.update(update_source, fact.value)
    update_latency = (time.perf_counter_ns() - tick) / 1000.0
    new_source = oracle_query if candidate_name == "oracle_identity_index" else query
    new_correct = candidate.query(new_source, 1) == fact.value
    after_ops = float(candidate.last_ops)
    old_source = tasks[0].oracle if candidate_name == "oracle_identity_index" else tasks[0].query
    retained = candidate.query(old_source, reasoning_depth) == tasks[0].expected
    accuracy = lambda rows: statistics.fmean(row[0] == task.expected for row, task in zip(rows, tasks))
    mean = lambda rows, index: statistics.fmean(row[index] for row in rows)
    workload = fit_ops + sum(row[1] for row in cold + near) + candidate.update_ops + 16 * after_ops
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "false_reuse_rate": 1.0 - accuracy(cold), "continual_new_fact_accuracy": float(new_correct),
        "continual_retention": float(retained), "fit_seconds": fit_seconds, "fit_ops": fit_ops,
        "fit_peak_bytes": float(fit_peak), "mean_query_ops": mean(cold, 1),
        "mean_warm_query_ops": mean(warm, 1), "mean_input_ops": float(DIMENSION),
        "mean_comparisons": mean(cold, 2), "mean_bytes_touched": mean(cold, 3),
        "p50_latency_us": percentile([row[4] for row in cold], 0.5),
        "p95_latency_us": percentile([row[4] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row[4] for row in warm], 0.5),
        "warm_p95_latency_us": percentile([row[4] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(candidate.state_bytes(), fit_peak)),
        "update_ops": float(candidate.update_ops), "update_latency_us": update_latency,
        "workload_ops": float(workload), "selected_dimensions": float(len(getattr(candidate, "dimensions", ()))),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
