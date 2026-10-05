from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .semantic_trace_compilation_adversarial_v2 import _cold_graph, _warm_graph, mutate_symbol, pack
from .successor_graph_v1 import load_candidate, percentile
from ..opaque_alias_core import (
    AliasMutation,
    AliasQuery,
    OracleAliasMutation,
    OracleAliasQuery,
    Rows,
    TrainingEpisode,
    exact_alignment,
    mapped_index,
)
from ..semantic_trace_adversarial_core import normal_form
from ..semantic_trace_core import MODULUS, evaluate, scan


BENCHMARK_VERSION = "opaque_alias_acquisition_v1"
REUSE_SCHEDULE = (1, 4, 16)


@dataclass(frozen=True)
class Task:
    cold: AliasQuery
    warm: AliasQuery
    near: AliasQuery
    cold_mapping: tuple[tuple[int, int], ...]
    warm_mapping: tuple[tuple[int, int], ...]
    target: int
    near_target: int
    mutation_alias: int


def _codebook(size: int, namespace: int, seed: int) -> tuple[int, ...]:
    values = list(range(namespace * 100, namespace * 100 + size))
    random.Random(seed).shuffle(values)
    return tuple(values)


def _supports(reference: tuple[int, ...], current: tuple[int, ...], seed: int) -> tuple[Rows, Rows]:
    size = len(reference)
    order = list(range(size))
    random.Random(seed).shuffle(order)

    def rows(aliases: tuple[int, ...], salt: int) -> Rows:
        rng, result = random.Random(seed ^ salt), []
        for row in order:
            values = [aliases[index] for index in range(size) if row in {index, (index + 1) % size, (index + 3) % size}]
            rng.shuffle(values)
            result.append(tuple(values))
        return tuple(result)

    return rows(reference, 0xC01D), rows(current, 0xA11A5)


def make_training(size: int, seed: int, count: int = 3) -> tuple[TrainingEpisode, ...]:
    episodes = []
    for index in range(count):
        namespace = 90_000_000 + seed * 10 + index * 2
        reference = _codebook(size, namespace, seed ^ index)
        current = _codebook(size, namespace + 1, seed ^ index ^ 0xBAD)
        left, right = _supports(reference, current, seed ^ index ^ 0x515)
        episodes.append(TrainingEpisode(left, right, tuple(zip(current, reference))))
    return tuple(episodes)


def _mapped_normal(source: AliasQuery, mapping: tuple[tuple[int, int], ...]):
    index, _, _, _ = scan(source.graph)
    mapped, _ = mapped_index(index, dict(mapping))
    return normal_form(mapped, source.graph.sink)[0]


def make_task(size: int, depth: int, seed: int, index: int) -> Task:
    namespace = 1_000_000 + seed * 10_000 + size * 100 + depth * 10 + index * 2
    reference = _codebook(size, namespace, seed ^ index)
    current = _codebook(size, namespace + 1, seed ^ index ^ 0xACE)
    left_rows, right_rows = _supports(reference, current, seed ^ depth ^ index)
    rng = random.Random(seed ^ depth * 65_537 ^ index * 104_729)
    values = [1 + rng.randrange(249) for _ in range(size)]
    indices = [0, 1] if depth == 1 else [0, 1, 0, 1, *range(2, depth - 1)]
    cold_terms = [pack(reference[i], values[i]) for i in indices]
    warm_terms = [pack(current[i], values[i]) for i in indices]
    if depth >= 6:
        first, second = 4, 5
        cold_terms[first], cold_terms[second] = pack(0, 1 + rng.randrange(120)), pack(0, 121 + rng.randrange(120))
        warm_terms[first], warm_terms[second] = cold_terms[first], cold_terms[second]
    if depth > 1:
        warm_terms = [warm_terms[0], warm_terms[2], warm_terms[1], warm_terms[3], *warm_terms[4:]]
    constants = [i for i, value in enumerate(warm_terms) if divmod(value, MODULUS)[0] == 0]
    if len(constants) >= 2:
        first, second = constants[:2]
        warm_terms[first] = pack(0, divmod(warm_terms[first], MODULUS)[1] + divmod(warm_terms[second], MODULUS)[1])
        warm_terms[second] = 0
    cold_graph = _cold_graph(cold_terms, 0, seed ^ index)
    warm_graph = _warm_graph(warm_terms, 0, seed ^ index ^ 0xA11CE)
    near_graph = mutate_symbol(warm_graph, current[0], 7)
    cold = AliasQuery(cold_graph, left_rows, left_rows)
    warm = AliasQuery(warm_graph, left_rows, right_rows)
    near = AliasQuery(near_graph, left_rows, right_rows)
    cold_mapping, warm_mapping = tuple(zip(reference, reference)), tuple(zip(current, reference))
    inferred = exact_alignment(left_rows, right_rows)
    if inferred.mapping != tuple(sorted(warm_mapping)) or any(len(row) == 1 for row in left_rows + right_rows):
        raise RuntimeError("support does not identify a nontrivial unique mapping")
    if _mapped_normal(cold, cold_mapping) != _mapped_normal(warm, warm_mapping):
        raise RuntimeError("opaque equivalent pair lacks a shared mapped normal form")
    target, near_target = evaluate(cold_graph), evaluate(near_graph)
    if target != evaluate(warm_graph) or target == near_target or _mapped_normal(warm, warm_mapping) == _mapped_normal(near, warm_mapping):
        raise RuntimeError("invalid opaque equivalent or near-equivalent target")
    return Task(cold, warm, near, cold_mapping, warm_mapping, target, near_target, current[0])


def make_tasks(size: int, depth: int, seed: int, count: int) -> tuple[Task, ...]:
    return tuple(make_task(size, depth, seed, index) for index in range(count))


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    training = make_training(knowledge_size, seed ^ 0xF17)
    tasks = make_tasks(knowledge_size, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_state = candidate.state_bytes()

    def source(query: AliasQuery, mapping: tuple[tuple[int, int], ...]):
        return OracleAliasQuery(query, mapping) if candidate_name == "mapping_oracle_dependency_trace" else query

    def measure(field: str, target_field: str, mapping_field: str):
        nonlocal peak_state
        rows = []
        for task in tasks:
            query, target, mapping = getattr(task, field), getattr(task, target_field), getattr(task, mapping_field)
            tick = time.perf_counter_ns()
            answer = candidate.query(source(query, mapping), reasoning_depth)
            rows.append({
                "answer": answer, "target": target, "latency": (time.perf_counter_ns() - tick) / 1000.0,
                "ops": candidate.last_ops, "input": candidate.last_input_ops,
                "alignment": getattr(candidate, "last_alignment_ops", 0),
                "verification": getattr(candidate, "last_verification_ops", 0),
                "equivalence": getattr(candidate, "last_equivalence_ops", 0),
                "execution": candidate.last_execution_ops, "reads": candidate.last_memory_reads,
                "bytes": candidate.last_bytes_loaded, "hit": float(candidate.last_cache_hit),
            })
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold = measure("cold", "target", "cold_mapping")
    warm = measure("warm", "target", "warm_mapping")
    near = measure("near", "near_target", "warm_mapping")
    current, update_ops, workload_by_reuse = tasks[0].warm, [], {}
    new_correct, retained, update_alignment, update_verification = [], [], [], []
    invalidated = []
    for stage, reuses in enumerate(REUSE_SCHEDULE):
        changed_graph = mutate_symbol(current.graph, tasks[0].mutation_alias, (17, 31, 47)[stage])
        changed = AliasQuery(changed_graph, current.reference_rows, current.current_rows)
        target = evaluate(changed_graph)
        mutation = (OracleAliasMutation(OracleAliasQuery(current, tasks[0].warm_mapping), OracleAliasQuery(changed, tasks[0].warm_mapping))
                    if candidate_name == "mapping_oracle_dependency_trace" else AliasMutation(current, changed))
        tick = time.perf_counter_ns()
        candidate.update(mutation, target)
        update_latency = (time.perf_counter_ns() - tick) / 1000.0
        update_ops.append(float(candidate.update_ops))
        update_alignment.append(float(getattr(candidate, "last_update_alignment_ops", 0)))
        update_verification.append(float(getattr(candidate, "last_update_verification_ops", 0)))
        invalidated.append(float(candidate.last_invalidated_entries))
        stage_ops, stage_correct = float(candidate.update_ops), []
        for _ in range(reuses):
            stage_correct.append(candidate.query(source(changed, tasks[0].warm_mapping), reasoning_depth) == target)
            stage_ops += candidate.last_ops
            peak_state = max(peak_state, candidate.state_bytes())
        new_correct.append(all(stage_correct))
        retained.append(candidate.query(source(tasks[1].warm, tasks[1].warm_mapping), reasoning_depth) == tasks[1].target)
        stage_ops += candidate.last_ops
        workload_by_reuse[reuses] = stage_ops
        peak_state = max(peak_state, candidate.state_bytes())
        current = changed

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    accuracy = lambda rows: statistics.fmean(float(row["answer"] == row["target"]) for row in rows)
    warm_hits = sum(row["hit"] for row in warm)
    correct_hits = sum(row["hit"] * float(row["answer"] == row["target"]) for row in warm)
    training_aliases = {alias for episode in training for row in episode.reference_rows + episode.current_rows for alias in row}
    query_aliases = {alias for task in tasks for row in task.cold.reference_rows + task.warm.current_rows for alias in row}
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "reuse_precision": correct_hits / warm_hits if warm_hits else 0.0,
        "reuse_coverage": warm_hits / len(warm), "false_reuse_rate": mean(near, "hit"),
        "cross_structure_hit_rate": mean(warm, "hit"),
        "continual_new_fact_accuracy": statistics.fmean(new_correct),
        "continual_retention": statistics.fmean(retained), "mapping_unique_rate": 1.0,
        "fit_query_alias_overlap_rate": float(bool(training_aliases & query_aliases)),
        "support_singleton_row_rate": 0.0,
        "supplied_atom_mapping_rate": float(candidate_name == "mapping_oracle_dependency_trace"),
        "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops), "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_input_ops": mean(cold, "input"), "mean_alignment_ops": mean(cold, "alignment"),
        "mean_warm_alignment_ops": mean(warm, "alignment"),
        "mean_verification_ops": mean(cold, "verification"),
        "mean_equivalence_ops": mean(cold, "equivalence"),
        "mean_execution_ops": mean(cold, "execution"), "mean_memory_reads": mean(cold, "reads"),
        "mean_bytes_loaded": mean(cold, "bytes"),
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.50),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.50),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(peak_state),
        "update_ops": statistics.fmean(update_ops), "cumulative_update_ops": sum(update_ops),
        "mean_update_alignment_ops": statistics.fmean(update_alignment),
        "mean_update_verification_ops": statistics.fmean(update_verification),
        "mean_invalidated_entries": statistics.fmean(invalidated),
        "workload_ops_r1": workload_by_reuse[1], "workload_ops_r4": workload_by_reuse[4],
        "workload_ops_r16": workload_by_reuse[16], "workload_ops": sum(workload_by_reuse.values()),
        "update_latency_us": update_latency, "support_rows": float(len(tasks[0].warm.reference_rows)),
        "support_incidences": float(sum(map(len, tasks[0].warm.reference_rows + tasks[0].warm.current_rows))),
        "cold_raw_nodes": float(len(tasks[0].cold.graph.nodes)), "warm_raw_nodes": float(len(tasks[0].warm.graph.nodes)),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
