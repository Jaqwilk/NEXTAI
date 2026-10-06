"""Fresh paired replication, reusing the unchanged MUC02 model and evaluator."""
import hashlib
import importlib
from pathlib import Path
import time
import tracemalloc

from .. import muc03_task
from ..muc02_negatives_stage import ROLES
from ..utils import sha256_json
from .mutable_contact_ledger_hard_negatives_v1 import (
    diagnostic_metrics, run_trial, selection_diagnostics,
)

BENCHMARK_VERSION = "mutable_contact_ledger_negatives_replication_v1"
DATA_TAG = "MUC02-NEGATIVES-REPLICATION-20261006-V1"
CORE_SHA256 = "1a33b1e1181ba50290ec1037d00def39173290c9676976a759e3d68bc12e4c63"


def fresh_worlds(seed, split, k, d, data_sink=None):
    return muc03_task.fresh_worlds(
        DATA_TAG, seed, split, k, d, 45 if split == "T" else 15, data_sink,
    )


def fresh_diagnostics(system, world, seed, k, d, index):
    queries = muc03_task.diagnostic_queries(DATA_TAG, world, seed, k, d, index)
    return selection_diagnostics(system, world, seed, k, d, index, queries_override=queries)


def _validate_plan(candidate_name, plan):
    matrix, protocol = plan["matrix"], plan["muc02_negatives_protocol"]
    seeds = matrix.get("seeds", [])
    historical = protocol.get("historical_seeds")
    if (tuple(plan["candidates"]) != ROLES or candidate_name not in ROLES
            or len(seeds) != 5 or any(type(seed) is not int for seed in seeds)
            or len(set(seeds)) != 5
            or matrix["knowledge_sizes"] != [32, 128, 512]
            or matrix["reasoning_depths"] != [1, 2, 4] or matrix["queries_per_cell"] != 16):
        raise ValueError("Frozen five-pair matrix/role mismatch")
    if (protocol.get("data_tag") != DATA_TAG or not isinstance(historical, list)
            or not historical or any(type(seed) is not int for seed in historical)
            or historical != sorted(set(historical))):
        raise ValueError("Fresh TAG or historical seed disclosure mismatch")
    if set(seeds).intersection(historical):
        raise ValueError("Historical MUC seed collision; no resampling or fit")
    expected_roles = {f"muc02_{arm}_neg_s{i}": {"arm": arm, "seed_index": i}
                      for i in range(5) for arm in ("random", "hard")}
    if (protocol["roles"] != expected_roles or protocol["fit_steps_cap"] != 192
            or protocol["recipe"]["training_pairs"] != 4096):
        raise ValueError("Frozen sampling role or training budget mismatch")
    core = Path(__file__).resolve().parents[1] / "candidates/muc02_core.py"
    if hashlib.sha256(core.read_bytes()).hexdigest() != CORE_SHA256:
        raise ValueError("Unchanged MUC02 model/core source mismatch")
    return matrix, protocol


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    # Every freshness check precedes candidate import, data generation and fit.
    matrix, protocol = _validate_plan(candidate_name, plan)
    learned = candidate_name != "symbolic_last_write_graph_v2"
    binding = protocol["roles"].get(candidate_name)
    seeds = [matrix["seeds"][binding["seed_index"]]] if learned else matrix["seeds"]
    trials = []
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    for seed in seeds:
        if learned:
            tick = time.perf_counter()
            train = tuple({"statements": world.statements, "knowledge_size": k, "reasoning_depth": d}
                          for k in matrix["knowledge_sizes"] for d in matrix["reasoning_depths"]
                          for world in fresh_worlds(seed, "T", k, d, data_sink))
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
            fit_sink({"seed": seed, "candidate": candidate_name, "fit_report": fit_report,
                      "fit_cost": system.fit_cost_report()})
        if phase_sink:
            phase_sink("evaluation")
        for k in matrix["knowledge_sizes"]:
            for d in matrix["reasoning_depths"]:
                trial = run_trial(
                    system, k, d, seed, fit_report, learned, data_sink,
                    worlds_provider=lambda: fresh_worlds(seed, "D", k, d, data_sink),
                    diagnostic_provider=fresh_diagnostics,
                )
                trials.append(trial)
                if trial_sink:
                    trial_sink(trial)
        del system
    if len(trials) != (9 if learned else 45):
        raise ValueError("Role/seed/cell coverage mismatch")
    if phase_sink:
        phase_sink("complete")
    return trials
