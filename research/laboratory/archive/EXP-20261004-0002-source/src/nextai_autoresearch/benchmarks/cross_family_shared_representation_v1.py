from __future__ import annotations

import math
import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any, Callable

from . import action_conditioned_predictive_equivalence_v1 as predictive
from . import behavioral_conjugacy_library_transfer_v1 as programs
from . import context_specific_probabilistic_circuit_v1 as probabilistic
from . import nonlinear_local_state_transfer_v1 as local
from .successor_graph_v1 import load_candidate, percentile
from ..cross_family_contract import (
    QUERY_WIDTH, SUPPORT_WIDTH, Example, MetaWorld, NativeWorld, PrivilegedQuery,
    PrivilegedTraining, PrivilegedUpdate, PublicQuery, PublicTraining, PublicUpdate,
    TestWorld, pack,
)


BENCHMARK_VERSION = "cross_family_shared_representation_v1"
FAMILIES = ("probabilistic", "predictive", "local", "program")
SALTS = {name: value for name, value in zip(FAMILIES, (0xC17, 0xA61, 0x10CA1, 0xB17))}
PRIVILEGED = {
    "specialist_contextual_chow_liu_suite",
    "specialist_empirical_joint_suite",
    "specialist_autoregressive_suite",
    "oracle_cross_family_suite",
}


@dataclass(frozen=True)
class Case:
    family: str
    public: PublicQuery
    native: Any
    target: tuple[float, ...]
    correct: Callable[[Any], bool]
    probability: float | None = None


@dataclass(frozen=True)
class BuiltWorld:
    family: str
    public_fit: Any
    oracle_fit: Any
    cold: tuple[tuple[Any, tuple[float, ...], Callable[[Any], bool], float | None], ...]
    near: tuple[tuple[Any, tuple[float, ...], Callable[[Any], bool], float | None], ...]


def _discrete(target: tuple[int, ...]) -> Callable[[Any], bool]:
    return lambda answer: tuple(round(float(value)) for value in answer[:len(target)]) == target


def _probability(truth: float) -> Callable[[Any], bool]:
    return lambda answer: bool(answer) and abs(float(answer[0]) - truth) <= 0.05


def _probabilistic_world(size: int, depth: int, count: int, seed: int) -> BuiltWorld:
    world = probabilistic.make_world(size, seed)
    def rows(near: bool):
        return tuple((query, (truth,), _probability(truth), truth)
                     for query, truth in probabilistic.make_queries(
                         world, depth, seed, count, near=near
                     ))
    return BuiltWorld("probabilistic", world.public, world, rows(False), rows(True))


def _predictive_world(size: int, depth: int, count: int, seed: int) -> BuiltWorld:
    data, oracle, _ = predictive.make_dataset(size, seed)
    tasks = predictive.make_tasks(size, depth, count, seed)
    def rows(near: bool):
        output = []
        for task in tasks:
            history = task.near_history if near else task.history
            expected = task.near_expected if near else task.expected
            best = task.near_best_action if near else task.best_action
            target = (*expected, best)
            output.append(((history, task.actions, depth), tuple(map(float, target)),
                           _discrete(target), None))
        return tuple(output)
    return BuiltWorld("predictive", data, oracle, rows(False), rows(True))


def _local_world(size: int, depth: int, count: int, seed: int) -> BuiltWorld:
    world = local.make_world(seed)
    tasks = tuple(local.make_task(world, size, seed ^ depth, index) for index in range(count))
    def rows(near: bool):
        output = []
        for task in tasks:
            query = local.damaged(task) if near else task
            target = local.oracle_answer(task, world, depth)
            output.append((query, tuple(map(float, target)), _discrete(target), None))
        return tuple(output)
    oracle = (local.OracleSpec({descriptor: kind for kind, descriptor in enumerate(
        world.descriptor_by_kind
    )}),)
    return BuiltWorld("local", world.training_cases, oracle, rows(False), rows(True))


def _program_world(size: int, depth: int, count: int, seed: int) -> BuiltWorld:
    public, oracle, tables, roles = programs.make_world(size, seed)
    tasks = programs.make_tasks(tables, roles, depth, seed, count)
    def rows(near: bool):
        output = []
        for task, shifted, _, _, program in tasks:
            query = shifted if near else task
            def correct(answer: Any, query: Any = query) -> bool:
                proposal = tuple(round(float(value)) for value in answer[:query.length])
                return programs._correct(proposal, query.examples, tables)
            output.append((query, tuple(map(float, program)), correct, None))
        return tuple(output)
    return BuiltWorld("program", public, oracle, rows(False), rows(True))


BUILDERS = (_probabilistic_world, _predictive_world, _local_world, _program_world)


def _build_worlds(size: int, depth: int, count: int, seed: int) -> tuple[BuiltWorld, ...]:
    return tuple(builder(size, depth, count, seed ^ SALTS[family])
                 for family, builder in zip(FAMILIES, BUILDERS))


def _training(size: int, depth: int, count: int, score_seed: int,
              training_seeds: tuple[int, ...]):
    if score_seed in training_seeds:
        raise ValueError("training/test seed collision")
    acquisition, meta_worlds = 0, []
    for train_seed in training_seeds:
        for world in _build_worlds(size, depth, min(count, 4), train_seed):
            support, ops = pack(world.public_fit, SUPPORT_WIDTH)
            acquisition += ops
            examples = []
            for native, target, _, _ in world.cold:
                query, query_ops = pack(native, QUERY_WIDTH)
                acquisition += query_ops
                examples.append(Example(query, target))
            meta_worlds.append(MetaWorld(support, tuple(examples)))

    test = _build_worlds(size, depth, count, score_seed)
    slots = random.Random(score_seed ^ size ^ (depth << 8)).sample(
        range(100, 10_000), len(test)
    )
    test_worlds, native_worlds = [], []
    cold: dict[str, tuple[Case, ...]] = {}
    near: dict[str, tuple[Case, ...]] = {}
    for slot, world in zip(slots, test):
        support, ops = pack(world.public_fit, SUPPORT_WIDTH)
        acquisition += ops
        test_worlds.append(TestWorld(slot, support))
        native_worlds.append(NativeWorld(slot, world.family, world.public_fit, world.oracle_fit))
        for destination, source in ((cold, world.cold), (near, world.near)):
            cases = []
            for index, (native, target, correct, truth) in enumerate(source):
                tokens, query_ops = pack(native, QUERY_WIDTH)
                acquisition += query_ops
                public = PublicQuery(slot, tokens, score_seed ^ slot ^ depth ^ index)
                cases.append(Case(world.family, public, native, target, correct, truth))
            destination[world.family] = tuple(cases)
    public = PublicTraining(tuple(meta_worlds), tuple(test_worlds), acquisition)
    return public, PrivilegedTraining(public, tuple(native_worlds)), cold, near


def _answer(value: Any) -> tuple[float, ...]:
    if isinstance(value, (int, float)):
        value = (value,)
    if not isinstance(value, (tuple, list)) or not value:
        raise ValueError("candidate answer must be a non-empty numeric sequence")
    answer = tuple(float(item) for item in value)
    if any(not math.isfinite(item) for item in answer):
        raise ValueError("candidate answer must be finite")
    return answer


def _number(candidate: Any, name: str, default: float = 0.0) -> float:
    value = getattr(candidate, name, default)
    return float(value() if callable(value) else value)


def _run_cell(candidate_name: str, size: int, depth: int, count: int, seed: int,
              training_seeds: tuple[int, ...], max_depth: int) -> list[dict[str, Any]]:
    public, privileged, cold, near = _training(size, depth, count, seed, training_seeds)
    candidate = load_candidate(candidate_name, seed)
    fit_data = privileged if candidate_name in PRIVILEGED else public
    tracemalloc.start()
    started = time.perf_counter()
    candidate.fit(fit_data, size, max_depth)
    fit_seconds = time.perf_counter() - started
    _, fit_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    observations: dict[str, dict[str, Any]] = {}
    total_query_ops = 0.0
    for family in FAMILIES:
        observations[family] = {"cold": [], "near": [], "latency": [], "bytes": []}
        for label, cases in (("cold", cold[family]), ("near", near[family])):
            for case in cases:
                source = PrivilegedQuery(case.public, family, case.native) \
                    if candidate_name in PRIVILEGED else case.public
                tick = time.perf_counter_ns()
                answer = _answer(candidate.query(source, depth))
                latency = (time.perf_counter_ns() - tick) / 1000.0
                ops = _number(candidate, "last_ops")
                total_query_ops += ops
                observations[family][label].append((case.correct(answer), answer, case))
                observations[family]["latency"].append(latency)
                observations[family]["bytes"].append(
                    _number(candidate, "last_bytes_touched", ops * 8)
                )

    retained, acquired, after_ops = {}, {}, 0.0
    for family in FAMILIES:
        revealed = cold[family][-1]
        update = PublicUpdate(revealed.public, revealed.target)
        source = PrivilegedUpdate(update, family, revealed.native) \
            if candidate_name in PRIVILEGED else update
        candidate.update(source, None)
        query_source = PrivilegedQuery(revealed.public, family, revealed.native) \
            if candidate_name in PRIVILEGED else revealed.public
        acquired_answer = _answer(candidate.query(query_source, depth))
        after_ops += _number(candidate, "last_ops")
        acquired[family] = revealed.correct(acquired_answer)
        old = cold[family][0]
        old_source = PrivilegedQuery(old.public, family, old.native) \
            if candidate_name in PRIVILEGED else old.public
        retained_answer = _answer(candidate.query(old_source, depth))
        after_ops += _number(candidate, "last_ops")
        retained[family] = old.correct(retained_answer)

    fit_ops = _number(candidate, "fit_ops")
    meta_fit_ops = _number(candidate, "meta_fit_ops", fit_ops)
    update_ops = _number(candidate, "update_ops")
    base = public.acquisition_ops + fit_ops + update_ops + after_ops
    workloads = {horizon: base + horizon * total_query_ops for horizon in (1, 4, 16)}
    state = _number(candidate, "state_bytes")
    rows = []
    for family in FAMILIES:
        cold_rows, near_rows = observations[family]["cold"], observations[family]["near"]
        probabilities = [(row[1][0], row[2].probability) for row in cold_rows + near_rows
                         if row[2].probability is not None]
        clipped = [(min(1 - 1e-12, max(1e-12, prediction)), truth)
                   for prediction, truth in probabilities]
        rows.append({
            "status": "complete", "world_family": family,
            "knowledge_size": size, "reasoning_depth": depth, "seed": seed,
            "query_count": count,
            "accuracy": statistics.fmean(row[0] for row in cold_rows),
            "warm_accuracy": statistics.fmean(row[0] for row in cold_rows),
            "near_equivalent_accuracy": statistics.fmean(row[0] for row in near_rows),
            "continual_new_fact_accuracy": float(acquired[family]),
            "continual_retention": float(retained[family]),
            "conditional_probability_mae": statistics.fmean(
                abs(prediction - truth) for prediction, truth in probabilities
            ) if probabilities else None,
            "conditional_log_loss": statistics.fmean(
                -truth * math.log(prediction) - (1 - truth) * math.log(1 - prediction)
                for prediction, truth in clipped
            ) if clipped else None,
            "calibration_error": abs(
                statistics.fmean(prediction for prediction, _ in probabilities)
                - statistics.fmean(truth for _, truth in probabilities)
            ) if probabilities else None,
            "fit_seconds": fit_seconds, "fit_ops": fit_ops,
            "meta_fit_ops": meta_fit_ops,
            "data_acquisition_ops": float(public.acquisition_ops),
            "fit_peak_bytes": float(fit_peak),
            "mean_query_ops": total_query_ops / (2 * count * len(FAMILIES)),
            "mean_warm_query_ops": total_query_ops / (2 * count * len(FAMILIES)),
            "mean_input_ops": float(QUERY_WIDTH),
            "mean_bytes_touched": statistics.fmean(observations[family]["bytes"]),
            "p50_latency_us": percentile(observations[family]["latency"], 0.5),
            "p95_latency_us": percentile(observations[family]["latency"], 0.95),
            "state_bytes": state, "peak_state_bytes": max(state, float(fit_peak)),
            "update_ops": update_ops, "update_latency_us": 0.0,
            "workload_ops": workloads[1], "workload_ops_r1": workloads[1],
            "workload_ops_r4": workloads[4], "workload_ops_r16": workloads[16],
        })
    return rows


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    training_seeds = tuple(
        int(seed) for seed in plan["transfer_protocol"]["training_world_seeds"]
    )
    maximum = max(map(int, matrix["reasoning_depths"]))
    return [row for seed in matrix["seeds"] for size in matrix["knowledge_sizes"]
            for depth in matrix["reasoning_depths"]
            for row in _run_cell(candidate_name, int(size), int(depth),
                                 int(matrix["queries_per_cell"]), int(seed),
                                 training_seeds, maximum)]
