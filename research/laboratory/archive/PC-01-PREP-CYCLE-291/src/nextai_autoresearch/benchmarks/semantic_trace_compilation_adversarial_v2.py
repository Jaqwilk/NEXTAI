from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..semantic_trace_adversarial_core import RewriteOracleInput, normal_form
from ..semantic_trace_core import MODULUS, GraphQuery, Mutation, Node, canonical_key, evaluate, scan


BENCHMARK_VERSION = "semantic_trace_compilation_adversarial_v2"
REUSE_SCHEDULE = (1, 4, 16)


@dataclass(frozen=True)
class Task:
    cold: GraphQuery
    warm: GraphQuery
    near: GraphQuery
    target: int
    near_target: int
    mutation_symbol: int


def pack(symbol: int, value: int) -> int:
    return symbol * MODULUS + value % MODULUS


def _relabel(nodes: list[Node], sink: int, distractors: int, seed: int, offset: int) -> GraphQuery:
    rng = random.Random(seed)
    for index in range(distractors):
        nodes.append(Node(len(nodes), value=pack(900_000 + index, rng.randrange(MODULUS))))
    fresh = list(range(offset, offset + len(nodes)))
    rng.shuffle(fresh)
    names = {node.node_id: fresh[index] for index, node in enumerate(nodes)}
    relabeled = [Node(names[node.node_id], node.op, node.value, tuple(names[child] for child in (reversed(node.children) if node.op >= 0 and rng.randrange(2) else node.children))) for node in nodes]
    rng.shuffle(relabeled)
    return GraphQuery(tuple(relabeled), names[sink])


def _cold_graph(terms: list[int], distractors: int, seed: int) -> GraphQuery:
    if len(terms) == 2:
        nodes = [Node(0, value=terms[0]), Node(1, value=terms[1]), Node(2, 0, children=(0, 1))]
        return _relabel(nodes, 2, distractors, seed, 1_000)
    nodes = [Node(0, value=terms[0]), Node(1, value=terms[1]), Node(2, 0, children=(0, 1)), Node(3, 0, children=(2, 2))]
    sink = 3
    for value in terms[4:]:
        previous = sink
        leaf = len(nodes)
        nodes.append(Node(leaf, value=value))
        sink = len(nodes)
        nodes.append(Node(sink, 0, children=(previous, leaf)))
    return _relabel(nodes, sink, distractors, seed, 1_000)


def _warm_graph(terms: list[int], distractors: int, seed: int) -> GraphQuery:
    nodes = [Node(index, value=value) for index, value in enumerate(terms)]
    level = list(range(len(nodes)))
    while len(level) > 1:
        following = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                following.append(level[index])
            else:
                node_id = len(nodes)
                nodes.append(Node(node_id, 0, children=(level[index], level[index + 1])))
                following.append(node_id)
        level = following
    return _relabel(nodes, level[0], distractors, seed, 100_000)


def mutate_symbol(query: GraphQuery, symbol: int, delta: int) -> GraphQuery:
    changed = []
    for node in query.nodes:
        seen_symbol, value = divmod(node.value, MODULUS) if node.op < 0 else (-1, 0)
        changed.append(Node(node.node_id, node.op, pack(symbol, value + delta), node.children) if seen_symbol == symbol else node)
    result = GraphQuery(tuple(changed), query.sink)
    if evaluate(result) == evaluate(query):
        raise RuntimeError("registered semantic mutation did not change the target")
    return result


def make_task(distractors: int, depth: int, seed: int, index: int) -> Task:
    rng = random.Random(seed ^ depth * 65_537 ^ index * 104_729)
    symbol = 10_000 + (seed % 10_000) * 100 + index * 20
    a, b = pack(symbol, 1 + rng.randrange(249)), pack(symbol + 1, 1 + rng.randrange(249))
    if depth == 1:
        cold_terms = [a, b]
    else:
        rest = [pack(symbol + 2 + i, 1 + rng.randrange(249)) for i in range(depth - 3)]
        if len(rest) >= 3:
            rest[0], rest[1] = pack(0, 1 + rng.randrange(120)), pack(0, 121 + rng.randrange(120))
        cold_terms = [a, b, a, b, *rest]
    warm_terms = ([a, a, b, b, *cold_terms[4:]] if depth > 1 else list(cold_terms))
    constants = [i for i, value in enumerate(warm_terms) if divmod(value, MODULUS)[0] == 0]
    if len(constants) >= 2:
        first, second = constants[:2]
        warm_terms[first] = pack(0, divmod(warm_terms[first], MODULUS)[1] + divmod(warm_terms[second], MODULUS)[1])
        warm_terms[second] = 0
    cold = _cold_graph(cold_terms, distractors, seed ^ index)
    warm = _warm_graph(warm_terms, distractors, seed ^ index ^ 0xA11CE)
    near = mutate_symbol(warm, symbol, 7)
    cold_index, _, _, _ = scan(cold)
    warm_index, _, _, _ = scan(warm)
    if normal_form(cold_index, cold.sink)[0] != normal_form(warm_index, warm.sink)[0]:
        raise RuntimeError("rewrite pair lacks a shared normal form")
    if canonical_key(cold) == canonical_key(warm) and depth > 1:
        raise RuntimeError("adversarial rewrite did not change the tree key")
    target, near_target = evaluate(cold), evaluate(near)
    if target != evaluate(warm) or target == near_target:
        raise RuntimeError("invalid equivalent or near-equivalent target")
    return Task(cold, warm, near, target, near_target, symbol)


def make_tasks(distractors: int, depth: int, seed: int, count: int) -> tuple[Task, ...]:
    return tuple(make_task(distractors, depth, seed, index) for index in range(count))


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    tasks = make_tasks(knowledge_size, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit((), knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_state = candidate.state_bytes()

    def source(query, target):
        return RewriteOracleInput(query, target) if candidate_name == "oracle_equivalence_trace" else query

    def measure(field: str, target_field: str):
        nonlocal peak_state
        rows = []
        for task in tasks:
            query, target = getattr(task, field), getattr(task, target_field)
            tick = time.perf_counter_ns()
            answer = candidate.query(source(query, target), reasoning_depth)
            rows.append({
                "answer": answer, "target": target, "latency": (time.perf_counter_ns() - tick) / 1000.0,
                "ops": candidate.last_ops, "input": candidate.last_input_ops,
                "equivalence": getattr(candidate, "last_equivalence_ops", 0),
                "execution": candidate.last_execution_ops, "reads": candidate.last_memory_reads,
                "bytes": candidate.last_bytes_loaded, "hit": float(candidate.last_cache_hit),
                "compiled": candidate.last_compiled_nodes,
            })
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold = measure("cold", "target")
    warm = measure("warm", "target")
    near = measure("near", "near_target")
    current, update_ops, update_execution, update_equivalence = tasks[0].warm, [], [], []
    new_correct, retained, workload_by_reuse = [], [], {}
    invalidated, invalidated_fraction = [], []
    for stage, reuses in enumerate(REUSE_SCHEDULE):
        changed = mutate_symbol(current, tasks[0].mutation_symbol, (17, 31, 47)[stage])
        target = evaluate(changed)
        tick = time.perf_counter_ns()
        candidate.update(Mutation(current, changed), target)
        update_latency = (time.perf_counter_ns() - tick) / 1000.0
        update_ops.append(float(candidate.update_ops))
        update_execution.append(float(getattr(candidate, "last_update_execution_ops", 0)))
        update_equivalence.append(float(getattr(candidate, "last_update_equivalence_ops", 0)))
        invalidated.append(float(candidate.last_invalidated_entries))
        invalidated_fraction.append(float(candidate.last_invalidated_fraction))
        stage_ops = float(candidate.update_ops)
        stage_correct = []
        for _ in range(reuses):
            stage_correct.append(candidate.query(source(changed, target), reasoning_depth) == target)
            stage_ops += candidate.last_ops
            peak_state = max(peak_state, candidate.state_bytes())
        new_correct.append(all(stage_correct))
        retained.append(candidate.query(source(tasks[1].warm, tasks[1].target), reasoning_depth) == tasks[1].target)
        stage_ops += candidate.last_ops
        workload_by_reuse[reuses] = stage_ops
        peak_state = max(peak_state, candidate.state_bytes())
        current = changed

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    accuracy = lambda rows: statistics.fmean(float(row["answer"] == row["target"]) for row in rows)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "cold_accuracy": accuracy(cold), "warm_accuracy": accuracy(warm),
        "near_equivalent_accuracy": accuracy(near), "false_reuse_rate": mean(near, "hit"),
        "cross_structure_hit_rate": mean(warm, "hit"),
        "continual_new_fact_accuracy": statistics.fmean(new_correct),
        "continual_retention": statistics.fmean(retained), "raw_identity_match_rate": 0.0,
        "supplied_node_mapping_rate": 0.0, "supplied_atom_identity_rate": 1.0,
        "associative_rewrite_rate": float(reasoning_depth > 1),
        "constant_fold_rate": float(reasoning_depth >= 6),
        "shared_subexpression_split_rate": float(reasoning_depth > 1),
        "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops), "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_input_ops": mean(cold, "input"), "mean_warm_input_ops": mean(warm, "input"),
        "mean_equivalence_ops": mean(cold, "equivalence"),
        "mean_warm_equivalence_ops": mean(warm, "equivalence"),
        "mean_execution_ops": mean(cold, "execution"),
        "mean_warm_execution_ops": mean(warm, "execution"),
        "mean_memory_reads": mean(cold, "reads"), "mean_bytes_loaded": mean(cold, "bytes"),
        "mean_compiled_nodes": mean(cold, "compiled"),
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.50),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.50),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(peak_state),
        "update_ops": statistics.fmean(update_ops), "mean_update_execution_ops": statistics.fmean(update_execution),
        "mean_update_equivalence_ops": statistics.fmean(update_equivalence),
        "cumulative_update_ops": sum(update_ops), "mean_invalidated_entries": statistics.fmean(invalidated),
        "invalidated_fraction": statistics.fmean(invalidated_fraction),
        "workload_ops_r1": workload_by_reuse[1], "workload_ops_r4": workload_by_reuse[4],
        "workload_ops_r16": workload_by_reuse[16], "workload_ops": sum(workload_by_reuse.values()),
        "update_latency_us": update_latency,
        "cold_raw_nodes": float(len(tasks[0].cold.nodes)), "warm_raw_nodes": float(len(tasks[0].warm.nodes)),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
