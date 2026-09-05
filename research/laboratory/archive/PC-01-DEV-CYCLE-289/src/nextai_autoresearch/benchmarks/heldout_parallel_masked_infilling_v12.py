from __future__ import annotations

import json
import random
import statistics
import time
import tracemalloc
from pathlib import Path
from typing import Any

from . import heldout_parallel_masked_infilling_v9 as v9
from . import heldout_repository_sequence_compression_v1 as repository_corpus
from .heldout_parallel_masked_infilling_v8 import (
    TEST_DEPTHS, TRAIN_MAX_DEPTH, delimiter_groups,
)
from .heldout_parallel_masked_infilling_v11 import _run_case
from ..masked_refinement_contract import ByteFile, MaskedTraining
from ..utils import project_root


BENCHMARK_VERSION = "heldout_parallel_masked_infilling_v12"
CORPUS_REGISTRY = "research/corpora/heldout_parallel_masked_infilling_v12.json"
CORPUS_GIT_SNAPSHOT = "87c5ab57816003eaa138fd9a3f9b34df86387411"


def _frozen_entry_bytes(base: Path, entry: dict[str, Any]) -> bytes:
    return repository_corpus._frozen_corpus_bytes(
        base, entry["path"], entry["size"], entry["sha256"], CORPUS_GIT_SNAPSHOT
    )


def _load_corpus(root: Path | None = None):
    base = root or project_root()
    registry = json.loads((base / CORPUS_REGISTRY).read_text(encoding="utf-8"))
    if registry["benchmark_version"] != BENCHMARK_VERSION:
        raise ValueError("v12 corpus registry benchmark mismatch")
    roles = {"train": [], "validation": [], "test": []}
    acquisition = 0
    for entry in registry["entries"]:
        data = _frozen_entry_bytes(base, entry)
        acquisition += len(data)
        roles[entry["role"]].append((entry["path"], data))
    return roles, acquisition


def make_stack_training(knowledge_size: int, seed: int):
    roles, acquisition = _load_corpus()
    rng = random.Random(seed ^ 0x57AC)
    permutation = list(range(256))
    rng.shuffle(permutation)
    permutation = tuple(permutation)
    slots = iter(rng.sample(range(10_000, 99_999),
                            len(roles["train"]) + len(roles["validation"])))

    def encoded(files, budget):
        output, used = [], 0
        for _, data in files:
            pieces, file_used = [], 0
            for trace, depth in delimiter_groups(data):
                if depth > TRAIN_MAX_DEPTH:
                    continue
                added = len(trace) + bool(pieces)
                if used + file_used + added > budget:
                    break
                pieces.append((b"\n" if pieces else b"") + trace)
                file_used += added
            shallow = b"".join(pieces)
            if shallow:
                output.append(ByteFile(next(slots), v9._permute(shallow, permutation)))
                used += len(shallow)
            if used >= budget:
                break
        return tuple(output), used

    train, train_bytes = encoded(roles["train"], knowledge_size * 1024)
    validation, validation_bytes = encoded(
        roles["validation"], min(4096, knowledge_size * 128)
    )
    tests = [(trace, depth) for _, data in roles["test"]
             for trace, depth in delimiter_groups(data)
             if depth in TEST_DEPTHS]
    selected = train_bytes + validation_bytes
    return (MaskedTraining(train, validation, 2 * acquisition + selected), tests,
            permutation)


def _run_cell(candidate_name: str, size: int, depth: int, count: int,
              seed: int, maximum_depth: int, protocol: dict[str, Any]):
    training, tests, permutation = make_stack_training(size, seed)
    candidate = v9.load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, size, maximum_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    state = v9._number(candidate, "state_bytes")
    if state > int(protocol["state_budget_bytes"]):
        raise ValueError("state budget exceeded")
    rows = [_run_case(candidate, candidate_name, case, 1)
            for case in v9._stack_cases(tests, depth, count, seed, permutation)]
    query_ops = sum(row["query_ops"] for row in rows)
    fit_ops = v9._number(candidate, "fit_ops")
    base = training.acquisition_ops + fit_ops
    workloads = {h: base + h * query_ops for h in (1, 4, 16)}
    latencies = [value for row in rows for value in row["latency"]]
    return {
        "status": "complete", "world_family": f"stack_depth_{depth}",
        "span_length": depth, "knowledge_size": size, "reasoning_depth": depth,
        "refinement_rounds": 1, "seed": seed, "query_count": count * depth,
        "accuracy": statistics.fmean(row["accuracy"] for row in rows),
        "warm_accuracy": statistics.fmean(row["accuracy"] for row in rows),
        "continual_retention": statistics.fmean(row["exact"] for row in rows),
        "exact_span_accuracy": statistics.fmean(row["exact"] for row in rows),
        "bits_per_byte": statistics.fmean(row["bits"] for row in rows),
        "critical_path_steps": max(row["critical"] for row in rows),
        "total_position_probabilities": sum(row["probabilities"] for row in rows),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops,
        "meta_fit_ops": v9._number(candidate, "meta_fit_ops", fit_ops),
        "data_acquisition_ops": float(training.acquisition_ops),
        "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": query_ops / (count * depth),
        "mean_warm_query_ops": query_ops / (count * depth),
        "mean_input_ops": statistics.fmean(row["input_ops"] for row in rows),
        "mean_bytes_touched": statistics.fmean(row["bytes"] for row in rows),
        "p50_latency_us": v9.percentile(latencies, 0.5),
        "p95_latency_us": v9.percentile(latencies, 0.95),
        "state_bytes": state, "peak_state_bytes": max(state, float(fit_peak)),
        "update_ops": 0.0, "update_latency_us": 0.0,
        "workload_ops": workloads[1], "workload_ops_r1": workloads[1],
        "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
    }


def run_suite(candidate_name: str, plan: dict[str, Any]):
    matrix, protocol = plan["matrix"], plan["masked_refinement_protocol"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [_run_cell(candidate_name, int(size), int(depth),
                      int(matrix["queries_per_cell"]), int(seed), maximum, protocol)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"]]
