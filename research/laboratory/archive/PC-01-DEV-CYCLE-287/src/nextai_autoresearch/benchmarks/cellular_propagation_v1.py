from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile


BENCHMARK_VERSION = "cellular_propagation_v1"


@dataclass(frozen=True)
class Task:
    side: int
    cells: tuple[int, ...]
    source: int
    goals: tuple[int, int]
    steps: int
    damage: str
    expected: bool


def _neighbors(cell: int, side: int) -> tuple[int, ...]:
    row, column = divmod(cell, side)
    return tuple(
        next_row * side + next_column
        for next_row in range(max(0, row - 1), min(side, row + 2))
        for next_column in range(max(0, column - 1), min(side, column + 2))
        if (next_row, next_column) != (row, column)
    )


def oracle_answer(task: Task) -> bool:
    active = {task.source}
    for _ in range(task.steps):
        active |= {
            cell
            for cell, open_cell in enumerate(task.cells)
            if open_cell and any(neighbor in active for neighbor in _neighbors(cell, task.side))
        }
    return any(goal in active for goal in task.goals)


def make_task(side: int, depth: int, seed: int, index: int) -> Task:
    if side < depth + 2:
        raise ValueError("grid side must exceed propagation depth")
    rng = random.Random(seed ^ (index * 104729) ^ (depth << 16))
    middle_row = side // 2
    rows = (middle_row - 1, middle_row + 1)
    start_column = 1
    source = middle_row * side + start_column
    cells = [0] * (side * side)
    cells[source] = 1
    for row in rows:
        for column in range(start_column + 1, start_column + depth + 1):
            cells[row * side + column] = 1
    break_column = start_column + rng.randrange(1, depth + 1)
    damage = "single" if index % 2 == 0 else "double"
    cells[rows[rng.randrange(2)] * side + break_column] = 0
    if damage == "double":
        cells[rows[0] * side + break_column] = 0
        cells[rows[1] * side + break_column] = 0
    goals = tuple(row * side + start_column + depth for row in rows)
    provisional = Task(side, tuple(cells), source, goals, depth, damage, False)
    return Task(side, tuple(cells), source, goals, depth, damage, oracle_answer(provisional))


def training_cases(seed: int) -> tuple[tuple[tuple[int, int], int], ...]:
    cases = [((0, 0), 0), ((0, 1), 0), ((1, 0), 0), ((1, 1), 1)]
    random.Random(seed).shuffle(cases)
    return tuple(cases)


def run_trial(
    candidate_name: str,
    knowledge_size: int,
    reasoning_depth: int,
    queries_per_cell: int,
    seed: int,
    max_depth: int,
) -> dict[str, Any]:
    tasks = tuple(
        make_task(knowledge_size, reasoning_depth, seed, index)
        for index in range(queries_per_cell)
    )
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training_cases(seed), knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure(items: tuple[Task, ...]):
        answers, operations, cell_updates, latencies = [], [], [], []
        for task in items:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(task, task.steps))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            cell_updates.append(float(candidate.last_cell_updates))
        return answers, operations, cell_updates, latencies

    answers, operations, cell_updates, latencies = measure(tasks)
    warm_answers, warm_operations, warm_cell_updates, warm_latencies = measure(tasks)
    update_started = time.perf_counter_ns()
    candidate.update((1, 1), 1)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_task = make_task(knowledge_size, reasoning_depth, seed, queries_per_cell + 1)
    new_answer = candidate.query(new_task, new_task.steps)
    retained = candidate.query(tasks[0], tasks[0].steps)
    expected = [task.expected for task in tasks]
    damage_mask = [task.damage == "single" for task in tasks]
    input_state_bytes = knowledge_size * knowledge_size * 8

    def accuracy(mask: list[bool]) -> float:
        return statistics.fmean(
            answer == target
            for answer, target, selected in zip(answers, expected, mask)
            if selected
        )

    return {
        "status": "complete",
        "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth,
        "seed": seed,
        "query_count": queries_per_cell,
        "accuracy": statistics.fmean(a == b for a, b in zip(answers, expected)),
        "warm_accuracy": statistics.fmean(a == b for a, b in zip(warm_answers, expected)),
        "damage_accuracy": accuracy(damage_mask),
        "blocked_accuracy": accuracy([not value for value in damage_mask]),
        "continual_new_fact_accuracy": float(new_answer == new_task.expected),
        "continual_retention": float(retained == tasks[0].expected),
        "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations),
        "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_cell_updates": statistics.fmean(cell_updates),
        "mean_warm_cell_updates": statistics.fmean(warm_cell_updates),
        "p50_latency_us": percentile(latencies, 0.50),
        "p95_latency_us": percentile(latencies, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies, 0.50),
        "warm_p95_latency_us": percentile(warm_latencies, 0.95),
        "update_latency_us": update_latency_us,
        "update_ops": float(candidate.update_ops),
        "input_state_bytes": float(input_state_bytes),
        "state_bytes": float(max(candidate.state_bytes() + input_state_bytes, traced_peak)),
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
