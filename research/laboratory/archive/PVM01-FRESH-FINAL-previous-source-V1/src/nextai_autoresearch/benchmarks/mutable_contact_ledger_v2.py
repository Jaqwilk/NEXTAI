"""Versioned calibration with exact coverage, per-world costs and true B1 timing."""
from __future__ import annotations

import importlib
import math
import statistics
import time
import tracemalloc

from ..muc02_task import training_worlds, calibration_worlds

BENCHMARK_VERSION = "mutable_contact_ledger_v2"


def percentile(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * q))] if ordered else 0.0


def checked_answers(answers, expected_count):
    if not isinstance(answers, (tuple, list)) or len(answers) != expected_count:
        raise ValueError(f"Expected exactly {expected_count} answers")
    if any(not isinstance(value, str) for value in answers):
        raise ValueError("Every answer must be a string")
    return tuple(value.strip() for value in answers)


def run_trial(system, k, d, queries, seed, fit_report, fit_worlds=135):
    if queries != 16:
        raise ValueError("v2 requires sixteen questions per world")
    worlds = calibration_worlds(k, d, seed)
    if len(worlds) != 15 or any(len(w.questions) != queries for w in worlds):
        raise ValueError("v2 world/question coverage mismatch")
    correct, flags, invalid, latencies, ingest, updates, costs, throughput = [], [], [], [], [], [], [], []
    for world in worlds:
        session = system.new_session()
        for statement in world.statements:
            system.synchronize()
            tick = time.perf_counter_ns()
            session.ingest(statement)
            system.synchronize()
            elapsed = (time.perf_counter_ns() - tick) / 1000
            ingest.append(elapsed)
            if session.last_replaced:
                updates.append(elapsed)
        # Warm-up is performed on a public dummy query and charged separately.
        tick = time.perf_counter_ns()
        system.warmup(session)
        warmup_us = (time.perf_counter_ns() - tick) / 1000
        for question in world.questions:
            system.synchronize()
            tick = time.perf_counter_ns()
            answer = checked_answers(session.answer_batch((question.text,)), 1)[0]
            system.synchronize()
            latencies.append((time.perf_counter_ns() - tick) / 1000)
            correct.append(answer == question.answer)
            flags.append(question)
            invalid.append(answer != "UNKNOWN" and not (len(answer) == 5 and answer.startswith("EF") and answer[2:].isdigit()))
        # Freeze the scored counters before the independently reported throughput run.
        cost = session.cost_report()
        cost["warmup_us"] = warmup_us
        system.synchronize()
        tick = time.perf_counter_ns()
        checked_answers(session.answer_batch(tuple(q.text for q in world.questions)), queries)
        system.synchronize()
        batch_us = (time.perf_counter_ns() - tick) / 1000
        throughput.append({"batch_size": queries, "elapsed_us": batch_us, "queries_per_second": queries * 1e6 / batch_us,
                           "extra_query_ops": session.cost_report()["query_ops"] - cost["query_ops"]})
        costs.append(cost)
    if len(correct) != len(worlds) * queries:
        raise ValueError("Scored answer coverage mismatch")
    required = ("query_ops", "input_ops", "search_ops", "update_ops", "build_ops", "preprocessing_ops", "state_bytes", "peak_state_bytes", "bytes_touched", "query_count")
    if any(any(name not in cost or not math.isfinite(float(cost[name])) or float(cost[name]) < 0 for name in required) for cost in costs):
        raise ValueError("Missing/nonfinite/negative world cost")
    if any(c["query_count"] != queries for c in costs):
        raise ValueError("Cost denominator differs from scored query count")
    subset = lambda fn: statistics.fmean(float(ok) for ok, flag in zip(correct, flags, strict=True) if fn(flag))
    mean = lambda name: statistics.fmean(float(c[name]) for c in costs)
    qops = mean("query_ops") / queries
    fit = system.fit_cost_report()
    fit_share = (float(fit["fit_ops"]) + float(fit["preprocessing_ops"])) / fit_worlds
    workload = lambda r: fit_share + mean("input_ops") + mean("build_ops") + mean("update_ops") + mean("preprocessing_ops") + mean("warmup_ops") + r * mean("query_ops")
    return {
        "status": "complete", "knowledge_size": k, "reasoning_depth": d, "seed": seed,
        "query_count": len(correct), "accuracy": statistics.fmean(map(float, correct)), "warm_accuracy": statistics.fmean(map(float, correct)),
        "continual_new_fact_accuracy": subset(lambda q: q.replacement_affected), "continual_retention": subset(lambda q: q.unchanged_retention),
        "exact_span_accuracy": subset(lambda q: q.unseen_composition) if d > 1 else None,
        "near_equivalent_accuracy": subset(lambda q: q.unknown), "stable_rollout_rate": 1 - statistics.fmean(map(float, invalid)),
        "mean_query_ops": qops, "mean_warm_query_ops": qops,
        "mean_search_ops": mean("search_ops") / queries, "mean_input_ops": mean("input_ops") / len(worlds[0].statements),
        "mean_bytes_touched": mean("bytes_touched") / queries, "update_ops": mean("update_ops"),
        "state_bytes": max(c["state_bytes"] for c in costs), "peak_state_bytes": max(c["peak_state_bytes"] for c in costs),
        "fit_seconds": fit["fit_seconds"], "fit_ops": fit["fit_ops"], "fit_peak_bytes": fit["fit_peak_bytes"],
        "preprocessing_ops": fit["preprocessing_ops"] + mean("preprocessing_ops"),
        "p50_latency_us": percentile(latencies, .5), "p95_latency_us": percentile(latencies, .95),
        "update_latency_us": percentile(updates, .95),
        "workload_ops_r1": workload(1), "workload_ops_r4": workload(4), "workload_ops_r16": workload(16),
        "latency_measurement": "synchronized_end_to_end_batch_1", "latency_samples_us": latencies,
        "ingest_latency_samples_us": ingest, "update_latency_samples_us": updates,
        "world_costs": costs, "throughput_samples": throughput,
        "cost_contract": {"unit": "one mean world, 16 queries repeated R times", "fit_worlds": fit_worlds,
                          "fit_share_ops": fit_share, "ops_kind": fit["ops_kind"], "counts_are_estimates": fit["counts_are_estimates"]},
        "calibration": {"fit_report": fit_report, "parser_failures": sum(c["parser_failures"] for c in costs),
                        "invalid_answer_rate": statistics.fmean(map(float, invalid)), "world_count": len(worlds)},
    }


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None):
    from ..audit_repair import ROLES
    matrix, protocol = plan["matrix"], plan["muc02_protocol"]
    if (candidate_name not in ROLES or matrix["knowledge_sizes"] != [32, 128, 512]
            or matrix["reasoning_depths"] != [1, 2, 4] or matrix["queries_per_cell"] != 16 or len(matrix["seeds"]) != 1):
        raise ValueError("v2 frozen roles/matrix mismatch")
    seed = matrix["seeds"][0]
    train, dev = [], []
    for k in matrix["knowledge_sizes"]:
        for d in matrix["reasoning_depths"]:
            first, second = training_worlds(k, d)
            public = lambda w: {"statements": w.statements, "questions": tuple({"text": q.text, "answer": q.answer} for q in w.questions), "knowledge_size": k, "reasoning_depth": d}
            train.extend(public(w) for w in first)
            dev.extend(public(w) for w in second)
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    system = module.Candidate(seed=seed, protocol=protocol)
    if phase_sink:
        phase_sink("fit")
    tracemalloc.start()
    tick = time.perf_counter()
    try:
        fit_report = system.fit(tuple(train), tuple(dev))
        fit_seconds = time.perf_counter() - tick
        _, fit_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    system.record_fit_resources(fit_seconds, fit_peak)
    if fit_seconds > protocol["fit_seconds_cap"]:
        raise TimeoutError("Fit exceeded v2 cap")
    if phase_sink:
        phase_sink("evaluation")
    trials = []
    for k in matrix["knowledge_sizes"]:
        for d in matrix["reasoning_depths"]:
            trial = run_trial(system, k, d, matrix["queries_per_cell"], seed, fit_report)
            trials.append(trial)
            if trial_sink:
                trial_sink(trial)
    if len(trials) != 9:
        raise ValueError("v2 cell coverage mismatch")
    if phase_sink:
        phase_sink("complete")
    return trials
