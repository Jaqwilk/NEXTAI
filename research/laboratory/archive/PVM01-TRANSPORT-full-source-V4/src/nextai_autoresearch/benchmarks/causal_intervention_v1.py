from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile


BENCHMARK_VERSION = "causal_intervention_v1"


@dataclass(frozen=True)
class World:
    parents: tuple[int, ...]
    biases: tuple[int, ...]
    order: tuple[int, ...]


@dataclass(frozen=True)
class Query:
    root_value: int
    interventions: tuple[tuple[int, int], ...]
    target: int


@dataclass(frozen=True)
class Task:
    query: Query
    expected: int
    mode: str


def make_world(size: int, seed: int) -> World:
    order = list(range(size))
    rng = random.Random(seed)
    rng.shuffle(order)
    parents, biases = [-1] * size, [0] * size
    for index in range(1, size):
        node = order[index]
        parents[node] = order[index - 1]
        biases[node] = rng.randrange(2)
    return World(tuple(parents), tuple(biases), tuple(order))


def simulate(world: World, root_value: int, interventions: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    forced = dict(interventions)
    values = [0] * len(world.order)
    for node in world.order:
        if node in forced:
            values[node] = forced[node]
        elif world.parents[node] == -1:
            values[node] = root_value
        else:
            values[node] = values[world.parents[node]] ^ world.biases[node]
    return tuple(values)


def training_corpus(world: World):
    episodes = []
    for root_value in (0, 1):
        episodes.append((root_value, (), simulate(world, root_value, ())))
        for node in range(len(world.order)):
            for value in (0, 1):
                interventions = ((node, value),)
                episodes.append((root_value, interventions, simulate(world, root_value, interventions)))
    return tuple(episodes)


def make_task(world: World, depth: int, seed: int, index: int) -> Task:
    root_value = (index // 2) % 2
    baseline = simulate(world, root_value, ())
    rng = random.Random(seed ^ (index * 65537) ^ (depth << 16))
    target = world.order[depth]
    if depth == 1:
        upstream, downstream = world.order[0], world.order[2]
    else:
        upstream = world.order[rng.randrange(depth - 1)]
        downstream = world.order[depth - 1]
    mode = "inconsistent" if index % 2 == 0 else "consistent"
    interventions = (
        (upstream, baseline[upstream]),
        (downstream, baseline[downstream] ^ int(mode == "inconsistent")),
    )
    interventions = tuple(sorted(interventions))
    query = Query(root_value, interventions, target)
    return Task(query, simulate(world, root_value, interventions)[target], mode)


def run_trial(
    candidate_name: str,
    knowledge_size: int,
    reasoning_depth: int,
    queries_per_cell: int,
    seed: int,
    max_depth: int,
) -> dict[str, Any]:
    world = make_world(knowledge_size, seed)
    corpus = training_corpus(world)
    tasks = tuple(
        make_task(world, reasoning_depth, seed, index)
        for index in range(queries_per_cell)
    )
    candidate = load_candidate(candidate_name, seed)
    fit_data = ((world.parents, world.biases, world.order),) if candidate_name == "oracle_local_causal" else corpus
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure(items: tuple[Task, ...]):
        answers, operations, visited, latencies = [], [], [], []
        for task in items:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(task.query, task.query.target))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            visited.append(float(candidate.last_visited_nodes))
        return answers, operations, visited, latencies

    answers, operations, visited, latencies = measure(tasks)
    warm_answers, warm_operations, warm_visited, warm_latencies = measure(tasks)
    update_task = tasks[0]
    update_episode = (
        update_task.query.root_value,
        update_task.query.interventions,
        simulate(world, update_task.query.root_value, update_task.query.interventions),
    )
    update_started = time.perf_counter_ns()
    candidate.update(update_episode, 0)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_task = make_task(world, reasoning_depth, seed, queries_per_cell + 1)
    new_answer = candidate.query(new_task.query, new_task.query.target)
    retained = candidate.query(tasks[0].query, tasks[0].query.target)
    expected = [task.expected for task in tasks]
    inconsistent = [task.mode == "inconsistent" for task in tasks]

    def accuracy(mask: list[bool]) -> float:
        return statistics.fmean(
            answer == target
            for answer, target, selected in zip(answers, expected, mask)
            if selected
        )

    structure_accuracy = float(
        getattr(candidate, "parents", ()) == world.parents
        and getattr(candidate, "biases", ()) == world.biases
        and getattr(candidate, "order", ()) == world.order
    )
    return {
        "status": "complete",
        "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth,
        "seed": seed,
        "query_count": queries_per_cell,
        "accuracy": statistics.fmean(a == b for a, b in zip(answers, expected)),
        "warm_accuracy": statistics.fmean(a == b for a, b in zip(warm_answers, expected)),
        "ood_intervention_accuracy": statistics.fmean(a == b for a, b in zip(answers, expected)),
        "inconsistent_accuracy": accuracy(inconsistent),
        "consistent_accuracy": accuracy([not value for value in inconsistent]),
        "structure_accuracy": structure_accuracy,
        "continual_new_fact_accuracy": float(new_answer == new_task.expected),
        "continual_retention": float(retained == tasks[0].expected),
        "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations),
        "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_visited_nodes": statistics.fmean(visited),
        "mean_warm_visited_nodes": statistics.fmean(warm_visited),
        "p50_latency_us": percentile(latencies, 0.50),
        "p95_latency_us": percentile(latencies, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies, 0.50),
        "warm_p95_latency_us": percentile(warm_latencies, 0.95),
        "update_latency_us": update_latency_us,
        "update_ops": float(candidate.update_ops),
        "state_bytes": float(max(candidate.state_bytes(), traced_peak)),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [
        run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
        for seed in matrix["seeds"]
        for size in matrix["knowledge_sizes"]
        for depth in matrix["reasoning_depths"]
    ]
