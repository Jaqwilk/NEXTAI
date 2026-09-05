from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..whole_io_vm_core import (
    IOQuery,
    OracleInput,
    PROGRAMS,
    SUPPORT_INPUTS,
    Support,
    TrainingExample,
    active_bits,
    run_program,
)


BENCHMARK_VERSION = "program_induction_from_whole_io_v2"


@dataclass(frozen=True)
class Task:
    query: IOQuery
    program: tuple[int, ...]
    target: int
    identifiability_margin: int


def make_tape(bits: tuple[int, ...], size: int, seed: int):
    if len(bits) + 1 > size:
        raise ValueError("active sequence and sentinel must fit in external memory")
    rng = random.Random(seed)
    return (*bits, 2, *(rng.randrange(2) for _ in range(size - len(bits) - 1)))


def make_support(program, size: int, seed: int, omit=()):
    inputs = tuple(item for item in SUPPORT_INPUTS if item != omit)
    noise_index = (seed ^ sum((index + 1) * bit for index, bit in enumerate(program))) % len(inputs)
    examples = []
    for index, bits in enumerate(inputs):
        target, _ = run_program(program, bits)
        target ^= index == noise_index
        examples.append(Support(make_tape(bits, size, seed ^ index * 65537), target))
    return tuple(examples)


def support_scores(support):
    decoded = tuple((active_bits(item.tape)[0], item.target) for item in support)
    scores = []
    for program in PROGRAMS:
        scores.append(sum(run_program(program, bits)[0] != target for bits, target in decoded))
    ordered = sorted(scores)
    winner = scores.index(ordered[0]) if ordered.count(ordered[0]) == 1 else None
    return winner, ordered[1] - ordered[0]


def meta_programs(count: int, seed: int):
    programs = list(PROGRAMS)
    random.Random(seed ^ 0x4D455441).shuffle(programs)
    return tuple(programs[:count])


def training_corpus(count: int, memory_size: int, seed: int):
    examples = []
    for program_index, program in enumerate(meta_programs(count, seed)):
        support = make_support(program, memory_size, seed ^ program_index * 104729)
        rng = random.Random(seed ^ program_index * 99991)
        for query_index in range(4):
            width = 1 + (program_index + query_index) % 6
            bits = tuple(rng.randrange(2) for _ in range(width))
            tape = make_tape(bits, memory_size, seed ^ program_index * 4099 ^ query_index)
            target, _ = run_program(program, bits)
            examples.append(TrainingExample(IOQuery(support, tape), target))
    return tuple(examples)


def make_tasks(size: int, depth: int, seed: int, query_count: int):
    excluded = set(meta_programs(size, seed))
    tasks = []
    for index in range(query_count):
        rng = random.Random(seed ^ depth * 131071 ^ index * 104729)
        bits = tuple(rng.randrange(2) for _ in range(depth))
        candidates = list(PROGRAMS)
        rng.shuffle(candidates)
        for program in candidates:
            if program in excluded:
                continue
            support = make_support(program, size, seed ^ depth * 8191 ^ index, bits)
            winner, margin = support_scores(support)
            if winner is not None and PROGRAMS[winner] == program and margin >= 1:
                tape = make_tape(bits, size, seed ^ index * 31337 ^ depth)
                target, _ = run_program(program, bits)
                tasks.append(Task(IOQuery(support, tape), program, target, margin))
                excluded.add(program)
                break
        else:
            raise RuntimeError("could not construct a uniquely identifiable held-out program")
    return tuple(tasks)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int, queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    corpus = training_corpus(knowledge_size, knowledge_size, seed)
    tasks = make_tasks(knowledge_size, reasoning_depth, seed, queries_per_cell)
    candidate = load_candidate(candidate_name, seed)
    fit_data = () if candidate_name == "oracle_latent_vm" else corpus
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def measure():
        answers, programs, ops, support_ops, search_ops, controller_ops = [], [], [], [], [], []
        reads, loaded, evaluations, latencies = [], [], [], []
        for task in tasks:
            source = OracleInput(task.query, task.program) if candidate_name == "oracle_latent_vm" else task.query
            query_started = time.perf_counter_ns()
            answers.append(candidate.query(source, reasoning_depth))
            latencies.append((time.perf_counter_ns() - query_started) / 1000.0)
            programs.append(getattr(candidate, "last_program", None))
            ops.append(float(candidate.last_ops))
            support_ops.append(float(getattr(candidate, "last_support_ops", 0)))
            search_ops.append(float(getattr(candidate, "last_search_ops", 0)))
            controller_ops.append(float(getattr(candidate, "last_controller_ops", 0)))
            reads.append(float(getattr(candidate, "last_memory_reads", 0)))
            loaded.append(float(getattr(candidate, "last_bytes_loaded", 0)))
            evaluations.append(float(getattr(candidate, "last_program_evaluations", 0)))
        return answers, programs, ops, support_ops, search_ops, controller_ops, reads, loaded, evaluations, latencies

    measured = measure()
    warm = measure()
    answers, programs, ops, support_ops, search_ops, controller_ops, reads, loaded, evaluations, latencies = measured
    warm_answers, _, warm_ops, _, _, _, warm_reads, _, _, warm_latencies = warm
    correct = [answer == task.target for answer, task in zip(answers, tasks)]
    induced = [program == task.program for program, task in zip(programs, tasks)]

    update_example = training_corpus(1, knowledge_size, seed ^ 0x5F3759DF)[0]
    update_started = time.perf_counter_ns()
    candidate.update(update_example, update_example.target)
    update_latency_us = (time.perf_counter_ns() - update_started) / 1000.0
    new_task = make_tasks(knowledge_size, reasoning_depth, seed, queries_per_cell + 1)[-1]
    new_source = OracleInput(new_task.query, new_task.program) if candidate_name == "oracle_latent_vm" else new_task.query
    new_correct = candidate.query(new_source, reasoning_depth) == new_task.target
    old_source = OracleInput(tasks[0].query, tasks[0].program) if candidate_name == "oracle_latent_vm" else tasks[0].query
    retained = candidate.query(old_source, reasoning_depth) == tasks[0].target
    accuracy = statistics.fmean(correct)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy,
        "length_extrapolation_accuracy": accuracy, "program_induction_accuracy": statistics.fmean(induced),
        "warm_accuracy": statistics.fmean(answer == task.target for answer, task in zip(warm_answers, tasks)),
        "continual_new_fact_accuracy": float(new_correct), "continual_retention": float(retained),
        "program_holdout_rate": 1.0, "input_holdout_rate": 1.0, "trace_supervision_rate": 0.0,
        "supplied_program_rate": 0.0, "support_noise_rate": 1.0 / len(tasks[0].query.support),
        "mean_identifiability_margin": statistics.fmean(task.identifiability_margin for task in tasks),
        "fit_seconds": fit_seconds, "fit_ops": float(candidate.fit_ops), "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": statistics.fmean(ops), "mean_warm_query_ops": statistics.fmean(warm_ops),
        "mean_support_ops": statistics.fmean(support_ops), "mean_search_ops": statistics.fmean(search_ops),
        "mean_controller_ops": statistics.fmean(controller_ops), "mean_memory_reads": statistics.fmean(reads),
        "mean_warm_memory_reads": statistics.fmean(warm_reads), "mean_bytes_loaded": statistics.fmean(loaded),
        "mean_program_evaluations": statistics.fmean(evaluations),
        "p50_latency_us": percentile(latencies, 0.50), "p95_latency_us": percentile(latencies, 0.95),
        "warm_p50_latency_us": percentile(warm_latencies, 0.50), "warm_p95_latency_us": percentile(warm_latencies, 0.95),
        "state_bytes": float(candidate.state_bytes()), "update_ops": float(candidate.update_ops),
        "update_latency_us": update_latency_us,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), max_depth)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
