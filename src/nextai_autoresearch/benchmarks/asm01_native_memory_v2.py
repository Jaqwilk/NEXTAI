"""Native ASM trajectory instance memory; fixed writer pairs and actual source state."""
import copy
import importlib
import time
from pathlib import Path

import numpy as np
import torch

from ..asm01_task_v2 import load_unit, pairs, episode, prepared_calibration, training_sets, arrays_hash, episode_hash, transform
from .har01_native_memory_v1 import source_state, copy_service_state, scores
from ..utils import load_json, project_root, sha256_file, sha256_json


BENCHMARK_VERSION = "asm01_native_memory_v2"
SOURCE_ARMS = {"source_trained": "transport_pca", "source_untrained": "transport_pca_untrained",
               "source_shuffled": "transport_pca_shuffled", "source_ridge": "ridge_pca_scan"}
SOURCE_PUBLICATION = "research/laboratory/EXP-20261005-0006-fitted-state-publication-V1.json"






def measure(system, item, unit):
    system.synchronize()
    started = time.perf_counter()
    session = system.new_session(len({row[1] for row in item.writes}))
    system.synchronize()
    allocated = time.perf_counter() - started
    ingest, updates, preprocessing = [], [], []
    seen = set()
    for timestamp, handle, raw, value, source in item.writes:
        tick = time.perf_counter()
        observation = transform(raw, "write", unit["mean"], unit["scale"])
        preprocessing.append(time.perf_counter() - tick)
        tick = time.perf_counter()
        session.ingest((int(timestamp), int(handle), observation.copy(), int(value), str(source)))
        system.synchronize()
        elapsed = time.perf_counter() - tick
        ingest.append(elapsed)
        if handle in seen:
            updates.append(elapsed)
        seen.add(handle)
    tick = time.perf_counter()
    session.answer(transform(item.queries[0], item.condition, unit["mean"], unit["scale"]))
    system.synchronize()
    warmup = time.perf_counter() - tick
    predictions, latencies, query_preprocessing = [], [], []
    for index, raw in enumerate(item.queries):
        system.synchronize()
        tick = time.perf_counter()
        observation = transform(raw, item.condition, unit["mean"], unit["scale"])
        prepared = time.perf_counter() - tick
        answer, handle, score, top_value, source = session.answer(observation.copy())
        system.synchronize()
        # Output assembly is part of query service; truth is revealed only afterwards.
        prediction = {"answer": int(answer), "top_handle": int(handle), "max_similarity": float(score),
                      "top_value": int(top_value), "source": source}
        elapsed = time.perf_counter() - tick
        prediction.update(truth=item.answers[index], target_handle=item.target_handles[index],
                          target_source=item.target_sources[index], stratum=item.strata[index])
        predictions.append(prediction)
        latencies.append(elapsed * 1e6)
        query_preprocessing.append(prepared)
    total = time.perf_counter() - started
    return {"predictions": predictions, "latency_samples_us": latencies, "allocation_seconds": allocated,
            "write_preprocessing_seconds": sum(preprocessing), "query_preprocessing_seconds_subset": sum(query_preprocessing),
            "ingest_seconds": sum(ingest), "update_seconds_subset_of_ingest": sum(updates),
            "warmup_seconds": warmup, "query_seconds": sum(latencies) / 1e6,
            "full_workload_seconds": total,
            "unattributed_python_output_seconds": max(0., total - allocated - sum(preprocessing) - sum(ingest)
                                                     - warmup - sum(latencies) / 1e6),
            "ingest_samples_seconds": ingest, "update_samples_seconds_subset": updates,
            "state_bytes": session.state_bytes()}




def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    root = project_root()
    protocol, matrix = plan["research_program_protocol"], plan["matrix"]
    if (plan["benchmark"] != BENCHMARK_VERSION or matrix["knowledge_sizes"] != [16, 32, 64]
            or matrix["reasoning_depths"] != [1, 2, 3] or len(set(matrix["seeds"])) != 5
            or fit_sink is None or data_sink is None or phase_sink is None):
        raise ValueError("Native task/matrix/trusted journal mismatch")
    contract = load_json(root / protocol["study_path"])
    if sha256_file(root / protocol["study_path"]) != protocol["study_sha256"]:
        raise ValueError("ASM scientific study changed")
    if sha256_file(root / protocol["task_contract_path"]) != protocol["task_contract_sha256"]:
        raise ValueError("Native task contract changed")
    private_path = (root / "research/tmp" / plan["experiment_id"] / "asm01-private-data.json").resolve()
    if (Path(plan["asm01_private_data_path"]).resolve() != private_path
            or sha256_file(private_path) != plan["asm01_private_data_sha256"]):
        raise ValueError("Native runner-private data binding mismatch")
    private = load_json(private_path)
    if private["experiment_id"] != plan["experiment_id"] or len(set(private["unit_nonces"])) != 5:
        raise ValueError("Native unit realization mismatch")
    role = protocol["roles"][candidate_name]
    index, arm = role["seed_index"], role["arm"]
    seed, nonce = matrix["seeds"][index], private["unit_nonces"][index]
    if not torch.cuda.is_available():
        raise RuntimeError("Frozen conventional target control requires declared CUDA hardware")
    torch.backends.cuda.matmul.allow_tf32 = False
    phase_sink("fit")
    tick = time.perf_counter()
    unit = load_unit(root, index, nonce)
    writes, queries = pairs(unit, nonce, "T-fit", 4096)
    held_writes, held_queries = pairs(unit, nonce, "T-validation", 512)
    sets = training_sets(unit, nonce) if arm == "target_dense" else None
    calibrations = [episode(unit, nonce, "T-calibration", size, updates, i)
                    for size in matrix["knowledge_sizes"] for updates in (0, 1, 4) for i in range(3)]
    native_preparation_seconds = time.perf_counter() - tick
    tick = time.perf_counter()
    source_arrays, source_provenance = source_state(root, arm, index, contract)
    source_load_seconds = time.perf_counter() - tick
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    system = module.Candidate(seed=seed, arm=arm, recipe=protocol["recipe"], source_arrays=source_arrays)
    report = system.fit(writes, queries, held_writes, held_queries, sets)
    tick = time.perf_counter()
    prepared = [prepared_calibration(unit, item) for item in calibrations]
    system.calibrate(prepared)
    system.synchronize()
    report.update(calibration_seconds=time.perf_counter() - tick, native_preparation_seconds=native_preparation_seconds,
                  source_load_seconds=source_load_seconds, source_provenance=source_provenance,
                  train_pairs_sha256=arrays_hash(writes, queries), training_validation_sha256=arrays_hash(held_writes, held_queries),
                  training_sets_sha256={str(k): arrays_hash(*v) for k, v in (sets or {}).items()},
                  calibration_sha256=sha256_json([episode_hash(item) for item in calibrations]),
                  scaler_sha256=arrays_hash(unit["mean"], unit["scale"]), unique_native_windows=unit["unique_counts"],
                  native_intake_sha256=unit["intake_sha256"], native_dataset_sha256=unit["dataset_sha256"],
                  private_data_sha256=plan["asm01_private_data_sha256"], seed_index=index,
                  train_subject=unit["train_subject"], dev_subject=unit["dev_subject"],
                  train_writer=unit["train_writer"], dev_writer=unit["dev_writer"],
                  torch_version=torch.__version__, gpu_name=torch.cuda.get_device_name(0),
                  full_answer_semantics="value AND actual current source; UNKNOWN has value-1 and no source")
    fit_sink({"candidate": candidate_name, "seed": seed, "fit_report": report})
    data_sink({"split": "T", "seed_index": index, "train_pairs_sha256": report["train_pairs_sha256"],
               "training_validation_sha256": report["training_validation_sha256"],
               "calibration_sha256": report["calibration_sha256"], "scaler_sha256": report["scaler_sha256"],
               "native_dataset_sha256": unit["dataset_sha256"], "private_data_sha256": plan["asm01_private_data_sha256"]})
    phase_sink("evaluation")
    trials = []
    for condition in ("nominal", "adverse"):
        for size in matrix["knowledge_sizes"]:
            for label, updates in ((1, 0), (2, 1), (3, 4)):
                tick = time.perf_counter()
                worlds = [episode(unit, nonce, "D", size, updates, i, condition=condition) for i in range(4)]
                generation = time.perf_counter() - tick
                digest = sha256_json([episode_hash(world) for world in worlds])
                data_sink({"split": "D", "seed_index": index, "K": size, "update_rounds": updates,
                           "condition": condition, "episodes_sha256": digest, "episode_count": 4,
                           "fixed_writer": unit["dev_writer"], "no_structural_resampling": True})
                tick = time.perf_counter()
                service = copy_service_state(system)
                serving_unit = dict(unit, mean=unit["mean"].copy(), scale=unit["scale"].copy())
                restore = time.perf_counter() - tick
                measurements = [measure(service, world, serving_unit) for world in worlds]
                records = [row for measurement in measurements for row in measurement["predictions"]]
                latency = [sample for measurement in measurements for sample in measurement["latency_samples_us"]]
                ordered = sorted(latency)
                current = scores(records)
                # Explicit coarse scalar estimates; timing, not these estimates, decides economics.
                operations = 4096 + 128 * size + (2 * report["parameter_count"] if arm in SOURCE_ARMS or arm == "target_dense" else 64 * 128)
                if arm == "target_dense":
                    operations += 2 * (24 * 64 * 64 + 8 * size * 64 + 4 * 64 * 256)
                elif arm == "target_kernel":
                    operations += 128 * 64 * 3
                elif arm == "native_dtw":
                    operations += size * 32 * 9 * 20
                trial = {"status": "complete", "seed": seed, "seed_index": index, "knowledge_size": size,
                         "reasoning_depth": label, "update_rounds": updates, "condition": condition,
                         "axis_warning": "reasoning_depth is a legacy UPDATE LABEL; not reasoning", **current,
                         "query_count": len(records), "warm_accuracy": current["accuracy"],
                         "continual_retention": current["retained_known_accuracy"],
                         "mean_query_ops": float(operations), "mean_warm_query_ops": float(operations),
                         "operation_count_type": "coarse estimated scalar operations, not machine instructions or measured complexity",
                         "p50_latency_us": ordered[(len(ordered) - 1) // 2], "p95_latency_us": ordered[int(.95 * (len(ordered) - 1))],
                         "latency_samples_us": latency, "state_bytes": max(item["state_bytes"] for item in measurements),
                         "fit_seconds": system.fit_seconds, "fit_ops": report["fit_operations_estimate"],
                         "preprocessing_ops": float(sum(len(world.writes) * 4096 for world in worlds) + len(records) * 4096),
                         "update_ops": float(4096 + 128), "update_latency_us": sum(item["update_seconds_subset_of_ingest"] for item in measurements) * 1e6 /
                            max(1, sum(len(item["update_samples_seconds_subset"]) for item in measurements)),
                         "fit_report": report, "dev_sha256": digest, "measurements": measurements,
                         "data_generation_seconds": generation, "service_state_restore_seconds": restore,
                         "full_workload_seconds": restore + sum(item["full_workload_seconds"] for item in measurements),
                         "component_seconds": {key: sum(item[key] for item in measurements) for key in
                            ("allocation_seconds", "write_preprocessing_seconds", "query_preprocessing_seconds_subset",
                             "ingest_seconds", "update_seconds_subset_of_ingest", "warmup_seconds", "query_seconds",
                             "unattributed_python_output_seconds")},
                         "runtime_device": "cpu", "training_and_evaluation_are_distinct": True}
                if system.source_before and system.source_before != system.source_identity():
                    raise ValueError("Evaluation altered actual frozen source weights")
                trials.append(trial)
                trial_sink(trial)
    manifest = load_json(root / "research/data_manifests/ASM01-ACQUISITION-V2.json")
    if (sha256_file(root / manifest["dataset_path"]) != unit["dataset_sha256"]
            or sha256_file(root / "research/data/asm01_native_v1/publisher.rar") != unit["publisher_sha256"]):
        raise ValueError("Native payload integrity changed after evaluation")
    phase_sink("complete")
    return trials
