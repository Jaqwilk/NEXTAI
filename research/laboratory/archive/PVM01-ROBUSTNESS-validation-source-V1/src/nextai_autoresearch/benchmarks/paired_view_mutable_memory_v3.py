"""Prospective delta-memory screen; unchanged PVM task, fresh private units."""
import importlib
from pathlib import Path
import re
import time

import numpy as np
import torch

from ..pvm01_task import pairs, episode, training_sets, arrays_hash, episode_hash
from ..utils import load_json, project_root, sha256_file, sha256_json
from .paired_view_mutable_memory_v1 import scores as reference_scores

BENCHMARK_VERSION = "paired_view_mutable_memory_v3"
COMPACT_ARMS = {"delta", "additive", "delta_untrained", "delta_shuffled"}


def bound_private_path(plan):
    identity = plan["experiment_id"]
    if not re.fullmatch(r"EXP-\d{8}-\d{4}", identity):
        raise ValueError("Invalid runner-private experiment identity")
    root = (project_root() / "research" / "tmp").resolve()
    expected = root / identity / "pvm01-private-data.json"
    actual = Path(plan["pvm01_private_data_path"]).resolve(strict=True)
    if not actual.is_relative_to(root) or actual != expected:
        raise ValueError("Runner-private path must match this experiment")
    private = load_json(actual)
    if sha256_file(actual) != plan["pvm01_private_data_sha256"] or private["experiment_id"] != identity:
        raise ValueError("Runner-private unit binding changed")
    return private


def measure(system, item):
    system.synchronize()
    started = time.perf_counter()
    session = system.new_session(len({r[1] for r in item.writes}))
    system.synchronize()
    allocated = time.perf_counter() - started
    ingest, updates, seen = [], [], set()
    for row in item.writes:
        system.synchronize()
        tick = time.perf_counter()
        session.ingest(row)
        system.synchronize()
        elapsed = time.perf_counter() - tick
        ingest.append(elapsed)
        if row[1] in seen:
            updates.append(elapsed)
        seen.add(row[1])
    tick = time.perf_counter()
    session.answer(item.queries[0])
    system.synchronize()
    warmup = time.perf_counter() - tick
    predictions, latencies = [], []
    for index, query in enumerate(item.queries):
        system.synchronize()
        tick = time.perf_counter()
        answer, handle, score, top_value = session.answer(query)
        system.synchronize()
        elapsed = time.perf_counter() - tick
        # No truth or stratum is read before answer().
        predictions.append({"answer": answer, "top_handle": handle, "decision_score": score,
                            "top_value": top_value, "truth": item.answers[index],
                            "target_handle": item.target_handles[index], "stratum": item.strata[index]})
        latencies.append(elapsed * 1e6)
    total = time.perf_counter() - started
    return {"predictions": predictions, "latency_samples_us": latencies,
            "allocation_seconds": allocated, "ingest_seconds": sum(ingest),
            "update_seconds_subset_of_ingest": sum(updates), "warmup_seconds": warmup,
            "query_seconds": sum(latencies) / 1e6, "full_workload_seconds": total,
            "unattributed_python_output_seconds": max(0., total - allocated - sum(ingest) - warmup - sum(latencies) / 1e6),
            "ingest_samples_seconds": ingest, "update_samples_seconds_subset": updates,
            "state_bytes": session.state_bytes()}


def scores(records, compact=False):
    result = reference_scores(records)
    known = [p for p in records if p["stratum"] != "absent"]
    accepted = [p for p in records if p["answer"] != -1]
    result.update(nonabstaining_known_value_accuracy=sum(p["top_value"] == p["truth"] for p in known) / len(known),
                  accepted_answer_accuracy=sum(p["answer"] == p["truth"] for p in accepted) / len(accepted) if accepted else None,
                  fact_handle_diagnostics_applicable=not compact)
    if compact:
        for key in ("fact_top1_accuracy", "wrong_fact_errors", "stale_or_value_errors_at_correct_handle"):
            result[key] = None
    return result


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    protocol, matrix = plan["research_program_protocol"], plan["matrix"]
    if (matrix["knowledge_sizes"] != [32, 128, 512] or matrix["reasoning_depths"] != [1, 2, 3]
            or len(set(matrix["seeds"])) != 5):
        raise ValueError("Frozen PVM01 matrix mismatch")
    private = bound_private_path(plan)
    if not torch.cuda.is_available():
        raise RuntimeError("Frozen PVM01 fit hardware requires CUDA")
    torch.backends.cuda.matmul.allow_tf32 = False
    role = protocol["roles"][candidate_name]
    index, arm = role["seed_index"], role["arm"]
    seed, nonce = matrix["seeds"][index], private["unit_nonces"][index]
    if phase_sink:
        phase_sink("fit")
    tick = time.perf_counter()
    writes, queries = pairs(nonce, "T-fit", protocol["data"]["train_pairs"])
    held_writes, held_queries = pairs(nonce, "T-validation", protocol["data"]["train_validation_pairs"])
    sets = training_sets(nonce) if arm.startswith("dense") else None
    calibrations = [episode(nonce, "T-calibration", size, rounds, i)
                    for size in matrix["knowledge_sizes"]
                    for rounds in protocol["data"]["train_calibration_update_rounds"]
                    for i in range(protocol["data"]["train_calibration_episodes_per_K_and_update"])]
    generation = time.perf_counter() - tick
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    system = module.Candidate(seed=seed, arm=arm, recipe=protocol["recipe"])
    report = system.fit(writes, queries, held_writes, held_queries, sets)
    tick = time.perf_counter()
    system.calibrate([(w.writes, w.queries.copy(), w.answers) for w in calibrations])
    system.synchronize()
    report.update(calibration_seconds=time.perf_counter() - tick, data_generation_seconds=generation,
                  train_pairs_sha256=arrays_hash(writes, queries),
                  training_validation_sha256=arrays_hash(held_writes, held_queries),
                  calibration_sha256=sha256_json([episode_hash(w) for w in calibrations]),
                  private_data_sha256=plan["pvm01_private_data_sha256"],
                  training_sets_sha256={str(k): arrays_hash(*v) for k, v in (sets or {}).items()},
                  torch_version=torch.__version__, gpu_name=torch.cuda.get_device_name(0), seed_index=index)
    report_digest = sha256_json(report)
    if fit_sink:
        fit_sink({"candidate": candidate_name, "seed": seed, "fit_report": report, "fit_report_sha256": report_digest})
    if data_sink:
        data_sink({"split": "T", "seed_index": index, "train_pairs_sha256": report["train_pairs_sha256"],
                   "private_data_sha256": plan["pvm01_private_data_sha256"], "no_structural_resampling": True})
    if phase_sink:
        phase_sink("evaluation")
    trials = []
    for size in matrix["knowledge_sizes"]:
        for label in matrix["reasoning_depths"]:
            rounds = protocol["data"]["axis_encoding"][str(label)]
            tick = time.perf_counter()
            worlds = [episode(nonce, "D", size, rounds, i)
                      for i in range(protocol["data"]["dev_episodes_per_cell"])]
            generation = time.perf_counter() - tick
            digest = sha256_json([episode_hash(w) for w in worlds])
            if data_sink:
                data_sink({"split": "D", "seed_index": index, "K": size, "update_rounds": rounds,
                           "episodes_sha256": digest, "episode_count": len(worlds), "structural_resampling": 0})
            measurements = [measure(system, w) for w in worlds]
            records = [p for m in measurements for p in m["predictions"]]
            latency = [v for m in measurements for v in m["latency_samples_us"]]
            current = scores(records, arm in COMPACT_ARMS)
            ordered = sorted(latency)
            if arm in COMPACT_ARMS:
                operations = 2 * report["parameter_count"] + 2 * 64 * 1024 + 2 * 2048 * 16
                update_operations = 2 * 64 * 1024 + 2 * 2048 * 16 * (1 if arm == "additive" else 2)
            else:
                operations = 128 * size + 2 * report["parameter_count"] + (64 * 128 if arm.startswith("ridge") else 0)
                update_operations = 128 + (2 * 2 * 64 * 64 if arm.startswith("dense_cached") else 0)
            trial = {"status": "complete", "seed": seed, "seed_index": index, "knowledge_size": size,
                     "reasoning_depth": label, "update_rounds": rounds,
                     "axis_warning": "reasoning_depth is a legacy UPDATE LABEL only",
                     "query_count": len(records), **current, "warm_accuracy": current["accuracy"],
                     "continual_retention": current["retained_known_accuracy"],
                     "mean_query_ops": float(operations), "mean_warm_query_ops": float(operations),
                     "operation_count_type": "coarse scalar estimate; tree and cache work measured in full wall, no FLOP/complexity claim",
                     "p50_latency_us": ordered[(len(latency) - 1) // 2],
                     "p95_latency_us": ordered[int(.95 * (len(latency) - 1))], "latency_samples_us": latency,
                     "state_bytes": max(m["state_bytes"] for m in measurements), "fit_seconds": system.fit_seconds,
                     "fit_ops": report["fit_operations_estimate"], "preprocessing_ops": float(sum(len(w.writes) * 128 for w in worlds)),
                     "update_ops": float(update_operations),
                     "update_latency_us": sum(m["update_seconds_subset_of_ingest"] for m in measurements) * 1e6 / max(1, sum(len(m["update_samples_seconds_subset"]) for m in measurements)),
                     "fit_report_sha256": report_digest, "dev_sha256": digest, "measurements": measurements,
                     "data_generation_seconds": generation, "full_workload_seconds": sum(m["full_workload_seconds"] for m in measurements),
                     "component_seconds": {name: sum(m[name] for m in measurements) for name in
                                           ("allocation_seconds", "ingest_seconds", "update_seconds_subset_of_ingest",
                                            "warmup_seconds", "query_seconds", "unattributed_python_output_seconds")},
                     "runtime_device": str(system.device), "training_and_evaluation_are_distinct": True,
                     "decision_score_kind": "max_class_activation" if arm in COMPACT_ARMS else "max_cosine"}
            if not trials:
                trial["fit_report"] = report
            trials.append(trial)
            if trial_sink:
                trial_sink(trial)
    if phase_sink:
        phase_sink("complete")
    return trials
