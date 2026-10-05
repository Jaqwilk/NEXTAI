from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..attractor_core import AttractorQuery


BENCHMARK_VERSION = "associative_relational_relaxation_v1"
BLOCKS, BLOCK_WIDTH = 6, 5


@dataclass(frozen=True)
class World:
    patterns: tuple[tuple[int, ...], ...]
    latent_patterns: tuple[tuple[int, ...], ...]
    components: tuple[tuple[tuple[int, int], ...], ...]


def encode(components: tuple[tuple[tuple[int, int], ...], ...], latent: tuple[int, ...]) -> tuple[int, ...]:
    state = [0] * (BLOCKS * BLOCK_WIDTH)
    for value, component in zip(latent, components):
        for position, polarity in component:
            state[position] = value ^ polarity
    return tuple(state)


def make_world(knowledge_size: int, seed: int) -> World:
    if knowledge_size not in (8, 32):
        raise ValueError("v1 supports K=8 or K=32")
    order = list(range(BLOCKS * BLOCK_WIDTH))
    random.Random(seed ^ 0xA771AC7).shuffle(order)
    rng = random.Random(seed ^ 0xB10C)
    components = tuple(
        tuple((order[block * BLOCK_WIDTH + offset], rng.randrange(2)) for offset in range(BLOCK_WIDTH))
        for block in range(BLOCKS)
    )
    masks = (1, 2, 3, 4, 5, 6)
    latent = tuple(tuple((index & mask).bit_count() & 1 for mask in masks) for index in range(knowledge_size))
    return World(tuple(encode(components, item) for item in latent), latent, components)


def latent_state(world: World, state: tuple[int, ...]) -> tuple[int, ...] | None:
    values = []
    for component in world.components:
        observed = {state[position] ^ polarity for position, polarity in component}
        if len(observed) != 1:
            return None
        values.append(observed.pop())
    return tuple(values)


def make_tasks(world: World, corruption_depth: int, seed: int, query_count: int):
    if not 1 <= corruption_depth <= BLOCKS:
        raise ValueError("corruption depth must be in [1, 6]")
    stored = set(world.latent_patterns)
    heldout = [tuple((value >> block) & 1 for block in range(BLOCKS)) for value in range(1 << BLOCKS)]
    heldout = [latent for latent in heldout if latent not in stored]
    random.Random(seed ^ (corruption_depth * 65537)).shuffle(heldout)
    tasks = []
    for index, latent in enumerate(heldout[:query_count]):
        target = encode(world.components, latent)
        corrupted = list(target)
        blocks = list(range(BLOCKS))
        random.Random(seed ^ (corruption_depth * 131071) ^ index).shuffle(blocks)
        for block in blocks[:corruption_depth]:
            component = world.components[block]
            position, _ = component[(index + block) % BLOCK_WIDTH]
            corrupted[position] ^= 1
        tasks.append((AttractorQuery(tuple(corrupted)), target))
    if len(tasks) != query_count:
        raise RuntimeError("not enough held-out compositions")
    return tuple(tasks)


def _monotonic(path: tuple[int, ...]) -> float:
    return float(bool(path) and all(right <= left for left, right in zip(path, path[1:])))


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world = make_world(knowledge_size, seed)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    fit_data = (world.components,) if candidate_name == "oracle_relational_energy" else world.patterns
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, BLOCKS * BLOCK_WIDTH, max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure():
        answers, operations, iterations, updates, byte_counts, monotonic, latencies = [], [], [], [], [], [], []
        for query, _ in tasks:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(query, reasoning_depth))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            iterations.append(float(candidate.last_iterations))
            updates.append(float(candidate.last_active_updates))
            byte_counts.append(float(candidate.last_bytes_scanned))
            monotonic.append(_monotonic(candidate.last_energy_path))
        return answers, operations, iterations, updates, byte_counts, monotonic, latencies

    answers, operations, iterations, updates, byte_counts, monotonic, latencies = measure()
    warm_answers, warm_operations, _, _, _, _, warm_latencies = measure()
    targets = tuple(target for _, target in tasks)
    exact = [answer == target for answer, target in zip(answers, targets)]
    warm_exact = [answer == target for answer, target in zip(warm_answers, targets)]
    bit_scores = [statistics.fmean(left == right for left, right in zip(answer, target)) for answer, target in zip(answers, targets)]
    spurious = [latent_state(world, answer) is None for answer in answers]

    update_query, update_pattern = tasks[-1]
    update_started = time.perf_counter_ns()
    candidate.update(update_pattern, 0)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    update_ops = candidate.update_ops
    new_fact = candidate.query(update_query, reasoning_depth) == update_pattern
    retained = candidate.query(tasks[0][0], reasoning_depth) == tasks[0][1]
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell,
        "accuracy": statistics.fmean(exact), "warm_accuracy": statistics.fmean(warm_exact),
        "heldout_composition_accuracy": statistics.fmean(exact), "bit_accuracy": statistics.fmean(bit_scores),
        "spurious_attractor_rate": statistics.fmean(spurious), "energy_monotonic_rate": statistics.fmean(monotonic),
        "mean_iterations": statistics.fmean(iterations), "mean_active_updates": statistics.fmean(updates),
        "mean_bytes_scanned": statistics.fmean(byte_counts),
        "target_not_stored_rate": statistics.fmean(target not in world.patterns for target in targets),
        "continual_new_fact_accuracy": float(new_fact), "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations), "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_visited_nodes": statistics.fmean(updates), "mean_warm_visited_nodes": statistics.fmean(updates),
        "p50_latency_us": percentile(latencies, 0.50), "p95_latency_us": percentile(latencies, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies, 0.50), "warm_p95_latency_us": percentile(warm_latencies, 0.95),
        "update_latency_us": update_latency_us, "update_ops": float(update_ops),
        "state_bytes": float(max(candidate.state_bytes(), traced_peak)),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
