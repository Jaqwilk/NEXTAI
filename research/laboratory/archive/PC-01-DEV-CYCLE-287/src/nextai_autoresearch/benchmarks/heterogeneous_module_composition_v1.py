from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..modular_composition_core import Demo, FEATURE_BITS, ModularQuery, PROBES, SPECS, apply_transform


BENCHMARK_VERSION = "heterogeneous_module_composition_v1"
ACTIVE_MODULES = 6


@dataclass(frozen=True)
class World:
    specs: tuple[tuple[int, int], ...]
    features: tuple[tuple[int, ...], ...]


def _distance(left, right):
    return sum(a != b for a, b in zip(left, right))


def make_world(knowledge_size: int, seed: int) -> World:
    specs = list(SPECS)
    random.Random(seed ^ 0x5EEC).shuffle(specs)
    rng, features = random.Random(seed ^ 0xFEA7), []
    while len(features) < knowledge_size:
        feature = tuple(rng.randrange(2) for _ in range(FEATURE_BITS))
        if all(_distance(feature, other) >= 5 for other in features):
            features.append(feature)
    return World(tuple(specs[:knowledge_size]), tuple(features))


def training_demos(world: World):
    return tuple(Demo(feature, source, apply_transform(spec, source))
                 for spec, feature in zip(world.specs, world.features) for source in PROBES)


def make_tasks(world: World, depth: int, seed: int, query_count: int):
    rng, tasks = random.Random(seed ^ depth * 131071), []
    while len(tasks) < query_count:
        route_ids = tuple(rng.randrange(ACTIVE_MODULES) for _ in range(depth))
        source = rng.randrange(4, 252)
        if source in PROBES:
            continue
        value, features = source, []
        for step, route_id in enumerate(route_ids):
            feature = list(world.features[route_id])
            feature[(len(tasks) * 5 + step * 7 + depth) % FEATURE_BITS] ^= 1
            features.append(tuple(feature))
            value = apply_transform(world.specs[route_id], value)
        if value == source:
            continue
        tasks.append((ModularQuery(source, tuple(features), route_ids), value))
    return tuple(tasks)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world = make_world(knowledge_size, seed)
    demos = training_demos(world)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    fit_data = ((world.specs, world.features),) if candidate_name == "oracle_sparse_modules" else demos
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure():
        answers, ops, route_scores, active, router, expert, loaded, full, latencies = [], [], [], [], [], [], [], [], []
        for query, _ in tasks:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(query, reasoning_depth))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            routes = getattr(candidate, "last_routes", ())
            route_scores.append(sum(a == b for a, b in zip(routes, query.route_ids)) / len(query.route_ids) if len(routes) == len(query.route_ids) else 0.0)
            ops.append(float(candidate.last_ops))
            active.append(float(getattr(candidate, "last_active_modules", 0)))
            router.append(float(getattr(candidate, "last_router_ops", 0)))
            expert.append(float(getattr(candidate, "last_expert_ops", 0)))
            loaded.append(float(getattr(candidate, "last_bytes_loaded", 0)))
            full.append(float(getattr(candidate, "last_full_expert_evaluations", 0)))
        return answers, ops, route_scores, active, router, expert, loaded, full, latencies

    targets = tuple(target for _, target in tasks)
    answers, ops, route_scores, active, router, expert, loaded, full, latencies = measure()
    warm_answers, warm_ops, _, _, _, _, _, _, warm_latencies = measure()
    update_started = time.perf_counter_ns()
    candidate.update(demos[-1], demos[-1].target)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    retained = candidate.query(tasks[0][0], reasoning_depth) == targets[0]
    accuracy = statistics.fmean(answer == target for answer, target in zip(answers, targets))
    models = getattr(candidate, "models", {})
    induction = statistics.fmean(models.get(feature) == spec for feature, spec in zip(world.features, world.specs)) if models else 0.0
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy, "heldout_composition_accuracy": accuracy,
        "warm_accuracy": statistics.fmean(answer == target for answer, target in zip(warm_answers, targets)),
        "routing_accuracy": statistics.fmean(route_scores), "expert_induction_accuracy": induction,
        "feature_holdout_rate": 1.0, "input_holdout_rate": 1.0, "composition_sequence_seen_rate": 0.0,
        "dormant_expert_fraction": (knowledge_size - ACTIVE_MODULES) / knowledge_size,
        "mean_active_modules": statistics.fmean(active), "mean_router_ops": statistics.fmean(router),
        "mean_expert_ops": statistics.fmean(expert), "mean_bytes_loaded": statistics.fmean(loaded),
        "mean_full_expert_evaluations": statistics.fmean(full), "mean_query_ops": statistics.fmean(ops),
        "mean_warm_query_ops": statistics.fmean(warm_ops), "continual_retention": float(retained),
        "p50_latency_us": percentile(latencies, 0.50), "p95_latency_us": percentile(latencies, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies, 0.50), "warm_p95_latency_us": percentile(warm_latencies, 0.95),
        "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops), "fit_peak_bytes": float(fit_peak),
        "state_bytes": float(candidate.state_bytes()), "update_ops": float(candidate.update_ops), "update_latency_us": update_latency_us,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
