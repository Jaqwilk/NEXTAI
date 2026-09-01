from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from typing import Any

from .heldout_mechanism_recombination_v1 import _maps
from .successor_graph_v1 import load_candidate, percentile
from ..operator_experience_contract import (
    LabeledPair, Mutation, Observation, Query, Training, canonical_table, encode,
    input_ops,
)


BENCHMARK_VERSION = "heldout_mechanism_recombination_v4"
STATE_COUNT = 144
EXPOSURES = (1, 4, 16)
PRIMITIVES = ("A", "B", "C")
TRAIN_SEQUENCES = (("A",), ("B",), ("C",), ("A", "B"), ("B", "C"), ("C", "A"))
TEST_SEQUENCE = ("C", "B", "A", "C")
BASELINES = (
    "operator_interpreter", "operator_exact_key_cache",
    "operator_structural_result_cache", "operator_canonical_table_cache",
    "operator_anti_unification_cache", "operator_nearest_canonical",
    "operator_random",
)


def _tables(seed: int, source_seed: int) -> dict[str, tuple[int, ...]]:
    maps = _maps(source_seed, seed)
    return {name: maps[(name,)] for name in PRIMITIVES}


def _term(sequence: tuple[str, ...], tables: dict[str, tuple[int, ...]], seed: int, variant: int):
    return encode(tuple(tables[name] for name in sequence), seed, fuse=bool(variant % 2))


def make_training(size: int, seed: int, source_seed: int) -> Training:
    if seed == source_seed:
        raise ValueError("mechanism-source/scoring seed collision")
    tables = _tables(seed, source_seed)
    pairs, acquisition = [], 0
    for index in range(size):
        sequence = TRAIN_SEQUENCES[index % len(TRAIN_SEQUENCES)]
        left = _term(sequence, tables, seed ^ index, 0)
        equivalent = index % 4 != 3
        other = sequence if equivalent else (*sequence[:-1], PRIMITIVES[(PRIMITIVES.index(sequence[-1]) + 1) % 3])
        right = _term(other, tables, seed ^ index ^ 0xA11CE, 1)
        pairs.append(LabeledPair(left, right, equivalent))
        acquisition += input_ops(left) + input_ops(right) + 1
    return Training(tuple(pairs), acquisition)


def _run_cell(candidate_name: str, size: int, exposures: int, count: int, seed: int,
              source_seed: int, state_budget: int,
              test_sequence: tuple[str, ...] = TEST_SEQUENCE) -> dict[str, Any]:
    if exposures not in EXPOSURES:
        raise ValueError("exposure count must be 1, 4 or 16")
    training = make_training(size, seed, source_seed)
    tables = _tables(seed, source_seed)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, size, max(EXPOSURES))
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if candidate.state_bytes() > state_budget:
        raise ValueError("state budget exceeded")

    exposure_ops, exposure_correct = [], []
    first_query_ops = 0.0
    base_term = _term(test_sequence, tables, seed ^ 0xC0DE, 0)
    for index in range(exposures):
        term = _term(test_sequence, tables, seed ^ 0xC0DE ^ (index + 1) * 7919, index)
        state = (seed + index * 17) % STATE_COUNT
        query = Query(term, state)
        target = canonical_table(term)[0][state]
        answer = int(candidate.query(query, exposures))
        if index == 0:
            first_query_ops = float(candidate.last_ops)
        exposure_ops.append(float(candidate.last_ops))
        exposure_correct.append(answer == target)
        candidate.update(Observation(query, target), None)

    warm_correct, warm_ops, warm_hits, near_correct, false_hits = [], [], [], [], []
    latencies, bytes_touched = [], []
    for index in range(count):
        term = _term(test_sequence, tables, seed ^ 0xBEEF ^ index * 104729, index)
        state = (seed * 3 + index * 19) % STATE_COUNT
        tick = time.perf_counter_ns()
        answer = int(candidate.query(Query(term, state), exposures))
        latencies.append((time.perf_counter_ns() - tick) / 1000.0)
        target = canonical_table(term)[0][state]
        warm_correct.append(answer == target)
        warm_ops.append(float(candidate.last_ops))
        warm_hits.append(float(getattr(candidate, "last_cache_hit", False)))
        bytes_touched.append(float(getattr(candidate, "last_bytes_touched", candidate.last_ops * 8)))

        near_sequence = (*test_sequence[:-1], "B")
        near = _term(near_sequence, tables, seed ^ 0xBAD ^ index * 65537, index)
        near_target = canonical_table(near)[0][state]
        near_answer = int(candidate.query(Query(near, state), exposures))
        near_correct.append(near_answer == near_target)
        false_hits.append(float(getattr(candidate, "last_cache_hit", False) and near_answer != near_target))

    changed = _term((*test_sequence[:-1], "A"), tables, seed ^ 0x5151, 1)
    mutation_state = (seed + 97) % STATE_COUNT
    candidate.update(Mutation(base_term, changed), None)
    update_ops = float(candidate.update_ops)
    new_correct = int(candidate.query(Query(changed, mutation_state), exposures)) == canonical_table(changed)[0][mutation_state]
    retained = int(candidate.query(Query(base_term, mutation_state), exposures)) == canonical_table(base_term)[0][mutation_state]

    fit_ops = float(getattr(candidate, "fit_ops", 0))
    meta_fit_ops = float(getattr(candidate, "meta_fit_ops", fit_ops))
    warm_mean = statistics.fmean(warm_ops)
    base = float(training.acquisition_ops) + fit_ops + sum(exposure_ops) + exposures + update_ops
    workloads = {reuse: base + reuse * warm_mean for reuse in EXPOSURES}
    capability = min(statistics.fmean(warm_correct), statistics.fmean(near_correct), float(new_correct), float(retained))
    return {
        "status": "complete", "world_family": "operator_experience_ood",
        "knowledge_size": size, "reasoning_depth": exposures, "seed": seed,
        "query_count": count, "accuracy": statistics.fmean(exposure_correct),
        "warm_accuracy": statistics.fmean(warm_correct),
        "near_equivalent_accuracy": statistics.fmean(near_correct),
        "false_reuse_rate": statistics.fmean(false_hits),
        "reuse_coverage": statistics.fmean(warm_hits),
        "minimum_combination_accuracy": capability,
        "continual_new_fact_accuracy": float(new_correct),
        "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops, "meta_fit_ops": meta_fit_ops,
        "data_acquisition_ops": float(training.acquisition_ops),
        "fit_peak_bytes": float(fit_peak), "mean_query_ops": first_query_ops,
        "mean_warm_query_ops": warm_mean,
        "mean_input_ops": statistics.fmean(input_ops(_term(test_sequence, tables, seed ^ index, index)) for index in range(count)),
        "mean_bytes_touched": statistics.fmean(bytes_touched),
        "p50_latency_us": percentile(latencies, 0.50),
        "p95_latency_us": percentile(latencies, 0.95),
        "state_bytes": float(candidate.state_bytes()),
        "peak_state_bytes": max(float(candidate.state_bytes()), float(fit_peak)),
        "update_ops": update_ops, "update_latency_us": 0.0,
        "workload_ops": workloads[exposures],
        "workload_ops_r1": workloads[1], "workload_ops_r4": workloads[4],
        "workload_ops_r16": workloads[16],
    }


def static_control_gate(seed: int = 1_501_103, source_seed: int = 1103) -> dict[str, Any]:
    tables = _tables(seed, source_seed)
    first = _term(TEST_SEQUENCE, tables, seed, 0)
    second = _term(TEST_SEQUENCE, tables, seed ^ 0xA11CE, 1)
    near = _term((*TEST_SEQUENCE[:-1], "B"), tables, seed ^ 0xBAD, 1)
    first_key, _ = canonical_table(first)
    second_key, _ = canonical_table(second)
    near_key, _ = canonical_table(near)
    training = make_training(8, seed, source_seed)
    return {
        "raw_reencoding_differs": first != second,
        "positive_canonical_match": first_key == second_key,
        "pair_breaking_changes_operator": first_key != near_key,
        "positive_pairs": sum(pair.equivalent for pair in training.pairs),
        "negative_pairs": sum(not pair.equivalent for pair in training.pairs),
        "train_max_composition_length": max(map(len, TRAIN_SEQUENCES)),
        "test_composition_length": len(TEST_SEQUENCE),
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix, protocol = plan["matrix"], plan["mechanism_recombination_protocol"]
    return [
        _run_cell(candidate_name, int(size), int(exposure), int(matrix["queries_per_cell"]),
                  int(seed), int(protocol["mechanism_source_seed"]),
                  int(protocol["state_budget_bytes"]))
        for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
        for exposure in matrix["reasoning_depths"]
    ]
