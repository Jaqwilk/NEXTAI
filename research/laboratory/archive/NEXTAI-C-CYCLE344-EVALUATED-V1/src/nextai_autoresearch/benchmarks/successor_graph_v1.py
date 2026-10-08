from __future__ import annotations

import importlib
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from nextai_autoresearch.candidates.base import CandidateBase, UnsupportedScale


BENCHMARK_VERSION = "successor_graph_v1"


@dataclass(frozen=True)
class World:
    facts: tuple[tuple[int, int], ...]
    oracle: dict[int, int]


def make_world(knowledge_size: int, seed: int) -> World:
    if knowledge_size < 4:
        raise ValueError("knowledge_size must be at least 4")
    rng = random.Random(seed)
    permutation = list(range(knowledge_size))
    rng.shuffle(permutation)
    oracle = {
        permutation[index]: permutation[(index + 1) % knowledge_size]
        for index in range(knowledge_size)
    }
    facts = list(oracle.items())
    rng.shuffle(facts)
    return World(tuple(facts), oracle)


def oracle_answer(oracle: dict[int, int], source: int, steps: int) -> int | None:
    current = source
    for _ in range(steps):
        current = oracle.get(current)
        if current is None:
            return None
    return current


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def load_candidate(candidate_name: str, seed: int) -> CandidateBase:
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    candidate_class = getattr(module, "Candidate")
    candidate = candidate_class(seed=seed)
    if not isinstance(candidate, CandidateBase):
        raise TypeError(f"{candidate_name}.Candidate must inherit CandidateBase")
    return candidate


def run_trial(
    candidate_name: str,
    knowledge_size: int,
    reasoning_depth: int,
    queries_per_cell: int,
    seed: int,
    max_depth: int,
) -> dict[str, Any]:
    world = make_world(knowledge_size, seed)
    candidate = load_candidate(candidate_name, seed)
    try:
        tracemalloc.start()
        fit_start = time.perf_counter()
        candidate.fit(world.facts, knowledge_size, max_depth)
        fit_seconds = time.perf_counter() - fit_start
        _, traced_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    except UnsupportedScale as exc:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        return {
            "status": "unsupported",
            "knowledge_size": knowledge_size,
            "reasoning_depth": reasoning_depth,
            "seed": seed,
            "reason": str(exc),
        }

    rng = random.Random(seed ^ (reasoning_depth << 16) ^ knowledge_size)
    queries = [rng.randrange(knowledge_size) for _ in range(queries_per_cell)]
    expected = [oracle_answer(world.oracle, source, reasoning_depth) for source in queries]

    answers: list[int | None] = []
    operations: list[float] = []
    latencies_us: list[float] = []
    for source in queries:
        started = time.perf_counter_ns()
        answers.append(candidate.query(source, reasoning_depth))
        latencies_us.append((time.perf_counter_ns() - started) / 1000.0)
        operations.append(float(candidate.last_ops))

    warm_answers: list[int | None] = []
    warm_operations: list[float] = []
    warm_latencies_us: list[float] = []
    for source in queries:
        started = time.perf_counter_ns()
        warm_answers.append(candidate.query(source, reasoning_depth))
        warm_latencies_us.append((time.perf_counter_ns() - started) / 1000.0)
        warm_operations.append(float(candidate.last_ops))

    old_expected = expected[: min(8, len(expected))]
    old_queries = queries[: min(8, len(queries))]
    new_entity = knowledge_size
    update_started = time.perf_counter_ns()
    candidate.update(new_entity, new_entity)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_answer = candidate.query(new_entity, max(1, min(reasoning_depth, max_depth)))
    retained = [
        candidate.query(source, reasoning_depth) == target
        for source, target in zip(old_queries, old_expected)
    ]

    accuracy = statistics.fmean(
        float(answer == target) for answer, target in zip(answers, expected)
    )
    warm_accuracy = statistics.fmean(
        float(answer == target) for answer, target in zip(warm_answers, expected)
    )
    return {
        "status": "complete",
        "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth,
        "seed": seed,
        "query_count": len(queries),
        "accuracy": accuracy,
        "warm_accuracy": warm_accuracy,
        "continual_new_fact_accuracy": float(new_answer == new_entity),
        "continual_retention": statistics.fmean(float(value) for value in retained),
        "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations),
        "mean_warm_query_ops": statistics.fmean(warm_operations),
        "p50_latency_us": percentile(latencies_us, 0.50),
        "p95_latency_us": percentile(latencies_us, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies_us, 0.50),
        "warm_p95_latency_us": percentile(warm_latencies_us, 0.95),
        "update_latency_us": update_latency_us,
        "update_ops": float(candidate.update_ops),
        "state_bytes": float(max(candidate.state_bytes(), traced_peak)),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(int(value) for value in matrix["reasoning_depths"])
    trials: list[dict[str, Any]] = []
    for seed in matrix["seeds"]:
        for knowledge_size in matrix["knowledge_sizes"]:
            for reasoning_depth in matrix["reasoning_depths"]:
                trials.append(
                    run_trial(
                        candidate_name=candidate_name,
                        knowledge_size=int(knowledge_size),
                        reasoning_depth=int(reasoning_depth),
                        queries_per_cell=int(matrix["queries_per_cell"]),
                        seed=int(seed),
                        max_depth=max_depth,
                    )
                )
    return trials

