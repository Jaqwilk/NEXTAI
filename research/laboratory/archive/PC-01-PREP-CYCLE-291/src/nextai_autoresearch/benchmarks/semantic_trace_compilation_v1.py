from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..semantic_trace_core import GraphQuery, Mutation, Node, OracleInput, canonical_key, evaluate, internal_keys


BENCHMARK_VERSION = "semantic_trace_compilation_v1"


@dataclass(frozen=True)
class Task:
    cold: GraphQuery
    warm: GraphQuery
    target: int


def make_graph(size: int, depth: int, seed: int) -> GraphQuery:
    if depth < 1 or depth + 2 > size:
        raise ValueError("D internal nodes and two leaves must fit in K")
    rng = random.Random(seed)
    nodes = [Node(0, value=2 + rng.randrange(113)), Node(1, value=127 + rng.randrange(113))]
    next_id, remaining = 2, depth - 1
    left_count = remaining // 2
    left = 0
    for _ in range(left_count):
        nodes.append(Node(next_id, rng.randrange(3), children=(left, 0)))
        left, next_id = next_id, next_id + 1
    right = 1
    for _ in range(remaining - left_count):
        nodes.append(Node(next_id, rng.randrange(3), children=(right, 1)))
        right, next_id = next_id, next_id + 1
    nodes.append(Node(next_id, rng.randrange(3), children=(left, right)))
    sink, next_id = next_id, next_id + 1
    while len(nodes) < size:
        nodes.append(Node(next_id, value=rng.randrange(251)))
        next_id += 1
    rng.shuffle(nodes)
    return GraphQuery(tuple(nodes), sink)


def rename_graph(query: GraphQuery, seed: int) -> GraphQuery:
    rng = random.Random(seed)
    fresh = list(range(10_000, 10_000 + len(query.nodes)))
    rng.shuffle(fresh)
    names = {node.node_id: fresh[index] for index, node in enumerate(query.nodes)}
    nodes = [Node(names[node.node_id], node.op, node.value, tuple(names[child] for child in reversed(node.children))) for node in query.nodes]
    rng.shuffle(nodes)
    return GraphQuery(tuple(nodes), names[query.sink])


def mutate_leaf(query: GraphQuery) -> GraphQuery:
    index, active, pending = {node.node_id: node for node in query.nodes}, set(), [query.sink]
    while pending:
        node = index[pending.pop()]
        if node.op < 0:
            active.add(node.node_id)
        else:
            pending.extend(node.children)
    old_target = evaluate(query)
    for leaf_id in sorted(active):
        for delta in range(1, 251):
            nodes = tuple(Node(node.node_id, node.op, (node.value + delta) % 251, node.children) if node.node_id == leaf_id else node for node in query.nodes)
            changed = GraphQuery(nodes, query.sink)
            if evaluate(changed) != old_target:
                return changed
    raise RuntimeError("graph output is insensitive to every active leaf")


def make_tasks(size: int, depth: int, seed: int, count: int) -> tuple[Task, ...]:
    tasks, used = [], set()
    attempt = 0
    while len(tasks) < count:
        cold = make_graph(size, depth, seed ^ depth * 65_537 ^ attempt * 104_729)
        key = canonical_key(cold)
        pieces = internal_keys(key)
        if not (pieces & used):
            warm = rename_graph(cold, seed ^ attempt * 99_991 ^ 0xA11CE)
            tasks.append(Task(cold, warm, evaluate(cold)))
            used |= pieces
        attempt += 1
        if attempt > 10_000:
            raise RuntimeError("could not construct distinct semantic traces")
    return tuple(tasks)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    tasks = make_tasks(knowledge_size, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit((), knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure(field: str):
        rows = []
        for task in tasks:
            query = getattr(task, field)
            source = OracleInput(query, task.target) if candidate_name == "oracle_trace_compiler" else query
            tick = time.perf_counter_ns()
            answer = candidate.query(source, reasoning_depth)
            rows.append({
                "answer": answer, "latency": (time.perf_counter_ns() - tick) / 1000.0,
                "ops": candidate.last_ops, "input": candidate.last_input_ops,
                "canonical": candidate.last_canonical_ops, "execution": candidate.last_execution_ops,
                "reads": candidate.last_memory_reads, "bytes": candidate.last_bytes_loaded,
                "hit": float(candidate.last_cache_hit), "compiled": candidate.last_compiled_nodes,
                "recomputed": candidate.last_recomputed_nodes,
            })
        return rows

    cold, warm = measure("cold"), measure("warm")
    changed = mutate_leaf(tasks[0].warm)
    changed_target = evaluate(changed)
    update_started = time.perf_counter_ns()
    candidate.update(Mutation(tasks[0].warm, changed), changed_target)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    update_ops = candidate.update_ops
    invalidated = candidate.last_invalidated_entries
    invalidated_fraction = candidate.last_invalidated_fraction
    recomputed = candidate.last_recomputed_nodes
    changed_source = OracleInput(changed, changed_target) if candidate_name == "oracle_trace_compiler" else changed
    new_correct = candidate.query(changed_source, reasoning_depth) == changed_target
    post_update_ops = candidate.last_ops
    retained_source = OracleInput(tasks[1].warm, tasks[1].target) if candidate_name == "oracle_trace_compiler" else tasks[1].warm
    retained = candidate.query(retained_source, reasoning_depth) == tasks[1].target
    retention_ops = candidate.last_ops

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    correct = lambda rows: statistics.fmean(float(row["answer"] == task.target) for row, task in zip(rows, tasks))
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": correct(cold),
        "cold_accuracy": correct(cold), "warm_accuracy": correct(warm),
        "continual_new_fact_accuracy": float(new_correct), "continual_retention": float(retained),
        "cross_structure_hit_rate": mean(warm, "hit"), "raw_identity_match_rate": 0.0,
        "supplied_name_mapping_rate": 0.0, "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops), "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_cold_query_ops": mean(cold, "ops"),
        "mean_warm_query_ops": mean(warm, "ops"), "mean_input_ops": mean(cold, "input"),
        "mean_warm_input_ops": mean(warm, "input"), "mean_canonical_ops": mean(cold, "canonical"),
        "mean_warm_canonical_ops": mean(warm, "canonical"), "mean_execution_ops": mean(cold, "execution"),
        "mean_warm_execution_ops": mean(warm, "execution"), "mean_memory_reads": mean(cold, "reads"),
        "mean_bytes_loaded": mean(cold, "bytes"), "mean_compiled_nodes": mean(cold, "compiled"),
        "mean_recomputed_nodes": mean(cold, "recomputed"),
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.50),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.50),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "update_ops": float(update_ops),
        "update_latency_us": update_latency_us, "invalidated_entries": float(invalidated),
        "invalidated_fraction": float(invalidated_fraction), "update_recomputed_nodes": float(recomputed),
        "post_update_ops": float(post_update_ops), "retention_ops": float(retention_ops),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
