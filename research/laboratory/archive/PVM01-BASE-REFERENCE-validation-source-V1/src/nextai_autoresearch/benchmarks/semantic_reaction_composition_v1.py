from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..reaction_core import ReactionEpisode, ReactionState


BENCHMARK_VERSION = "semantic_reaction_composition_v1"
SYMBOLS = 4


@dataclass(frozen=True)
class ReactionTask:
    source: ReactionState
    target: ReactionState
    rule_keys: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class World:
    rules: dict[tuple[int, int], tuple[int, int]]
    codes: tuple[int, ...]
    heldout_key: tuple[int, int]
    training: tuple[ReactionEpisode, ...]
    update_episode: ReactionEpisode


def make_rules(seed: int) -> tuple[dict[tuple[int, int], tuple[int, int]], tuple[int, ...]]:
    codes = list(range(SYMBOLS))
    random.Random(seed ^ 0xC4E5).shuffle(codes)
    rules = {}
    for carrier in range(SYMBOLS):
        for symbol in range(SYMBOLS):
            rules[codes[carrier], codes[symbol]] = (
                codes[(carrier + symbol + 1) % SYMBOLS],
                codes[(2 * carrier + symbol + 1) % SYMBOLS],
            )
    return rules, tuple(codes)


def react_once(state: ReactionState, rules: dict[tuple[int, int], tuple[int, int]]) -> ReactionState:
    source = state.active.index(1)
    successor = state.next_nodes[source]
    output = rules[state.values[source], state.values[successor]]
    values, active = list(state.values), list(state.active)
    values[source], values[successor] = output
    active[source], active[successor] = 0, 1
    return ReactionState(state.next_nodes, tuple(values), tuple(active))


def make_episode(key: tuple[int, int], rules: dict[tuple[int, int], tuple[int, int]], codes: tuple[int, ...], knowledge_size: int, seed: int) -> ReactionEpisode:
    rng = random.Random(seed)
    source, successor = rng.sample(range(knowledge_size), 2)
    next_nodes = list(range(knowledge_size))
    next_nodes[source] = successor
    values = [rng.choice(codes) for _ in range(knowledge_size)]
    values[source], values[successor] = key
    active = [0] * knowledge_size
    active[source] = 1
    before = ReactionState(tuple(next_nodes), tuple(values), tuple(active))
    return ReactionEpisode(before, react_once(before, rules))


def make_world(knowledge_size: int, seed: int) -> World:
    rules, codes = make_rules(seed)
    heldout_key = (codes[3], codes[3])
    observed = [(key, output) for key, output in rules.items() if key != heldout_key]
    training = [make_episode(key, rules, codes, knowledge_size, seed ^ (index * 104729)) for index, (key, _) in enumerate(observed, 1)]
    random.Random(seed ^ knowledge_size).shuffle(training)
    update_episode = make_episode(heldout_key, rules, codes, knowledge_size, seed ^ 0xF00D)
    return World(rules, codes, heldout_key, tuple(training), update_episode)


def _simulate(state: ReactionState, rules: dict[tuple[int, int], tuple[int, int]], steps: int) -> ReactionState:
    for _ in range(steps):
        state = react_once(state, rules)
    return state


def make_task(world: World, knowledge_size: int, depth: int, seed: int, index: int, *, update: bool = False) -> ReactionTask:
    if depth + 1 > knowledge_size:
        raise ValueError("reaction path must fit the particle state")
    rng = random.Random(seed ^ (depth << 16) ^ (index * 130363) ^ int(update))
    path = rng.sample(range(knowledge_size), depth + 1)
    next_nodes = list(range(knowledge_size))
    for source, target in zip(path, path[1:]):
        next_nodes[source] = target
    values = [rng.choice(world.codes) for _ in range(knowledge_size)]
    active = [0] * knowledge_size
    active[path[0]] = 1
    carrier = world.heldout_key[0] if update else rng.choice(world.codes)
    values[path[0]] = carrier
    keys = []
    for step in range(depth):
        options = [symbol for symbol in world.codes if update or (carrier, symbol) != world.heldout_key]
        symbol = world.heldout_key[1] if update else rng.choice(options)
        values[path[step + 1]] = symbol
        key = (carrier, symbol)
        keys.append(key)
        carrier = world.rules[key][1]
        update = False
    source = ReactionState(tuple(next_nodes), tuple(values), tuple(active))
    return ReactionTask(source, _simulate(source, world.rules, depth), tuple(keys))


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world = make_world(knowledge_size, seed)
    tasks = tuple(make_task(world, knowledge_size, reasoning_depth, seed, index) for index in range(queries_per_cell))
    candidate = load_candidate(candidate_name, seed)
    fit_data = (world.rules,) if candidate_name == "oracle_reaction_engine" else world.training
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    candidate_rules = getattr(candidate, "rules", {})
    observed = {key: output for key, output in world.rules.items() if key != world.heldout_key}
    observed_rule_accuracy = statistics.fmean(candidate_rules.get(key) == output for key, output in observed.items())

    def measure():
        answers, operations, events, scans, bytes_scanned, convergence, oscillation, latencies = [], [], [], [], [], [], [], []
        for task in tasks:
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(task.source, reasoning_depth))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            operations.append(float(candidate.last_ops))
            events.append(float(candidate.last_active_events))
            scans.append(float(candidate.last_full_scans))
            bytes_scanned.append(float(candidate.last_bytes_scanned))
            convergence.append(float(candidate.last_converged))
            oscillation.append(float(candidate.last_oscillated))
        return answers, operations, events, scans, bytes_scanned, convergence, oscillation, latencies

    answers, operations, events, scans, bytes_scanned, convergence, oscillation, latencies = measure()
    warm_answers, warm_operations, warm_events, _, _, _, _, warm_latencies = measure()
    exact = [answer == task.target for answer, task in zip(answers, tasks)]
    warm_exact = [answer == task.target for answer, task in zip(warm_answers, tasks)]
    training_sources = {episode.before for episode in world.training}
    update_started = time.perf_counter_ns()
    candidate.update(world.update_episode, 0)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    update_task = make_task(world, knowledge_size, 1, seed, queries_per_cell + 1, update=True)
    new_fact = candidate.query(update_task.source, 1) == update_task.target
    retained = candidate.query(tasks[0].source, reasoning_depth) == tasks[0].target
    input_state_bytes = 17 * knowledge_size
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell,
        "accuracy": statistics.fmean(exact), "warm_accuracy": statistics.fmean(warm_exact),
        "heldout_composition_accuracy": statistics.fmean(exact), "observed_rule_accuracy": observed_rule_accuracy,
        "target_not_memorized_rate": statistics.fmean(task.source not in training_sources for task in tasks),
        "continual_new_fact_accuracy": float(new_fact), "continual_retention": float(retained),
        "convergence_rate": statistics.fmean(convergence), "oscillation_rate": statistics.fmean(oscillation),
        "mean_active_events": statistics.fmean(events), "mean_full_scans": statistics.fmean(scans),
        "mean_bytes_scanned": statistics.fmean(bytes_scanned),
        "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops),
        "mean_query_ops": statistics.fmean(operations), "mean_warm_query_ops": statistics.fmean(warm_operations),
        "mean_visited_nodes": statistics.fmean(events), "mean_warm_visited_nodes": statistics.fmean(warm_events),
        "p50_latency_us": percentile(latencies, 0.50), "p95_latency_us": percentile(latencies, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies, 0.50), "warm_p95_latency_us": percentile(warm_latencies, 0.95),
        "update_latency_us": update_latency_us, "update_ops": float(candidate.update_ops),
        "input_state_bytes": float(input_state_bytes),
        "state_bytes": float(max(candidate.state_bytes() + input_state_bytes, traced_peak)),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
