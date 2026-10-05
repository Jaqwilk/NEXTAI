from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..pointer_machine_core import ALT, BRANCH, NEXT, PRIMITIVES, READ_NEXT, Demo, Task, encode, execute, step


BENCHMARK_VERSION = "pointer_machine_composition_v1"
ACTIVE_CELLS = 8


@dataclass(frozen=True)
class MemoryCase:
    memory: tuple[tuple[int, int, int], ...]
    addresses: tuple[int, ...]


def token_mapping(seed: int) -> dict[int, int]:
    actions = list(PRIMITIVES)
    random.Random(seed ^ 0xA17C).shuffle(actions)
    return dict(zip((101, 211, 307, 401), actions))


def make_case(size: int, seed: int, adversarial: bool) -> MemoryCase:
    if size < ACTIVE_CELLS:
        raise ValueError("pointer memory requires at least eight cells")
    positions = [(index * (size - 1)) // (ACTIVE_CELLS - 1) for index in range(ACTIVE_CELLS)]
    random.Random(seed ^ 0x51A7).shuffle(positions)
    addresses = tuple(positions)
    if adversarial:
        bits = tuple((index // 2) % 2 for index in range(ACTIVE_CELLS))
        next_nodes = tuple((index + 1) % ACTIVE_CELLS for index in range(ACTIVE_CELLS))
        alt_nodes = tuple((index + 4) % ACTIVE_CELLS for index in range(ACTIVE_CELLS))
    else:
        rng = random.Random(seed)
        bits = tuple(rng.randrange(2) for _ in range(ACTIVE_CELLS))
        next_nodes, alt_nodes = [], []
        for node in range(ACTIVE_CELLS):
            choices = [item for item in range(ACTIVE_CELLS) if item != node]
            left, right = rng.sample(choices, 2)
            next_nodes.append(left)
            alt_nodes.append(right)
        next_nodes, alt_nodes = tuple(next_nodes), tuple(alt_nodes)
    memory = [(index % 2, index, index) for index in range(size)]
    for node, address in enumerate(addresses):
        memory[address] = (bits[node], addresses[next_nodes[node]], addresses[alt_nodes[node]])
    return MemoryCase(tuple(memory), addresses)


def training_corpus(size: int, seed: int, mapping: dict[int, int]) -> tuple[Demo, ...]:
    demos = []
    for token, true_action in sorted(mapping.items()):
        valid = set(PRIMITIVES)
        for index in range(64):
            case = make_case(size, seed ^ 0xD300 ^ (index * 65537), bool(index % 2))
            start = case.addresses[(index * 3 + true_action) % ACTIVE_CELLS]
            accumulator = (index // 2) % 2
            pointer, value, _, _ = step(case.memory, start, accumulator, true_action)
            demo = Demo(token, case.memory, start, accumulator, encode(pointer, value))
            reduced = {
                action
                for action in valid
                if encode(*step(case.memory, start, accumulator, action)[:2]) == demo.expected
            }
            if len(reduced) < len(valid):
                demos.append(demo)
                valid = reduced
            if valid == {true_action}:
                break
        if valid != {true_action}:
            raise RuntimeError(f"primitive {true_action} was not identifiable")
    return tuple(demos)


def make_task(size: int, depth: int, seed: int, index: int, query_count: int, mapping: dict[int, int]) -> Task:
    adversarial = index >= query_count // 2
    case = make_case(size, seed ^ (index * 104729), adversarial)
    base = (NEXT, READ_NEXT, BRANCH, ALT)
    actions = tuple(base[(index + offset) % len(base)] for offset in range(depth))
    inverse = {action: token for token, action in mapping.items()}
    return Task(
        case.memory,
        case.addresses[(index * 3 + 1) % ACTIVE_CELLS],
        (index // 2) % 2,
        tuple(inverse[action] for action in actions),
        "adversarial" if adversarial else "typical",
    )


def expected(task: Task, mapping: dict[int, int]) -> int:
    answer, _, _ = execute(task, mapping, dense=False, lookup_cost=0)
    if answer is None:
        raise RuntimeError("oracle mapping is incomplete")
    return answer


def run_trial(
    candidate_name: str,
    knowledge_size: int,
    reasoning_depth: int,
    queries_per_cell: int,
    seed: int,
    max_depth: int,
) -> dict[str, Any]:
    mapping = token_mapping(seed)
    demos = training_corpus(knowledge_size, seed, mapping)
    tasks = tuple(
        make_task(knowledge_size, reasoning_depth, seed, index, queries_per_cell, mapping)
        for index in range(queries_per_cell)
    )
    targets = tuple(expected(task, mapping) for task in tasks)
    candidate = load_candidate(candidate_name, seed)
    fit_data = (tuple(sorted(mapping.items())),) if candidate_name == "oracle_pointer_machine" else demos
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure():
        answers, operations, reads, visited, latencies = [], [], [], [], []
        for task in tasks:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(task, len(task.program)))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            reads.append(float(candidate.last_memory_reads))
            visited.append(float(candidate.last_visited_nodes))
        return answers, operations, reads, visited, latencies

    answers, operations, reads, visited, latencies = measure()
    warm_answers, warm_operations, warm_reads, warm_visited, warm_latencies = measure()
    update_started = time.perf_counter_ns()
    candidate.update(demos[0], 0)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_task = make_task(knowledge_size, reasoning_depth, seed, queries_per_cell + 1, queries_per_cell, mapping)
    new_correct = candidate.query(new_task, reasoning_depth) == expected(new_task, mapping)
    retained = candidate.query(tasks[0], reasoning_depth) == targets[0]
    correct = [answer == target for answer, target in zip(answers, targets)]
    adversarial = [task.mode == "adversarial" for task in tasks]

    def masked_accuracy(mask: list[bool]) -> float:
        return statistics.fmean(value for value, selected in zip(correct, mask) if selected)

    mean_ops = statistics.fmean(operations)
    return {
        "status": "complete",
        "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth,
        "seed": seed,
        "query_count": queries_per_cell,
        "accuracy": statistics.fmean(correct),
        "composition_accuracy": statistics.fmean(correct) if reasoning_depth > 1 else None,
        "adversarial_accuracy": masked_accuracy(adversarial),
        "typical_accuracy": masked_accuracy([not item for item in adversarial]),
        "warm_accuracy": statistics.fmean(answer == target for answer, target in zip(warm_answers, targets)),
        "continual_new_fact_accuracy": float(new_correct),
        "continual_retention": float(retained),
        "identified_primitives": float(len(getattr(candidate, "mapping", {}))),
        "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": mean_ops,
        "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_memory_reads": statistics.fmean(reads),
        "mean_warm_memory_reads": statistics.fmean(warm_reads),
        "mean_visited_nodes": statistics.fmean(visited),
        "mean_warm_visited_nodes": statistics.fmean(warm_visited),
        "amortized_ops": mean_ops + float(candidate.fit_ops) / queries_per_cell,
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
