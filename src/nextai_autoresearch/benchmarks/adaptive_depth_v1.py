from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile


BENCHMARK_VERSION = "adaptive_depth_v1"


@dataclass(frozen=True)
class World:
    facts: tuple[tuple[int, int], ...]
    source: int
    terminal: int


def make_world(knowledge_size: int, depth: int, seed: int) -> World:
    if depth < 1 or knowledge_size < depth + 3:
        raise ValueError("need depth >= 1 and at least two distractor nodes")
    rng = random.Random(seed)
    nodes = list(range(knowledge_size))
    rng.shuffle(nodes)
    chain = nodes[: depth + 1]
    distractors = nodes[depth + 1 :]
    facts = [(chain[i], chain[i + 1]) for i in range(depth)]
    facts.append((chain[-1], chain[-1]))
    facts.extend(
        (node, distractors[(i + 1) % len(distractors)])
        for i, node in enumerate(distractors)
    )
    rng.shuffle(facts)
    return World(tuple(facts), chain[0], chain[-1])


def run_trial(
    candidate_name: str,
    knowledge_size: int,
    reasoning_depth: int,
    queries_per_cell: int,
    seed: int,
    max_depth: int,
) -> dict[str, Any]:
    world = make_world(knowledge_size, reasoning_depth, seed)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(world.facts, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure() -> tuple[list[int | None], list[float], list[float]]:
        answers, operations, latencies = [], [], []
        for _ in range(queries_per_cell):
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(world.source, 0))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
        return answers, operations, latencies

    answers, operations, latencies = measure()
    warm_answers, warm_operations, warm_latencies = measure()
    new_entity = knowledge_size
    update_started = time.perf_counter_ns()
    candidate.update(new_entity, new_entity)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_answer = candidate.query(new_entity, 0)
    retained = candidate.query(world.source, 0) == world.terminal

    accuracy = statistics.fmean(answer == world.terminal for answer in answers)
    warm_accuracy = statistics.fmean(
        answer == world.terminal for answer in warm_answers
    )
    return {
        "status": "complete",
        "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth,
        "seed": seed,
        "query_count": queries_per_cell,
        "accuracy": accuracy,
        "warm_accuracy": warm_accuracy,
        "continual_new_fact_accuracy": float(new_answer == new_entity),
        "continual_retention": float(retained),
        "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations),
        "mean_warm_query_ops": statistics.fmean(warm_operations),
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
        run_trial(
            candidate_name,
            int(knowledge_size),
            int(depth),
            int(matrix["queries_per_cell"]),
            int(seed),
            max_depth,
        )
        for seed in matrix["seeds"]
        for knowledge_size in matrix["knowledge_sizes"]
        for depth in matrix["reasoning_depths"]
    ]
