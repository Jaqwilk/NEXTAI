from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import statistics
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Callable

import numpy as np
import psutil
import torch
from torch import nn

from nextai_autoresearch.benchmarks.heldout_parallel_masked_infilling_v12 import (
    _load_corpus,
)
from nextai_autoresearch.candidates.dense_autoregressive_byte import (
    Candidate as DenseAR,
)
from nextai_autoresearch.candidates.masked_baselines import CTWByteModel, PPMDModel
from nextai_autoresearch.repository_sequence_contract import (
    ByteContext,
    ByteFile,
    CompressionTraining,
)
from nextai_autoresearch.utils import project_root


CALIBRATION_ID = "CAL-20260901-0001"
CONTRACT = "research/checks/real_system_calibration_v1_preregistered.json"
CONTRACT_SHA256 = "d2004bc548a2253dcd1072cf9641b1369d9ce1dff9edd786f23a52095a384829"
OUTPUT = "research/checks/real_system_calibration_cycle_228.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _examples(files: list[tuple[str, bytes]], context: int, limit: int | None = None):
    xs, ys = [], []
    remaining = limit
    for _, raw in files:
        data = np.frombuffer(raw, dtype=np.uint8)
        if len(data) <= context:
            continue
        windows = np.lib.stride_tricks.sliding_window_view(data, context + 1)
        take = len(windows) if remaining is None else min(len(windows), remaining)
        xs.append(windows[:take, :-1].copy())
        ys.append(windows[:take, -1].copy())
        if remaining is not None:
            remaining -= take
            if remaining == 0:
                break
    return np.concatenate(xs), np.concatenate(ys)


def _measure(function: Callable[[], object], cuda: bool = False):
    process = psutil.Process()
    peak = process.memory_info().rss
    stop = threading.Event()

    def sample() -> None:
        nonlocal peak
        while not stop.wait(0.002):
            peak = max(peak, process.memory_info().rss)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    if cuda:
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    value = function()
    if cuda:
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    stop.set()
    thread.join()
    peak = max(peak, process.memory_info().rss)
    gpu = int(torch.cuda.max_memory_allocated()) if cuda else 0
    return value, elapsed, peak, gpu


class LocalRetrieval:
    def __init__(self, context: int = 32, bucket_cap: int = 64, nearest: int = 4):
        self.context = context
        self.bucket_cap = bucket_cap
        self.nearest = nearest
        self.buckets: dict[bytes, list[tuple[bytes, int]]] = defaultdict(list)
        self.fit_ops = 0

    def fit(self, files: list[tuple[str, bytes]]) -> None:
        for _, raw in files:
            for index in range(self.context, len(raw)):
                key = raw[index - 2:index]
                bucket = self.buckets[key]
                if len(bucket) < self.bucket_cap:
                    bucket.append((raw[index - self.context:index], raw[index]))
                self.fit_ops += self.context + 2

    def distribution(self, history: np.ndarray) -> list[float]:
        context = bytes(history[-self.context:])
        ranked = sorted(
            self.buckets.get(context[-2:], ()),
            key=lambda row: (sum(a != b for a, b in zip(context, row[0])), row[0], row[1]),
        )[: self.nearest]
        counts = [0] * 256
        for _, target in ranked:
            counts[target] += 1
        total = len(ranked) + 128.0
        return [(count + 0.5) / total for count in counts]

    def update(self, history: np.ndarray, target: int) -> None:
        context = bytes(history[-self.context:])
        bucket = self.buckets[context[-2:]]
        if len(bucket) < self.bucket_cap:
            bucket.append((context, int(target)))

    def state_bytes(self) -> int:
        return sum(64 + len(key) + sum(80 + len(row[0]) for row in rows)
                   for key, rows in self.buckets.items())


class TinyTransformer(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.token = nn.Embedding(256, 64)
        self.position = nn.Embedding(64, 64)
        layer = nn.TransformerEncoderLayer(
            64, 4, 128, dropout=0.0, batch_first=True, norm_first=True
        )
        self.encoder = nn.TransformerEncoder(layer, 2)
        self.output = nn.Linear(64, 256)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        positions = torch.arange(tokens.shape[1], device=tokens.device)
        hidden = self.token(tokens) + self.position(positions)
        mask = torch.triu(torch.ones(tokens.shape[1], tokens.shape[1],
                                    dtype=torch.bool, device=tokens.device), 1)
        return self.output(self.encoder(hidden, mask=mask)[:, -1])


def _quality_cpu(predict, xs: np.ndarray, ys: np.ndarray):
    loss = correct = 0.0
    for history, target in zip(xs, ys):
        row = predict(history)
        loss -= math.log2(max(float(row[int(target)]), 2.0 ** -52))
        correct += max(range(256), key=row.__getitem__) == int(target)
    return {"bits_per_byte": loss / len(ys), "top1_accuracy": correct / len(ys)}


def _cpu_record(name, fit, predict, update, state, fit_ops, query_ops,
                validation, test, repeats: int):
    _, fit_seconds, fit_ram, _ = _measure(fit)
    validation_quality = _quality_cpu(predict, *validation)
    batch_x, batch_y = test[0][:256], test[1][:256]

    def batch_query():
        return [predict(row) for row in batch_x]

    _, cold, _, _ = _measure(batch_query)
    warm = []
    for _ in range(repeats):
        started = time.perf_counter()
        batch_query()
        warm.append(time.perf_counter() - started)
    test_quality, query_seconds, query_ram, _ = _measure(
        lambda: _quality_cpu(predict, *test)
    )
    _, update_seconds, update_ram, _ = _measure(
        lambda: update(batch_x[0], int(batch_y[0]))
    )
    n = len(test[1])
    fit_work = int(fit_ops())
    query_work = int(query_ops()) * n
    return {
        "model": name,
        "device": "cpu",
        "status": "complete",
        "validation": validation_quality,
        "test": test_quality,
        "fit_seconds": fit_seconds,
        "query_seconds": query_seconds,
        "update_supported": True,
        "update_seconds": update_seconds,
        "cold_latency_us_per_byte": cold * 1e6 / len(batch_y),
        "warm_latency_us_per_byte": statistics.median(warm) * 1e6 / len(batch_y),
        "throughput_bytes_per_second": n / query_seconds,
        "fit_work_units": fit_work,
        "query_work_units": query_work,
        "work_units_are_estimates": True,
        "resident_state_bytes": int(state()),
        "peak_host_rss_bytes": max(fit_ram, query_ram, update_ram),
        "peak_cuda_allocated_bytes": 0,
        "fit_host_device_transfer_bytes": 0,
        "query_host_device_transfer_bytes": 0,
        "update_host_device_transfer_bytes": 0,
        "workload_seconds": {str(r): fit_seconds + r * query_seconds for r in (1, 4, 16)},
    }


def _transformer_record(train_files, validation, test, spec):
    torch.manual_seed(spec["initialization_seed"])
    random.seed(spec["initialization_seed"])
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = torch.device("cuda")
    model = TinyTransformer().to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=spec["learning_rate"], weight_decay=spec["weight_decay"]
    )
    rng = random.Random(spec["initialization_seed"])
    usable = [(raw, len(raw) - 64) for _, raw in train_files if len(raw) > 64]
    total = sum(count for _, count in usable)
    cumulative = np.cumsum([count for _, count in usable])

    def batch():
        contexts, targets = [], []
        for _ in range(spec["batch_size"]):
            chosen = rng.randrange(total)
            slot = int(np.searchsorted(cumulative, chosen, side="right"))
            prior = 0 if slot == 0 else int(cumulative[slot - 1])
            raw, _ = usable[slot]
            end = 64 + chosen - prior
            contexts.append(list(raw[end - 64:end]))
            targets.append(raw[end])
        return (torch.tensor(contexts, dtype=torch.long, device=device),
                torch.tensor(targets, dtype=torch.long, device=device))

    def fit():
        model.train()
        for _ in range(spec["fit_steps"]):
            x, y = batch()
            optimizer.zero_grad(set_to_none=True)
            nn.functional.cross_entropy(model(x), y).backward()
            nn.utils.clip_grad_norm_(model.parameters(), spec["gradient_clip"])
            optimizer.step()

    _, fit_seconds, fit_ram, fit_gpu = _measure(fit, cuda=True)
    model.eval()

    def quality(data):
        xs, ys = data
        loss = correct = 0.0
        with torch.no_grad():
            for start in range(0, len(ys), spec["evaluation_batch_size"]):
                x = torch.as_tensor(xs[start:start + spec["evaluation_batch_size"]],
                                    dtype=torch.long, device=device)
                y = torch.as_tensor(ys[start:start + spec["evaluation_batch_size"]],
                                    dtype=torch.long, device=device)
                logits = model(x)
                loss += float(nn.functional.cross_entropy(logits, y, reduction="sum"))
                correct += int((logits.argmax(1) == y).sum())
        return {"bits_per_byte": loss / len(ys) / math.log(2.0),
                "top1_accuracy": correct / len(ys)}

    validation_quality = quality(validation)
    batch_x = test[0][:256]

    def timed_batch():
        with torch.no_grad():
            x = torch.as_tensor(batch_x, dtype=torch.long, device=device)
            model(x)

    _, cold, _, _ = _measure(timed_batch, cuda=True)
    warm = []
    for _ in range(7):
        torch.cuda.synchronize()
        started = time.perf_counter()
        timed_batch()
        torch.cuda.synchronize()
        warm.append(time.perf_counter() - started)
    test_quality, query_seconds, query_ram, query_gpu = _measure(
        lambda: quality(test), cuda=True
    )

    def update():
        model.train()
        x = torch.as_tensor(validation[0][:spec["batch_size"]], dtype=torch.long, device=device)
        y = torch.as_tensor(validation[1][:spec["batch_size"]], dtype=torch.long, device=device)
        optimizer.zero_grad(set_to_none=True)
        nn.functional.cross_entropy(model(x), y).backward()
        nn.utils.clip_grad_norm_(model.parameters(), spec["gradient_clip"])
        optimizer.step()

    _, update_seconds, update_ram, update_gpu = _measure(update, cuda=True)
    parameter_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    optimizer_bytes = sum(v.numel() * v.element_size() for state in optimizer.state.values()
                          for v in state.values() if torch.is_tensor(v))
    b, length, width, ff, layers = spec["batch_size"], 64, 64, 128, 2
    forward = layers * (4 * b * length * width * width
                        + 2 * b * length * length * width
                        + 2 * b * length * width * ff) + 2 * b * width * 256
    fit_ops = 3 * forward * spec["fit_steps"]
    query_ops = forward * len(test[1]) / b
    fit_transfer = spec["fit_steps"] * b * 65 * 8
    query_transfer = len(test[1]) * 65 * 8
    update_transfer = b * 65 * 8
    return {
        "model": "small_dense_transformer",
        "device": "cuda",
        "status": "complete",
        "validation": validation_quality,
        "test": test_quality,
        "fit_seconds": fit_seconds,
        "query_seconds": query_seconds,
        "update_supported": True,
        "update_seconds": update_seconds,
        "cold_latency_us_per_byte": cold * 1e6 / len(batch_x),
        "warm_latency_us_per_byte": statistics.median(warm) * 1e6 / len(batch_x),
        "throughput_bytes_per_second": len(test[1]) / query_seconds,
        "fit_work_units": int(fit_ops),
        "query_work_units": int(query_ops),
        "work_units_are_estimates": True,
        "resident_state_bytes": int(parameter_bytes + optimizer_bytes),
        "peak_host_rss_bytes": max(fit_ram, query_ram, update_ram),
        "peak_cuda_allocated_bytes": max(fit_gpu, query_gpu, update_gpu),
        "fit_host_device_transfer_bytes": fit_transfer,
        "query_host_device_transfer_bytes": query_transfer,
        "update_host_device_transfer_bytes": update_transfer,
        "workload_seconds": {str(r): fit_seconds + r * query_seconds for r in (1, 4, 16)},
    }


def run() -> dict:
    root = project_root()
    contract_path = root / CONTRACT
    if _sha256(contract_path) != CONTRACT_SHA256:
        raise RuntimeError("calibration contract changed after preregistration")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    registry = root / contract["corpus"]["registry"]
    if _sha256(registry) != contract["corpus"]["registry_sha256"]:
        raise RuntimeError("frozen corpus registry mismatch")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required by the frozen calibration contract")

    started = time.perf_counter()
    roles, acquisition_bytes = _load_corpus(root)
    acquisition_seconds = time.perf_counter() - started
    observed = {role: {"files": len(files), "bytes": sum(len(raw) for _, raw in files)}
                for role, files in roles.items()}
    if observed != contract["corpus"]["roles"]:
        raise RuntimeError("frozen corpus role counts changed")
    validation = _examples(roles["validation"], 64, 8192)
    test = _examples(roles["test"], 64)
    records = []

    ppm = PPMDModel(5)
    ppm_ops = [0]

    def fit_ppm():
        for _, raw in roles["train"]:
            history: tuple[int, ...] = ()
            for target in raw:
                ppm.update(history, target)
                history = (*history[-4:], target)
                ppm_ops[0] += min(5, len(history)) + 1
        ppm.prune(4000)

    records.append(_cpu_record(
        "ppm_d_order5", fit_ppm, lambda x: ppm.distribution(tuple(map(int, x))),
        lambda x, y: ppm.update(tuple(map(int, x[-5:])), y), ppm.state_bytes,
        lambda: ppm_ops[0], lambda: 256 * 7, validation, test, 7,
    ))

    ctw = CTWByteModel(2)
    ctw_ops = [0]

    def fit_ctw():
        for _, raw in roles["train"]:
            ctw.fit_file(tuple(raw))
            ctw_ops[0] += max(0, len(raw) - 2) * 3
        ctw.finalize()

    def update_ctw(x, y):
        ctw.root.update(tuple(reversed(tuple(map(int, x[-2:])))), y)
        ctw.finalize()

    records.append(_cpu_record(
        "ctw_depth2", fit_ctw, lambda x: ctw.distribution(tuple(map(int, x))),
        update_ctw, ctw.state_bytes, lambda: ctw_ops[0], lambda: 256 * 3,
        validation, test, 7,
    ))

    training = CompressionTraining(
        tuple(ByteFile(index, tuple(raw)) for index, (_, raw) in enumerate(roles["train"])),
        tuple(ByteFile(10000 + index, tuple(raw))
              for index, (_, raw) in enumerate(roles["validation"])),
        acquisition_bytes,
    )
    dense = DenseAR(0)
    records.append(_cpu_record(
        "dense_autoregressive_order5", lambda: dense.fit(training, 256, 5),
        lambda x: dense.query(ByteContext(0, tuple(map(int, x))), 1),
        lambda x, y: dense.update(ByteContext(0, tuple(map(int, x))), y),
        dense.state_bytes, lambda: dense.fit_ops, lambda: dense.last_ops,
        validation, test, 7,
    ))

    retrieval = LocalRetrieval()
    records.append(_cpu_record(
        "bounded_local_retrieval", lambda: retrieval.fit(roles["train"]),
        retrieval.distribution, retrieval.update, retrieval.state_bytes,
        lambda: retrieval.fit_ops, lambda: 64 * 32 + 256,
        validation, test, 7,
    ))
    records.append(_transformer_record(
        roles["train"], validation, test, contract["models"]["small_dense_transformer"]
    ))
    return {
        "schema_version": 1,
        "calibration_id": CALIBRATION_ID,
        "cycle": 228,
        "kind": "systems_calibration_not_scientific_experiment",
        "scientific_evidence": False,
        "g1_window_increment": False,
        "contract_path": CONTRACT,
        "contract_sha256": CONTRACT_SHA256,
        "corpus_registry_sha256": contract["corpus"]["registry_sha256"],
        "corpus": observed,
        "acquisition_bytes": acquisition_bytes,
        "acquisition_seconds": acquisition_seconds,
        "validation_positions": len(validation[1]),
        "test_positions": len(test[1]),
        "environment": {
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(0),
            "device_count": torch.cuda.device_count(),
        },
        "models": records,
        "interpretation_allowed": "systems measurement only; no hypothesis, confidence, Pareto or promotion update",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()
    result = run()
    path = project_root() / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    print(path)


if __name__ == "__main__":
    main()
