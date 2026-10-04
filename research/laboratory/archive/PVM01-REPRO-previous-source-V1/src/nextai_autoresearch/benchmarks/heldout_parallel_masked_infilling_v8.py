from __future__ import annotations

import io
import random
import statistics
import time
import tokenize
import tracemalloc
from typing import Any

from .heldout_parallel_masked_infilling_v1 import (
    _load_corpus, _number, _run_case, load_candidate, percentile,
)
from ..masked_refinement_contract import ByteFile, MASK, MaskedTraining


BENCHMARK_VERSION = "heldout_parallel_masked_infilling_v8"
TRAIN_MAX_DEPTH = 2
TEST_DEPTHS = (3, 4, 5)
_PAIRS = {")": "(", "]": "[", "}": "{"}
_OPEN = frozenset(_PAIRS.values())
_CLOSE = frozenset(_PAIRS)


def delimiter_groups(data: bytes) -> tuple[tuple[bytes, int], ...]:
    """Return balanced real-Python delimiter traces, excluding strings/comments."""
    stack, trace, groups, maximum = [], bytearray(), [], 0
    try:
        tokens = tokenize.tokenize(io.BytesIO(data).readline)
        for token in tokens:
            symbol = token.string
            if token.type != tokenize.OP or symbol not in _OPEN | _CLOSE:
                continue
            if symbol in _OPEN:
                if not stack:
                    trace, maximum = bytearray(), 0
                stack.append(symbol)
                trace.extend(symbol.encode("ascii"))
                maximum = max(maximum, len(stack))
            elif stack and stack[-1] == _PAIRS[symbol]:
                trace.extend(symbol.encode("ascii"))
                stack.pop()
                if not stack:
                    groups.append((bytes(trace), maximum))
            else:
                stack, trace, maximum = [], bytearray(), 0
    except (IndentationError, tokenize.TokenError):
        pass
    return tuple(groups)


def _permute(data: bytes, permutation: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(permutation[value] for value in data)


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
                output.append(ByteFile(next(slots), _permute(shallow, permutation)))
                used += len(shallow)
            if used >= budget:
                break
        return tuple(output), used

    train, train_bytes = encoded(roles["train"], knowledge_size * 1024)
    validation, validation_bytes = encoded(
        roles["validation"], min(4096, knowledge_size * 128)
    )
    tests = [(trace, depth) for _, data in roles["test"]
             for trace, depth in delimiter_groups(data) if depth in TEST_DEPTHS]
    selected = train_bytes + validation_bytes
    return (MaskedTraining(train, validation, 2 * acquisition + selected), tests,
            permutation)


def _stack_cases(tests, depth: int, count: int, seed: int,
                 permutation: tuple[int, ...]):
    eligible = [trace for trace, maximum in tests if maximum == depth]
    if not eligible:
        raise ValueError(f"no immutable depth-{depth} stack cases")
    rng = random.Random(seed ^ (depth << 12))
    rng.shuffle(eligible)
    slots = rng.sample(range(100, 9_999), len(eligible))
    cases = []
    for index in range(count):
        raw = eligible[index % len(eligible)]
        stack, position = [], None
        for offset, value in enumerate(raw.decode("ascii")):
            if value in _OPEN:
                stack.append(value)
            else:
                if len(stack) == depth and position is None:
                    position = offset
                stack.pop()
        if position is None:
            raise ValueError("depth-labelled trace lacks its target close")
        encoded = list(_permute(raw, permutation))
        target = encoded[position]
        encoded[position] = MASK
        cases.append((slots[index % len(slots)], tuple(encoded), (position,), (target,)))
    return cases


def _run_cell(candidate_name: str, size: int, depth: int, count: int,
              seed: int, maximum_depth: int, protocol: dict[str, Any]):
    training, tests, permutation = make_stack_training(size, seed)
    candidate = load_candidate(candidate_name, seed)
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(training, size, maximum_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    state = _number(candidate, "state_bytes")
    if state > int(protocol["state_budget_bytes"]):
        raise ValueError("state budget exceeded")
    rows = [_run_case(candidate, candidate_name, case, 1)
            for case in _stack_cases(tests, depth, count, seed, permutation)]
    query_ops = sum(row["query_ops"] for row in rows)
    fit_ops = _number(candidate, "fit_ops")
    base = training.acquisition_ops + fit_ops
    workloads = {h: base + h * query_ops for h in (1, 4, 16)}
    latencies = [value for row in rows for value in row["latency"]]
    return {
        "status": "complete", "world_family": f"stack_depth_{depth}",
        "span_length": 1, "knowledge_size": size, "reasoning_depth": depth,
        "refinement_rounds": 1, "seed": seed, "query_count": count,
        "accuracy": statistics.fmean(row["accuracy"] for row in rows),
        "warm_accuracy": statistics.fmean(row["accuracy"] for row in rows),
        "continual_retention": statistics.fmean(row["exact"] for row in rows),
        "exact_span_accuracy": statistics.fmean(row["exact"] for row in rows),
        "bits_per_byte": statistics.fmean(row["bits"] for row in rows),
        "critical_path_steps": max(row["critical"] for row in rows),
        "total_position_probabilities": sum(row["probabilities"] for row in rows),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops,
        "meta_fit_ops": _number(candidate, "meta_fit_ops", fit_ops),
        "data_acquisition_ops": float(training.acquisition_ops),
        "fit_peak_bytes": float(fit_peak), "mean_query_ops": query_ops / count,
        "mean_warm_query_ops": query_ops / count,
        "mean_input_ops": statistics.fmean(row["input_ops"] for row in rows),
        "mean_bytes_touched": statistics.fmean(row["bytes"] for row in rows),
        "p50_latency_us": percentile(latencies, 0.5),
        "p95_latency_us": percentile(latencies, 0.95),
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
