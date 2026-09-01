from __future__ import annotations

import statistics
import time
import tracemalloc
from typing import Any

import numpy as np

from .successor_graph_v1 import load_candidate, percentile
from ..metrics import aggregate_trials
from ..raw_sensor_acquisition_contract import (
    PrivilegedRawProbeSession,
    RawProbeSession,
    RawSensorTraining,
    RawSensorWorld,
)


BENCHMARK_VERSION = "heldout_raw_sensor_active_identification_v1"
TRAIN_WORLD_SEEDS = (1103, 2207, 3301)
DEVELOPMENT_SEED = 117031
SENSOR_COUNT = 48
SUPPORT_REPETITIONS = 3
NOISE_STD = 0.20
KNOWLEDGE_SIZES = (8, 32, 128)
PROBE_BUDGETS = (4, 8, 16)
BASELINES = (
    "raw_sensor_no_probe_prior_v1", "raw_sensor_observe_all_v1",
    "raw_sensor_random_probe_v1", "raw_sensor_fisher_fixed_probe_v1",
    "raw_sensor_gaussian_information_gain_v1", "raw_sensor_kernel_information_gain_v1",
    "privileged_raw_sensor_target_v1",
)


def _latent(size: int) -> np.ndarray:
    labels = np.arange(size, dtype=np.int64)
    return 2.0 * ((labels[:, None] >> np.arange(8)) & 1) - 1.0


def _means(size: int, world_seed: int) -> np.ndarray:
    latent = _latent(size)
    base = np.random.default_rng(7401)
    left = base.normal(size=(SENSOR_COUNT, 8)) / np.sqrt(8.0)
    right = base.normal(size=(SENSOR_COUNT, 8)) / np.sqrt(8.0)
    raw = np.tanh(latent @ left.T + 0.35 * np.sin(1.7 * latent @ right.T))
    rng = np.random.default_rng(world_seed)
    label_permutation = rng.permutation(size)
    sensor_permutation = rng.permutation(SENSOR_COUNT)
    signs = rng.choice((-1.0, 1.0), size=SENSOR_COUNT)
    return raw[label_permutation][:, sensor_permutation] * signs


def _support(size: int, world_seed: int) -> RawSensorWorld:
    rng = np.random.default_rng(world_seed ^ 0x53555050)
    values = _means(size, world_seed)[:, None, :] + rng.normal(
        0.0, NOISE_STD, size=(size, SUPPORT_REPETITIONS, SENSOR_COUNT)
    )
    return RawSensorWorld(tuple(tuple(tuple(map(float, row)) for row in label) for label in values))


def _training(size: int, scoring_seed: int, include_meta: bool = True) -> RawSensorTraining:
    meta = tuple(_support(size, seed ^ size * 8191) for seed in TRAIN_WORLD_SEEDS) if include_meta else ()
    return RawSensorTraining(meta, _support(size, scoring_seed))


def _queries(size: int, count: int, scoring_seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(scoring_seed ^ size * 104729 ^ 0x51554552)
    targets = rng.integers(0, size, size=count)
    values = _means(size, scoring_seed)[targets] + rng.normal(0.0, NOISE_STD, size=(count, SENSOR_COUNT))
    return targets, values


def _uses_meta_worlds(candidate_name: str, protocol: dict[str, Any]) -> bool:
    return candidate_name in {
        str(protocol.get("shared_candidate", "")),
        str(protocol.get("frozen_representation_ablation", "")),
    }


def _run_trial(candidate_name: str, size: int, budget: int, count: int,
               scoring_seed: int, state_limit: int, protocol: dict[str, Any]) -> dict[str, Any]:
    training = _training(size, scoring_seed, include_meta=_uses_meta_worlds(candidate_name, protocol))
    candidate = load_candidate(candidate_name, scoring_seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, size, max(PROBE_BUDGETS))
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if candidate.state_bytes() > state_limit:
        raise ValueError("raw sensor candidate exceeds frozen state budget")
    targets, values = _queries(size, count, scoring_seed)
    correct, probes, ops, bytes_touched, latencies = [], [], [], [], []
    privileged = candidate_name.startswith("privileged_")
    for target, row in zip(targets, values):
        payload = tuple(map(float, row))
        session = PrivilegedRawProbeSession(payload, int(target)) if privileged else RawProbeSession(payload)
        tick = time.perf_counter_ns()
        answer = candidate.query(session, budget)
        latencies.append((time.perf_counter_ns() - tick) / 1000.0)
        correct.append(int(answer) == int(target))
        probes.append(float(session.calls))
        ops.append(float(candidate.last_ops))
        bytes_touched.append(float(getattr(candidate, "last_bytes_touched", 0.0)))
    acquisition = float(sum(np.asarray(world.samples).size for world in training.meta_worlds)
                        + np.asarray(training.support.samples).size)
    query_ops = statistics.fmean(ops)
    base = acquisition + float(candidate.fit_ops)
    return {
        "status": "complete", "knowledge_size": size, "reasoning_depth": budget,
        "seed": scoring_seed, "query_count": count,
        "accuracy": statistics.fmean(correct), "warm_accuracy": statistics.fmean(correct),
        "continual_retention": statistics.fmean(correct), "mean_probe_count": statistics.fmean(probes),
        "data_acquisition_ops": acquisition, "fit_ops": float(candidate.fit_ops),
        "meta_fit_ops": float(candidate.fit_ops), "fit_seconds": fit_seconds,
        "fit_peak_bytes": float(fit_peak), "mean_query_ops": query_ops,
        "mean_warm_query_ops": query_ops, "mean_input_ops": 2.0 * statistics.fmean(probes),
        "mean_bytes_touched": statistics.fmean(bytes_touched),
        "p50_latency_us": percentile(latencies, 0.5), "p95_latency_us": percentile(latencies, 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(fit_peak, candidate.state_bytes())),
        "update_ops": 0.0, "update_latency_us": 0.0,
        "workload_ops": base + count * query_ops, "workload_ops_r1": base + count * query_ops,
        "workload_ops_r4": base + 4 * count * query_ops,
        "workload_ops_r16": base + 16 * count * query_ops,
        "world_family": "unseen_raw_sensor_transform",
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix, protocol = plan["matrix"], plan["active_sensor_protocol"]
    return [_run_trial(candidate_name, int(size), int(budget), int(matrix["queries_per_cell"]),
                       int(seed), int(protocol["state_budget_bytes"]), protocol)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for budget in matrix["reasoning_depths"]]


def development_smoke() -> dict[str, Any]:
    protocol = {"support_only_ablation": "source_identical_support_only_raw_sensor_probe_v1",
                "shared_candidate": "shared_raw_sensor_probe_learner_v1",
                "frozen_representation_ablation": "source_identical_frozen_raw_sensor_probe_v1",
                "state_budget_bytes": 16_777_216}
    results = {name: aggregate_trials([
        _run_trial(name, size, budget, 128, DEVELOPMENT_SEED, 16_777_216, protocol)
        for size in KNOWLEDGE_SIZES for budget in PROBE_BUDGETS
    ]) for name in BASELINES}
    fixed = results["raw_sensor_fisher_fixed_probe_v1"]
    gates = {
        "no_probe_is_not_solution": float(results["raw_sensor_no_probe_prior_v1"]["accuracy"]) < 0.10,
        "full_observation_is_identifiable": float(results["raw_sensor_observe_all_v1"]["minimum_cell_accuracy"]) >= 0.98,
        "small_budget_not_saturated": float(fixed["minimum_cell_accuracy"]) < 0.80,
        "three_knowledge_scales": len(KNOWLEDGE_SIZES) == 3,
        "three_probe_budgets": len(PROBE_BUDGETS) == 3,
    }
    return {"development_seed": DEVELOPMENT_SEED, "scoring_targets_read": False,
            "results": results, "gates": gates, "decision": "pass" if all(gates.values()) else "reject"}
