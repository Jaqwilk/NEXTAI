from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..temporal_binding_core import Demo, Episode, Event, OracleEpisode, Signature, TimedQuery


BENCHMARK_VERSION = "asynchronous_temporal_binding_v1"
MOTIFS: dict[int, Signature] = {1: (1, 2, 3), 2: (1, 3, 2), 3: (2, 1, 3), 4: (3, 1, 2)}
SUPPORT_PATTERNS = ((1,), (2,), (3,), (4,), (1, 2), (3, 4), (1, 3), (2, 4), (1, 4), (2, 3))
REUSE_SCHEDULE = (1, 4, 16)
UPDATE_SIGNATURES = ((2, 3, 1), (3, 2, 1), (2, 2, 2))


@dataclass(frozen=True)
class World:
    width: int
    active_channel: int


@dataclass(frozen=True)
class Task:
    cold: TimedQuery
    warm: TimedQuery
    near: TimedQuery
    target: tuple[int, ...]
    near_target: tuple[int, ...]


def make_world(width: int, seed: int) -> World:
    return World(width, random.Random(seed ^ width * 65537).randrange(width))


def render(labels: tuple[int, ...], world: World, motifs: dict[int, Signature], seed: int) -> tuple[Event, ...]:
    rng, events, start = random.Random(seed), [], 2 + random.Random(seed ^ 17).randrange(4)
    last_time = start
    for label in labels:
        times = [start]
        for delay in motifs[label]:
            times.append(times[-1] + delay)
        events.extend(Event(value, world.active_channel) for value in times)
        last_time = times[-1]
        start = last_time + 20 + rng.randrange(5)
    horizon = last_time + 5
    for channel in range(world.width):
        if channel == world.active_channel:
            continue
        count = 3 * len(labels)
        for value in rng.sample(range(horizon + 1), count):
            events.append(Event(value, channel))
    return tuple(sorted(events))


def make_episode(world: World, seed: int, motifs: dict[int, Signature] | None = None) -> Episode:
    current = MOTIFS if motifs is None else motifs
    return Episode(tuple(Demo(render(labels, world, current, seed ^ index * 7919), labels)
                         for index, labels in enumerate(SUPPORT_PATTERNS)))


def _labels(depth: int, seed: int, index: int) -> tuple[int, ...]:
    rng = random.Random(seed ^ depth * 8191 ^ index * 104729)
    while True:
        labels = tuple(1 + rng.randrange(4) for _ in range(depth))
        if depth == 1 or (labels not in SUPPORT_PATTERNS and all(a != b for a, b in zip(labels, labels[1:]))):
            return labels


def make_tasks(world: World, depth: int, seed: int, count: int,
               motifs: dict[int, Signature] | None = None) -> tuple[Task, ...]:
    current, tasks = (MOTIFS if motifs is None else motifs), []
    for index in range(count):
        labels = _labels(depth, seed, index)
        changed = list(labels)
        changed[index % depth] = changed[index % depth] % 4 + 1
        near_labels = tuple(changed)
        tasks.append(Task(
            TimedQuery(render(labels, world, current, seed ^ index ^ 0xC01D)),
            TimedQuery(render(labels, world, current, seed ^ index ^ 0xA11CE)),
            TimedQuery(render(near_labels, world, current, seed ^ index ^ 0xBAD)),
            labels,
            near_labels,
        ))
    return tuple(tasks)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world, motifs = make_world(knowledge_size, seed), dict(MOTIFS)
    episode = make_episode(world, seed, motifs)
    tasks = make_tasks(world, reasoning_depth, seed, queries_per_cell, motifs)
    candidate = load_candidate(candidate_name, seed)

    def wrapped(current: Episode, dictionary: dict[int, Signature]):
        return OracleEpisode(current, world.active_channel, tuple(sorted(dictionary.items()))) if candidate_name == "oracle_temporal_binder" else current

    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(wrapped(episode, motifs), knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    initial_fit_ops, peak_state = float(candidate.fit_ops), candidate.state_bytes()

    def measure(field: str, target_field: str):
        nonlocal peak_state
        rows = []
        for task in tasks:
            query, target = getattr(task, field), getattr(task, target_field)
            tick = time.perf_counter_ns()
            answer = candidate.query(query, reasoning_depth)
            horizon = query.events[-1].time + 1
            rows.append({
                "correct": answer == target, "latency": (time.perf_counter_ns() - tick) / 1000,
                "ops": candidate.last_ops, "input": candidate.last_input_ops, "search": candidate.last_search_ops,
                "execution": candidate.last_execution_ops, "reads": candidate.last_memory_reads,
                "bytes": candidate.last_bytes_loaded, "hit": float(candidate.last_cache_hit),
                "events": len(query.events), "horizon": horizon, "idle": horizon - len({e.time for e in query.events}),
            })
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold, warm, near = measure("cold", "target"), measure("warm", "target"), measure("near", "near_target")
    retained_query = TimedQuery(render((4,) * reasoning_depth, world, motifs, seed ^ 0x5151))
    retained_target = (4,) * reasoning_depth
    updates, update_latencies, new_correct, retained, workloads = [], [], [], [], {}
    for stage, reuses in enumerate(REUSE_SCHEDULE):
        motifs[1] = UPDATE_SIGNATURES[stage]
        local = Episode((Demo(render((1,), world, motifs, seed ^ stage ^ 0xBEEF), (1,)),))
        tick = time.perf_counter_ns()
        candidate.update(wrapped(local, motifs), None)
        update_latencies.append((time.perf_counter_ns() - tick) / 1000)
        updates.append(float(candidate.update_ops))
        changed = TimedQuery(render((1,) * reasoning_depth, world, motifs, seed ^ stage ^ 0xCAFE))
        stage_ops, correctness = float(candidate.update_ops), []
        for _ in range(reuses):
            correctness.append(candidate.query(changed, reasoning_depth) == (1,) * reasoning_depth)
            stage_ops += candidate.last_ops
        new_correct.append(all(correctness))
        retained.append(candidate.query(retained_query, reasoning_depth) == retained_target)
        stage_ops += candidate.last_ops
        workloads[reuses] = stage_ops
        peak_state = max(peak_state, candidate.state_bytes())

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    accuracy = lambda rows: statistics.fmean(float(row["correct"]) for row in rows)
    reuse_rows, hits = warm + near, sum(row["hit"] for row in warm + near)
    correct_hits = sum(row["hit"] * row["correct"] for row in reuse_rows)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "reuse_precision": correct_hits / hits if hits else 0.0, "reuse_coverage": hits / len(reuse_rows),
        "false_reuse_rate": (hits - correct_hits) / hits if hits else 0.0,
        "continual_new_fact_accuracy": statistics.fmean(new_correct), "continual_retention": statistics.fmean(retained),
        "fit_seconds": fit_seconds, "fit_ops": initial_fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_input_ops": mean(cold, "input"), "mean_alignment_ops": mean(cold, "search"),
        "mean_execution_ops": mean(cold, "execution"), "mean_memory_reads": mean(cold, "reads"),
        "mean_bytes_loaded": mean(cold, "bytes"), "p50_latency_us": percentile([r["latency"] for r in cold], 0.5),
        "p95_latency_us": percentile([r["latency"] for r in cold], 0.95),
        "warm_p50_latency_us": percentile([r["latency"] for r in warm], 0.5),
        "warm_p95_latency_us": percentile([r["latency"] for r in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(peak_state, fit_peak)),
        "update_ops": statistics.fmean(updates), "cumulative_update_ops": sum(updates),
        "mean_invalidated_entries": 1.0, "workload_ops_r1": workloads[1], "workload_ops_r4": workloads[4],
        "workload_ops_r16": workloads[16], "workload_ops": initial_fit_ops + sum(workloads.values()),
        "update_latency_us": statistics.fmean(update_latencies), "mean_delivered_events": mean(cold, "events"),
        "mean_event_horizon": mean(cold, "horizon"), "mean_idle_ticks": mean(cold, "idle"),
        "relevant_channels": 1.0, "heldout_composition_rate": float(reasoning_depth > 1),
        "timing_jitter": 0.0, "pretokenized_addresses": 1.0,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
