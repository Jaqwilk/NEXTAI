from __future__ import annotations

from collections import Counter, defaultdict
import random
import statistics
import time
import tracemalloc
from typing import Any

from . import action_conditioned_predictive_equivalence_v1 as predictive
from . import behavioral_conjugacy_library_transfer_v1 as programs
from . import nonlinear_local_state_transfer_v1 as local
from .successor_graph_v1 import load_candidate, percentile
from ..mechanism_recombination_contract import (
    Pair, PrivilegedQuery, PrivilegedTraining, PrivilegedUpdate, PublicQuery,
    PublicTraining, PublicUpdate, TestWorld, TrainingWorld,
)


BENCHMARK_VERSION = "heldout_mechanism_recombination_v1"
ALPHABET = 12
STATE_COUNT = ALPHABET * ALPHABET
TRAIN_COMPOSITIONS = (
    ("A",), ("B",), ("C",),
    ("A", "A"), ("A", "B"), ("A", "C"),
    ("B", "A"), ("B", "B"), ("B", "C"),
    ("C", "A"), ("C", "C"),
)
HELDOUT_COMPOSITION = ("C", "B")
PRIVILEGED = {"oracle_composition_graph"}


def _source_functions(seed: int) -> dict[str, tuple[int, ...]]:
    _, _, tables, _ = programs.make_world(8, seed)
    program = tuple(next(iter(tables.values())))
    _, oracle, _ = predictive.make_dataset(8, seed)
    transition = tuple(
        (oracle.transitions[(x % 4, (x // 4) % 2)] * 3 + oracle.outcomes[x % 4])
        % ALPHABET
        for x in range(ALPHABET)
    )
    world = local.make_world(seed)
    dynamics = tuple(
        (target[0] * 4 + target[1]) % ALPHABET
        for _, target in world.training_cases[:ALPHABET]
    )
    return {"A": program, "B": transition, "C": dynamics}


def _feistel(function: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(
        y * ALPHABET + (x + function[y]) % ALPHABET
        for x in range(ALPHABET) for y in range(ALPHABET)
    )


def _compose(maps: dict[str, tuple[int, ...]], names: tuple[str, ...]) -> tuple[int, ...]:
    output = []
    for state in range(STATE_COUNT):
        for name in names:
            state = maps[name][state]
        output.append(state)
    return tuple(output)


def _maps(source_seed: int, score_seed: int) -> dict[tuple[str, ...], tuple[int, ...]]:
    permutation = list(range(STATE_COUNT))
    random.Random(score_seed ^ 0x5151).shuffle(permutation)
    inverse = [0] * STATE_COUNT
    for source, target in enumerate(permutation):
        inverse[target] = source
    modules = {
        name: tuple(permutation[mapping[inverse[state]]] for state in range(STATE_COUNT))
        for name, mapping in (
            (name, _feistel(function))
            for name, function in _source_functions(source_seed).items()
        )
    }
    return {
        names: _compose(modules, names)
        for names in (*TRAIN_COMPOSITIONS, HELDOUT_COMPOSITION)
    }


def _salt(names: tuple[str, ...]) -> int:
    return sum((index + 1) * ord(name) for index, name in enumerate(names))


def _indices(seed: int, names: tuple[str, ...], repeat: int) -> list[int]:
    values = list(range(STATE_COUNT))
    random.Random(seed ^ (_salt(names) << 8) ^ (repeat << 16) ^ 0x9191).shuffle(values)
    return values


def _apply(mapping: tuple[int, ...], state: int, depth: int) -> int:
    for _ in range(depth):
        state = mapping[state]
    return state


def _training(
    size: int, depth: int, count: int, score_seed: int, source_seed: int,
) -> tuple[PublicTraining, PrivilegedTraining, tuple[tuple[PublicQuery, int], ...], dict]:
    if score_seed == source_seed:
        raise ValueError("mechanism-source/scoring seed collision")
    if not 1 <= size <= 64 or not 1 <= count <= 32:
        raise ValueError("unsupported support/query size")
    maps = _maps(source_seed, score_seed)
    worlds: list[TrainingWorld] = []
    acquisition = 0
    for names in TRAIN_COMPOSITIONS:
        mapping = maps[names]
        for repeat in range(3):
            order = _indices(score_seed, names, repeat)
            support_states = order[:size]
            example_states = order[size:size + count]
            support = tuple(Pair(state, mapping[state]) for state in support_states)
            examples = tuple(Pair(state, mapping[state]) for state in example_states)
            acquisition += 2 * (len(support) + len(examples))
            worlds.append(TrainingWorld(support, examples))
    random.Random(score_seed ^ 0x3131).shuffle(worlds)

    test_order = _indices(score_seed, HELDOUT_COMPOSITION, 7)
    support_states = test_order[:size]
    query_states = test_order[size:size + count]
    mapping = maps[HELDOUT_COMPOSITION]
    support = tuple(Pair(state, mapping[state]) for state in support_states)
    slot = random.Random(score_seed ^ 0x7171).randrange(100, 10_000)
    queries = tuple(
        (PublicQuery(slot, state), _apply(mapping, state, depth))
        for state in query_states
    )
    acquisition += 2 * len(support) + len(queries)
    public = PublicTraining(tuple(worlds), (TestWorld(slot, support),), acquisition)
    audit = {
        "train_compositions": TRAIN_COMPOSITIONS,
        "heldout_composition": HELDOUT_COMPOSITION,
        "maps": maps,
        "support_states": tuple(support_states),
        "query_states": tuple(query_states),
    }
    return public, PrivilegedTraining(public), queries, audit


def _number(candidate: Any, name: str, default: float = 0.0) -> float:
    value = getattr(candidate, name, default)
    return float(value() if callable(value) else value)


def _answer(value: Any) -> int:
    if isinstance(value, (tuple, list)):
        if len(value) != 1:
            raise ValueError("candidate must return one opaque state")
        value = value[0]
    answer = int(round(float(value)))
    if not 0 <= answer < STATE_COUNT:
        raise ValueError("candidate returned an out-of-alphabet state")
    return answer


def _run_cell(
    candidate_name: str, size: int, depth: int, count: int, seed: int,
    source_seed: int, state_budget: int,
) -> dict[str, Any]:
    public, privileged, queries, _ = _training(size, depth, count, seed, source_seed)
    candidate = load_candidate(candidate_name, seed)
    fit_data = privileged if candidate_name in PRIVILEGED else public
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, size, depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    state = _number(candidate, "state_bytes")
    if state > state_budget:
        raise ValueError(f"state budget exceeded: {state} > {state_budget}")

    correct, latencies, bytes_touched = [], [], []
    query_ops = 0.0
    for query, target in queries:
        supplied = PrivilegedQuery(query, target) if candidate_name in PRIVILEGED else query
        tick = time.perf_counter_ns()
        prediction = _answer(candidate.query(supplied, depth))
        latencies.append((time.perf_counter_ns() - tick) / 1000.0)
        ops = _number(candidate, "last_ops")
        query_ops += ops
        bytes_touched.append(_number(candidate, "last_bytes_touched", ops * 8))
        correct.append(prediction == target)

    revealed_query, revealed_target = queries[-1]
    update = PublicUpdate(revealed_query, revealed_target)
    candidate.update(PrivilegedUpdate(update) if candidate_name in PRIVILEGED else update, None)
    after_ops = 0.0
    acquired = retained = False
    for index, (query, target) in enumerate((queries[-1], queries[0])):
        supplied = PrivilegedQuery(query, target) if candidate_name in PRIVILEGED else query
        value = _answer(candidate.query(supplied, depth)) == target
        after_ops += _number(candidate, "last_ops")
        if index == 0:
            acquired = value
        else:
            retained = value

    fit_ops = _number(candidate, "fit_ops")
    meta_fit_ops = _number(candidate, "meta_fit_ops", fit_ops)
    update_ops = _number(candidate, "update_ops")
    base = public.acquisition_ops + fit_ops + update_ops + after_ops
    workload = {h: base + h * query_ops for h in (1, 4, 16)}
    accuracy = statistics.fmean(correct)
    return {
        "status": "complete", "world_family": "heldout_CB",
        "knowledge_size": size, "reasoning_depth": depth, "seed": seed,
        "query_count": count, "accuracy": accuracy, "warm_accuracy": accuracy,
        "minimum_combination_accuracy": accuracy,
        "continual_new_fact_accuracy": float(acquired),
        "continual_retention": float(retained),
        "fit_seconds": fit_seconds, "fit_ops": fit_ops,
        "meta_fit_ops": meta_fit_ops,
        "data_acquisition_ops": float(public.acquisition_ops),
        "fit_peak_bytes": float(fit_peak),
        "mean_query_ops": query_ops / len(queries),
        "mean_warm_query_ops": query_ops / len(queries),
        "mean_input_ops": 1.0,
        "mean_bytes_touched": statistics.fmean(bytes_touched),
        "p50_latency_us": percentile(latencies, 0.5),
        "p95_latency_us": percentile(latencies, 0.95),
        "state_bytes": state, "peak_state_bytes": max(state, float(fit_peak)),
        "update_ops": update_ops, "update_latency_us": 0.0,
        "workload_ops": workload[1], "workload_ops_r1": workload[1],
        "workload_ops_r4": workload[4], "workload_ops_r16": workload[16],
    }


def simple_control_gate(size: int, count: int, seed: int, source_seed: int) -> dict[str, float]:
    _, _, _, audit = _training(size, 1, count, seed, source_seed)
    maps = audit["maps"]
    heldout = maps[HELDOUT_COMPOSITION]
    support, queries = audit["support_states"], audit["query_states"]
    targets = Counter(
        mapping[state] for names, mapping in maps.items()
        if names in TRAIN_COMPOSITIONS for state in range(STATE_COUNT)
    )
    mode = min(targets, key=lambda value: (-targets[value], value))
    unigram = statistics.fmean(heldout[state] == mode for state in queries)
    by_input: defaultdict[int, Counter[int]] = defaultdict(Counter)
    for names in TRAIN_COMPOSITIONS:
        for state, target in enumerate(maps[names]):
            by_input[state][target] += 1
    markov = statistics.fmean(
        heldout[state] == min(by_input[state], key=lambda value: (-by_input[state][value], value))
        for state in queries
    )
    nearest = min(
        TRAIN_COMPOSITIONS,
        key=lambda names: (sum(maps[names][state] != heldout[state] for state in support), names),
    )
    nearest_accuracy = statistics.fmean(maps[nearest][state] == heldout[state] for state in queries)
    matches = [
        names for names, mapping in maps.items()
        if all(mapping[state] == heldout[state] for state in support)
    ]
    oracle = float(
        len(matches) == 1 and matches[0] == HELDOUT_COMPOSITION
        and all(maps[matches[0]][state] == heldout[state] for state in queries)
    )
    return {"unigram": unigram, "markov_upper_bound": markov,
            "nearest_template": nearest_accuracy, "composition_oracle": oracle,
            "matching_compositions": float(len(matches))}


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix, protocol = plan["matrix"], plan["mechanism_recombination_protocol"]
    return [
        _run_cell(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]),
                  int(seed), int(protocol["mechanism_source_seed"]),
                  int(protocol["state_budget_bytes"]))
        for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
        for depth in matrix["reasoning_depths"]
    ]
