from __future__ import annotations

import math
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..active_acquisition_core import Codebook, CodebookUpdate, OracleBatch, ProbeBatch, ProbeSession


BENCHMARK_VERSION = "active_information_acquisition_v1"
REUSE_SCHEDULE = (1, 4, 16)


@dataclass(frozen=True)
class Task:
    targets: tuple[int, ...]
    near_targets: tuple[int, ...]


def make_codebook(size: int, seed: int) -> Codebook:
    bits = int(math.log2(size))
    if 2 ** bits != size:
        raise ValueError("this cohort requires power-of-two K")
    rng = random.Random(seed ^ size * 65537)
    ranks = list(range(size))
    rng.shuffle(ranks)
    columns = [tuple((ranks[label] >> bit) & 1 for label in range(size)) for bit in range(bits)]
    columns += [tuple(int(label == chosen) for label in range(size)) for chosen in range(size)]
    columns += [tuple(0 for _ in range(size)), tuple(1 for _ in range(size))]
    rng.shuffle(columns)
    return Codebook(tuple(tuple(column[label] for column in columns) for label in range(size)))


def make_tasks(size: int, depth: int, count: int, seed: int) -> tuple[Task, ...]:
    rng, tasks = random.Random(seed ^ size * 8191 ^ depth * 104729), []
    for _ in range(count):
        targets = tuple(rng.randrange(size) for _ in range(depth))
        changed = list(targets)
        changed[0] = (changed[0] + 1 + rng.randrange(size - 1)) % size
        tasks.append(Task(targets, tuple(changed)))
    return tuple(tasks)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    codebook = make_codebook(knowledge_size, seed)
    tasks = make_tasks(knowledge_size, reasoning_depth, queries_per_cell, seed)
    candidate = load_candidate(candidate_name, seed)

    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(codebook, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    initial_fit_ops = float(candidate.fit_ops)
    initial_policy_ops = float(candidate.policy_build_ops)
    peak_state = candidate.state_bytes()

    def measure(target_field: str):
        nonlocal peak_state
        rows = []
        for task in tasks:
            targets = getattr(task, target_field)
            batch = ProbeBatch(tuple(ProbeSession(codebook.rows[label]) for label in targets))
            wrapped = OracleBatch(batch, targets) if candidate_name == "oracle_target_reader" else batch
            tick = time.perf_counter_ns()
            answer = candidate.query(wrapped, reasoning_depth)
            rows.append({
                "correct": answer == targets, "latency": (time.perf_counter_ns() - tick) / 1000,
                "ops": candidate.last_ops, "input": candidate.last_input_ops,
                "search": candidate.last_search_ops, "execution": candidate.last_execution_ops,
                "reads": candidate.last_memory_reads, "bytes": candidate.last_bytes_loaded,
                "probes": sum(session.calls for session in batch.sessions),
                "hit": float(candidate.last_cache_hit),
            })
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold, warm, near = measure("targets"), measure("targets"), measure("near_targets")
    current = list(codebook.rows)
    retained_label = knowledge_size - 1
    updates, update_latencies, new_correct, retained, workloads = [], [], [], [], {}
    for stage, reuses in enumerate(REUSE_SCHEDULE):
        left, right = 2 * stage, 2 * stage + 1
        current[left], current[right] = current[right], current[left]
        change = CodebookUpdate(((left, current[left]), (right, current[right])))
        tick = time.perf_counter_ns()
        candidate.update(change, None)
        update_latencies.append((time.perf_counter_ns() - tick) / 1000)
        updates.append(float(candidate.update_ops))
        stage_ops, correctness = float(candidate.update_ops), []
        updated_targets = (left,) * reasoning_depth
        for _ in range(reuses):
            batch = ProbeBatch(tuple(ProbeSession(current[label]) for label in updated_targets))
            wrapped = OracleBatch(batch, updated_targets) if candidate_name == "oracle_target_reader" else batch
            correctness.append(candidate.query(wrapped, reasoning_depth) == updated_targets)
            stage_ops += candidate.last_ops
        new_correct.append(all(correctness))
        old_targets = (retained_label,) * reasoning_depth
        batch = ProbeBatch(tuple(ProbeSession(current[label]) for label in old_targets))
        wrapped = OracleBatch(batch, old_targets) if candidate_name == "oracle_target_reader" else batch
        retained.append(candidate.query(wrapped, reasoning_depth) == old_targets)
        stage_ops += candidate.last_ops
        workloads[reuses] = stage_ops
        peak_state = max(peak_state, candidate.state_bytes())

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    accuracy = lambda rows: statistics.fmean(float(row["correct"]) for row in rows)
    reuse_rows, hits = warm + near, sum(row["hit"] for row in warm + near)
    correct_hits = sum(row["hit"] * row["correct"] for row in reuse_rows)
    lower_bound = reasoning_depth * math.log2(knowledge_size)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "reuse_precision": correct_hits / hits if hits else 0.0, "reuse_coverage": hits / len(reuse_rows),
        "false_reuse_rate": (hits - correct_hits) / hits if hits else 0.0,
        "continual_new_fact_accuracy": statistics.fmean(new_correct),
        "continual_retention": statistics.fmean(retained), "fit_seconds": fit_seconds,
        "fit_ops": initial_fit_ops, "policy_build_ops": initial_policy_ops,
        "fit_peak_bytes": float(fit_peak), "mean_query_ops": mean(cold, "ops"),
        "mean_warm_query_ops": mean(warm, "ops"), "mean_input_ops": mean(cold, "input"),
        "mean_alignment_ops": mean(cold, "search"), "mean_execution_ops": mean(cold, "execution"),
        "mean_memory_reads": mean(cold, "reads"), "mean_bytes_loaded": mean(cold, "bytes"),
        "mean_probe_count": mean(cold, "probes"), "probe_lower_bound": lower_bound,
        "probe_excess_ratio": mean(cold, "probes") / lower_bound if lower_bound else 0.0,
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.5),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.5),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(peak_state, fit_peak)),
        "update_ops": statistics.fmean(updates), "cumulative_update_ops": sum(updates),
        "mean_invalidated_entries": 2.0, "workload_ops_r1": workloads[1],
        "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
        "workload_ops": initial_fit_ops + sum(workloads.values()),
        "update_latency_us": statistics.fmean(update_latencies),
        "codebook_columns": float(len(codebook.rows[0])), "labeled_codebook_bits": float(knowledge_size * len(codebook.rows[0])),
        "binary_probe_outcomes": 1.0, "episode_specific_column_permutation": 1.0,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]

