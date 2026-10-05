from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile


BENCHMARK_VERSION = "behavioral_conjugacy_library_transfer_v1"
STATE_COUNT = 12
BASE = (
    (3, 11, 5, 0, 8, 2, 10, 9, 4, 7, 6, 1),
    (4, 9, 7, 10, 0, 11, 8, 2, 6, 1, 3, 5),
    (9, 6, 8, 5, 10, 3, 1, 11, 2, 0, 4, 7),
    (3, 6, 8, 0, 10, 7, 1, 5, 2, 11, 4, 9),
    (7, 11, 9, 8, 6, 10, 4, 0, 3, 2, 5, 1),
    (6, 3, 4, 1, 2, 9, 0, 10, 11, 5, 7, 8),
)


@dataclass(frozen=True)
class Domain:
    traces: tuple[tuple[int, tuple[int, ...]], ...]
    programs: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class FitBundle:
    training: tuple[Domain, ...]
    target_traces: tuple[tuple[int, tuple[int, ...]], ...]


@dataclass(frozen=True)
class OracleBundle:
    public: FitBundle
    target_by_role: tuple[int, ...]


@dataclass(frozen=True)
class Task:
    examples: tuple[tuple[int, int], ...]
    length: int
    signature: int


@dataclass(frozen=True)
class OracleTask:
    public: Task
    program: tuple[int, ...]


def compose(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(left[right[index]] for index in range(STATE_COUNT))


def execute(program: tuple[int, ...], tables: dict[int, tuple[int, ...]]) -> tuple[int, ...]:
    result = tuple(range(STATE_COUNT))
    for token in program:
        result = compose(tables[token], result)
    return result


def cycle_type(table: tuple[int, ...]) -> tuple[int, ...]:
    seen, sizes = set(), []
    for start in range(STATE_COUNT):
        if start not in seen:
            node, size = start, 0
            while node not in seen:
                seen.add(node)
                node, size = table[node], size + 1
            sizes.append(size)
    return tuple(sorted(sizes))


def relational_fingerprints(traces: tuple[tuple[int, tuple[int, ...]], ...]):
    tables = dict(traces)
    return {
        token: tuple(sorted(cycle_type(compose(table, other))
                            for other_token, other in traces if other_token != token))
        for token, table in traces
    }


def _domain(seed: int, index: int, knowledge_size: int, training: bool) -> tuple[Domain, tuple[int, ...]]:
    rng = random.Random(seed ^ (index * 104729))
    state_labels = list(range(STATE_COUNT))
    rng.shuffle(state_labels)
    inverse = [0] * STATE_COUNT
    for position, label in enumerate(state_labels):
        inverse[label] = position
    tokens = rng.sample(range(1000 + index * 100, 1099 + index * 100), len(BASE))
    tables = []
    for role, base in enumerate(BASE):
        table = tuple(state_labels[base[inverse[value]]] for value in range(STATE_COUNT))
        tables.append((tokens[role], table))
    rng.shuffle(tables)
    programs = []
    if training:
        for item in range(knowledge_size):
            if item % 2 == 0:
                canonical = (0, 1, 2 + item % 4, 0, 1, 2 + (item * 3) % 4)
            else:
                canonical = tuple(rng.randrange(len(BASE)) for _ in range(4 + 2 * (item % 3 == 0)))
                while any(canonical[pos:pos + 2] == (0, 1) for pos in range(len(canonical) - 1)):
                    canonical = tuple(rng.randrange(len(BASE)) for _ in canonical)
            programs.append(tuple(tokens[role] for role in canonical))
    return Domain(tuple(tables), tuple(programs)), tuple(tokens)


def make_world(knowledge_size: int, seed: int):
    training = tuple(_domain(seed, index, knowledge_size, True)[0] for index in range(3))
    target, target_by_role = _domain(seed, 17, knowledge_size, False)
    public = FitBundle(training, target.traces)
    return public, OracleBundle(public, target_by_role), dict(target.traces), target_by_role


def make_tasks(tables: dict[int, tuple[int, ...]], target_by_role: tuple[int, ...], depth: int,
               seed: int, count: int):
    rng, tasks = random.Random(seed ^ (depth * 65537)), []
    for index in range(count):
        if depth == 1:
            roles = (2 + index % 4,)
        elif depth == 4:
            roles = (0, 1, 2 + index % 4, 2 + (index * 3) % 4)
        else:
            roles = (0, 1, 2 + index % 4, 0, 1, 2 + (index * 3) % 4)
        program = tuple(target_by_role[role] for role in roles)
        output = execute(program, tables)
        examples = list(enumerate(output))
        rng.shuffle(examples)
        task = Task(tuple(examples), depth, index + depth * 100)
        near = Task(tuple(reversed(examples)), depth, task.signature + 10000)
        tasks.append((task, near, OracleTask(task, program), OracleTask(near, program), program))
    return tuple(tasks)


def _correct(program: object, examples: tuple[tuple[int, int], ...], tables) -> bool:
    return isinstance(program, tuple) and all(isinstance(token, int) and token in tables for token in program) \
        and tuple(target for _, target in sorted(examples)) == execute(program, tables)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    public, oracle, tables, target_by_role = make_world(knowledge_size, seed)
    tasks = make_tasks(tables, target_by_role, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    fit_data = oracle if candidate_name == "oracle_conjugacy_library" else public
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    fit_ops = float(candidate.fit_ops)

    def measure(near: bool = False):
        rows = []
        for task, shifted, oracle_task, oracle_shifted, _ in tasks:
            if candidate_name == "oracle_conjugacy_library":
                source = oracle_shifted if near else oracle_task
            else:
                source = shifted if near else task
            public_task = shifted if near else task
            tick = time.perf_counter_ns()
            answer = candidate.query(source, reasoning_depth)
            rows.append((_correct(answer, public_task.examples, tables), float(candidate.last_ops),
                         float(getattr(candidate, "last_comparisons", 0)),
                         float(getattr(candidate, "last_bytes_touched", 0)),
                         (time.perf_counter_ns() - tick) / 1000.0))
        return rows

    cold, warm, near = measure(), measure(), measure(True)
    first_task, _, first_oracle, _, first_program = tasks[0]
    update_task = Task(first_task.examples, first_task.length, 0xADD)
    update_source = OracleTask(update_task, first_program) if candidate_name == "oracle_conjugacy_library" else (update_task, first_program)
    tick = time.perf_counter_ns()
    candidate.update(update_source, None)
    update_latency = (time.perf_counter_ns() - tick) / 1000.0
    new_source = update_source if candidate_name == "oracle_conjugacy_library" else update_task
    new_correct = _correct(candidate.query(new_source, reasoning_depth), update_task.examples, tables)
    after_ops = float(candidate.last_ops)
    retained_source = first_oracle if candidate_name == "oracle_conjugacy_library" else first_task
    retained = _correct(candidate.query(retained_source, reasoning_depth), first_task.examples, tables)
    accuracy = lambda rows: statistics.fmean(row[0] for row in rows)
    mean = lambda rows, index: statistics.fmean(row[index] for row in rows)
    query_work = sum(row[1] for row in cold + near)
    workload = fit_ops + query_work + candidate.update_ops + 16 * after_ops
    workload_r16 = fit_ops + 16 * query_work + candidate.update_ops + 16 * after_ops
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "false_reuse_rate": 1.0 - accuracy(cold), "continual_new_fact_accuracy": float(new_correct),
        "continual_retention": float(retained), "fit_seconds": fit_seconds, "fit_ops": fit_ops,
        "fit_peak_bytes": float(fit_peak), "mean_query_ops": mean(cold, 1),
        "mean_warm_query_ops": mean(warm, 1), "mean_input_ops": float(2 * STATE_COUNT),
        "mean_comparisons": mean(cold, 2), "mean_bytes_touched": mean(cold, 3),
        "p50_latency_us": percentile([row[4] for row in cold], 0.5),
        "p95_latency_us": percentile([row[4] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row[4] for row in warm], 0.5),
        "warm_p95_latency_us": percentile([row[4] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()),
        "peak_state_bytes": float(max(candidate.state_bytes(), fit_peak)),
        "update_ops": float(candidate.update_ops), "update_latency_us": update_latency,
        "workload_ops": float(workload), "workload_ops_r16": float(workload_r16),
        "search_nodes": float(getattr(candidate, "last_nodes", 0)),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed),
                      max(map(int, matrix["reasoning_depths"])))
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"]]
