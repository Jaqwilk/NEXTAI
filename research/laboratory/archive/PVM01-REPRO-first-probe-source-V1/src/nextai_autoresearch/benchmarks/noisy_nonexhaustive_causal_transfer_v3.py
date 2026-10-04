from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from typing import Any

from .latent_causal_transfer_adversarial_v2 import (
    branch_node,
    make_tasks,
    make_world,
    observe,
    oracle_model,
    representation,
    root_context,
    simulate,
)
from .successor_graph_v1 import load_candidate, percentile
from ..latent_causal_core import Episode, LatentQuery


BENCHMARK_VERSION = "noisy_nonexhaustive_causal_transfer_v3"
TRAIN_CONTEXTS, CONTEXTS_PER_TARGET, REPEATS, NOISE_RATE = 32, 8, 5, 0.10


def _noisy_observation(observation, noise_seed: int):
    rng, changed = random.Random(noise_seed), 0
    result = []
    for sensor, value in observation:
        flip = rng.random() < NOISE_RATE
        changed += flip
        result.append((sensor, value ^ flip))
    return tuple(result), changed, len(result)


def training_data(world, seed: int, max_depth: int):
    episodes, examples = [], []
    flips = total = 0
    targets = tuple(world.merge_nodes[:max_depth])
    for context_index in range(TRAIN_CONTEXTS):
        context = root_context(world, seed, context_index)
        values = simulate(world, context, {})
        clean = observe(world, values, context_index, complete_active=True)
        for repeat in range(REPEATS):
            noisy, changed, count = _noisy_observation(clean, seed ^ 0xB451 ^ context_index * 4099 ^ repeat * 65537)
            episodes.append(Episode(-1 - context_index, None, None, noisy))
            flips, total = flips + changed, total + count
        noisy_context, changed, count = _noisy_observation(observe(world, values, context_index, roots_only=True), seed ^ 0xC017 ^ context_index)
        flips, total = flips + changed, total + count
        for target in targets:
            label = values[target] ^ world.polarities[target]
            label_flip = random.Random(seed ^ 0x1ABE1 ^ context_index * 8191 ^ target).random() < NOISE_RATE
            examples.append((LatentQuery(noisy_context, (), world.sensors[target]), label ^ label_flip))
            flips, total = flips + label_flip, total + 1

    active_count = world.merge_nodes[-1] + 1
    for node in range(active_count):
        contexts = random.Random(seed ^ 0x1A73 ^ node * 104729).sample(range(TRAIN_CONTEXTS), CONTEXTS_PER_TARGET)
        for context_index in contexts:
            context = root_context(world, seed, context_index)
            pair_id = node * TRAIN_CONTEXTS + context_index
            for forced in (0, 1):
                values = simulate(world, context, {node: forced})
                clean = observe(world, values, context_index, complete_active=True)
                for repeat in range(REPEATS):
                    noise_seed = seed ^ 0xE915 ^ pair_id * 131071 ^ forced * 524287 ^ repeat * 65537
                    noisy, changed, count = _noisy_observation(clean, noise_seed)
                    episodes.append(Episode(pair_id, world.tokens[node], forced, noisy))
                    flips, total = flips + changed, total + count
                base_context = observe(world, simulate(world, context, {}), context_index, roots_only=True)
                for target in targets:
                    noise_seed = seed ^ 0x51A6 ^ pair_id * 4099 ^ forced * 8191 ^ target
                    noisy_context, changed, count = _noisy_observation(base_context, noise_seed)
                    label = values[target] ^ world.polarities[target]
                    label_flip = random.Random(noise_seed ^ 0x1ABE1).random() < NOISE_RATE
                    query = LatentQuery(noisy_context, ((world.tokens[node], forced),), world.sensors[target])
                    examples.append((query, label ^ label_flip))
                    flips, total = flips + changed + label_flip, total + count + 1
    metadata = {
        "training_noise_rate": flips / total,
        "intervention_context_coverage": CONTEXTS_PER_TARGET / TRAIN_CONTEXTS,
        "intervention_target_coverage": active_count / len(world.parents),
        "training_pair_rate": 0.0,
    }
    return (tuple(episodes), tuple(examples)), metadata


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world = make_world(knowledge_size, seed, max_depth)
    bundle, data_metrics = training_data(world, seed, max_depth)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    if candidate_name == "oracle_representation_noisy":
        fit_data = (representation(world), bundle)
    elif candidate_name == "oracle_noisy_causal":
        fit_data = (oracle_model(world),)
    else:
        fit_data = bundle
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, len(world.parents), max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure():
        answers, operations, encoding, representation_ops, local, visited, latencies = [], [], [], [], [], [], []
        for query, _ in tasks:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(query, reasoning_depth))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            encoding.append(float(getattr(candidate, "last_encoding_ops", 0)))
            representation_ops.append(float(getattr(candidate, "last_representation_ops", 0)))
            residual = candidate.last_ops - encoding[-1] - representation_ops[-1]
            local.append(float(getattr(candidate, "last_local_ops", residual)))
            visited.append(float(getattr(candidate, "last_visited_nodes", 0)))
        return answers, operations, encoding, representation_ops, local, visited, latencies

    targets = tuple(target for _, target in tasks)
    answers, operations, encoding, representation_ops, local, visited, latencies = measure()
    warm_answers, warm_operations, _, _, _, warm_visited, warm_latencies = measure()
    update_started = time.perf_counter_ns()
    candidate.update(bundle[0][-1], 0)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    retained = candidate.query(tasks[0][0], reasoning_depth) == targets[0]
    active_count = world.merge_nodes[-1] + 1
    true_targets = {world.tokens[node]: world.sensors[node] for node in range(active_count)}
    true_parents = {world.sensors[node]: tuple(sorted(world.sensors[parent] for parent in world.parents[node])) for node in range(active_count)}
    true_models = dict(oracle_model(world)[1])
    learned_targets = getattr(candidate, "token_targets", {})
    learned_parents = getattr(candidate, "parents", {})
    learned_models = getattr(candidate, "models", {})
    accuracy = statistics.fmean(answer == target for answer, target in zip(answers, targets))
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy, "ood_intervention_accuracy": accuracy,
        "warm_accuracy": statistics.fmean(answer == target for answer, target in zip(warm_answers, targets)),
        "label_positive_rate": statistics.fmean(targets), "unseen_pair_rate": 1.0, **data_metrics,
        "target_mapping_accuracy": statistics.fmean(learned_targets.get(token) == sensor for token, sensor in true_targets.items()),
        "structure_accuracy": statistics.fmean(learned_parents.get(sensor) == parents for sensor, parents in true_parents.items()),
        "gate_accuracy": statistics.fmean(learned_models.get(sensor) == table for sensor, table in true_models.items() if sensor in true_parents),
        "identified_fraction": sum(sensor in learned_parents for sensor in true_parents) / len(true_parents),
        "continual_retention": float(retained), "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations), "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_encoding_ops": statistics.fmean(encoding), "mean_representation_ops": statistics.fmean(representation_ops),
        "mean_local_ops": statistics.fmean(local), "mean_visited_nodes": statistics.fmean(visited),
        "mean_warm_visited_nodes": statistics.fmean(warm_visited),
        "p50_latency_us": percentile(latencies, 0.50), "p95_latency_us": percentile(latencies, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies, 0.50), "warm_p95_latency_us": percentile(warm_latencies, 0.95),
        "update_latency_us": update_latency_us, "update_ops": float(candidate.update_ops),
        "state_bytes": float(candidate.state_bytes()), "fit_peak_bytes": float(fit_peak),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
