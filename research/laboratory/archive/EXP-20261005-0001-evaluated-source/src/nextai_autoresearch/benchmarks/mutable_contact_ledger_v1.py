"""Frozen evaluator for the single MUC-01 baseline calibration."""
from __future__ import annotations

import importlib
import statistics
import time
import tracemalloc
from typing import Any

from nextai_autoresearch.muc01_task import PublicWorld, split_worlds


BENCHMARK_VERSION = "mutable_contact_ledger_v1"


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * q))] if ordered else 0.0


def _public(worlds: tuple[PublicWorld, ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"statements": world.statements, "questions": tuple({"text": q.text, "answer": q.answer} for q in world.questions)} for world in worlds)


def run_trial(system: Any, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, fit_report: dict[str, Any]) -> dict[str, Any]:
    if queries_per_cell != 16:
        raise ValueError("MUC-01 freezes sixteen questions per world")
    _, _, final = split_worlds(knowledge_size, reasoning_depth, seed)

    predictions: list[str] = []
    expected: list[str] = []
    flags: list[Any] = []
    query_latencies: list[float] = []
    update_latencies: list[float] = []
    ingest_latencies: list[float] = []
    for world in final:
        session = system.new_session()
        for statement in world.statements:
            started = time.perf_counter_ns()
            session.ingest(statement)
            elapsed = (time.perf_counter_ns() - started) / 1000.0
            ingest_latencies.append(elapsed)
            if "replacing" in statement or getattr(session, "last_replaced", False):
                update_latencies.append(elapsed)
        started = time.perf_counter_ns()
        answers = session.answer_batch(tuple(q.text for q in world.questions))
        elapsed = (time.perf_counter_ns() - started) / 1000.0
        per_query = elapsed / len(world.questions)
        query_latencies.extend([per_query] * len(world.questions))
        predictions.extend(str(value).strip() for value in answers)
        expected.extend(q.answer for q in world.questions)
        flags.extend(world.questions)
    correct = [prediction == target for prediction, target in zip(predictions, expected)]
    subset = lambda predicate: statistics.fmean(float(ok) for ok, flag in zip(correct, flags) if predicate(flag))
    invalid = [p != "UNKNOWN" and not (len(p) == 5 and p.startswith("EF") and p[2:].isdigit()) for p in predictions]
    costs = system.cost_report()
    query_ops = float(costs.get("mean_query_ops", knowledge_size * reasoning_depth))
    state_bytes = float(costs.get("state_bytes", 0))
    update_ops = float(costs.get("update_ops", 1))
    trial = {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": len(expected), "accuracy": statistics.fmean(map(float, correct)),
        "warm_accuracy": subset(lambda _: True), "continual_new_fact_accuracy": subset(lambda q: q.replacement_affected),
        "continual_retention": subset(lambda q: q.unchanged_retention),
        "exact_span_accuracy": subset(lambda q: q.unseen_composition) if reasoning_depth > 1 else subset(lambda _: True),
        "near_equivalent_accuracy": subset(lambda q: q.unknown), "stable_rollout_rate": 1.0 - statistics.fmean(map(float, invalid)),
        "mean_query_ops": query_ops, "mean_warm_query_ops": query_ops,
        "p50_latency_us": _percentile(query_latencies, .50), "p95_latency_us": _percentile(query_latencies, .95),
        "fit_seconds": float(costs.get("fit_seconds", 0)), "fit_ops": float(costs.get("fit_ops", 0)),
        "preprocessing_ops": float(costs.get("preprocessing_ops", 0)), "fit_peak_bytes": float(costs.get("fit_peak_bytes", 0)),
        "state_bytes": state_bytes, "peak_state_bytes": float(costs.get("peak_state_bytes", state_bytes)),
        "mean_input_ops": float(costs.get("mean_input_ops", 0)), "mean_search_ops": float(costs.get("mean_search_ops", 0)),
        "mean_bytes_touched": float(costs.get("mean_bytes_touched", 0)), "update_ops": update_ops,
        "update_latency_us": _percentile(update_latencies or ingest_latencies, .95),
        "workload_ops_r1": float(costs.get("build_ops", 0)) + update_ops + query_ops,
        "workload_ops_r4": float(costs.get("build_ops", 0)) + update_ops + 4 * query_ops,
        "workload_ops_r16": float(costs.get("build_ops", 0)) + update_ops + 16 * query_ops,
        "calibration": {"replacement_accuracy": subset(lambda q: q.replacement_affected), "retention_accuracy": subset(lambda q: q.unchanged_retention), "unknown_accuracy": subset(lambda q: q.unknown), "unseen_composition_accuracy": subset(lambda q: q.unseen_composition) if reasoning_depth > 1 else None, "invalid_answer_rate": statistics.fmean(map(float, invalid)), "parser_failures": int(costs.get("parser_failures", 0)), "fit_report": fit_report, "ingestion_p95_us": _percentile(ingest_latencies, .95), "update_p50_us": _percentile(update_latencies or ingest_latencies, .50)},
    }
    return trial


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    protocol = plan["muc01_calibration_protocol"]
    if len(matrix["seeds"]) != 1:
        raise ValueError("MUC-01 calibration permits one runner-random seed")
    seed = matrix["seeds"][0]
    train_public = []
    development_public = []
    for k in matrix["knowledge_sizes"]:
        for d in matrix["reasoning_depths"]:
            train, development, _ = split_worlds(k, d, seed)
            train_public.extend(_public(train))
            development_public.extend(_public(development))
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    system = module.Candidate(seed=seed, protocol=protocol)
    tracemalloc.start()
    fit_started = time.perf_counter()
    fit_report = system.fit(tuple(train_public), tuple(development_public))
    fit_seconds = time.perf_counter() - fit_started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    system.record_fit_resources(fit_seconds, fit_peak)
    return [run_trial(system, k, d, matrix["queries_per_cell"], seed, fit_report) for k in matrix["knowledge_sizes"] for d in matrix["reasoning_depths"]]
