from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..attractor_core import AttractorQuery


BENCHMARK_VERSION = "associative_relational_relaxation_adversarial_v2"
BLOCK_WIDTHS = (3, 4, 5, 3, 6, 4, 5, 6)
BLOCKS, WIDTH = len(BLOCK_WIDTHS), sum(BLOCK_WIDTHS)


@dataclass(frozen=True)
class World:
    patterns: tuple[tuple[int, ...], ...]
    clean_patterns: tuple[tuple[int, ...], ...]
    latent_patterns: tuple[tuple[int, ...], ...]
    components: tuple[tuple[tuple[int, int], ...], ...]


def encode(components: tuple[tuple[tuple[int, int], ...], ...], latent: tuple[int, ...]) -> tuple[int, ...]:
    state = [0] * WIDTH
    for value, component in zip(latent, components):
        for position, polarity in component:
            state[position] = value ^ polarity
    return tuple(state)


def _base_rows() -> tuple[tuple[int, ...], ...]:
    residues, signs = {1, 2, 4}, [[1] * 8]
    for left in range(7):
        signs.append([-1] + [1 if left == right or (right - left) % 7 in residues else -1 for right in range(7)])
    bits = tuple(tuple(int(value < 0) for value in row) for row in signs)
    return tuple(tuple(bits[component][row] for component in range(BLOCKS)) for row in range(BLOCKS))


BASE_ROWS = _base_rows()


def make_world(knowledge_size: int, seed: int) -> World:
    if knowledge_size not in (8, 32, 128):
        raise ValueError("v2 supports K=8, K=32 or K=128")
    rng = random.Random(seed ^ 0xADB2)
    component_order, row_order, positions = list(range(BLOCKS)), list(range(BLOCKS)), list(range(WIDTH))
    rng.shuffle(component_order)
    rng.shuffle(row_order)
    rng.shuffle(positions)
    polarities = [rng.randrange(2) for _ in range(WIDTH)]
    components, offset = [], 0
    for block_width in BLOCK_WIDTHS:
        members = positions[offset : offset + block_width]
        components.append(tuple((position, polarities[position]) for position in members))
        offset += block_width
    components = tuple(components)

    representatives = list(range(0, 32, 2))
    rng.shuffle(representatives)
    latent_patterns, clean_patterns, patterns = [], [], []
    for representative in representatives[: knowledge_size // BLOCKS]:
        for base_row in row_order:
            original = tuple(BASE_ROWS[base_row][index] ^ ((representative >> index) & 1) for index in range(BLOCKS))
            latent = [0] * BLOCKS
            for original_index, actual_index in enumerate(component_order):
                latent[actual_index] = original[original_index]
            latent_tuple = tuple(latent)
            clean = encode(components, latent_tuple)
            noisy = list(clean)
            noisy_component = components[component_order[base_row]]
            noisy[noisy_component[0][0]] ^= 1
            noisy[noisy_component[1][0]] ^= 1
            latent_patterns.append(latent_tuple)
            clean_patterns.append(clean)
            patterns.append(tuple(noisy))
    if len(set(latent_patterns)) != knowledge_size:
        raise RuntimeError("training compositions must be unique")
    return World(tuple(patterns), tuple(clean_patterns), tuple(latent_patterns), components)


def latent_state(world: World, state: tuple[int, ...]) -> tuple[int, ...] | None:
    values = []
    for component in world.components:
        observed = {state[position] ^ polarity for position, polarity in component}
        if len(observed) != 1:
            return None
        values.append(observed.pop())
    return tuple(values)


def relation_bounds(world: World) -> tuple[float, float]:
    count, within, cross = len(world.patterns), 1.0, 0.5
    for left_block, left_component in enumerate(world.components):
        for left_offset, (left, _) in enumerate(left_component):
            for right, _ in left_component[left_offset + 1 :]:
                same = sum(pattern[left] == pattern[right] for pattern in world.patterns)
                within = min(within, max(same, count - same) / count)
            for right_component in world.components[left_block + 1 :]:
                for right, _ in right_component:
                    same = sum(pattern[left] == pattern[right] for pattern in world.patterns)
                    cross = max(cross, max(same, count - same) / count)
    return within, cross


def make_tasks(world: World, corruption_depth: int, seed: int, query_count: int):
    if not 1 <= corruption_depth <= BLOCKS:
        raise ValueError("corruption depth must be in [1, 8]")
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
            position, _ = component[(index + block) % len(component)]
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
    candidate.fit(fit_data, WIDTH, max_depth)
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
    new_fact = candidate.query(update_query, reasoning_depth) == update_pattern
    retained = candidate.query(tasks[0][0], reasoning_depth) == tasks[0][1]
    within, cross = relation_bounds(world)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell,
        "accuracy": statistics.fmean(exact), "warm_accuracy": statistics.fmean(warm_exact),
        "heldout_composition_accuracy": statistics.fmean(exact), "bit_accuracy": statistics.fmean(bit_scores),
        "spurious_attractor_rate": statistics.fmean(spurious), "energy_monotonic_rate": statistics.fmean(monotonic),
        "mean_iterations": statistics.fmean(iterations), "mean_active_updates": statistics.fmean(updates),
        "mean_bytes_scanned": statistics.fmean(byte_counts),
        "target_not_stored_rate": statistics.fmean(target not in world.clean_patterns for target in targets),
        "training_bit_noise_rate": statistics.fmean(statistics.fmean(left != right for left, right in zip(noisy, clean)) for noisy, clean in zip(world.patterns, world.clean_patterns)),
        "within_relation_agreement": within, "cross_relation_association": cross,
        "latent_unbalanced_components": float(sum(sum(pattern[index] for pattern in world.latent_patterns) != knowledge_size / 2 for index in range(BLOCKS))),
        "continual_new_fact_accuracy": float(new_fact), "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations), "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_visited_nodes": statistics.fmean(updates), "mean_warm_visited_nodes": statistics.fmean(updates),
        "p50_latency_us": percentile(latencies, 0.50), "p95_latency_us": percentile(latencies, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies, 0.50), "warm_p95_latency_us": percentile(warm_latencies, 0.95),
        "update_latency_us": update_latency_us, "update_ops": float(candidate.update_ops),
        "state_bytes": float(max(candidate.state_bytes(), traced_peak)),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
