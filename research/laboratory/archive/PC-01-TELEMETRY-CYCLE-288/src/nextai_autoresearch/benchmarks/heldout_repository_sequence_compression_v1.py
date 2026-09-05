from __future__ import annotations

import hashlib
import math
import random
import statistics
import subprocess
import time
import tracemalloc
from pathlib import Path
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..repository_sequence_contract import (
    ByteContext, ByteFile, CompressionTraining, PrivilegedByteContext,
)
from ..utils import project_root


BENCHMARK_VERSION = "heldout_repository_sequence_compression_v1"
SEGMENT_MULTIPLIER = 128
CORPUS_GIT_SNAPSHOT = "8ed7272c9047f0b5a7ff50221aa783fd6bc6b74a"
PRIVILEGED = {"oracle_test_table_byte"}
CORPUS = (
    ("train", "AGENTS.md", 5648, "0a8a8b9ad54828cffbdca28f29d7d86db4842e5ccababf3c5243a98bf7e6ac46"),
    ("test", "program.md", 5717, "e50270647d6d2eba47958f0a3ffcad24f72e276fdf18256b9906b43295640948"),
    ("train", "README.md", 6434, "2d6a8d90195960bf66c06a71a0b37f12b0edeab14cab9ca91850152c8896e592"),
    ("train", "docs/ARCHITECTURE.md", 4808, "d6081ba0ee735cc94a0ecec965d0c06abdac8127e3f2d64e449a3526318ec29e"),
    ("train", "docs/BENCHMARK_PROGRAM_LIBRARY_V1.md", 1831, "f43736bea5a54e3b7ee2646514615260c06d64e0261975abfe0dfbfa59133006"),
    ("train", "docs/CODEX_SETUP.md", 2497, "3310540df29faf51b52e8efeb2d407d9979cb9171827d0e0c0fff57d2e3b311c"),
    ("validation", "docs/DATA_MODEL.md", 2663, "e3b30c3878f49dd50a5d92c55f39725409db86ac10e4cdc56f83f376505a133b"),
    ("train", "docs/IDEA_CATALOG.md", 10045, "7c5044ebb190a088e540958fe350a79f7b136e9e80cd0b04915c448c4d4b69c9"),
    ("train", "docs/METRICS.md", 4210, "382f8fba353a252d8cd717a169849bb07b6efdb6e1521574521aa40041091921"),
    ("train", "docs/OCENA_POMYSLU.md", 8463, "99a7da58a0e3e07a5ee7b85de6ec208780d79a00923641643fa10166a94d9952"),
    ("train", "docs/ORIGINAL_MANIFEST.md", 30274, "aba7b0c1010eb98643b35a71a9cdf02ff9f57fd8ba0dc2f97313f1388e0f25ae"),
    ("train", "docs/PRIOR_ART.md", 7872, "ffdf549b7bdb0035416f492feb825b4b2b86fab6ddbda920a434b84d0df319c8"),
    ("train", "docs/ROADMAP.md", 4772, "37ed41ff3f2e5954ab83b8241480ac7ad0ed1d807249586c31df9c5b7b802df7"),
    ("validation", "docs/SAFETY.md", 3045, "431485357affdb2822d7f498d7059f96383be0880ea8edd663e4c3a8ef3433eb"),
    ("test", "src/nextai_autoresearch/active_acquisition_core.py", 8434, "b2e1b176d911be0f3c0fa026f69f78557797fba9d5d48b12754bc0303268d47d"),
    ("train", "src/nextai_autoresearch/adaptive_transition_core.py", 8257, "cea4ce203ed9d973da21fb5886f7747a826765d3ed0e812f568c3cfb62d6424e"),
    ("train", "src/nextai_autoresearch/attractor_core.py", 13861, "82098772682a95de08aab65461355fb0e2592b205698d9c79bb7f5490c8abe85"),
    ("train", "src/nextai_autoresearch/byte_motif_core.py", 15292, "cee8ef23766f7962ea7b1f66c0a97ccb684f8980e0e51a92f45b1e9cfe7921d3"),
    ("train", "src/nextai_autoresearch/causal_adversarial_core.py", 8561, "0cc1e96741d37c5d4bf30e93de120295cd2abd7a65f6fb7bce539081947b74f5"),
    ("train", "src/nextai_autoresearch/causal_core.py", 8665, "d6e44726970374cef3ce3575550894dc5bc40df7cfd3920655bd809cd14fa17c"),
    ("test", "src/nextai_autoresearch/cellular_core.py", 6212, "d17bbc79aad8f32c6f72df0289600129cf54761ae6a4c46acb963ac04afd3404"),
    ("train", "src/nextai_autoresearch/continuous_event_core.py", 12282, "7098ddca8eb6b52b5fe4f3a05ed967676be6ae513ab0dc62e07aa1d83c96c4b3"),
    ("train", "src/nextai_autoresearch/cross_family_contract.py", 2578, "7a7100712b42a073db5139c5164573b9ff8bf062b5c40b5f95e58e9701ae45ff"),
    ("validation", "src/nextai_autoresearch/entity_binding_core.py", 7166, "57850c320f7c959e198d35b929dc263c6235b6ecf80327613fb940fb564673ef"),
    ("train", "src/nextai_autoresearch/latent_causal_core.py", 11308, "841db45ad7ceaace325dc375a1a65db69736a5323cf57e621150d58674c2a52e"),
    ("train", "src/nextai_autoresearch/latent_causal_mixed_core.py", 6867, "c87beb3c9b41de80cdde4bdda7e4675c23c61c30daa739426dbc375bd212c461"),
    ("validation", "src/nextai_autoresearch/ledger.py", 8019, "1bff8f252efc8707989495ce9d2504fe3c4e8c4382c1c7fe386086928c7ffc4e"),
    ("train", "src/nextai_autoresearch/local_state_core.py", 6517, "b67b526d141475525aae60568ac24302ac213a597721a9e374869c15e215abb2"),
    ("test", "src/nextai_autoresearch/modular_composition_core.py", 14256, "9e23dad4f8037193342609b42cc76859af239ae14b7edc4b91d8d121167d9f06"),
    ("train", "src/nextai_autoresearch/noisy_causal_core.py", 11335, "5f0f5975ad93c70d9f051228c3cb58ab0e4b2e0b08f91a24a7868f056b53f598"),
    ("train", "src/nextai_autoresearch/opaque_alias_core.py", 18708, "a3b560b98cc851b593fa8b6cb35c77d0ed35cf925341aede170c3d10d76241f7"),
    ("train", "src/nextai_autoresearch/pareto.py", 2404, "be18de616fcd656836c23075a8b62a4bf32ffb173c0cdcac8cb6efbe06c16a21"),
    ("train", "src/nextai_autoresearch/parity_energy_core.py", 9579, "a69529b39f09818d0c5624eff3bb513106dc7650475cecb0c60a5545e0cac532"),
    ("validation", "src/nextai_autoresearch/pointer_machine_core.py", 7278, "bb05a0c88b34849fea219c6c6c988523a34f3213ff68c6c01300f3974bf03a19"),
    ("train", "src/nextai_autoresearch/predictive_state_core.py", 14727, "5ef38f51147dbc691080b23d771fee890b008db4c0135f5988f5002f4c17df52"),
    ("train", "src/nextai_autoresearch/program_search.py", 5044, "88a4b41a38ba250610ab1165944f5e275a7042cbab2d1af0f9afc6aa9b817a8a"),
    ("test", "src/nextai_autoresearch/reaction_core.py", 7779, "bd4bb4a1d449fc4299df28878f3470326e2eb59a602b2fcde3ba26415324e362"),
    ("train", "src/nextai_autoresearch/semantic_trace_adversarial_core.py", 7241, "7ee97896d082490040a7aaeae387e273cf3d1f2ef8d531bce6b26c56a6d0cd2e"),
    ("train", "src/nextai_autoresearch/semantic_trace_core.py", 10660, "341739809db45285d9337c266e4a4d9735dd5566a8e45c45dfe862a7d4b3c86f"),
    ("train", "src/nextai_autoresearch/temporal_binding_core.py", 10958, "ade5b5d16c1f35b1d36d09c03c41b55aa47fef559495b9f4f943c3aa1663af49"),
    ("train", "src/nextai_autoresearch/utils.py", 2061, "9b01f846a8fcf5866cd7e34162449ae8b36ea8c3194950b9dcf1dc5f62d43b7a"),
    ("train", "src/nextai_autoresearch/vsa_capacity_core.py", 10782, "70d7d2697028a2975e5060fb1544d056c65806e18078a0e4418329d82c5d5639"),
    ("train", "src/nextai_autoresearch/whole_io_vm_core.py", 12145, "65b287af63a85ac6b2d0e77501bb84e5809675a95406d63004b6b34d2e0d174b"),
)


def _frozen_corpus_bytes(
    base: Path, relative: str, size: int, digest: str, snapshot: str = CORPUS_GIT_SNAPSHOT
) -> bytes:
    current = base / relative
    data = current.read_bytes() if current.is_file() else b""
    if len(data) == size and hashlib.sha256(data).hexdigest() == digest:
        return data
    recovered = subprocess.run(
        ["git", "cat-file", "blob", f"{snapshot}:{relative}"],
        cwd=base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    data = recovered.stdout
    if recovered.returncode or len(data) != size or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"immutable corpus mismatch: {relative}")
    return data


def _load_corpus(root: Path | None = None) -> tuple[dict[str, list[tuple[str, bytes]]], int]:
    base = root or project_root()
    roles: dict[str, list[tuple[str, bytes]]] = {"train": [], "validation": [], "test": []}
    acquisition = 0
    for role, relative, expected_size, expected_hash in CORPUS:
        data = _frozen_corpus_bytes(base, relative, expected_size, expected_hash)
        acquisition += len(data)
        roles[role].append((relative, data))
    return roles, acquisition


def _allocate(files: list[tuple[str, bytes]], budget: int, slots: list[int]) -> tuple[ByteFile, ...]:
    remaining = budget
    offsets = [0] * len(files)
    chunks = [bytearray() for _ in files]
    while remaining and any(offset < len(item[1]) for offset, item in zip(offsets, files)):
        for index, (_, data) in enumerate(files):
            if remaining == 0:
                break
            take = min(128, remaining, len(data) - offsets[index])
            chunks[index].extend(data[offsets[index]: offsets[index] + take])
            offsets[index] += take
            remaining -= take
    return tuple(ByteFile(slot, tuple(data)) for slot, data in zip(slots, chunks) if data)


def make_training(knowledge_size: int, seed: int) -> tuple[CompressionTraining, list[tuple[str, bytes]]]:
    roles, acquisition = _load_corpus()
    rng = random.Random(seed ^ 0xC0DEC0DE)
    slots = rng.sample(range(10_000, 99_999), len(roles["train"]) + len(roles["validation"]))
    train = _allocate(roles["train"], knowledge_size * 1024, slots[:len(roles["train"])])
    validation = _allocate(roles["validation"], min(4096, knowledge_size * 128), slots[len(roles["train"]):])
    return CompressionTraining(train, validation, acquisition), roles["test"]


def _distribution(value: Any) -> tuple[float, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != 256:
        raise ValueError("byte predictor must return 256 probabilities")
    probabilities = tuple(float(item) for item in value)
    if any(not math.isfinite(item) or item < 0 for item in probabilities):
        raise ValueError("byte probabilities must be finite and nonnegative")
    total = sum(probabilities)
    if total <= 0:
        raise ValueError("byte probabilities must have positive mass")
    return tuple(item / total for item in probabilities)


def _number(candidate: Any, name: str, default: float = 0.0) -> float:
    value = getattr(candidate, name, default)
    return float(value() if callable(value) else value)


def _run_trial(candidate_name: str, knowledge_size: int, depth: int, count: int,
               seed: int, state_limit: int) -> list[dict[str, Any]]:
    training, test_files = make_training(knowledge_size, seed)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, knowledge_size, depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if _number(candidate, "state_bytes") > state_limit:
        raise ValueError("candidate exceeds preregistered resident-state budget")

    rng = random.Random(seed ^ knowledge_size ^ (depth << 12))
    slots = rng.sample(range(100, 9_999), len(test_files))
    rows = []
    total_queries = total_updates = total_query_bytes = total_update_bytes = 0.0
    total_targets = 0
    for (path, data), slot in zip(test_files, slots):
        length = min(count * SEGMENT_MULTIPLIER, len(data) - depth)
        start = rng.randrange(depth, len(data) - length + 1)
        history = list(data[start - depth:start])
        losses: list[float] = []
        correct = 0
        query_ops = update_ops = query_bytes = update_bytes = 0.0
        query_latencies, update_latencies = [], []
        peak_state = _number(candidate, "state_bytes")
        counts = [0] * 256
        for value in data:
            counts[value] += 1
        histogram = tuple(counts)
        for target in data[start:start + length]:
            public = ByteContext(slot, tuple(history[-depth:]))
            source: Any = PrivilegedByteContext(public, histogram) if candidate_name in PRIVILEGED else public
            tick = time.perf_counter_ns()
            probabilities = _distribution(candidate.query(source, 1))
            query_latencies.append((time.perf_counter_ns() - tick) / 1000.0)
            losses.append(-math.log2(max(probabilities[target], 2.0 ** -52)))
            correct += int(max(range(256), key=probabilities.__getitem__) == target)
            query_ops += _number(candidate, "last_ops")
            query_bytes += _number(candidate, "last_bytes_touched", _number(candidate, "last_ops") * 8)
            tick = time.perf_counter_ns()
            candidate.update(ByteContext(slot, tuple(history[-depth:])), target)
            update_latencies.append((time.perf_counter_ns() - tick) / 1000.0)
            update_ops += _number(candidate, "update_ops")
            update_bytes += _number(candidate, "last_update_bytes", _number(candidate, "update_ops") * 8)
            history.append(target)
            peak_state = max(peak_state, _number(candidate, "state_bytes"))
            if peak_state > state_limit:
                raise ValueError("candidate exceeds preregistered resident-state budget")
        bpb = statistics.fmean(losses)
        total_queries += query_ops
        total_updates += update_ops
        total_query_bytes += query_bytes
        total_update_bytes += update_bytes
        total_targets += length
        rows.append({
            "status": "complete", "world_family": path, "knowledge_size": knowledge_size,
            "reasoning_depth": depth, "seed": seed, "query_count": length,
            "accuracy": correct / length, "warm_accuracy": correct / length,
            "continual_retention": correct / length, "bits_per_byte": bpb,
            "cold_bits_per_byte": statistics.fmean(losses[:min(128, length)]),
            "worst_file_bits_per_byte": bpb, "compression_ratio": bpb / 8.0,
            "fit_seconds": fit_seconds, "fit_ops": _number(candidate, "fit_ops"),
            "meta_fit_ops": _number(candidate, "meta_fit_ops", _number(candidate, "fit_ops")),
            "data_acquisition_ops": float(training.acquisition_ops), "fit_peak_bytes": float(fit_peak),
            "mean_query_ops": 0.0, "mean_warm_query_ops": 0.0,
            "mean_input_ops": float(depth), "mean_bytes_touched": 0.0,
            "p50_latency_us": percentile(query_latencies, 0.5), "p95_latency_us": percentile(query_latencies, 0.95),
            "state_bytes": _number(candidate, "state_bytes"), "peak_state_bytes": max(float(fit_peak), peak_state),
            "update_ops": 0.0, "update_latency_us": statistics.fmean(update_latencies),
            "workload_ops": 0.0, "workload_ops_r1": 0.0,
            "workload_ops_r4": 0.0, "workload_ops_r16": 0.0,
        })
    offline = max(_number(candidate, "fit_ops"), _number(candidate, "meta_fit_ops", 0.0))
    base = training.acquisition_ops + offline + total_updates
    for row in rows:
        row["mean_query_ops"] = row["mean_warm_query_ops"] = total_queries / total_targets
        row["mean_bytes_touched"] = (total_query_bytes + total_update_bytes) / (2 * total_targets)
        row["update_ops"] = total_updates / total_targets
        row["workload_ops"] = row["workload_ops_r1"] = base + total_queries
        row["workload_ops_r4"] = base + 4 * total_queries
        row["workload_ops_r16"] = base + 16 * total_queries
    return rows


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix, protocol = plan["matrix"], plan["compression_protocol"]
    return [row for seed in matrix["seeds"] for knowledge in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"] for row in _run_trial(
                candidate_name, int(knowledge), int(depth), int(matrix["queries_per_cell"]),
                int(seed), int(protocol["state_budget_bytes"]))]
