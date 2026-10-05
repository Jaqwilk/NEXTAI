from __future__ import annotations

import math
import random
import statistics
import time
import tracemalloc
from typing import Any

from .cross_family_shared_representation_v1 import (
    FAMILIES, SALTS, Case, _answer, _build_worlds, _number,
)
from .successor_graph_v1 import load_candidate, percentile
from ..cross_family_transfer_v2_contract import (
    Example, NativeWorld, PrivilegedQuery, PrivilegedTraining, PrivilegedUpdate,
    PublicQuery, PublicTraining, PublicUpdate, TestWorld, TrainingWorld, encode,
)


BENCHMARK_VERSION = "cross_family_shared_representation_v2"
PRIVILEGED = {
    "specialist_contextual_chow_liu_suite_v2",
    "specialist_empirical_joint_suite_v2",
    "specialist_autoregressive_suite_v2",
    "oracle_cross_family_suite_v2",
}


def _derived_seeds(seed: int) -> set[int]:
    return {seed ^ SALTS[family] for family in FAMILIES}


def _training(size: int, depth: int, count: int, score_seed: int,
              training_seeds: tuple[int, ...]):
    test_seeds = _derived_seeds(score_seed)
    train_seeds = set().union(*(_derived_seeds(seed) for seed in training_seeds))
    if test_seeds & train_seeds:
        raise ValueError("derived training/test seed collision")

    acquisition = 0
    training_worlds = []
    for seed in training_seeds:
        for world in _build_worlds(size, depth, min(count, 4), seed):
            support, ops = encode(world.public_fit)
            acquisition += ops
            examples = []
            for native, target, _, _ in world.cold:
                query, query_ops = encode(native)
                acquisition += query_ops + len(target)
                examples.append(Example(query, target))
            training_worlds.append(TrainingWorld(support, tuple(examples)))

    test = _build_worlds(size, depth, count, score_seed)
    slots = random.Random(score_seed ^ size ^ (depth << 8)).sample(
        range(100, 10_000), len(test)
    )
    public_test, native_test = [], []
    cold: dict[str, tuple[Case, ...]] = {}
    near: dict[str, tuple[Case, ...]] = {}
    for slot, world in zip(slots, test):
        support, ops = encode(world.public_fit)
        acquisition += ops
        public_test.append(TestWorld(slot, support))
        native_test.append(NativeWorld(slot, world.family, world.public_fit, world.oracle_fit))
        for destination, source in ((cold, world.cold), (near, world.near)):
            cases = []
            for native, target, correct, truth in source:
                tokens, query_ops = encode(native)
                acquisition += query_ops
                cases.append(Case(world.family, PublicQuery(slot, tokens), native,
                                  target, correct, truth))
            destination[world.family] = tuple(cases)
    public = PublicTraining(tuple(training_worlds), tuple(public_test), acquisition)
    return public, PrivilegedTraining(public, tuple(native_test)), cold, near


def _run_cell(candidate_name: str, size: int, depth: int, count: int, seed: int,
              training_seeds: tuple[int, ...], max_depth: int,
              state_budget: int) -> list[dict[str, Any]]:
    public, privileged, cold, near = _training(
        size, depth, count, seed, training_seeds
    )
    candidate = load_candidate(candidate_name, seed)
    fit_data = privileged if candidate_name in PRIVILEGED else public
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    state = _number(candidate, "state_bytes")
    if state > state_budget:
        raise ValueError(f"state budget exceeded: {state} > {state_budget}")

    observations: dict[str, dict[str, Any]] = {}
    total_query_ops = 0.0
    for family in FAMILIES:
        observations[family] = {"cold": [], "near": [], "latency": [], "bytes": []}
        for label, cases in (("cold", cold[family]), ("near", near[family])):
            for case in cases:
                source = PrivilegedQuery(case.public, family, case.native) \
                    if candidate_name in PRIVILEGED else case.public
                tick = time.perf_counter_ns()
                answer = _answer(candidate.query(source, depth))
                latency = (time.perf_counter_ns() - tick) / 1000.0
                ops = _number(candidate, "last_ops")
                total_query_ops += ops
                observations[family][label].append((case.correct(answer), answer, case))
                observations[family]["latency"].append(latency)
                observations[family]["bytes"].append(
                    _number(candidate, "last_bytes_touched", ops * 8)
                )

    retained, acquired, after_ops = {}, {}, 0.0
    for family in FAMILIES:
        revealed = cold[family][-1]
        update = PublicUpdate(revealed.public, revealed.target)
        source = PrivilegedUpdate(update, family, revealed.native) \
            if candidate_name in PRIVILEGED else update
        candidate.update(source, None)
        query_source = PrivilegedQuery(revealed.public, family, revealed.native) \
            if candidate_name in PRIVILEGED else revealed.public
        acquired[family] = revealed.correct(_answer(candidate.query(query_source, depth)))
        after_ops += _number(candidate, "last_ops")
        old = cold[family][0]
        old_source = PrivilegedQuery(old.public, family, old.native) \
            if candidate_name in PRIVILEGED else old.public
        retained[family] = old.correct(_answer(candidate.query(old_source, depth)))
        after_ops += _number(candidate, "last_ops")

    fit_ops = _number(candidate, "fit_ops")
    meta_fit_ops = _number(candidate, "meta_fit_ops", fit_ops)
    update_ops = _number(candidate, "update_ops")
    base = public.acquisition_ops + fit_ops + update_ops + after_ops
    workloads = {horizon: base + horizon * total_query_ops for horizon in (1, 4, 16)}
    rows = []
    for family in FAMILIES:
        cold_rows = observations[family]["cold"]
        near_rows = observations[family]["near"]
        probabilities = [(row[1][0], row[2].probability)
                         for row in cold_rows + near_rows
                         if row[2].probability is not None]
        clipped = [(min(1 - 1e-12, max(1e-12, prediction)), truth)
                   for prediction, truth in probabilities]
        rows.append({
            "status": "complete", "world_family": family,
            "knowledge_size": size, "reasoning_depth": depth, "seed": seed,
            "query_count": count,
            "accuracy": statistics.fmean(row[0] for row in cold_rows),
            "warm_accuracy": statistics.fmean(row[0] for row in cold_rows),
            "near_equivalent_accuracy": statistics.fmean(row[0] for row in near_rows),
            "continual_new_fact_accuracy": float(acquired[family]),
            "continual_retention": float(retained[family]),
            "conditional_probability_mae": statistics.fmean(
                abs(prediction - truth) for prediction, truth in probabilities
            ) if probabilities else None,
            "conditional_log_loss": statistics.fmean(
                -truth * math.log(prediction) - (1 - truth) * math.log(1 - prediction)
                for prediction, truth in clipped
            ) if clipped else None,
            "calibration_error": abs(
                statistics.fmean(prediction for prediction, _ in probabilities)
                - statistics.fmean(truth for _, truth in probabilities)
            ) if probabilities else None,
            "fit_seconds": fit_seconds, "fit_ops": fit_ops,
            "meta_fit_ops": meta_fit_ops,
            "data_acquisition_ops": float(public.acquisition_ops),
            "fit_peak_bytes": float(fit_peak),
            "mean_query_ops": total_query_ops / (2 * count * len(FAMILIES)),
            "mean_warm_query_ops": total_query_ops / (2 * count * len(FAMILIES)),
            "mean_input_ops": statistics.fmean(
                len(case.public.tokens) for case in cold[family] + near[family]
            ),
            "mean_bytes_touched": statistics.fmean(observations[family]["bytes"]),
            "p50_latency_us": percentile(observations[family]["latency"], 0.5),
            "p95_latency_us": percentile(observations[family]["latency"], 0.95),
            "state_bytes": state, "peak_state_bytes": max(state, float(fit_peak)),
            "update_ops": update_ops, "update_latency_us": 0.0,
            "workload_ops": workloads[1], "workload_ops_r1": workloads[1],
            "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
        })
    return rows


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    protocol = plan["transfer_protocol"]
    training_seeds = tuple(map(int, protocol["training_world_seeds"]))
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [row for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"]
            for row in _run_cell(candidate_name, int(size), int(depth),
                                 int(matrix["queries_per_cell"]), int(seed),
                                 training_seeds, maximum,
                                 int(protocol["state_budget_bytes"]))]
