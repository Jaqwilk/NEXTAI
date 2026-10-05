from __future__ import annotations

import math
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

import numpy as np

from .successor_graph_v1 import load_candidate, percentile
from ..online_update_contract import (
    LabeledObservation, MetaStream, OnlineObservation, OnlineTraining,
    PrivilegedObservation, PrivilegedTraining,
)


BENCHMARK_VERSION = "nonstationary_online_update_battery_v1"
MECHANISMS = ("mixed_linear", "mixed_quadratic", "mixed_periodic")
PHASES = (("stable", 0), ("switch", 1), ("recurrence", 0), ("distractor", 2), ("recovery", 0))
SALTS = (0xA11, 0xB22, 0xC33)
PRIVILEGED = {"oracle_segmented_online"}


@dataclass(frozen=True)
class Stream:
    mechanism: str
    slot: int
    sequence: tuple[LabeledObservation, ...]
    phase_by_index: tuple[str, ...]
    parameters: tuple[tuple[tuple[float, ...], tuple[float, ...]], ...]


def _unit(rng: np.random.Generator, width: int) -> np.ndarray:
    value = rng.normal(size=width)
    return value / np.linalg.norm(value)


def _parameters(width: int, seed: int):
    rng = np.random.default_rng(seed)
    mixing, _ = np.linalg.qr(rng.normal(size=(width, width)))
    return tuple((tuple(map(float, mixing @ _unit(rng, width))),
                  tuple(map(float, mixing @ _unit(rng, width)))) for _ in range(3))


def _target(mechanism: str, values: tuple[float, ...], first: tuple[float, ...], second: tuple[float, ...]) -> float:
    x, a, b = np.asarray(values), np.asarray(first), np.asarray(second)
    projection = float(x @ a)
    if mechanism == "mixed_linear":
        return projection
    if mechanism == "mixed_quadratic":
        return projection * float(x @ b)
    return math.sin(projection)


def make_stream(mechanism: str, width: int, depth: int, count: int, seed: int, slot: int) -> Stream:
    if mechanism not in MECHANISMS:
        raise ValueError("unknown stream mechanism")
    rng = np.random.default_rng(seed)
    parameters = _parameters(width, seed ^ 0x51A7E)
    sequence, names = [], []
    base = count + 2 * depth
    for phase_index, (phase, regime) in enumerate(PHASES):
        jitter = int(rng.integers(-max(1, base // 5), max(2, base // 5 + 1)))
        length = max(6, base + jitter)
        first, second = parameters[regime]
        for _ in range(length):
            values = tuple(map(float, rng.normal(size=width)))
            observation = OnlineObservation(slot, values)
            sequence.append(LabeledObservation(observation, _target(mechanism, values, first, second)))
            names.append(phase)
    return Stream(mechanism, slot, tuple(sequence), tuple(names), parameters)


def _training(width: int, depth: int, count: int, seeds: tuple[int, ...]) -> OnlineTraining:
    streams, acquisition = [], 0
    for seed_index, seed in enumerate(seeds):
        slots = random.Random(seed ^ width ^ (depth << 7)).sample(
            range(10_000, 99_999), len(MECHANISMS)
        )
        for mechanism_index, (mechanism, slot) in enumerate(zip(MECHANISMS, slots)):
            stream = make_stream(mechanism, width, depth, count, seed ^ SALTS[mechanism_index], slot)
            streams.append(MetaStream(slot, stream.sequence))
            acquisition += len(stream.sequence) * (width + 1)
    return OnlineTraining(tuple(streams), acquisition)


def _test_streams(width: int, depth: int, count: int, seed: int) -> tuple[Stream, ...]:
    slots = random.Random(seed ^ width ^ (depth << 9)).sample(range(100, 9_999), len(MECHANISMS))
    return tuple(make_stream(mechanism, width, depth, count, seed ^ salt, slot)
                 for mechanism, salt, slot in zip(MECHANISMS, SALTS, slots))


def _answer(value: Any) -> float:
    if isinstance(value, (tuple, list)):
        if not value:
            raise ValueError("empty online prediction")
        value = value[0]
    answer = float(value)
    if not math.isfinite(answer):
        raise ValueError("online prediction must be finite")
    return answer


def _score(predictions: list[float], targets: list[float]) -> float:
    residual = sum((prediction - target) ** 2 for prediction, target in zip(predictions, targets))
    scale = sum(target ** 2 for target in targets) + 1e-12
    return max(0.0, 1.0 - residual / scale)


def _number(candidate: Any, name: str, default: float = 0.0) -> float:
    value = getattr(candidate, name, default)
    return float(value() if callable(value) else value)


def _run_trial(candidate_name: str, width: int, depth: int, count: int, seed: int,
               training_seeds: tuple[int, ...], max_depth: int, state_limit: int) -> list[dict[str, Any]]:
    if seed in training_seeds:
        raise ValueError("training/test seed collision")
    training = _training(width, max_depth, count, training_seeds)
    streams = _test_streams(width, depth, count, seed)
    candidate = load_candidate(candidate_name, seed)
    fit_data = PrivilegedTraining(training) if candidate_name in PRIVILEGED else training
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, width, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if candidate_name not in PRIVILEGED and _number(candidate, "state_bytes") > state_limit:
        raise ValueError("candidate exceeds preregistered resident-state budget")

    rows, total_query_ops, total_update_ops, peak_state = [], 0.0, 0.0, _number(candidate, "state_bytes")
    total_query_bytes = total_update_bytes = 0.0
    total_steps = sum(len(item.sequence) for item in streams)
    for stream in streams:
        predictions: dict[str, list[float]] = {name: [] for name, _ in PHASES}
        targets: dict[str, list[float]] = {name: [] for name, _ in PHASES}
        query_latencies, update_latencies = [], []
        for item, phase in zip(stream.sequence, stream.phase_by_index):
            source: Any = item.observation
            if candidate_name in PRIVILEGED:
                regime = dict(PHASES)[phase]
                first, second = stream.parameters[regime]
                source = PrivilegedObservation(item.observation, stream.mechanism, first, second)
            tick = time.perf_counter_ns()
            prediction = _answer(candidate.query(source, 1))
            query_latencies.append((time.perf_counter_ns() - tick) / 1000.0)
            predictions[phase].append(prediction)
            targets[phase].append(item.target)
            total_query_ops += _number(candidate, "last_ops")
            total_query_bytes += _number(candidate, "last_bytes_touched", _number(candidate, "last_ops") * 8)
            tick = time.perf_counter_ns()
            candidate.update(item.observation, item.target)
            update_latencies.append((time.perf_counter_ns() - tick) / 1000.0)
            total_update_ops += _number(candidate, "update_ops")
            total_update_bytes += _number(candidate, "last_update_bytes", _number(candidate, "update_ops") * 8)
            peak_state = max(peak_state, _number(candidate, "state_bytes"))
            if candidate_name not in PRIVILEGED and peak_state > state_limit:
                raise ValueError("candidate exceeds preregistered resident-state budget")
        phase_scores = {phase: _score(predictions[phase], targets[phase]) for phase, _ in PHASES}
        all_predictions = [value for phase, _ in PHASES for value in predictions[phase]]
        all_targets = [value for phase, _ in PHASES for value in targets[phase]]
        mse = statistics.fmean((prediction - target) ** 2 for prediction, target in zip(all_predictions, all_targets))
        recovery_window = max(2, min(depth + 2, len(predictions["switch"])))
        recovery = statistics.fmean((
            _score(predictions["switch"][:recovery_window], targets["switch"][:recovery_window]),
            _score(predictions["recovery"][:recovery_window], targets["recovery"][:recovery_window]),
        ))
        rows.append({
            "status": "complete", "world_family": stream.mechanism,
            "knowledge_size": width, "reasoning_depth": depth, "seed": seed,
            "query_count": len(stream.sequence), "accuracy": _score(all_predictions, all_targets),
            "warm_accuracy": phase_scores["recovery"],
            "near_equivalent_accuracy": min(phase_scores.values()),
            "continual_new_fact_accuracy": phase_scores["switch"],
            "continual_retention": phase_scores["recurrence"],
            "prequential_loss": mse, "worst_phase_accuracy": min(phase_scores.values()),
            "post_switch_recovery": recovery,
            "recurrence_retention": phase_scores["recurrence"],
            "distractor_interference": max(0.0, phase_scores["recurrence"] - phase_scores["recovery"]),
            "fit_seconds": fit_seconds, "fit_ops": _number(candidate, "fit_ops"),
            "meta_fit_ops": _number(candidate, "meta_fit_ops", _number(candidate, "fit_ops")),
            "data_acquisition_ops": float(training.acquisition_ops + sum(len(item.sequence) * (width + 1) for item in streams)),
            "fit_peak_bytes": float(fit_peak),
            "mean_query_ops": 0.0, "mean_warm_query_ops": 0.0,
            "mean_input_ops": float(width),
            "mean_bytes_touched": 0.0,
            "p50_latency_us": percentile(query_latencies, 0.5), "p95_latency_us": percentile(query_latencies, 0.95),
            "state_bytes": _number(candidate, "state_bytes"), "peak_state_bytes": max(float(fit_peak), peak_state),
            "update_ops": 0.0,
            "update_latency_us": statistics.fmean(update_latencies),
        })
    fit_ops = _number(candidate, "fit_ops")
    acquisition = rows[0]["data_acquisition_ops"]
    base = acquisition + fit_ops + total_update_ops
    for row in rows:
        row["mean_query_ops"] = row["mean_warm_query_ops"] = total_query_ops / total_steps
        row["mean_bytes_touched"] = (total_query_bytes + total_update_bytes) / (2 * total_steps)
        row["update_ops"] = total_update_ops / total_steps
        row["workload_ops_r1"] = base + total_query_ops
        row["workload_ops_r4"] = base + 4 * total_query_ops
        row["workload_ops_r16"] = base + 16 * total_query_ops
        row["workload_ops"] = row["workload_ops_r1"]
    return rows


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix, protocol = plan["matrix"], plan["online_update_protocol"]
    training_seeds = tuple(map(int, protocol["training_stream_seeds"]))
    state_limit = (int(protocol["state_budget_bytes_per_slot"]) * len(MECHANISMS)
                   + int(protocol["shared_state_budget_bytes"]))
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [row for seed in matrix["seeds"] for width in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"] for row in _run_trial(
                candidate_name, int(width), int(depth), int(matrix["queries_per_cell"]),
                int(seed), training_seeds, maximum, state_limit)]
