from __future__ import annotations

import math
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile


BENCHMARK_VERSION = "context_specific_probabilistic_circuit_v1"


@dataclass(frozen=True)
class Training:
    samples: tuple[tuple[int, ...], ...]
    variable_count: int


@dataclass(frozen=True)
class OracleTraining:
    public: Training
    selector: int
    matchings: tuple[tuple[tuple[int, int], ...], ...]
    epsilons: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class Query:
    evidence: tuple[tuple[int, int], ...]
    target: int
    signature: int


@dataclass(frozen=True)
class UpdateBatch:
    samples: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class OracleUpdate:
    public: UpdateBatch
    epsilons: tuple[tuple[float, ...], ...]


def _canonical_matchings(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    first = tuple((index, index + 1) for index in range(0, size, 2))
    shifted = tuple((index, (index + 1) % size) for index in range(1, size, 2))
    return first, shifted


def _sample(
    rng: random.Random,
    selector: int,
    matchings: tuple[tuple[tuple[int, int], ...], ...],
    epsilons: tuple[tuple[float, ...], ...],
) -> tuple[int, ...]:
    row = [0] * (1 + 2 * len(matchings[0]))
    context = rng.randrange(2)
    row[selector] = context
    for pair, epsilon in zip(matchings[context], epsilons[context]):
        value = rng.randrange(2)
        row[pair[0]] = value
        row[pair[1]] = value ^ int(rng.random() < epsilon)
    return tuple(row)


def make_world(knowledge_size: int, seed: int) -> OracleTraining:
    rng = random.Random(seed ^ (knowledge_size * 104729))
    observed_to_canonical = list(range(knowledge_size + 1))
    rng.shuffle(observed_to_canonical)
    selector = observed_to_canonical.index(0)
    canonical = _canonical_matchings(knowledge_size)
    matchings = tuple(
        tuple(
            (observed_to_canonical.index(left + 1), observed_to_canonical.index(right + 1))
            for left, right in matching
        )
        for matching in canonical
    )
    epsilons = tuple(tuple(0.1 for _ in matching) for matching in matchings)
    samples = tuple(
        _sample(rng, selector, matchings, epsilons) for _ in range(64 * knowledge_size)
    )
    return OracleTraining(Training(samples, knowledge_size + 1), selector, matchings, epsilons)


def _component_probability(
    evidence: dict[int, int],
    context: int,
    world: OracleTraining,
    epsilons: tuple[tuple[float, ...], ...] | None = None,
) -> float:
    if world.selector in evidence and evidence[world.selector] != context:
        return 0.0
    probability = 0.5
    active = epsilons or world.epsilons
    for (left, right), epsilon in zip(world.matchings[context], active[context]):
        has_left, has_right = left in evidence, right in evidence
        if has_left and has_right:
            probability *= (1.0 - epsilon) / 2.0 if evidence[left] == evidence[right] else epsilon / 2.0
        elif has_left or has_right:
            probability *= 0.5
    return probability


def oracle_probability(
    query: Query,
    world: OracleTraining,
    epsilons: tuple[tuple[float, ...], ...] | None = None,
) -> float:
    evidence = dict(query.evidence)
    denominator = sum(_component_probability(evidence, context, world, epsilons) for context in range(2))
    evidence[query.target] = 1
    numerator = sum(_component_probability(evidence, context, world, epsilons) for context in range(2))
    return numerator / denominator


def joint_probability(row: tuple[int, ...], world: OracleTraining) -> float:
    evidence = dict(enumerate(row))
    return sum(_component_probability(evidence, context, world) for context in range(2))


def _neighbor(target: int, matching: tuple[tuple[int, int], ...]) -> int:
    for left, right in matching:
        if target == left:
            return right
        if target == right:
            return left
    raise ValueError("target absent from matching")


def make_queries(
    world: OracleTraining,
    depth: int,
    seed: int,
    count: int,
    *,
    near: bool = False,
) -> tuple[tuple[Query, float], ...]:
    rng = random.Random(seed ^ (depth * 65537) ^ (0x9E37 if near else 0))
    payload = [index for index in range(world.public.variable_count) if index != world.selector]
    rows = []
    for index in range(count):
        source = world.public.samples[rng.randrange(len(world.public.samples))]
        target = payload[(index * 7 + depth) % len(payload)]
        context = index % 2
        evidence_variables = [_neighbor(target, world.matchings[context])]
        if near and depth > 1:
            other = _neighbor(target, world.matchings[1 - context])
            if other not in evidence_variables:
                evidence_variables.append(other)
        choices = [item for item in payload if item != target and item not in evidence_variables]
        rng.shuffle(choices)
        evidence_variables.extend(choices[: depth - len(evidence_variables)])
        evidence = [(variable, source[variable]) for variable in evidence_variables]
        if not near and index % 2 == 0:
            evidence.append((world.selector, context))
        query = Query(tuple(sorted(evidence)), target, depth * 10000 + int(near) * 1000 + index)
        rows.append((query, oracle_probability(query, world)))
    return tuple(rows)


def make_update(world: OracleTraining, seed: int) -> tuple[OracleUpdate, Query, Query]:
    changed = [list(values) for values in world.epsilons]
    changed[0][0] = 0.25
    epsilons = tuple(tuple(values) for values in changed)
    rng = random.Random(seed ^ 0xADD5EED)
    batch = UpdateBatch(tuple(
        _sample(rng, world.selector, world.matchings, epsilons)
        for _ in range(16 * (world.public.variable_count - 1))
    ))
    changed_pair = world.matchings[0][0]
    retained_pair = world.matchings[1][-1]
    changed_query = Query(((world.selector, 0), (changed_pair[0], 1)), changed_pair[1], 0xADD)
    retained_query = Query(((world.selector, 1), (retained_pair[0], 1)), retained_pair[1], 0xBEEF)
    return OracleUpdate(batch, epsilons), changed_query, retained_query


def _number(candidate: Any, name: str) -> float:
    value = getattr(candidate, name)
    return float(value() if callable(value) else value)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    world = make_world(knowledge_size, seed)
    cold = make_queries(world, reasoning_depth, seed, queries_per_cell)
    near = make_queries(world, reasoning_depth, seed, queries_per_cell, near=True)
    candidate = load_candidate(candidate_name, seed)
    fit_data = world if candidate_name == "oracle_context_spn" else world.public
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    fit_ops = _number(candidate, "fit_ops")

    def measure(tasks: tuple[tuple[Query, float], ...]):
        measured = []
        for query, truth in tasks:
            tick = time.perf_counter_ns()
            prediction = float(candidate.query(query, reasoning_depth))
            latency = (time.perf_counter_ns() - tick) / 1000.0
            if not math.isfinite(prediction) or not 0.0 <= prediction <= 1.0:
                raise ValueError("candidate probability must be finite and in [0, 1]")
            clipped = min(1.0 - 1e-12, max(1e-12, prediction))
            loss = -truth * math.log(clipped) - (1.0 - truth) * math.log(1.0 - clipped)
            measured.append((abs(prediction - truth) <= 0.05, prediction, truth, loss,
                             _number(candidate, "last_ops"),
                             float(getattr(candidate, "last_comparisons", 0)),
                             float(getattr(candidate, "last_bytes_touched", 0)), latency))
        return measured

    cold_rows, warm_rows, near_rows = measure(cold), measure(cold), measure(near)
    update, changed_query, retained_query = make_update(world, seed)
    update_source = update if candidate_name == "oracle_context_spn" else update.public
    tick = time.perf_counter_ns()
    candidate.update(update_source, None)
    update_latency = (time.perf_counter_ns() - tick) / 1000.0
    changed_prediction = float(candidate.query(changed_query, reasoning_depth))
    changed_ops = _number(candidate, "last_ops")
    changed_truth = oracle_probability(changed_query, world, update.epsilons)
    retained_prediction = float(candidate.query(retained_query, reasoning_depth))
    retained_ops = _number(candidate, "last_ops")
    retained_truth = oracle_probability(retained_query, world, update.epsilons)
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0
           for value in (changed_prediction, retained_prediction)):
        raise ValueError("updated candidate probability must be finite and in [0, 1]")
    accuracy = lambda rows: statistics.fmean(float(row[0]) for row in rows)
    mean = lambda rows, at: statistics.fmean(row[at] for row in rows)
    evaluated = cold_rows + near_rows
    query_work = sum(row[4] for row in evaluated)
    after_work = changed_ops + retained_ops
    update_ops = _number(candidate, "update_ops")
    workload = fit_ops + query_work + update_ops + 16 * after_work
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold_rows),
        "warm_accuracy": accuracy(warm_rows), "near_equivalent_accuracy": accuracy(near_rows),
        "continual_new_fact_accuracy": float(abs(changed_prediction - changed_truth) <= 0.05),
        "continual_retention": float(abs(retained_prediction - retained_truth) <= 0.05),
        "conditional_probability_mae": statistics.fmean(
            abs(row[1] - row[2]) for row in evaluated
        ),
        "conditional_log_loss": mean(evaluated, 3),
        "calibration_error": abs(mean(evaluated, 1) - mean(evaluated, 2)),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold_rows, 4), "mean_warm_query_ops": mean(warm_rows, 4),
        "mean_input_ops": statistics.fmean(len(query.evidence) for query, _ in cold),
        "mean_comparisons": mean(cold_rows, 5), "mean_bytes_touched": mean(cold_rows, 6),
        "p50_latency_us": percentile([row[7] for row in cold_rows], 0.5),
        "p95_latency_us": percentile([row[7] for row in cold_rows], 0.95),
        "state_bytes": _number(candidate, "state_bytes"),
        "peak_state_bytes": max(_number(candidate, "state_bytes"), float(fit_peak)),
        "circuit_nodes": _number(candidate, "circuit_nodes"),
        "update_ops": update_ops, "update_latency_us": update_latency,
        "rebuilt_nodes": float(getattr(candidate, "rebuilt_nodes", 0)),
        "workload_ops": workload, "workload_ops_r1": workload,
        "workload_ops_r4": fit_ops + 4 * query_work + update_ops + 16 * after_work,
        "workload_ops_r16": fit_ops + 16 * query_work + update_ops + 16 * after_work,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]),
                      int(seed), max(map(int, matrix["reasoning_depths"])))
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"]]
