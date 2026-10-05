"""Fresh MUC v2 development comparison: fixed ranking, rejection and full costs."""
import hashlib
import importlib
import math
import statistics
import time
import tracemalloc

from ..muc02_negatives_stage import ROLES
from ..muc02_negatives_task import diagnostic_queries, fresh_worlds
from ..muc_contract import parse_statement
from ..utils import sha256_json
from .mutable_contact_ledger_v2 import checked_answers, percentile

BENCHMARK_VERSION = "mutable_contact_ledger_hard_negatives_v1"


def selection_diagnostics(system, world, seed, k, d, index, *, queries_override=None):
    queries, rows = diagnostic_queries(world, seed, k, d, index) if queries_override is None else (queries_override, tuple(parse_statement(s) for s in world.statements))
    keys = [f"{row[1]} {row[2]}" for row in rows]
    observations, flops, preparation = [], 0, 0
    for subject, relation in queries:
        query = f"{subject} {relation}"
        system.synchronize()
        tick = time.perf_counter_ns()
        probabilities = system.scores(query, keys)
        system.synchronize()
        elapsed = (time.perf_counter_ns() - tick) / 1000
        if len(probabilities) != len(rows) or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
            raise ValueError("Dense diagnostic probability coverage/validity mismatch")
        # Gold selection is computed only after the score vector was produced.
        matches = [i for i, row in enumerate(rows) if (row[1], row[2]) == (subject, relation)]
        latest = max(matches, key=lambda i: rows[i][0]) if matches else None
        best = max(range(len(rows)), key=lambda i: (probabilities[i], rows[i][0]))
        maximum = probabilities[best]
        reject = maximum < .5
        negative = [i for i in range(len(rows)) if i not in matches]
        same_subject = [i for i in negative if rows[i][1] == subject]
        same_relation = [i for i in negative if rows[i][2] == relation]
        observations.append({"query": query, "known": bool(matches), "unknown_type": None if matches else "subject" if subject.endswith("999") else "relation",
                             "selected_key": keys[best], "selected_timestamp": rows[best][0], "gold_timestamp": rows[latest][0] if latest is not None else None,
                             "top1_correct": best == latest, "accepted_correct": best == latest and not reject,
                             "rejected": reject, "max_probability": maximum,
                             "positive_probability": probabilities[latest] if latest is not None else None,
                             "pair_fp": sum(probabilities[i] >= .5 for i in negative), "pair_negatives": len(negative),
                             "subject_fp": sum(probabilities[i] >= .5 for i in same_subject), "subject_negatives": len(same_subject),
                             "relation_fp": sum(probabilities[i] >= .5 for i in same_relation), "relation_negatives": len(same_relation),
                             "latency_us": elapsed, "rows_scored": len(rows)})
        flops += system.model.estimated_forward_flops(len(rows))
        preparation += sum(system.model.length + len(query) + len(key) + 3 for key in keys) + 3 * len(keys)
    return {"observations": observations, "estimated_flops": flops, "preparation_ops": preparation,
            "latency_us": sum(o["latency_us"] for o in observations)}


def diagnostic_metrics(diagnostics, *, worlds_expected=15):
    observations = [o for group in diagnostics for o in group["observations"]]
    known = [o for o in observations if o["known"]]
    unknown = [o for o in observations if not o["known"]]
    if worlds_expected < 1 or len(diagnostics) != worlds_expected or len(known) != 2 * worlds_expected or len(unknown) != 2 * worlds_expected:
        raise ValueError("Fixed diagnostic strata coverage mismatch")
    rate = lambda rows, name: statistics.fmean(float(o[name]) for o in rows)
    ratio = lambda rows, num, den: sum(o[num] for o in rows) / sum(o[den] for o in rows)
    return {"fact_top1_accuracy": rate(known, "top1_correct"), "accepted_fact_accuracy": rate(known, "accepted_correct"),
            "known_false_abstention": rate(known, "rejected"), "dense_unknown_rejection": rate(unknown, "rejected"),
            "unknown_subject_rejection": rate([o for o in unknown if o["unknown_type"] == "subject"], "rejected"),
            "unknown_relation_rejection": rate([o for o in unknown if o["unknown_type"] == "relation"], "rejected"),
            "pair_false_positive_rate": ratio(known, "pair_fp", "pair_negatives"),
            "pair_false_negative_rate": statistics.fmean(o["positive_probability"] < .5 for o in known),
            "hard_subject_fpr": ratio(known, "subject_fp", "subject_negatives"),
            "hard_relation_fpr": ratio(known, "relation_fp", "relation_negatives")}


def run_trial(system, k, d, seed, fit_report, learned=True, data_sink=None, *, worlds_provider=None, diagnostic_provider=None):
    tick = time.perf_counter()
    worlds = fresh_worlds(seed, "D", k, d, data_sink) if worlds_provider is None else worlds_provider()
    dev_generation_seconds = time.perf_counter() - tick
    correct, flags, latencies, ingest, updates, costs, diagnostics, answers, invalid = [], [], [], [], [], [], [], [], []
    for index, world in enumerate(worlds):
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
        system.synchronize()
        tick = time.perf_counter_ns()
        system.warmup(session)
        system.synchronize()
        warmup_us = (time.perf_counter_ns() - tick) / 1000
        world_answers = []
        for question in world.questions:
            system.synchronize()
            tick = time.perf_counter_ns()
            answer = checked_answers(session.answer_batch((question.text,)), 1)[0]
            system.synchronize()
            latencies.append((time.perf_counter_ns() - tick) / 1000)
            world_answers.append(answer)
            invalid.append(answer != "UNKNOWN" and not (len(answer) == 5 and answer.startswith("ED") and answer[2:].isdigit()))
            correct.append(answer == question.answer)
            flags.append(question)
        answers.append({"predictions": world_answers, "expected": [q.answer for q in world.questions]})
        cost = session.cost_report()
        cost["warmup_us"] = warmup_us
        if cost["query_count"] != 16:
            raise ValueError("Scored E2E denominator mismatch")
        required = ("query_ops", "input_ops", "search_ops", "update_ops", "build_ops", "preprocessing_ops", "state_bytes", "peak_state_bytes", "bytes_touched")
        if any(not math.isfinite(float(cost[name])) or cost[name] < 0 for name in required):
            raise ValueError("Invalid world cost")
        costs.append(cost)
        if learned:
            provider = diagnostic_provider or selection_diagnostics
            diagnostics.append(provider(system, world, seed, k, d, index))
    if len(correct) != 240 or len(worlds) != 15:
        raise ValueError("Frozen dev coverage mismatch")
    subset = lambda fn: statistics.fmean(float(ok) for ok, flag in zip(correct, flags, strict=True) if fn(flag))
    mean = lambda name: statistics.fmean(c[name] for c in costs)
    fit = system.fit_cost_report()
    share = (fit["fit_ops"] + fit["preprocessing_ops"]) / 135
    workload = lambda r: share + sum(mean(n) for n in ("input_ops", "build_ops", "update_ops", "preprocessing_ops", "warmup_ops")) + r * mean("query_ops")
    return {"status": "complete", "knowledge_size": k, "reasoning_depth": d, "seed": seed,
            "query_count": 240, "accuracy": statistics.fmean(correct), "warm_accuracy": statistics.fmean(correct),
            "e2e_known_accuracy": subset(lambda q: not q.unknown), "e2e_unknown_rejection": subset(lambda q: q.unknown),
            "continual_new_fact_accuracy": subset(lambda q: q.replacement_affected), "continual_retention": subset(lambda q: q.unchanged_retention),
            "near_equivalent_accuracy": subset(lambda q: q.unknown), "stable_rollout_rate": 1 - statistics.fmean(invalid),
            "mean_query_ops": mean("query_ops") / 16, "mean_warm_query_ops": mean("query_ops") / 16,
            "mean_search_ops": mean("search_ops") / 16, "mean_input_ops": mean("input_ops") / len(worlds[0].statements),
            "mean_bytes_touched": mean("bytes_touched") / 16, "update_ops": mean("update_ops"),
            "state_bytes": max(c["state_bytes"] for c in costs), "peak_state_bytes": max(c["peak_state_bytes"] for c in costs),
            "fit_seconds": fit["fit_seconds"], "fit_ops": fit["fit_ops"], "fit_peak_bytes": fit["fit_peak_bytes"], "preprocessing_ops": fit["preprocessing_ops"],
            "p50_latency_us": percentile(latencies, .5), "p95_latency_us": percentile(latencies, .95), "update_latency_us": percentile(updates, .95),
            "latency_measurement": "synchronized_end_to_end_batch_1", "latency_samples_us": latencies,
            "ingest_latency_samples_us": ingest, "update_latency_samples_us": updates, "world_costs": costs,
            "workload_ops_r1": workload(1), "workload_ops_r4": workload(4), "workload_ops_r16": workload(16),
            "cost_contract": {"unit": "one mean dev world, 16 E2E queries repeated R times; dense diagnostics separate", "fit_worlds": 135, "fit_share_ops": share,
                              "counts_are_estimates": True, "ops_kind": fit["ops_kind"]},
            "development_sha256": sha256_json([{"statements": w.statements, "questions": [(q.text, q.answer) for q in w.questions]} for w in worlds]),
            "development_generation_seconds": dev_generation_seconds,
            "diagnostics": diagnostics, "diagnostic_flops": sum(group["estimated_flops"] for group in diagnostics),
            "diagnostic_preparation_ops": sum(group["preparation_ops"] for group in diagnostics),
            "diagnostic_seconds": sum(group["latency_us"] for group in diagnostics) / 1e6,
            "answers": answers, "calibration": {"fit_report": fit_report, "world_count": 15, "parser_failures": sum(c["parser_failures"] for c in costs)},
            **(diagnostic_metrics(diagnostics) if learned else {})}


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    matrix, protocol = plan["matrix"], plan["muc02_negatives_protocol"]
    if (tuple(plan["candidates"]) != ROLES or len(matrix["seeds"]) != 5 or len(set(matrix["seeds"])) != 5
            or matrix["knowledge_sizes"] != [32, 128, 512] or matrix["reasoning_depths"] != [1, 2, 4] or matrix["queries_per_cell"] != 16):
        raise ValueError("Frozen five-pair matrix mismatch")
    learned = candidate_name != "symbolic_last_write_graph_v2"
    binding = protocol["roles"].get(candidate_name)
    if learned and binding is None:
        raise ValueError("Unregistered sampling role")
    seeds = [matrix["seeds"][binding["seed_index"]]] if learned else matrix["seeds"]
    trials = []
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    for seed in seeds:
        if learned:
            tick = time.perf_counter()
            train = tuple({"statements": world.statements, "knowledge_size": k, "reasoning_depth": d}
                          for k in matrix["knowledge_sizes"] for d in matrix["reasoning_depths"] for world in fresh_worlds(seed, "T", k, d, data_sink))
            data_seconds = time.perf_counter() - tick
            data_digest = sha256_json(train)
            if phase_sink:
                phase_sink("fit")
            tracemalloc.start()
            tick = time.perf_counter()
            try:
                system = module.Candidate(seed=seed, protocol={**protocol, "negative_arm": binding["arm"]})
                digest = hashlib.sha256()
                for value in system.model.state_dict().values():
                    digest.update(value.detach().cpu().numpy().tobytes())
                initial_digest = digest.hexdigest()
                fit_report = system.fit(train, ())
                system.synchronize()
                fit_seconds = time.perf_counter() - tick
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            system.record_fit_resources(fit_seconds, peak)
            fit_report.update(initial_parameters_sha256=initial_digest, training_worlds_sha256=data_digest,
                              data_generation_seconds=data_seconds, seed=seed, arm=binding["arm"])
            if fit_seconds > protocol["fit_seconds_cap"] or fit_report["optimizer_steps"] != 192:
                raise TimeoutError("Fixed 192-step fit cap/coverage failed")
            del train
        else:
            system = module.Candidate(seed=seed, protocol=protocol)
            system.record_fit_resources(0, 0)
            fit_report = {"optimizer_steps": 0, "selection": "no fit; classical last-write map"}
        if fit_sink:
            fit_sink({"seed": seed, "candidate": candidate_name, "fit_report": fit_report, "fit_cost": system.fit_cost_report()})
        if phase_sink:
            phase_sink("evaluation")
        for k in matrix["knowledge_sizes"]:
            for d in matrix["reasoning_depths"]:
                trial = run_trial(system, k, d, seed, fit_report, learned, data_sink)
                trials.append(trial)
                if trial_sink:
                    trial_sink(trial)
        del system
    if len(trials) != (9 if learned else 45):
        raise ValueError("Role/seed/cell coverage mismatch")
    if phase_sink:
        phase_sink("complete")
    return trials
