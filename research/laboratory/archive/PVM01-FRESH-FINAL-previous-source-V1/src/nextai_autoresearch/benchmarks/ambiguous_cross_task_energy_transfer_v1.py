from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..parity_energy_core import ParityQuery


BENCHMARK_VERSION = "ambiguous_cross_task_energy_transfer_v1"
WIDTH, LATENT = 63, 6


@dataclass(frozen=True)
class World:
    patterns: tuple[tuple[int, ...], ...]
    codewords: tuple[tuple[int, ...], ...]
    full_codebook: frozenset[tuple[int, ...]]
    training_messages: frozenset[int]
    factors: tuple[tuple[int, int, int, int], ...]


@dataclass(frozen=True)
class Task:
    query: ParityQuery
    near_query: ParityQuery
    target: tuple[int, ...]


def encode(message: int, columns: tuple[int, ...], polarities: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(((message & column).bit_count() & 1) ^ polarity
                 for column, polarity in zip(columns, polarities))


def make_world(knowledge_size: int, seed: int) -> World:
    if knowledge_size not in (8, 32):
        raise ValueError("v1 quick supports K=8 or K=32")
    rng = random.Random(seed ^ 0xE71)
    columns = list(range(1, 1 << LATENT))
    rng.shuffle(columns)
    columns = tuple(columns)
    polarities = tuple(rng.randrange(2) for _ in range(WIDTH))
    full = tuple(encode(message, columns, polarities) for message in range(1 << LATENT))
    messages = [0, 1, 2, 4, 8, 16, 32, 63]
    remaining = [message for message in range(1 << LATENT) if message not in messages]
    rng.shuffle(remaining)
    messages += remaining[: knowledge_size - len(messages)]
    rng.shuffle(messages)
    factors = []
    for left in range(WIDTH):
        for middle in range(left + 1, WIDTH):
            for right in range(middle + 1, WIDTH):
                if columns[left] ^ columns[middle] ^ columns[right] == 0:
                    factors.append((left, middle, right,
                                    polarities[left] ^ polarities[middle] ^ polarities[right]))
    return World(tuple(full[message] for message in messages), full, frozenset(full),
                 frozenset(messages), tuple(factors))


def make_tasks(world: World, depth: int, seed: int, count: int) -> tuple[Task, ...]:
    heldout = [message for message in range(1 << LATENT) if message not in world.training_messages]
    random.Random(seed ^ (depth * 65537)).shuffle(heldout)
    tasks = []
    for index, message in enumerate(heldout[:count]):
        target = world.codewords[message]
        positions = list(range(WIDTH))
        random.Random(seed ^ message ^ (index * 131071) ^ depth).shuffle(positions)
        near_positions = list(range(WIDTH))
        random.Random(seed ^ message ^ (index * 524287) ^ depth ^ 0x55AA).shuffle(near_positions)
        corrupted, near = list(target), list(target)
        for position in positions[:depth]:
            corrupted[position] ^= 1
        for position in near_positions[:depth]:
            near[position] ^= 1
        tasks.append(Task(ParityQuery(tuple(corrupted)), ParityQuery(tuple(near)), target))
    if len(tasks) != count:
        raise RuntimeError("not enough held-out messages")
    return tuple(tasks)


def energy(state: tuple[int, ...], factors: tuple[tuple[int, int, int, int], ...]) -> int:
    return sum(state[left] ^ state[middle] ^ state[right] ^ parity
               for left, middle, right, parity in factors)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world, candidate = make_world(knowledge_size, seed), load_candidate(candidate_name, seed)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell)
    fit_data = (world.factors,) if candidate_name == "oracle_parallel_parity_energy" else world.patterns
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, WIDTH, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    fit_ops, peak_state = float(candidate.fit_ops), candidate.state_bytes()

    def measure(near: bool = False):
        nonlocal peak_state
        rows = []
        for task in tasks:
            query = task.near_query if near else task.query
            tick = time.perf_counter_ns()
            answer = candidate.query(query, reasoning_depth)
            rows.append({"correct": float(answer == task.target),
                         "spurious": float(answer not in world.full_codebook),
                         "monotonic": float(energy(answer, world.factors) <= energy(query.state, world.factors)),
                         "converged": float(energy(answer, world.factors) == 0),
                         "ops": float(candidate.last_ops),
                         "iterations": float(getattr(candidate, "last_iterations", 0)),
                         "updates": float(getattr(candidate, "last_active_updates", 0)),
                         "bytes": float(getattr(candidate, "last_bytes_scanned", 0)),
                         "latency": (time.perf_counter_ns() - tick) / 1000.0})
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold, warm, near = measure(), measure(), measure(True)
    update_task = tasks[-1]
    tick = time.perf_counter_ns()
    candidate.update(update_task.target, 0)
    update_latency = (time.perf_counter_ns() - tick) / 1000.0
    update_ops = float(candidate.update_ops)
    new_correct = candidate.query(update_task.query, reasoning_depth) == update_task.target
    after_ops = float(candidate.last_ops)
    retained = candidate.query(tasks[0].query, reasoning_depth) == tasks[0].target
    mean = lambda rows, key: statistics.fmean(row[key] for row in rows)
    accuracy = lambda rows: mean(rows, "correct")
    workload = fit_ops + sum(row["ops"] for row in cold + near) + update_ops + 16 * after_ops
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "heldout_composition_accuracy": accuracy(cold), "spurious_attractor_rate": mean(cold, "spurious"),
        "energy_monotonic_rate": mean(cold, "monotonic"), "constraint_convergence_rate": mean(cold, "converged"),
        "mean_iterations": mean(cold, "iterations"), "mean_active_updates": mean(cold, "updates"),
        "mean_bytes_scanned": mean(cold, "bytes"), "target_not_stored_rate": 1.0,
        "reuse_precision": 0.0, "reuse_coverage": 0.0, "false_reuse_rate": mean(cold, "spurious"),
        "continual_new_fact_accuracy": float(new_correct), "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_input_ops": float(WIDTH), "mean_controller_ops": mean(cold, "ops") - WIDTH,
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.5),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.5),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(peak_state, fit_peak)),
        "update_ops": update_ops, "update_latency_us": update_latency, "workload_ops": workload,
        "learned_rank": float(getattr(candidate, "affine_rank", 0)),
        "learned_factor_count": float(getattr(candidate, "factor_count", 0)),
        "factor_signature": float(getattr(candidate, "factor_signature", 0)),
        "true_factor_count": float(len(world.factors)), "minimum_code_distance": 32.0,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
