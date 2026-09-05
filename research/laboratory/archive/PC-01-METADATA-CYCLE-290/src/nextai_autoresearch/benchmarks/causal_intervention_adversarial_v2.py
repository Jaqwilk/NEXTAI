from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from nextai_autoresearch.causal_adversarial_core import AND, COPY, NOT, OR, XOR, XNOR, apply_gate

from .successor_graph_v1 import load_candidate, percentile


BENCHMARK_VERSION = "causal_intervention_adversarial_v2"
ROOTS = 10
MAIN_DEPTH = 8
GATES = (XOR, AND, OR, XNOR)


@dataclass(frozen=True)
class World:
    models: tuple[Any, ...]
    pools: tuple[tuple[int, ...], ...]
    main_nodes: tuple[int, ...]
    ambiguous_nodes: tuple[int, ...]


@dataclass(frozen=True)
class Query:
    root_values: tuple[int, ...]
    interventions: tuple[tuple[int, int], ...]
    target: int


def _pool(true_parents: tuple[int, ...], seed: int) -> tuple[int, ...]:
    values = list(true_parents)
    rng = random.Random(seed)
    for candidate in range(8):
        if candidate not in values:
            values.append(candidate)
        if len(values) == 4:
            break
    rng.shuffle(values)
    return tuple(values)


def make_world(knowledge_size: int, seed: int) -> World:
    rng = random.Random(seed)
    models: list[Any] = [None] * ROOTS
    pools: list[tuple[int, ...]] = [()] * ROOTS
    main_nodes = tuple(range(ROOTS, ROOTS + MAIN_DEPTH))
    for layer, node in enumerate(main_nodes):
        previous = 0 if layer == 0 else main_nodes[layer - 1]
        parents = tuple(sorted((previous, 1 + layer)))
        models.append((GATES[(layer + seed) % len(GATES)], parents))
        pools.append(_pool(parents, seed ^ node))

    ambiguous = []
    for offset in range(2 * knowledge_size):
        node = len(models)
        if offset % 8 == 0:
            models.append((COPY, (8,)))
            pools.append((8, 9))
            ambiguous.append(node)
            continue
        if offset % 3 == 0:
            parent = rng.randrange(ROOTS + MAIN_DEPTH)
            models.append(((COPY, NOT)[offset % 2], (parent,)))
            pools.append(_pool((parent,), seed ^ node))
        else:
            parents = tuple(sorted(rng.sample(range(ROOTS + MAIN_DEPTH), 2)))
            models.append((GATES[offset % len(GATES)], parents))
            pools.append(_pool(parents, seed ^ node))
    return World(tuple(models), tuple(pools), main_nodes, tuple(ambiguous))


def simulate(world: World, roots: tuple[int, ...], interventions: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    forced = dict(interventions)
    values = list(roots) + [0] * (len(world.models) - ROOTS)
    for node, value in forced.items():
        if node < ROOTS:
            values[node] = value
    for node in range(ROOTS, len(world.models)):
        if node in forced:
            values[node] = forced[node]
        else:
            gate, parents = world.models[node]
            values[node] = apply_gate(gate, tuple(values[parent] for parent in parents))
    return tuple(values)


def training_episodes(world: World, seed: int):
    episodes = []
    identifiable = [node for node in range(ROOTS + MAIN_DEPTH, len(world.models)) if node not in world.ambiguous_nodes]
    for index in range(96):
        episode_rng = random.Random(seed ^ 0x5F3759DF ^ (index * 104729))
        roots = [episode_rng.randrange(2) for _ in range(ROOTS)]
        roots[9] = roots[8]
        baseline = simulate(world, tuple(roots), ())
        if index < 72:
            targets = {world.main_nodes[(index + 2 * step) % MAIN_DEPTH] for step in range(4)}
            interventions = tuple(sorted((node, 1 - baseline[node]) for node in targets))
        elif index < 80 and identifiable:
            node = identifiable[(index - 72) % len(identifiable)]
            interventions = ((node, 1 - baseline[node]),)
        else:
            interventions = ()
        values = list(simulate(world, tuple(roots), interventions))
        for node in range(len(values)):
            if node == 9:
                continue
            noise_rng = random.Random(seed ^ (index * 65537) ^ (node * 8191))
            if noise_rng.random() < 0.05:
                values[node] ^= 1
        values[9] = values[8]
        episodes.append((tuple(roots), interventions, tuple(values)))
    return tuple(episodes)


def make_query(world: World, depth: int, seed: int, index: int) -> tuple[Query, int]:
    rng = random.Random(seed ^ (index * 104729) ^ (depth << 16))
    roots = tuple(rng.randrange(2) for _ in range(ROOTS))
    baseline = simulate(world, roots, ())
    target = world.main_nodes[depth - 1]
    upstream = 0 if depth == 1 else world.main_nodes[max(0, depth // 2 - 1)]
    side_root = depth
    irrelevant = ROOTS + MAIN_DEPTH + (index % (len(world.models) - ROOTS - MAIN_DEPTH))
    interventions = tuple(
        sorted(
            (
                (upstream, baseline[upstream] ^ (index % 2)),
                (side_root, baseline[side_root] ^ ((index // 2) % 2)),
                (irrelevant, 1 - baseline[irrelevant]),
            )
        )
    )
    query = Query(roots, interventions, target)
    return query, simulate(world, roots, interventions)[target]


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world = make_world(knowledge_size, seed)
    episodes = training_episodes(world, seed)
    tasks = tuple(make_query(world, reasoning_depth, seed, index) for index in range(queries_per_cell))
    candidate = load_candidate(candidate_name, seed)
    fit_data = ((world.models, ROOTS),) if candidate_name == "oracle_adversarial_causal" else (world.pools, episodes)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure(items):
        answers, operations, visited, latencies = [], [], [], []
        for query, _ in items:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(query, reasoning_depth))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            visited.append(float(candidate.last_visited_nodes))
        return answers, operations, visited, latencies

    answers, operations, visited, latencies = measure(tasks)
    warm_answers, warm_operations, warm_visited, warm_latencies = measure(tasks)
    update_query, _ = tasks[0]
    update_episode = (update_query.root_values, update_query.interventions, simulate(world, update_query.root_values, update_query.interventions))
    update_started = time.perf_counter_ns()
    candidate.update(update_episode, 0)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_query, new_expected = make_query(world, reasoning_depth, seed, queries_per_cell + 1)
    new_answer = candidate.query(new_query, reasoning_depth)
    retained = candidate.query(tasks[0][0], reasoning_depth)
    expected = [value for _, value in tasks]
    models = getattr(candidate, "models", None)
    main_structure = 0.0 if models is None else statistics.fmean(models[node] == world.models[node] for node in world.main_nodes)
    ambiguous_abstention = 0.0 if models is None else statistics.fmean(models[node] is None for node in world.ambiguous_nodes)
    structure_coverage = 0.0 if models is None else statistics.fmean(model is not None for model in models[ROOTS:])
    return {
        "status": "complete",
        "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth,
        "seed": seed,
        "query_count": queries_per_cell,
        "accuracy": statistics.fmean(answer == target for answer, target in zip(answers, expected)),
        "warm_accuracy": statistics.fmean(answer == target for answer, target in zip(warm_answers, expected)),
        "ood_intervention_accuracy": statistics.fmean(answer == target for answer, target in zip(answers, expected)),
        "main_structure_accuracy": main_structure,
        "ambiguous_abstention_rate": ambiguous_abstention,
        "structure_coverage": structure_coverage,
        "continual_new_fact_accuracy": float(new_answer == new_expected),
        "continual_retention": float(retained == tasks[0][1]),
        "fit_seconds": fit_seconds,
        "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations),
        "mean_warm_query_ops": statistics.fmean(warm_operations),
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
