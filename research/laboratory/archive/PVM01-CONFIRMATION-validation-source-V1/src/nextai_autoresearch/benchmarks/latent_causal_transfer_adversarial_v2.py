from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..latent_causal_core import Episode, LatentQuery
from ..latent_causal_mixed_core import apply_table


BENCHMARK_VERSION = "latent_causal_transfer_adversarial_v2"
COPY, NOT, XOR, XNOR, AND, OR = 0b10, 0b01, 0b0110, 0b1001, 0b1000, 0b1110


@dataclass(frozen=True)
class World:
    parents: tuple[tuple[int, ...], ...]
    tables: tuple[int, ...]
    sensors: tuple[int, ...]
    tokens: tuple[int, ...]
    polarities: tuple[int, ...]
    merge_nodes: tuple[int, ...]
    roots: tuple[int, ...]


def _codes(count: int, seed: int) -> tuple[int, ...]:
    rng, values = random.Random(seed), []
    while len(values) < count:
        value = rng.randrange(1 << 20, 1 << 31)
        if value not in values:
            values.append(value)
    return tuple(values)


def make_world(distractors: int, seed: int, max_depth: int = 6) -> World:
    parents: list[tuple[int, ...]] = [(), ()]
    tables, merges = [0, 0], []
    for level in range(1, max_depth + 1):
        previous_left = 0 if level == 1 else 2 + 3 * (level - 2)
        previous_right = 1 if level == 1 else previous_left + 1
        left = len(parents)
        parents.extend(((previous_left,), (previous_right,), (left, left + 1)))
        branch_rng = random.Random(seed ^ (level * 65537))
        tables.extend((branch_rng.choice((COPY, NOT)), branch_rng.choice((COPY, NOT)), (XOR, AND, OR, XNOR)[(seed + level) % 4]))
        merges.append(left + 2)
    parents.extend(() for _ in range(distractors))
    tables.extend(0 for _ in range(distractors))
    total = len(parents)
    sensors = _codes(total, seed ^ 0x51A7C0DE)
    tokens = _codes(total, seed ^ 0x17E2BEEF)
    polarities = tuple(random.Random(seed ^ 0xF11F ^ (node * 31337)).randrange(2) for node in range(total))
    roots = tuple(node for node, source in enumerate(parents) if not source)
    return World(tuple(parents), tuple(tables), sensors, tokens, polarities, tuple(merges), roots)


def root_context(world: World, seed: int, index: int) -> dict[int, int]:
    values = {0: index & 1, 1: (index >> 1) & 1}
    for node in world.roots[2:]:
        values[node] = random.Random(seed ^ (index * 104729) ^ (node * 8191)).randrange(2)
    return values


def simulate(world: World, context: dict[int, int], interventions: dict[int, int]):
    values = [0] * len(world.parents)
    for node, parents in enumerate(world.parents):
        if node in interventions:
            values[node] = interventions[node]
        elif not parents:
            values[node] = context[node]
        else:
            values[node] = apply_table(world.tables[node], tuple(values[parent] for parent in parents))
    return tuple(values)


def observe(
    world: World,
    values: tuple[int, ...],
    mask: int,
    *,
    roots_only: bool = False,
    complete_active: bool = False,
):
    protected = set(world.roots) | set(world.merge_nodes)
    active_count = world.merge_nodes[-1] + 1
    pairs = []
    for node, value in enumerate(values):
        if roots_only and node not in world.roots:
            continue
        if not roots_only and node not in protected and not (complete_active and node < active_count) and (node + mask) % 4 == 0:
            continue
        pairs.append((world.sensors[node], value ^ world.polarities[node]))
    random.Random(mask ^ len(values) ^ 0x0B51).shuffle(pairs)
    return tuple(pairs)


def training_episodes(world: World, seed: int, query_count: int):
    episodes = []
    for index in range(query_count):
        context = root_context(world, seed, index)
        episodes.append(
            Episode(
                -1 - index,
                None,
                None,
                observe(world, simulate(world, context, {}), index, complete_active=True),
            )
        )
        for node, token in enumerate(world.tokens):
            pair_id = node * query_count + index
            for forced in (0, 1):
                values = simulate(world, context, {node: forced})
                episodes.append(Episode(pair_id, token, forced, observe(world, values, index)))
    return tuple(episodes)


def branch_node(side: int, level: int) -> int:
    if level == 0:
        return side
    return 2 + 3 * (level - 1) + side


def _task(world: World, depth: int, seed: int, attempt: int):
    context = root_context(world, seed, attempt)
    baseline = simulate(world, context, {})
    rng = random.Random(seed ^ (depth * 131071) ^ (attempt * 524287))
    left = branch_node(0, rng.randrange(depth + 1))
    right = branch_node(1, rng.randrange(depth + 1))
    interventions = {left: rng.randrange(2), right: rng.randrange(2)}
    target = 2 + 3 * (depth - 1) + 2
    changed = simulate(world, context, interventions)
    query = LatentQuery(
        observe(world, baseline, attempt, roots_only=True),
        tuple(sorted((world.tokens[node], value) for node, value in interventions.items())),
        world.sensors[target],
    )
    return query, changed[target] ^ world.polarities[target]


def parity_prediction(query: LatentQuery, seed: int) -> int:
    return (seed + query.target_code + sum(token + value for token, value in query.interventions)) & 1


def make_tasks(world: World, depth: int, seed: int, query_count: int):
    rng = random.Random(seed)
    random_predictions = [rng.randrange(2) for _ in range(query_count)]
    for batch in range(2048):
        tasks = tuple(_task(world, depth, seed, batch * query_count + index) for index in range(query_count))
        labels = [target for _, target in tasks]
        parity = [parity_prediction(query, seed) for query, _ in tasks]
        if sum(labels) != query_count // 2:
            continue
        if sum(left == right for left, right in zip(labels, parity)) > 5:
            continue
        if sum(left == right for left, right in zip(labels, random_predictions)) > 5:
            continue
        return tasks
    raise RuntimeError("could not construct balanced shortcut-resistant tasks")


def representation(world: World):
    return world.sensors, world.tokens, world.polarities


def observed_table(world: World, node: int) -> int:
    parents = tuple(sorted(world.parents[node], key=lambda parent: world.sensors[parent]))
    table = 0
    for observed_index in range(1 << len(parents)):
        observed_inputs = tuple((observed_index >> (len(parents) - 1 - index)) & 1 for index in range(len(parents)))
        latent_inputs = tuple(value ^ world.polarities[parent] for value, parent in zip(observed_inputs, parents))
        output = apply_table(world.tables[node], latent_inputs) ^ world.polarities[node]
        table |= output << observed_index
    return table


def oracle_model(world: World):
    parents = tuple(
        (
            world.sensors[node],
            tuple(sorted(world.sensors[parent] for parent in source)),
        )
        for node, source in enumerate(world.parents)
    )
    models = tuple((world.sensors[node], observed_table(world, node)) for node, source in enumerate(world.parents) if source)
    targets = tuple((world.tokens[node], world.sensors[node]) for node in range(len(world.parents)))
    flips = tuple((world.tokens[node], world.polarities[node]) for node in range(len(world.parents)))
    return parents, models, targets, flips


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world = make_world(knowledge_size, seed, max_depth)
    episodes = training_episodes(world, seed, queries_per_cell)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    if candidate_name == "oracle_representation_mixed":
        fit_data = (representation(world), episodes)
    elif candidate_name == "oracle_latent_mixed":
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
    retained = candidate.query(tasks[0][0], reasoning_depth) == targets[0]
    true_targets = {world.tokens[node]: world.sensors[node] for node in range(len(world.parents))}
    true_parents = {
        world.sensors[node]: tuple(sorted(world.sensors[parent] for parent in world.parents[node]))
        for node in range(len(world.parents))
    }
    true_models = {world.sensors[node]: observed_table(world, node) for node in range(len(world.parents)) if world.parents[node]}
    learned_targets = getattr(candidate, "token_targets", {})
    learned_parents = getattr(candidate, "parents", {})
    learned_models = getattr(candidate, "models", {})
    active_count = len(world.parents) - knowledge_size
    accuracy = statistics.fmean(answer == target for answer, target in zip(answers, targets))
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy,
        "warm_accuracy": statistics.fmean(answer == target for answer, target in zip(warm_answers, targets)),
        "ood_intervention_accuracy": accuracy, "label_positive_rate": statistics.fmean(targets),
        "target_mapping_accuracy": statistics.fmean(learned_targets.get(token) == sensor for token, sensor in true_targets.items()),
        "structure_accuracy": statistics.fmean(learned_parents.get(world.sensors[node]) == true_parents[world.sensors[node]] for node in range(active_count)),
        "gate_accuracy": statistics.fmean(learned_models.get(world.sensors[node]) == true_models[world.sensors[node]] for node in range(active_count) if world.parents[node]),
        "continual_new_fact_accuracy": accuracy, "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations), "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_perception_ops": statistics.fmean(perception), "mean_local_ops": statistics.fmean(local),
        "mean_visited_nodes": statistics.fmean(visited), "mean_warm_visited_nodes": statistics.fmean(warm_visited),
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
