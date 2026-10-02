from __future__ import annotations

import importlib
import math
import random
import statistics
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from . import continuous_event_predictive_state_v1 as event
from .heldout_dronepropa_factor_recombination_v1 import (
    ARCHIVE_BYTES, EXTRACTED_BYTES, _corpus_rows, _load_flights,
)
from .successor_graph_v1 import percentile
from ..three_family_tensor_contract import (
    Training, World, fit_normalizer, masked_mse, pad,
)
from ..utils import load_json, project_root, sha256_file


BENCHMARK_VERSION = "heldout_three_family_continuous_transfer_v1"
FAMILIES = ("ncmapss_ds08a", "dronepropa", "continuous_event")
TRAIN_UNITS = (1, 2, 3, 4, 5, 10, 11, 12, 13)
TEST_UNITS = (6, 7, 8, 9, 14, 15)
DS_SEGMENTS = {
    1: ("dev", 30606, 36283), 2: ("dev", 367885, 388179),
    3: ("dev", 1099059, 1104736), 4: ("dev", 1539854, 1552149),
    5: ("dev", 2117683, 2129978), 6: ("dev", 2674498, 2694018),
    7: ("dev", 3519837, 3532087), 8: ("dev", 3911368, 3923618),
    9: ("dev", 4515352, 4521029), 10: ("test", 58449, 64126),
    11: ("test", 495752, 508194), 12: ("test", 1127275, 1147120),
    13: ("test", 2454742, 2475036), 14: ("test", 3294444, 3314738),
    15: ("test", 3480802, 3486479),
}
ROLE = {
    "shared_tensor_dynamics_v1": "shared",
    "independent_tensor_dynamics_v1": "independent",
    "cross_family_only_tensor_dynamics_v1": "cross_family_only",
    "support_only_tensor_dynamics_v1": "support_only",
    "tensor_persistence_v1": "shared",
    "tensor_ridge_arx_v1": "shared",
    "tensor_rls_arx_v1": "shared",
    "tensor_empirical_gaussian_joint_v1": "shared",
    "tensor_contextual_gaussian_chow_liu_v1": "shared",
    "tensor_autoregressive_v1": "shared",
    "privileged_tensor_support_v1": "privileged",
    "tensor_raw_window_local_linear_v1": "shared",
    "tensor_random_projection_hash_v1": "shared",
    "shared_predictive_index_v1": "shared",
    "independent_predictive_index_v1": "independent",
    "cross_family_only_predictive_index_v1": "cross_family_only",
    "support_only_predictive_index_v1": "support_only",
    "shared_bounded_recurrent_residual_v1": "shared",
    "independent_bounded_recurrent_residual_v1": "independent",
    "cross_family_only_bounded_recurrent_residual_v1": "cross_family_only",
    "support_only_bounded_recurrent_residual_v1": "support_only",
    "shared_local_update_law_v1": "shared",
    "independent_local_update_law_v1": "independent",
    "cross_family_only_local_update_law_v1": "cross_family_only",
    "support_only_local_update_law_v1": "support_only",
    "shared_invariant_residual_module_v1": "shared",
    "independent_invariant_residual_module_v1": "independent",
    "cross_family_only_invariant_residual_module_v1": "cross_family_only",
    "support_only_invariant_residual_module_v1": "support_only",
    "pooled_without_invariance_residual_module_v1": "shared",
    "frozen_partition_invariant_residual_module_v1": "shared",
}
BASE_IMPLEMENTATION = {
    "independent_tensor_dynamics_v1": "shared_tensor_dynamics_v1",
    "cross_family_only_tensor_dynamics_v1": "shared_tensor_dynamics_v1",
    "support_only_tensor_dynamics_v1": "shared_tensor_dynamics_v1",
    "independent_predictive_index_v1": "shared_predictive_index_v1",
    "cross_family_only_predictive_index_v1": "shared_predictive_index_v1",
    "support_only_predictive_index_v1": "shared_predictive_index_v1",
    "independent_bounded_recurrent_residual_v1": "shared_bounded_recurrent_residual_v1",
    "cross_family_only_bounded_recurrent_residual_v1": "shared_bounded_recurrent_residual_v1",
    "support_only_bounded_recurrent_residual_v1": "shared_bounded_recurrent_residual_v1",
    "independent_local_update_law_v1": "shared_local_update_law_v1",
    "cross_family_only_local_update_law_v1": "shared_local_update_law_v1",
    "support_only_local_update_law_v1": "shared_local_update_law_v1",
    "independent_invariant_residual_module_v1": "shared_invariant_residual_module_v1",
    "cross_family_only_invariant_residual_module_v1": "shared_invariant_residual_module_v1",
    "support_only_invariant_residual_module_v1": "shared_invariant_residual_module_v1",
}
UPDATE_LAW_ROLES = frozenset({
    "shared_local_update_law_v1", "independent_local_update_law_v1",
    "cross_family_only_local_update_law_v1", "support_only_local_update_law_v1",
})
DS_BYTES = 688_671_648


def _world(slot: int, support_x: np.ndarray, support_y: np.ndarray,
           history: np.ndarray, future: np.ndarray, output: np.ndarray) -> World:
    return World(slot, pad(support_x, 108), pad(support_y, 108),
                 pad(history, 32), pad(future, 50), pad(output, 50))


def _anchors(start: int, stop: int, count: int, seed: int) -> tuple[int, ...]:
    low, high = start + 160, stop - 51
    if high < low:
        raise ValueError("frozen segment is too short")
    rng = random.Random(seed ^ start ^ stop)
    return tuple(rng.randint(low, high) for _ in range(count))


def _ds_worlds(knowledge: int, count: int, seed: int) -> tuple[list[World], list[World]]:
    base = project_root() / "research/data/ncmapss_ds08a_portable_v1"
    manifest = load_json(base / "manifest.json")
    arrays: dict[str, np.ndarray] = {}
    for role in ("dev", "test"):
        for name in ("A", "W", "X_s"):
            path = base / f"{name}_{role}.npy"
            record = manifest["files"][path.name]
            if path.stat().st_size != int(record["bytes"]) or sha256_file(path) != record["sha256"]:
                raise ValueError(f"DS08a portable component mismatch: {path.name}")
            arrays[f"{name}_{role}"] = np.load(path, mmap_mode="r")

    def build(unit: int, anchor: int, slot: int) -> World:
        role, start, stop = DS_SEGMENTS[unit]
        a, w, x = arrays[f"A_{role}"], arrays[f"W_{role}"], arrays[f"X_s_{role}"]
        if not (np.all(a[start:stop, 0] == unit) and np.all(a[start:stop, 1] == a[start, 1])):
            raise ValueError("DS08a unit/cycle segment mismatch")
        support_x = np.column_stack((w[start:start + 108], x[start:start + 108]))
        return _world(slot, support_x, x[start + 1:start + 109],
                      np.column_stack((w[anchor - 31:anchor + 1], x[anchor - 31:anchor + 1])),
                      w[anchor + 1:anchor + 51], x[anchor + 1:anchor + 51])

    train = []
    for slot, unit in enumerate(TRAIN_UNITS[:knowledge]):
        _, start, stop = DS_SEGMENTS[unit]
        train.append(build(unit, _anchors(start, stop, 1, 1103 + unit)[0], slot))
    test = []
    per_unit = max(1, math.ceil(count / len(TEST_UNITS)))
    for unit in TEST_UNITS:
        _, start, stop = DS_SEGMENTS[unit]
        for anchor in _anchors(start, stop, per_unit, seed ^ unit):
            test.append(build(unit, anchor, 10_000 + len(test)))
    return train, test[:count]


def _drone_worlds(knowledge: int, count: int, seed: int) -> tuple[list[World], list[World]]:
    rows = _corpus_rows(project_root())
    train = _load_flights([row for row in rows if row["role"] == "train"][:knowledge])
    test = _load_flights([row for row in rows if row["role"] == "test"][:max(1, min(6, count))])

    def build(flight: Any, anchor: int, slot: int) -> World:
        start = 32
        support_x = np.column_stack((flight.controls[start:start + 108], flight.states[start:start + 108]))
        return _world(slot, support_x, flight.states[start + 1:start + 109],
                      np.column_stack((flight.controls[anchor - 31:anchor + 1], flight.states[anchor - 31:anchor + 1])),
                      flight.controls[anchor + 1:anchor + 51], flight.states[anchor + 1:anchor + 51])

    training = [build(flight, 300, flight.slot) for flight in train]
    testing = []
    per_flight = max(1, math.ceil(count / len(test)))
    for flight in test:
        for anchor in _anchors(300, len(flight.states), per_flight, seed ^ flight.slot):
            testing.append(build(flight, anchor, 20_000 + len(testing)))
    return training, testing[:count]


def _event_worlds(knowledge: int, count: int, seed: int) -> tuple[list[World], list[World]]:
    def build(world_seed: int, slot: int) -> World:
        native = event.make_world(32, world_seed)
        episode = event.make_episode(native, world_seed)
        task = event.make_tasks(native, 50, world_seed ^ 17, 1)[0]
        return _world(slot, episode.channels, np.asarray(episode.targets)[:, None],
                      episode.channels[-32:], task.cold.channels,
                      np.asarray(task.target)[:, None])

    train = [build(1103 + index * 104729, 30_000 + index) for index in range(knowledge)]
    test = [build(seed ^ (index + 1) * 65537, 40_000 + index) for index in range(count)]
    return train, test


def build_worlds(knowledge: int, count: int, seed: int) -> tuple[dict[str, list[World]], dict[str, list[World]]]:
    if not 4 <= knowledge <= len(TRAIN_UNITS):
        raise ValueError("knowledge size must be in [4, 9]")
    pairs = (_ds_worlds(knowledge, count, seed), _drone_worlds(knowledge, count, seed),
             _event_worlds(knowledge, count, seed))
    return ({family: pair[0] for family, pair in zip(FAMILIES, pairs)},
            {family: pair[1] for family, pair in zip(FAMILIES, pairs)})


def _load(name: str, seed: int) -> Any:
    module = importlib.import_module(
        f"nextai_autoresearch.candidates.{BASE_IMPLEMENTATION.get(name, name)}"
    )
    return module.Candidate(seed=seed)


def _assignment(role: str, family: str, training: dict[str, list[World]]) -> tuple[World, ...]:
    if role in {"shared", "privileged"}:
        selected = FAMILIES
    elif role == "independent":
        selected = (family,)
    elif role == "cross_family_only":
        selected = tuple(item for item in FAMILIES if item != family)
    elif role == "support_only":
        selected = ()
    else:
        raise ValueError(f"unknown causal role: {role}")
    return tuple(world for item in selected for world in training[item])


def _reported_update_ops(candidate_name: str, adaptation_ops: float, sessions: int) -> float:
    if candidate_name not in UPDATE_LAW_ROLES:
        return 0.0
    return adaptation_ops / sessions if sessions else 0.0


def _run_cell(candidate_name: str, knowledge: int, depth: int, count: int, seed: int) -> list[dict[str, Any]]:
    role = ROLE[candidate_name]
    training, testing = build_worlds(knowledge, count, seed)
    runtimes: dict[str, tuple[Any, Any]] = {}
    fit_seconds = 0.0
    for family in FAMILIES:
        key = "pooled" if role in {"shared", "privileged"} else family
        if key in runtimes:
            continue
        assigned = _assignment(role, family, training)
        if role == "privileged":
            assigned += tuple(
                World(world.slot, world.support_input, world.support_target,
                      world.history, world.future_public, None)
                for worlds in testing.values() for world in worlds
            )
        normalizer = fit_normalizer(assigned)
        candidate = _load(candidate_name, seed ^ len(runtimes) * 7919)
        started = time.perf_counter()
        candidate.fit(Training(tuple(normalizer.apply(world) for world in assigned)))
        fit_seconds += time.perf_counter() - started
        runtimes[key] = candidate, normalizer

    total_fit = sum(float(getattr(item[0], "fit_ops", 0)) for item in runtimes.values())
    total_state = sum(float(item[0].state_bytes()) for item in runtimes.values())
    if total_state > 67_108_864:
        raise ValueError("summed state budget exceeded")
    rows = []
    acquisition = float(DS_BYTES + ARCHIVE_BYTES + EXTRACTED_BYTES)
    for family in FAMILIES:
        key = "pooled" if role in {"shared", "privileged"} else family
        candidate, normalizer = runtimes[key]
        errors, horizon_errors, latencies, query_ops, stable = [], {1: [], 10: [], 50: []}, [], [], []
        adaptation_ops = 0.0
        for raw in testing[family]:
            world = normalizer.apply(raw)
            session = candidate.adapt(world.support_input, world.support_target)
            adaptation_ops += float(getattr(candidate, "adaptation_ops", 0))
            started = time.perf_counter_ns()
            predicted = candidate.predict(session, world.history, world.future_public)
            stable.append(float(getattr(candidate, "last_stable", True)))
            latencies.append((time.perf_counter_ns() - started) / 1000.0)
            query_ops.append(float(getattr(candidate, "last_ops", 0)))
            errors.append(masked_mse(predicted, world.output))
            for horizon in horizon_errors:
                target = type(world.output)(world.output.values[:horizon], world.output.mask[:horizon])
                horizon_errors[horizon].append(masked_mse(np.asarray(predicted)[:horizon], target))
        nrmse = math.sqrt(statistics.fmean(errors))
        mean_query = statistics.fmean(query_ops)
        query_work = mean_query * len(errors)
        preprocessing = float(sum(
            tensor.values.size for worlds in training.values() for world in worlds
            for tensor in (world.support_input, world.support_target, world.history,
                           world.future_public, world.output)
        ))
        base_cost = acquisition + preprocessing + total_fit
        workloads = {reuse: base_cost + reuse * (adaptation_ops + query_work) for reuse in (1, 4, 16)}
        rows.append({
            "status": "complete", "world_family": family, "knowledge_size": knowledge,
            "reasoning_depth": depth, "seed": seed, "accuracy": 1.0 / (1.0 + nrmse),
            "family_router_accuracy": 1.0,
            "warm_accuracy": 1.0 / (1.0 + nrmse), "continual_retention": 1.0,
            "normalized_rmse": nrmse,
            "teacher_forced_nrmse": math.sqrt(statistics.fmean(horizon_errors[1])),
            "rollout_10_nrmse": math.sqrt(statistics.fmean(horizon_errors[10])),
            "rollout_50_nrmse": math.sqrt(statistics.fmean(horizon_errors[50])),
            "stable_rollout_rate": statistics.fmean(stable),
            "fit_seconds": fit_seconds, "fit_ops": total_fit, "meta_fit_ops": total_fit,
            "data_acquisition_ops": acquisition, "preprocessing_ops": preprocessing,
            "adaptation_ops": adaptation_ops, "mean_query_ops": mean_query,
            "mean_warm_query_ops": mean_query, "p50_latency_us": percentile(latencies, .5),
            "p95_latency_us": percentile(latencies, .95), "state_bytes": total_state,
            "peak_state_bytes": total_state, "mean_input_ops": 4096.0,
            "mean_bytes_touched": float(getattr(candidate, "last_bytes_touched", 0)),
            "update_ops": _reported_update_ops(candidate_name, adaptation_ops, len(errors)),
            "update_latency_us": 0.0,
            "workload_ops": workloads[1], "workload_ops_r1": workloads[1],
            "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
        })
    return rows


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    if candidate_name not in ROLE:
        raise ValueError(f"candidate has no frozen causal role: {candidate_name}")
    matrix = plan["matrix"]
    return [row for seed in matrix["seeds"] for knowledge in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"] for row in _run_cell(
                candidate_name, int(knowledge), int(depth),
                int(matrix["queries_per_cell"]), int(seed))]
