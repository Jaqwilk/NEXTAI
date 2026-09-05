"""Visible historical WT-01 mechanism diagnostic; never a hidden holdout.

The repository configuration keeps this evaluator in maintenance.  A later,
separate authority is required before its real-data entry point may run.
"""
from __future__ import annotations

import hashlib
import random
import statistics
import time
import tracemalloc
from typing import Any

import numpy as np

from . import heldout_wt_changepoints_prequential_v1 as historical
from .successor_graph_v1 import load_candidate, percentile
from ..utils import load_json, project_root, sha256_file
from ..wt01_dev1 import CANDIDATES, expected_protocol
from ..wt_prequential_contract import PredictionArtifact, WTQuery, WTReveal, WTTraining, WTEpisode


BENCHMARK_VERSION = "wt01_causal_factorial_diagnostic_v1"
TRAIN_SEEDS = tuple(range(6))
VISIBLE_DEVELOPMENT_SEEDS = (6, 7)
VISIBLE_DIAGNOSTIC_SEEDS = (8, 9)
KNOWLEDGE_SIZES = (18, 36, 54)
HORIZONS = (16, 32, 96)
FACTORIAL_CANDIDATES = tuple(
    f"wt01_r{r}_u{u}_c{c}_v1" for r in (0, 1) for u in (0, 1) for c in (0, 1)
)
CLASSICAL_CONTROL = "wt01_var2_rls_bound_v1"
PRIMARY_CONTRAST = ("wt01_r0_u1_c1_v1", "wt01_r1_u1_c1_v1")
CAUSAL_ATTRIBUTION_THRESHOLD = 0.03343253453162794


def verify_static_contract(root=None) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    manifest_path = base / "research/data/wt_changepoints_v1/manifest.json"
    manifest = load_json(manifest_path)
    records = {str(item["file"]): item for item in manifest["files"]}
    if manifest.get("dataset_id") != "causal_chambers_wt_changepoints_v1":
        raise ValueError("WT dataset identity mismatch")
    # DEV-1 deliberately does not open or hash files 8-9.
    for seed in (*TRAIN_SEEDS, *VISIBLE_DEVELOPMENT_SEEDS):
        path = historical._data_path(base, seed)
        record = records.get(path.name)
        if record is None or sha256_file(path) != record["sha256"]:
            raise ValueError(f"WT frozen fit/development file mismatch: seed {seed}")
    if any(historical._data_path(base, seed).name not in records for seed in VISIBLE_DIAGNOSTIC_SEEDS):
        raise ValueError("WT manifest lacks preserved historical diagnostic identities")
    return {
        "files_verified": 8,
        "manifest_sha256": sha256_file(manifest_path),
        "fit": list(TRAIN_SEEDS),
        "development": list(VISIBLE_DEVELOPMENT_SEEDS),
        "forbidden_files_opened": False,
        "data_role": "visible_development_only",
        "hidden_holdout": False,
        "fresh_physical_replications": 0,
    }


def _run_trial(candidate_name: str, knowledge: int, horizon: int, scoring_seed: int,
               evaluation_seeds: tuple[int, ...], state_limit: int,
               data_role: str) -> list[dict[str, Any]]:
    ordered_train, evaluation, acquisition, preprocessing = historical._dataset(
        scoring_seed, evaluation_seeds
    )
    training = WTTraining(
        tuple(WTEpisode(ep.history, ep.control, ep.target[:historical.FIT_HORIZON])
              for ep in ordered_train[:knowledge]), acquisition, preprocessing
    )
    candidate = load_candidate(candidate_name, scoring_seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, knowledge, max(HORIZONS))
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if historical._number(candidate, "state_bytes") > state_limit:
        raise ValueError("WT candidate exceeds frozen state budget")
    slots = random.Random(scoring_seed ^ knowledge ^ horizon).sample(range(1000, 9999), len(evaluation))
    rows, total_query_ops, total_update_ops = [], 0.0, 0.0
    query_bytes = update_bytes = 0.0
    peak_state = historical._number(candidate, "state_bytes")
    for private_file, (physical_file, slot, episodes) in enumerate(
        zip(evaluation_seeds, slots, evaluation)
    ):
        squared, episode_nrmse, first16_area, recovery_nrmse = [], [], [], []
        latencies, update_latencies, digests = [], [], []
        stable = 0
        for episode in episodes:
            query = WTQuery(slot, episode.history, episode.control, horizon)
            tick = time.perf_counter_ns()
            prediction, artifact = historical._artifact(slot, candidate.query(query, horizon), horizon)
            latencies.append((time.perf_counter_ns() - tick) / 1000.0)
            digests.append(artifact.sha256)
            target = np.asarray(episode.target[:horizon], dtype=np.float64)
            error = np.square(prediction - target)
            squared.append(error)
            episode_nrmse.append(float(np.sqrt(error.mean())))
            per_step = np.sqrt(error.mean(axis=1))
            first16_area.append(float(per_step[:16].sum()))
            recovery_nrmse.append(float(np.sqrt(error[12:16].mean())))
            stable += int(np.isfinite(prediction).all())
            total_query_ops += historical._number(candidate, "last_ops")
            query_bytes += historical._number(candidate, "last_bytes_touched")
            tick = time.perf_counter_ns()
            candidate.update(WTReveal(slot, episode.history, episode.control, episode.target[:horizon]))
            update_latencies.append((time.perf_counter_ns() - tick) / 1000.0)
            total_update_ops += historical._number(candidate, "update_ops")
            update_bytes += historical._number(candidate, "last_update_bytes")
            peak_state = max(peak_state, historical._number(candidate, "state_bytes"))
            if peak_state > state_limit:
                raise ValueError("WT candidate exceeds frozen state budget after local update")
        nrmse = float(np.sqrt(np.concatenate([value.reshape(-1) for value in squared]).mean()))
        first16_nrmse = float(np.sqrt(np.concatenate(
            [value[:16].reshape(-1) for value in squared]
        ).mean()))
        recovery = statistics.fmean(recovery_nrmse)
        row = {
            "status": "complete", "knowledge_size": knowledge, "reasoning_depth": horizon,
            "seed": scoring_seed, "query_count": len(episodes),
            "accuracy": 1.0 / (1.0 + nrmse), "warm_accuracy": 1.0 / (1.0 + episode_nrmse[-1]),
            "continual_retention": 1.0 / (1.0 + max(episode_nrmse)),
            "normalized_rmse": nrmse, "worst_file_normalized_rmse": nrmse,
            "worst_transition_normalized_rmse": max(episode_nrmse),
            "rollout_16_nrmse": first16_nrmse,
            f"rollout_{horizon}_nrmse": nrmse,
            "post_change_error_area_16": statistics.fmean(first16_area),
            "recovery_13_16_nrmse": recovery,
            "post_switch_recovery": 1.0 / (1.0 + recovery),
            "stable_rollout_rate": stable / len(episodes),
            "fit_seconds": fit_seconds, "fit_ops": historical._number(candidate, "fit_ops"),
            "meta_fit_ops": historical._number(candidate, "meta_fit_ops",
                                                   historical._number(candidate, "fit_ops")),
            "data_acquisition_ops": float(acquisition), "preprocessing_ops": float(preprocessing),
            "adaptation_ops": 0.0, "fit_peak_bytes": float(fit_peak),
            "mean_query_ops": 0.0, "mean_warm_query_ops": 0.0,
            "mean_input_ops": float(historical.FIT_DEPTH * 10 + 1), "mean_bytes_touched": 0.0,
            "p50_latency_us": percentile(latencies, 0.5), "p95_latency_us": percentile(latencies, 0.95),
            "state_bytes": historical._number(candidate, "state_bytes"),
            "peak_state_bytes": max(float(fit_peak), peak_state), "update_ops": 0.0,
            "update_latency_us": statistics.fmean(update_latencies),
            "prediction_artifact_count": len(digests),
            "prediction_artifact_chain_sha256": hashlib.sha256("".join(digests).encode()).hexdigest(),
            "private_file_index": private_file,
            "visible_development_file": int(physical_file),
            "data_role": data_role,
        }
        rows.append(row)
    steps = sum(row["query_count"] for row in rows)
    base = acquisition + preprocessing + historical._number(candidate, "fit_ops") + total_update_ops
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
    if candidate_name not in CANDIDATES:
        raise ValueError("WT-01 diagnostic accepts only the frozen factorial and VAR control")
    matrix, protocol = plan["matrix"], plan["wt01_factorial_protocol"]
    if tuple(matrix["knowledge_sizes"]) != KNOWLEDGE_SIZES or tuple(matrix["reasoning_depths"]) != HORIZONS:
        raise ValueError("WT-01 diagnostic matrix changed")
    if protocol != expected_protocol():
        raise ValueError("WT-01 DEV-1 protocol changed")
    evaluation_seeds = tuple(int(value) for value in protocol["evaluation_files"])
    if evaluation_seeds != VISIBLE_DEVELOPMENT_SEEDS:
        raise ValueError("WT-01 DEV-1 may evaluate only visible development files 6-7")
    if set(evaluation_seeds) & set(protocol["forbidden_files"]):
        raise ValueError("WT-01 forbidden historical diagnostic file requested")
    state_limit = int(protocol["state_budget_bytes"])
    return [row for seed in matrix["seeds"] for knowledge in matrix["knowledge_sizes"]
            for horizon in matrix["reasoning_depths"] for row in _run_trial(
                candidate_name, int(knowledge), int(horizon), int(seed),
                evaluation_seeds, state_limit, "visible_development")]
