"""Prospective transport compression and paired adverse noise; unchanged scoring/costs."""
import hashlib
import importlib
import time

import torch
import numpy as np

from torch.nn.attention import SDPBackend, sdpa_kernel
from ..pvm01_adverse_task import episode as adverse_episode
from ..pvm01_task import pairs, episode, training_sets, arrays_hash, episode_hash
from ..utils import sha256_json
from .paired_view_mutable_memory_v3 import bound_private_path, measure, scores

BENCHMARK_VERSION = "paired_view_mutable_memory_v6"


def decoder_hash(decoder):
    """Hash the public fitted report boundary without importing candidate code."""
    if decoder is None:
        return None
    digest = hashlib.sha256()
    for value in decoder.state_dict().values():
        digest.update(value.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    protocol, matrix = plan["research_program_protocol"], plan["matrix"]
    if (matrix["knowledge_sizes"] != [32, 128, 512] or matrix["reasoning_depths"] != [1, 2, 3]
            or len(set(matrix["seeds"])) != 5):
        raise ValueError("Frozen PVM01 matrix mismatch")
    private = bound_private_path(plan)
    if not torch.cuda.is_available():
        raise RuntimeError("Frozen PVM01 fit requires CUDA")
    torch.backends.cuda.matmul.allow_tf32 = False
    role = protocol["roles"][candidate_name]
    index, arm = role["seed_index"], role["arm"]
    seed, nonce = matrix["seeds"][index], private["unit_nonces"][index]
    compact = arm == "delta"
    if phase_sink:
        phase_sink("fit")
    tick = time.perf_counter()
    writes, queries = pairs(nonce, "T-fit", protocol["data"]["train_pairs"])
    held_writes, held_queries = pairs(nonce, "T-validation", protocol["data"]["train_validation_pairs"])
    sets = training_sets(nonce)
    calibrations = [episode(nonce, "T-calibration", size, rounds, i)
                    for size in matrix["knowledge_sizes"]
                    for rounds in protocol["data"]["train_calibration_update_rounds"]
                    for i in range(protocol["data"]["train_calibration_episodes_per_K_and_update"])]
    generation = time.perf_counter() - tick
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    system = module.Candidate(seed=seed, arm=arm, recipe=protocol["recipe"])
    deterministic = torch.are_deterministic_algorithms_enabled()
    warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        torch.use_deterministic_algorithms(True)
        with sdpa_kernel(SDPBackend.MATH):
            policy = {"deterministic": torch.are_deterministic_algorithms_enabled(),
                      "warn_only": torch.is_deterministic_algorithms_warn_only_enabled(),
                      "math_sdp": torch.backends.cuda.math_sdp_enabled(),
                      "efficient_sdp": torch.backends.cuda.mem_efficient_sdp_enabled(),
                      "flash_sdp": torch.backends.cuda.flash_sdp_enabled(),
                      "cudnn_sdp": torch.backends.cuda.cudnn_sdp_enabled()}
            report = system.fit(writes, queries, held_writes, held_queries, sets)
            report["fit_policy_snapshot"] = policy
    finally:
        torch.use_deterministic_algorithms(deterministic, warn_only=warn_only)
    tick = time.perf_counter()
    system.calibrate([(w.writes, w.queries.copy(), w.answers) for w in calibrations])
    system.synchronize()
    report.update(calibration_seconds=time.perf_counter() - tick, data_generation_seconds=generation,
                  final_decoder_sha256=decoder_hash(system.decoder),
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
    for observation_noise in protocol["data"]["evaluation_noise_standard_deviations"]:
        for size in matrix["knowledge_sizes"]:
            for label in matrix["reasoning_depths"]:
                rounds = protocol["data"]["axis_encoding"][str(label)]
                tick = time.perf_counter()
                worlds = [adverse_episode(nonce, "D", size, rounds, i, noise=observation_noise)
                          for i in range(protocol["data"]["dev_episodes_per_cell"])]
                generation = time.perf_counter() - tick
                digest = sha256_json([episode_hash(w) for w in worlds])
                if data_sink:
                    data_sink({"split": "D", "observation_noise": observation_noise, "seed_index": index, "K": size, "update_rounds": rounds,
                               "episodes_sha256": digest, "episode_count": len(worlds), "structural_resampling": 0})
                measurements = [measure(system, w) for w in worlds]
                records = [p for m in measurements for p in m["predictions"]]
                latency = [v for m in measurements for v in m["latency_samples_us"]]
                current = scores(records, compact)
                ordered = sorted(latency)
                if compact:
                    width = report.get("memory_feature_dimension", protocol["recipe"]["memory_feature_dimension"])
                    operations = 2 * report["parameter_count"] + 2 * 64 * (width // 2) + 2 * width * 16
                    update_operations = 2 * 64 * (width // 2) + 2 * width * 16 * (1 if arm == "exposure_additive" else 2)
                else:
                    operations = 128 * size + 2 * report["parameter_count"] + (64 * 128 if arm.startswith("ridge") else 0)
                    update_operations = 128 + (2 * 2 * 64 * 64 if arm.startswith("dense_cached") else 0)
                trial = {"status": "complete", "observation_noise": observation_noise, "seed": seed, "seed_index": index, "knowledge_size": size,
                         "reasoning_depth": label, "update_rounds": rounds,
                         "axis_warning": "reasoning_depth is a legacy UPDATE LABEL only",
                         "query_count": len(records), **current, "warm_accuracy": current["accuracy"],
                         "continual_retention": current["retained_known_accuracy"],
                         "mean_query_ops": float(operations), "mean_warm_query_ops": float(operations),
                         "operation_count_type": "coarse scalar estimate; trig/tree/cache work measured in full wall; no complexity claim",
                         "p50_latency_us": ordered[(len(latency) - 1) // 2],
                         "p95_latency_us": ordered[int(.95 * (len(latency) - 1))], "latency_samples_us": latency,
                         "state_bytes": max(m["state_bytes"] for m in measurements), "fit_seconds": system.fit_seconds,
                         "fit_ops": report["fit_operations_estimate"], "preprocessing_ops": float(sum(len(w.writes) * 128 for w in worlds)),
                         "update_ops": float(update_operations),
                         "update_latency_us": sum(m["update_seconds_subset_of_ingest"] for m in measurements) * 1e6 / max(1, sum(len(m["update_samples_seconds_subset"]) for m in measurements)),
                         "fit_report_sha256": report_digest, "dev_sha256": digest, "measurements": measurements,
                         "truth_pair_sha256": sha256_json([[w.answers, w.target_handles, w.strata, [(r[0], r[1], r[3]) for r in w.writes]] for w in worlds]),
                         "data_generation_seconds": generation, "full_workload_seconds": sum(m["full_workload_seconds"] for m in measurements),
                         "component_seconds": {name: sum(m[name] for m in measurements) for name in
                                               ("allocation_seconds", "ingest_seconds", "update_seconds_subset_of_ingest",
                                                "warmup_seconds", "query_seconds", "unattributed_python_output_seconds")},
                         "runtime_device": str(system.device), "training_and_evaluation_are_distinct": True,
                         "decision_score_kind": "max_class_activation" if compact else "max_cosine"}
                if not trials:
                    trial["fit_report"] = report
                trials.append(trial)
                if trial_sink:
                    trial_sink(trial)
    if phase_sink:
        phase_sink("complete")
    return trials
