from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..byte_motif_core import ByteQuery, Demo, Episode, OracleEpisode


BENCHMARK_VERSION = "raw_byte_motif_composition_v1"
REUSE_SCHEDULE = (1, 4, 16)
SUPPORT_PATTERNS = (
    (1, 2), (3, 4), (1, 3), (2, 4), (1, 4), (2, 3),
    (1, 2, 3), (2, 3, 4), (4, 1, 2), (3, 4, 1), (2, 1, 4), (3, 2, 1),
    (1, 2, 4, 3), (4, 3, 2, 1), (2, 4, 1, 3), (3, 1, 4, 2),
)


@dataclass(frozen=True)
class Task:
    cold: ByteQuery
    warm: ByteQuery
    near: ByteQuery
    target: tuple[int, ...]
    near_target: tuple[int, ...]


def make_motifs(seed: int) -> dict[int, tuple[int, ...]]:
    rng = random.Random(seed)
    shared = (10 + rng.randrange(10), 30 + rng.randrange(10))
    motifs: dict[int, tuple[int, ...]] = {}
    used_trigrams: set[tuple[int, ...]] = set()
    for label, length in enumerate((4, 5, 6, 7), start=1):
        while True:
            body = tuple(rng.sample(range(50, 128), length - 2))
            motif = shared + body
            trigrams = {motif[i : i + 3] for i in range(len(motif) - 2)}
            if not trigrams & used_trigrams and all(motif not in old and old not in motif for old in motifs.values()):
                motifs[label] = motif
                used_trigrams |= trigrams
                break
    return motifs


def _render(labels: tuple[int, ...], motifs: dict[int, tuple[int, ...]], seed: int) -> tuple[int, ...]:
    rng, raw = random.Random(seed), []
    raw.extend(rng.sample(range(200, 240), 1 + rng.randrange(2)))
    for label in labels:
        raw.extend(motifs[label])
        raw.extend(rng.sample(range(200, 240), 1 + rng.randrange(2)))
    return tuple(raw)


def make_episode(size: int, seed: int, motifs: dict[int, tuple[int, ...]]) -> Episode:
    supports = tuple(Demo(_render(labels, motifs, seed ^ (index + 1) * 7919), labels)
                     for index, labels in enumerate(SUPPORT_PATTERNS))
    distractors = []
    for index in range(size):
        rng = random.Random(seed ^ 0xD157 ^ index * 104729)
        pair = (128 + rng.randrange(36), 164 + rng.randrange(36))
        distractors.append(tuple(pair[i % 2] if i < 24 else 128 + rng.randrange(72) for i in range(40)))
    return Episode(supports, tuple(distractors))


def _heldout_labels(depth: int, seed: int, index: int) -> tuple[int, ...]:
    rng = random.Random(seed ^ depth * 65537 ^ index * 104729)
    while True:
        labels = tuple(1 + rng.randrange(4) for _ in range(depth))
        if labels not in SUPPORT_PATTERNS and all(left != right for left, right in zip(labels, labels[1:])):
            return labels


def make_tasks(depth: int, seed: int, count: int, motifs: dict[int, tuple[int, ...]]) -> tuple[Task, ...]:
    tasks = []
    for index in range(count):
        labels = _heldout_labels(depth, seed, index)
        position = index % depth
        changed = list(labels)
        changed[position] = changed[position] % 4 + 1
        near_labels = tuple(changed)
        tasks.append(Task(
            ByteQuery(_render(labels, motifs, seed ^ index ^ 0xC01D)),
            ByteQuery(_render(labels, motifs, seed ^ index ^ 0xA11CE)),
            ByteQuery(_render(near_labels, motifs, seed ^ index ^ 0xBAD)),
            labels,
            near_labels,
        ))
    return tuple(tasks)


def _variant_motif(seed: int, label: int, current: dict[int, tuple[int, ...]]) -> tuple[int, ...]:
    rng, length = random.Random(seed ^ label * 8191), len(current[label])
    while True:
        motif = tuple(rng.sample(range(20, 128), length))
        if all(motif not in old and old not in motif for key, old in current.items() if key != label):
            return motif


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    motifs = make_motifs(seed)
    episode = make_episode(knowledge_size, seed, motifs)
    tasks = make_tasks(reasoning_depth, seed, queries_per_cell, motifs)
    candidate = load_candidate(candidate_name, seed)

    def wrapped(current: Episode, dictionary: dict[int, tuple[int, ...]]):
        return OracleEpisode(current, tuple(sorted(dictionary.items()))) if candidate_name == "oracle_motif_composer" else current

    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(wrapped(episode, motifs), knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    initial_fit_ops = float(candidate.fit_ops)
    peak_state = candidate.state_bytes()

    def measure(field: str, target_field: str):
        nonlocal peak_state
        rows = []
        for task in tasks:
            query, target = getattr(task, field), getattr(task, target_field)
            tick = time.perf_counter_ns()
            answer = candidate.query(query, reasoning_depth)
            rows.append({
                "answer": answer, "target": target, "latency": (time.perf_counter_ns() - tick) / 1000.0,
                "ops": candidate.last_ops, "input": candidate.last_input_ops,
                "search": candidate.last_search_ops, "execution": candidate.last_execution_ops,
                "reads": candidate.last_memory_reads, "bytes": candidate.last_bytes_loaded,
                "hit": float(candidate.last_cache_hit),
            })
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold = measure("cold", "target")
    warm = measure("warm", "target")
    near = measure("near", "near_target")
    retained_query = ByteQuery(_render((4,) * reasoning_depth, motifs, seed ^ 0x5151))
    retained_target = (4,) * reasoning_depth
    update_ops, invalidated, new_correct, retained, workloads = [], [], [], [], {}
    current_motifs = dict(motifs)
    for stage, reuses in enumerate(REUSE_SCHEDULE):
        label = stage + 1
        current_motifs[label] = _variant_motif(seed ^ stage * 17, label, current_motifs)
        updated = make_episode(knowledge_size, seed ^ stage ^ 0xBEEF, current_motifs)
        tick = time.perf_counter_ns()
        candidate.update(wrapped(updated, current_motifs), None)
        update_latency = (time.perf_counter_ns() - tick) / 1000.0
        update_ops.append(float(candidate.update_ops))
        invalidated.append(float(len(updated.supports)))
        labels = tuple(label if i == 0 else 4 for i in range(reasoning_depth))
        changed = ByteQuery(_render(labels, current_motifs, seed ^ stage ^ 0xCAFE))
        stage_ops, correct = float(candidate.update_ops), []
        for _ in range(reuses):
            correct.append(candidate.query(changed, reasoning_depth) == labels)
            stage_ops += candidate.last_ops
            peak_state = max(peak_state, candidate.state_bytes())
        new_correct.append(all(correct))
        retained.append(candidate.query(retained_query, reasoning_depth) == retained_target)
        stage_ops += candidate.last_ops
        workloads[reuses] = stage_ops
        peak_state = max(peak_state, candidate.state_bytes())

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    accuracy = lambda rows: statistics.fmean(float(row["answer"] == row["target"]) for row in rows)
    reuse_rows = warm + near
    hits = sum(row["hit"] for row in reuse_rows)
    correct_hits = sum(row["hit"] * float(row["answer"] == row["target"]) for row in reuse_rows)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "reuse_precision": correct_hits / hits if hits else 0.0,
        "reuse_coverage": hits / len(reuse_rows),
        "false_reuse_rate": (hits - correct_hits) / hits if hits else 0.0,
        "continual_new_fact_accuracy": statistics.fmean(new_correct),
        "continual_retention": statistics.fmean(retained),
        "fit_seconds": fit_seconds, "fit_ops": initial_fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_input_ops": mean(cold, "input"), "mean_alignment_ops": mean(cold, "search"),
        "mean_execution_ops": mean(cold, "execution"), "mean_memory_reads": mean(cold, "reads"),
        "mean_bytes_loaded": mean(cold, "bytes"),
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.50),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.50),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(peak_state),
        "update_ops": statistics.fmean(update_ops), "cumulative_update_ops": sum(update_ops),
        "mean_invalidated_entries": statistics.fmean(invalidated),
        "workload_ops_r1": workloads[1], "workload_ops_r4": workloads[4],
        "workload_ops_r16": workloads[16], "workload_ops": initial_fit_ops + sum(workloads.values()),
        "update_latency_us": update_latency, "distractor_bytes": float(sum(map(len, episode.distractors))),
        "support_examples": float(len(episode.supports)), "support_singleton_rate": 0.0,
        "boundary_supervision_rate": 0.0, "heldout_composition_rate": 1.0,
        "motif_lengths_min": float(min(map(len, motifs.values()))),
        "motif_lengths_max": float(max(map(len, motifs.values()))),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
