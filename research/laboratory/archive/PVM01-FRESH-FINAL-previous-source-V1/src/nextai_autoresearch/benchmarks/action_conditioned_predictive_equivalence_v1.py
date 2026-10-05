from __future__ import annotations

import itertools
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

from .successor_graph_v1 import load_candidate, percentile
from ..predictive_state_core import OracleDataset, PredictiveDataset, TransitionRecord, context


BENCHMARK_VERSION = "action_conditioned_predictive_equivalence_v1"
BASE = {(0, 0): 1, (1, 0): 2, (2, 0): 3, (3, 0): 0,
        (0, 1): 2, (1, 1): 0, (2, 1): 3, (3, 1): 1}
REUSE_SCHEDULE = (1, 4, 16)


@dataclass(frozen=True)
class Task:
    history: tuple[int, ...]
    near_history: tuple[int, ...]
    actions: tuple[int, ...]
    expected: tuple[int, ...]
    near_expected: tuple[int, ...]
    best_action: int
    near_best_action: int


def outcome_map(seed: int) -> dict[int, int]:
    flip = seed & 1
    return {state: ((state & 1) ^ flip) * 2 + int(state == 3) for state in range(4)}


def state_histories(size: int, seed: int, outcomes: dict[int, int]) -> dict[int, tuple[tuple[int, ...], ...]]:
    rng = random.Random(seed ^ size * 65537)
    result: dict[int, list[tuple[int, ...]]] = {state: [] for state in range(4)}
    for state in range(4):
        for prior_action in (0, 1):
            prior = next(source for source in range(4) if BASE[(source, prior_action)] == state)
            prefix = tuple(8 + rng.randrange(8) for _ in range(size))
            result[state].append((*prefix, outcomes[prior], 4 + prior_action, outcomes[state]))
    return {state: tuple(rows) for state, rows in result.items()}


def make_dataset(size: int, seed: int, transitions=None, only=None):
    transitions = dict(transitions or BASE)
    outcomes = outcome_map(seed)
    histories = state_histories(size, seed, outcomes)
    records = []
    for state in range(4):
        for history in histories[state]:
            for action in (0, 1):
                if only is not None and (state, action) not in only:
                    continue
                for repeat in range(8):
                    next_state = transitions[(state, action)] if repeat < 7 else state
                    next_history = (*history, 4 + action, outcomes[next_state])
                    records.append(TransitionRecord(history, action, outcomes[next_state], next_history))
    context_states = {context(history): state for state, rows in histories.items() for history in rows}
    return PredictiveDataset(tuple(records)), OracleDataset(tuple(records), context_states, transitions, outcomes), histories


def rollout(state: int, actions: tuple[int, ...], transitions, outcomes):
    result = []
    for action in actions:
        state = transitions[(state, action)]
        result.append(outcomes[state])
    return tuple(result)


def best_action(state: int, depth: int, transitions, outcomes) -> int:
    scored = []
    for program in itertools.product((0, 1), repeat=depth):
        reward = sum(value & 1 for value in rollout(state, program, transitions, outcomes))
        scored.append((reward, tuple(-value for value in program), program[0]))
    return max(scored)[2]


def make_tasks(size: int, depth: int, count: int, seed: int, transitions=None) -> tuple[Task, ...]:
    transitions = dict(transitions or BASE)
    outcomes = outcome_map(seed)
    histories = state_histories(size, seed, outcomes)
    rng = random.Random(seed ^ size * 8191 ^ depth * 104729)
    tasks = []
    for index in range(count):
        state = (0, 2)[index & 1]
        near_state = 2 - state
        actions = tuple(rng.randrange(2) for _ in range(depth))
        if rollout(state, actions, transitions, outcomes) == rollout(near_state, actions, transitions, outcomes):
            actions = (0, *actions[1:])
        suffix = histories[state][index % 2][-3:]
        near_suffix = histories[near_state][index % 2][-3:]
        prefix = tuple(8 + rng.randrange(8) for _ in range(size))
        near_prefix = tuple(8 + rng.randrange(8) for _ in range(size))
        tasks.append(Task((*prefix, *suffix), (*near_prefix, *near_suffix), actions,
                          rollout(state, actions, transitions, outcomes),
                          rollout(near_state, actions, transitions, outcomes),
                          best_action(state, depth, transitions, outcomes),
                          best_action(near_state, depth, transitions, outcomes)))
    return tuple(tasks)


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    data, oracle_data, _ = make_dataset(knowledge_size, seed)
    tasks = make_tasks(knowledge_size, reasoning_depth, queries_per_cell, seed)
    candidate = load_candidate(candidate_name, seed)
    fit_data = oracle_data if candidate_name == "oracle_predictive_state" else data
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, knowledge_size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    initial_fit_ops, peak_state = float(candidate.fit_ops), candidate.state_bytes()

    def measure(near: bool = False):
        nonlocal peak_state
        rows = []
        for task in tasks:
            history = task.near_history if near else task.history
            expected = task.near_expected if near else task.expected
            plan = task.near_best_action if near else task.best_action
            tick = time.perf_counter_ns()
            answer, action = candidate.query(history, task.actions, reasoning_depth)
            rows.append({"correct": answer == expected and action == plan,
                         "forecast": answer == expected, "plan": action == plan,
                         "latency": (time.perf_counter_ns() - tick) / 1000,
                         "ops": candidate.last_ops, "input": candidate.last_input_ops,
                         "search": candidate.last_search_ops, "execution": candidate.last_execution_ops,
                         "bytes": candidate.state_bytes()})
            peak_state = max(peak_state, candidate.state_bytes())
        return rows

    cold, warm, near = measure(), measure(), measure(True)
    changed = dict(BASE)
    changed[(0, 1)] = 3
    delta, oracle_delta, _ = make_dataset(knowledge_size, seed, changed, {(0, 1)})
    tick = time.perf_counter_ns()
    candidate.update(oracle_delta if candidate_name == "oracle_predictive_state" else delta)
    update_latency = (time.perf_counter_ns() - tick) / 1000
    update_ops = float(candidate.update_ops)
    _, _, histories = make_dataset(knowledge_size, seed)
    outcomes = outcome_map(seed)
    new_actions = (1,) * reasoning_depth
    new_history = histories[0][0]
    answer, action = candidate.query(new_history, new_actions, reasoning_depth)
    new_correct = (answer == rollout(0, new_actions, changed, outcomes)
                   and action == best_action(0, reasoning_depth, changed, outcomes))
    retained_actions = (0,) * reasoning_depth
    retained_history = histories[2][0]
    answer, action = candidate.query(retained_history, retained_actions, reasoning_depth)
    retained = (answer == rollout(2, retained_actions, changed, outcomes)
                and action == best_action(2, reasoning_depth, changed, outcomes))
    after_query_ops = float(candidate.last_ops)
    peak_state = max(peak_state, candidate.state_bytes())
    workloads = {reuse: update_ops + reuse * after_query_ops for reuse in REUSE_SCHEDULE}

    mean = lambda rows, key: statistics.fmean(float(row[key]) for row in rows)
    accuracy = lambda rows, key="correct": statistics.fmean(float(row[key]) for row in rows)
    return {
        "status": "complete", "knowledge_size": knowledge_size, "reasoning_depth": reasoning_depth,
        "seed": seed, "query_count": queries_per_cell, "accuracy": accuracy(cold),
        "warm_accuracy": accuracy(warm), "near_equivalent_accuracy": accuracy(near),
        "reuse_precision": 0.0, "reuse_coverage": 0.0, "false_reuse_rate": 0.0,
        "continual_new_fact_accuracy": float(new_correct), "continual_retention": float(retained),
        "forecast_accuracy": accuracy(cold, "forecast"), "planning_accuracy": accuracy(cold, "plan"),
        "near_forecast_accuracy": accuracy(near, "forecast"), "near_planning_accuracy": accuracy(near, "plan"),
        "fit_seconds": fit_seconds, "fit_ops": initial_fit_ops, "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": mean(cold, "ops"), "mean_warm_query_ops": mean(warm, "ops"),
        "mean_input_ops": mean(cold, "input"), "mean_alignment_ops": mean(cold, "search"),
        "mean_execution_ops": mean(cold, "execution"), "mean_bytes_loaded": mean(cold, "bytes"),
        "p50_latency_us": percentile([row["latency"] for row in cold], 0.5),
        "p95_latency_us": percentile([row["latency"] for row in cold], 0.95),
        "warm_p50_latency_us": percentile([row["latency"] for row in warm], 0.5),
        "warm_p95_latency_us": percentile([row["latency"] for row in warm], 0.95),
        "state_bytes": float(candidate.state_bytes()), "peak_state_bytes": float(max(peak_state, fit_peak)),
        "update_ops": update_ops, "cumulative_update_ops": update_ops,
        "mean_invalidated_entries": float(len(delta.records)), "update_latency_us": update_latency,
        "workload_ops_r1": workloads[1], "workload_ops_r4": workloads[4],
        "workload_ops_r16": workloads[16],
        "workload_ops": initial_fit_ops + sum(row["ops"] for row in cold + near) + workloads[16],
        "raw_transition_records": float(len(data.records)),
        "raw_history_tokens": float(sum(len(row.history) for row in data.records)),
        "latent_state_labels_supplied": float(candidate_name == "oracle_predictive_state"),
        "episode_specific_observation_permutation": 1.0,
    }


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]), int(seed), maximum)
            for seed in matrix["seeds"] for size in matrix["knowledge_sizes"] for depth in matrix["reasoning_depths"]]
