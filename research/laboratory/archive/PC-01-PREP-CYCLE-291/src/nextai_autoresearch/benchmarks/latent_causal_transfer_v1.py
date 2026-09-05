from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..latent_causal_core import Episode, LatentQuery


BENCHMARK_VERSION = "latent_causal_transfer_v1"


@dataclass(frozen=True)
class World:
    parents: tuple[tuple[int, ...], ...]
    biases: tuple[int, ...]
    sensors: tuple[int, ...]
    tokens: tuple[int, ...]
    polarities: tuple[int, ...]
    merge_nodes: tuple[int, ...]
    roots: tuple[int, ...]


def make_world(distractors: int, seed: int, max_depth: int = 6) -> World:
    parents: list[tuple[int, ...]] = [(), ()]
    merge_nodes = []
    for level in range(1, max_depth + 1):
        previous_left = 0 if level == 1 else 2 + 3 * (level - 2)
        previous_right = 1 if level == 1 else previous_left + 1
        left = len(parents)
        parents.extend(((previous_left,), (previous_right,), (left, left + 1)))
        merge_nodes.append(left + 2)
    parents.extend(() for _ in range(distractors))
    total = len(parents)
    biases = tuple(0 if not parent else random.Random(seed ^ (node * 65537)).randrange(2) for node, parent in enumerate(parents))
    offset = (seed * 104729) % 1009
    sensors = tuple(10_000_019 + offset + node * 7919 for node in range(total))
    tokens = tuple(50_000_017 + offset + node * 15401 for node in range(total))
    polarities = tuple(random.Random(seed ^ 0xF11F ^ (node * 31337)).randrange(2) for node in range(total))
    roots = tuple(node for node, parent in enumerate(parents) if not parent)
    return World(tuple(parents), biases, sensors, tokens, polarities, tuple(merge_nodes), roots)


def root_context(world: World, seed: int, index: int) -> dict[int, int]:
    rng = random.Random(seed ^ 0xC017 ^ (index * 104729))
    return {node: rng.randrange(2) for node in world.roots}


def simulate(world: World, context: dict[int, int], interventions: dict[int, int]):
    values = [0] * len(world.parents)
    for node, parents in enumerate(world.parents):
        if node in interventions:
            values[node] = interventions[node]
        elif not parents:
            values[node] = context[node]
        else:
            value = world.biases[node]
            for parent in parents:
                value ^= values[parent]
            values[node] = value
    return tuple(values)


def observe(world: World, values: tuple[int, ...], mask: int, *, roots_only: bool = False):
    protected = set(world.roots) | set(world.merge_nodes)
    pairs = []
    for node, value in enumerate(values):
        if roots_only and node not in world.roots:
            continue
        if not roots_only and node not in protected and (node + mask) % 4 == 0:
            continue
        pairs.append((world.sensors[node], value ^ world.polarities[node]))
    random.Random(mask ^ len(values) ^ 0x0B51).shuffle(pairs)
    return tuple(pairs)


def training_episodes(world: World, seed: int, query_count: int):
    episodes = []
    for index in range(query_count):
        context = root_context(world, seed, index)
        baseline = simulate(world, context, {})
        episodes.append(Episode(-1 - index, None, None, observe(world, baseline, index)))
        for node, token in enumerate(world.tokens):
            pair_id = node * query_count + index
            for forced in (0, 1):
                values = simulate(world, context, {node: forced})
                episodes.append(Episode(pair_id, token, forced, observe(world, values, index)))
    return tuple(episodes)


def level_nodes(depth: int):
    left = 2 + 3 * (depth - 1)
    return left, left + 1, left + 2


def make_task(world: World, depth: int, seed: int, index: int) -> tuple[LatentQuery, int]:
    context = root_context(world, seed, index)
    baseline = simulate(world, context, {})
    _, _, target = level_nodes(depth)
    interventions = ((world.tokens[0], baseline[0] ^ 1), (world.tokens[1], baseline[1] ^ 1))
    changed = simulate(world, context, {0: baseline[0] ^ 1, 1: baseline[1] ^ 1})
    query = LatentQuery(observe(world, baseline, index, roots_only=True), interventions, world.sensors[target])
    return query, changed[target] ^ world.polarities[target]


def representation(world: World):
    return world.sensors, world.tokens, world.polarities


def oracle_model(world: World):
    parents = []
    biases = []
    for node, latent_parents in enumerate(world.parents):
        sensor_parents = tuple(world.sensors[parent] for parent in latent_parents)
        parents.append((world.sensors[node], sensor_parents))
        if latent_parents:
            observed_bias = world.biases[node] ^ world.polarities[node]
            for parent in latent_parents:
                observed_bias ^= world.polarities[parent]
            biases.append((world.sensors[node], observed_bias))
    targets = tuple((world.tokens[node], world.sensors[node]) for node in range(len(world.parents)))
    flips = tuple((world.tokens[node], world.polarities[node]) for node in range(len(world.parents)))
    return tuple(parents), tuple(biases), targets, flips


def run_trial(
    candidate_name: str,
    knowledge_size: int,
    reasoning_depth: int,
    queries_per_cell: int,
    seed: int,
    max_depth: int,
) -> dict[str, Any]:
    world = make_world(knowledge_size, seed, max_depth)
    episodes = training_episodes(world, seed, queries_per_cell)
    tasks = tuple(make_task(world, reasoning_depth, seed, index) for index in range(queries_per_cell))
    candidate = load_candidate(candidate_name, seed)
    if candidate_name == "oracle_representation_causal":
        fit_data = (representation(world), episodes)
    elif candidate_name == "oracle_latent_causal":
        fit_data = (oracle_model(world),)
    else:
        fit_data = episodes
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, len(world.parents), max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure():
        answers, operations, perception, local, visited, latencies = [], [], [], [], [], []
        for query, _ in tasks:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(query, reasoning_depth))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            perception.append(float(candidate.last_perception_ops))
            local.append(float(candidate.last_local_ops))
            visited.append(float(candidate.last_visited_nodes))
        return answers, operations, perception, local, visited, latencies

    targets = tuple(target for _, target in tasks)
    answers, operations, perception, local, visited, latencies = measure()
    warm_answers, warm_operations, _, _, warm_visited, warm_latencies = measure()
    update_started = time.perf_counter_ns()
    candidate.update(episodes[-1], 0)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_query, new_target = make_task(world, reasoning_depth, seed, queries_per_cell + 1)
    new_correct = candidate.query(new_query, reasoning_depth) == new_target
    retained = candidate.query(tasks[0][0], reasoning_depth) == targets[0]
    true_targets = {world.tokens[node]: world.sensors[node] for node in range(len(world.parents))}
    true_parents = {world.sensors[node]: tuple(world.sensors[parent] for parent in world.parents[node]) for node in range(len(world.parents))}
    learned_targets = getattr(candidate, "token_targets", {})
    learned_parents = getattr(candidate, "parents", {})
    target_accuracy = statistics.fmean(learned_targets.get(token) == sensor for token, sensor in true_targets.items())
    active_structure = statistics.fmean(
        learned_parents.get(world.sensors[node]) == true_parents[world.sensors[node]]
        for node in range(len(world.parents) - knowledge_size)
    )
    accuracy = statistics.fmean(answer == target for answer, target in zip(answers, targets))
    return {
        "status": "complete",
        "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth,
        "seed": seed,
        "query_count": queries_per_cell,
        "accuracy": accuracy,
        "warm_accuracy": statistics.fmean(answer == target for answer, target in zip(warm_answers, targets)),
        "ood_intervention_accuracy": accuracy,
        "target_mapping_accuracy": target_accuracy,
        "structure_accuracy": active_structure,
        "continual_new_fact_accuracy": float(new_correct),
        "continual_retention": float(retained),
        "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations),
        "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_perception_ops": statistics.fmean(perception),
        "mean_local_ops": statistics.fmean(local),
        "mean_visited_nodes": statistics.fmean(visited),
        "mean_warm_visited_nodes": statistics.fmean(warm_visited),
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
