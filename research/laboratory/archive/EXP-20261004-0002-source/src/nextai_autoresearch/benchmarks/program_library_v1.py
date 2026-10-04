from __future__ import annotations

import importlib
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from nextai_autoresearch.program_search import DOMAIN_SIZE, TARGET_MACRO, execute

from .successor_graph_v1 import percentile


BENCHMARK_VERSION = "program_library_v1"


@dataclass(frozen=True)
class Task:
    program: tuple[int, ...]
    examples: tuple[tuple[int, int], ...]
    test_input: int
    expected: int


def make_training_corpus(size: int, seed: int) -> tuple[tuple[int, ...], ...]:
    offset = seed % 2
    return tuple(
        (
            2 + (index + offset) % 2,
            *TARGET_MACRO,
            2 + (index + offset + 1) % 2,
            *TARGET_MACRO,
            2 + (index // 2 + offset) % 2,
        )
        for index in range(size)
    )


def make_task(depth: int, seed: int, index: int) -> Task:
    if depth == 1:
        program = (2 + index % 2,)
    elif depth >= 4:
        chunks = [TARGET_MACRO, TARGET_MACRO, *((2,) for _ in range(depth - 4))]
        random.Random(seed ^ (index * 65537) ^ depth).shuffle(chunks)
        program = tuple(value for chunk in chunks for value in chunk)
    else:
        raise ValueError("program_library_v1 supports depth 1 or depth >= 4")
    rng = random.Random(seed ^ (index * 104729) ^ (depth << 16))
    inputs = rng.sample(range(DOMAIN_SIZE), 5)
    examples = tuple((value, execute(program, value)) for value in inputs[:4])
    return Task(program, examples, inputs[4], execute(program, inputs[4]))


def load_candidate(name: str, seed: int):
    module = importlib.import_module(f"nextai_autoresearch.candidates.{name}")
    return module.Candidate(seed=seed)


def run_trial(
    candidate_name: str,
    knowledge_size: int,
    reasoning_depth: int,
    queries_per_cell: int,
    seed: int,
    max_depth: int,
) -> dict[str, Any]:
    corpus = make_training_corpus(knowledge_size, seed)
    tasks = tuple(make_task(reasoning_depth, seed, index) for index in range(queries_per_cell))
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(corpus, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure(items: tuple[Task, ...]):
        answers, operations, nodes, descriptions, latencies = [], [], [], [], []
        for task in items:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(task.examples, task.test_input, reasoning_depth))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            nodes.append(float(candidate.last_nodes))
            descriptions.append(float(candidate.last_description_length))
        return answers, operations, nodes, descriptions, latencies

    answers, operations, nodes, descriptions, latencies = measure(tasks)
    warm_answers, warm_operations, _, _, warm_latencies = measure(tasks)
    update_program = make_training_corpus(1, seed ^ 0x5F3759DF)[0]
    update_started = time.perf_counter_ns()
    candidate.update(update_program)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_task = make_task(reasoning_depth, seed, queries_per_cell + 1)
    new_answer = candidate.query(new_task.examples, new_task.test_input, reasoning_depth)
    retained = candidate.query(tasks[0].examples, tasks[0].test_input, reasoning_depth)
    expected = [task.expected for task in tasks]
    accuracy = statistics.fmean(answer == target for answer, target in zip(answers, expected))
    warm_accuracy = statistics.fmean(
        answer == target for answer, target in zip(warm_answers, expected)
    )
    fit_ops = float(candidate.fit_ops)
    return {
        "status": "complete",
        "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth,
        "seed": seed,
        "query_count": queries_per_cell,
        "accuracy": accuracy,
        "warm_accuracy": warm_accuracy,
        "continual_new_fact_accuracy": float(new_answer == new_task.expected),
        "continual_retention": float(retained == tasks[0].expected),
        "fit_seconds": fit_seconds,
        "fit_ops": fit_ops,
        "mean_query_ops": statistics.fmean(operations),
        "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_search_nodes": statistics.fmean(nodes),
        "mean_description_length": statistics.fmean(descriptions),
        "amortized_cold_ops": (fit_ops + sum(operations)) / queries_per_cell,
        "learned_fragment": [list(item) for item in candidate.library],
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
