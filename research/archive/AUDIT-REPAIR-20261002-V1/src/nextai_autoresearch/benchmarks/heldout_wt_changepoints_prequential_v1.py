from __future__ import annotations

import hashlib
import random
import statistics
import time
import tracemalloc
from pathlib import Path
from typing import Any

import numpy as np

from .successor_graph_v1 import load_candidate, percentile
from ..metrics import aggregate_trials
from ..utils import load_json, project_root, sha256_file
from ..wt_prequential_contract import (
    PredictionArtifact, WTEpisode, WTQuery, WTReveal, WTTraining,
)


BENCHMARK_VERSION = "heldout_wt_changepoints_prequential_v1"
TRAIN_SEEDS = tuple(range(6))
DEVELOPMENT_SEEDS = (6, 7)
TEST_SEEDS = (8, 9)
KNOWLEDGE_SIZES = (18, 36, 54)
HORIZONS = (16, 32, 96)
FIT_DEPTH = FIT_HORIZON = 32
PRIVATE = {"timestamp", "config", "counter", "flag", "intervention"}
BASELINES = (
    "wt_persistence_v1", "wt_pooled_mean_v1", "wt_control_level_bank_v1",
    "wt_lms_v1", "wt_rls_v1", "wt_transition_bank_v1",
    "wt_bounded_replay_v1", "wt_ridge_fir_v1",
)


def _data_path(root: Path, seed: int) -> Path:
    return root / f"research/data/wt_changepoints_v1/extracted/wt_changepoints_v1/load_in_seed_{seed}.csv"


def verify_static_contract(root: Path | None = None) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    manifest_path = base / "research/data/wt_changepoints_v1/manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("dataset_id") != "causal_chambers_wt_changepoints_v1":
        raise ValueError("WT dataset identity mismatch")
    records = {str(item["file"]): item for item in manifest["files"]}
    for seed in (*TRAIN_SEEDS, *DEVELOPMENT_SEEDS, *TEST_SEEDS):
        path = _data_path(base, seed)
        record = records.get(path.name)
        if record is None or sha256_file(path) != record["sha256"]:
            raise ValueError(f"WT frozen file mismatch: seed {seed}")
    return {
        "files": 10,
        "manifest_sha256": sha256_file(manifest_path),
        "archive_sha256": manifest["archive"]["sha256"],
        "train": list(TRAIN_SEEDS), "development": list(DEVELOPMENT_SEEDS),
        "test": list(TEST_SEEDS),
    }


def _load(root: Path, seeds: tuple[int, ...]) -> list[np.ndarray]:
    arrays = [np.genfromtxt(_data_path(root, seed), delimiter=",", names=True,
                            dtype=None, encoding="utf-8") for seed in seeds]
    names = arrays[0].dtype.names
    if names is None or any(array.dtype.names != names for array in arrays):
        raise ValueError("WT schema mismatch")
    return arrays


def _partition(train: list[np.ndarray]) -> tuple[str, tuple[str, ...]]:
    names = train[0].dtype.names or ()
    numeric = [name for name in names if np.issubdtype(train[0].dtype[name], np.number)]
    controls = []
    for name in numeric:
        if all(
            set((np.flatnonzero(np.diff(array[name].astype(float)) != 0.0) + 1).tolist())
            == set(np.flatnonzero(array["intervention"] == 1.0)[1:].tolist())
            for array in train
        ):
            controls.append(name)
    if len(controls) != 1:
        raise ValueError(f"WT control is not mechanically unique: {controls}")
    responses = []
    for name in numeric:
        if name in PRIVATE or name == controls[0]:
            continue
        if any(any((index + 1) not in set(np.flatnonzero(array["intervention"] == 1.0))
                       and delta != 0.0
                       for index, delta in enumerate(np.diff(array[name].astype(float))))
               for array in train):
            responses.append(name)
    if len(responses) != 10:
        raise ValueError(f"WT anonymous response width changed: {responses}")
    return controls[0], tuple(responses)


def _normalization(train: list[np.ndarray], control: str, responses: tuple[str, ...]):
    values = np.concatenate([
        np.column_stack([array[name].astype(float) for name in responses]) for array in train
    ])
    mean, scale = values.mean(axis=0), values.std(axis=0)
    controls = np.concatenate([array[control].astype(float) for array in train])
    cmean, cscale = float(controls.mean()), float(controls.std())
    if np.any(scale < 1e-9) or cscale < 1e-9:
        raise ValueError("WT train normalization is degenerate")
    return mean, scale, cmean, cscale


def _slot_episodes(array: np.ndarray, control: str, responses: tuple[str, ...],
                   mean: np.ndarray, scale: np.ndarray, cmean: float, cscale: float,
                   permutation: np.ndarray) -> list[WTEpisode]:
    values = (np.column_stack([array[name].astype(float) for name in responses]) - mean) / scale
    values = values[:, permutation]
    episodes = []
    for start in np.flatnonzero(array["intervention"] == 1.0)[1:]:
        history = values[start - FIT_DEPTH:start]
        target = values[start:start + max(HORIZONS)]
        if history.shape != (32, 10) or target.shape != (96, 10):
            raise ValueError("WT episode crosses a frozen segment boundary")
        episodes.append(WTEpisode(
            tuple(map(tuple, history)),
            (float(array[control][start]) - cmean) / cscale,
            tuple(map(tuple, target)),
        ))
    if len(episodes) != 9:
        raise ValueError("WT file must contain nine history-bearing events")
    return episodes


def _dataset(scoring_seed: int, evaluation_seeds: tuple[int, ...]):
    root = project_root()
    train, evaluation = _load(root, TRAIN_SEEDS), _load(root, evaluation_seeds)
    control, responses = _partition(train)
    mean, scale, cmean, cscale = _normalization(train, control, responses)
    permutation = np.random.default_rng(int(scoring_seed) ^ 0x574154).permutation(10)
    train_slots = [_slot_episodes(array, control, responses, mean, scale, cmean, cscale, permutation)
                   for array in train]
    ordered_train = [train_slots[slot][event] for event in range(9) for slot in range(6)]
    evaluation_slots = [_slot_episodes(array, control, responses, mean, scale, cmean, cscale,
                                       permutation) for array in evaluation]
    manifest = load_json(root / "research/data/wt_changepoints_v1/manifest.json")
    acquisition = int(manifest["archive"]["bytes"] + manifest["archive_safety"]["uncompressed_bytes"])
    preprocessing = int(sum(len(array) for array in train + evaluation) * 37
                        + sum(len(array) for array in train) * 20)
    return ordered_train, evaluation_slots, acquisition, preprocessing


def _artifact(slot: int, prediction: Any, horizon: int) -> tuple[np.ndarray, PredictionArtifact]:
    array = np.asarray(prediction, dtype=np.float64)
    if array.shape != (horizon, 10) or not np.isfinite(array).all():
        raise ValueError(f"WT prediction must be a finite {(horizon, 10)} matrix")
    frozen = array.copy()
    frozen.flags.writeable = False
    return frozen, PredictionArtifact(slot, frozen.shape, hashlib.sha256(frozen.tobytes()).hexdigest())


def _number(candidate: Any, name: str, default: float = 0.0) -> float:
    value = getattr(candidate, name, default)
    return float(value() if callable(value) else value)


def _run_trial(candidate_name: str, knowledge: int, horizon: int, scoring_seed: int,
               evaluation_seeds: tuple[int, ...], state_limit: int) -> list[dict[str, Any]]:
    ordered_train, evaluation, acquisition, preprocessing = _dataset(scoring_seed, evaluation_seeds)
    training = WTTraining(
        tuple(WTEpisode(ep.history, ep.control, ep.target[:FIT_HORIZON])
              for ep in ordered_train[:knowledge]), acquisition, preprocessing
    )
    candidate = load_candidate(candidate_name, scoring_seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, knowledge, max(HORIZONS))
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if _number(candidate, "state_bytes") > state_limit:
        raise ValueError("WT candidate exceeds frozen state budget")
    slots = random.Random(scoring_seed ^ knowledge ^ horizon).sample(range(1000, 9999), len(evaluation))
    rows, total_query_ops, total_update_ops = [], 0.0, 0.0
    query_bytes = update_bytes = 0.0
    peak_state = _number(candidate, "state_bytes")
    for private_file, (slot, episodes) in enumerate(zip(slots, evaluation)):
        squared, episode_nrmse, latencies, update_latencies, digests = [], [], [], [], []
        for episode in episodes:
            query = WTQuery(slot, episode.history, episode.control, horizon)
            tick = time.perf_counter_ns()
            prediction, artifact = _artifact(slot, candidate.query(query, horizon), horizon)
            latencies.append((time.perf_counter_ns() - tick) / 1000.0)
            digests.append(artifact.sha256)
            target = np.asarray(episode.target[:horizon], dtype=np.float64)
            error = np.square(prediction - target)
            squared.append(error)
            episode_nrmse.append(float(np.sqrt(error.mean())))
            total_query_ops += _number(candidate, "last_ops")
            query_bytes += _number(candidate, "last_bytes_touched")
            tick = time.perf_counter_ns()
            candidate.update(WTReveal(slot, episode.history, episode.control, episode.target[:horizon]))
            update_latencies.append((time.perf_counter_ns() - tick) / 1000.0)
            total_update_ops += _number(candidate, "update_ops")
            update_bytes += _number(candidate, "last_update_bytes")
            peak_state = max(peak_state, _number(candidate, "state_bytes"))
            if peak_state > state_limit:
                raise ValueError("WT candidate exceeds frozen state budget after local update")
        nrmse = float(np.sqrt(np.concatenate([value.reshape(-1) for value in squared]).mean()))
        row = {
            "status": "complete", "knowledge_size": knowledge, "reasoning_depth": horizon,
            "seed": scoring_seed, "query_count": len(episodes),
            "accuracy": 1.0 / (1.0 + nrmse), "warm_accuracy": 1.0 / (1.0 + episode_nrmse[-1]),
            "continual_retention": 1.0 / (1.0 + max(episode_nrmse)),
            "normalized_rmse": nrmse, "worst_file_normalized_rmse": nrmse,
            "worst_transition_normalized_rmse": max(episode_nrmse),
            f"rollout_{horizon}_nrmse": nrmse,
            "stable_rollout_rate": 1.0,
            "fit_seconds": fit_seconds, "fit_ops": _number(candidate, "fit_ops"),
            "meta_fit_ops": _number(candidate, "meta_fit_ops", _number(candidate, "fit_ops")),
            "data_acquisition_ops": float(acquisition), "preprocessing_ops": float(preprocessing),
            "adaptation_ops": 0.0, "fit_peak_bytes": float(fit_peak),
            "mean_query_ops": 0.0, "mean_warm_query_ops": 0.0,
            "mean_input_ops": float(FIT_DEPTH * 10 + 1), "mean_bytes_touched": 0.0,
            "p50_latency_us": percentile(latencies, 0.5), "p95_latency_us": percentile(latencies, 0.95),
            "state_bytes": _number(candidate, "state_bytes"),
            "peak_state_bytes": max(float(fit_peak), peak_state), "update_ops": 0.0,
            "update_latency_us": statistics.fmean(update_latencies),
            "prediction_artifact_count": len(digests),
            "prediction_artifact_chain_sha256": hashlib.sha256("".join(digests).encode()).hexdigest(),
            "private_file_index": private_file,
        }
        rows.append(row)
    steps = sum(row["query_count"] for row in rows)
    base = acquisition + preprocessing + _number(candidate, "fit_ops") + total_update_ops
    for row in rows:
        row["mean_query_ops"] = row["mean_warm_query_ops"] = total_query_ops / steps
        row["mean_bytes_touched"] = (query_bytes + update_bytes) / steps
        row["update_ops"] = total_update_ops / steps
        row["adaptation_ops"] = total_update_ops
        row["workload_ops_r1"] = row["workload_ops"] = base + total_query_ops
        row["workload_ops_r4"] = base + 4 * total_query_ops
        row["workload_ops_r16"] = base + 16 * total_query_ops
    return rows


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix, protocol = plan["matrix"], plan["wt_prequential_protocol"]
    state_limit = int(protocol["state_budget_bytes"])
    return [row for seed in matrix["seeds"] for knowledge in matrix["knowledge_sizes"]
            for horizon in matrix["reasoning_depths"] for row in _run_trial(
                candidate_name, int(knowledge), int(horizon), int(seed), TEST_SEEDS, state_limit)]


def development_smoke(scoring_seed: int = 117031) -> dict[str, Any]:
    results = {}
    for candidate in BASELINES:
        rows = _run_trial(candidate, 54, 96, scoring_seed, DEVELOPMENT_SEEDS, 16_777_216)
        results[candidate] = aggregate_trials(rows)
    saturating = [name for name, item in results.items()
                  if float(item["normalized_rmse"]) <= 0.50
                  and float(item["worst_file_normalized_rmse"]) <= 0.75
                  and float(item["stable_rollout_rate"]) == 1.0]
    return {
        "development_seeds": list(DEVELOPMENT_SEEDS), "test_seeds_read": False,
        "knowledge_size": 54, "horizon": 96, "results": results,
        "saturating_baselines": saturating,
        "decision": "reject_before_activation" if saturating else "pass",
    }
