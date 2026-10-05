"""Preregistered step-length and namespace diagnostic; no final access/tuning."""
import hashlib
import importlib
import time
import tracemalloc

import torch

from ..muc03_task import fresh_worlds, iid_namespace, diagnostic_queries
from ..utils import sha256_json
from .mutable_contact_ledger_hard_negatives_v1 import run_trial, selection_diagnostics, diagnostic_metrics

BENCHMARK_VERSION = "muc03_undertraining_v1"


def domain_diagnostic(tag, system, world, seed, k, d, index):
    return selection_diagnostics(system, world, seed, k, d, index,
                                 queries_override=diagnostic_queries(tag, world, seed, k, d, index))


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    protocol, matrix = plan["research_program_protocol"], plan["matrix"]
    if (candidate_name not in protocol["roles"] or len(matrix["seeds"]) != 5 or len(set(matrix["seeds"])) != 5
            or matrix["knowledge_sizes"] != [32, 128, 512] or matrix["reasoning_depths"] != [1, 2, 4]
            or matrix["queries_per_cell"] != 16):
        raise ValueError("Frozen diagnostic role/seed/matrix mismatch")
    if not torch.cuda.is_available():
        raise RuntimeError("Frozen diagnostic hardware requires CUDA")
    role = protocol["roles"][candidate_name]
    learned = role["fit_steps"] != 0
    seeds = [matrix["seeds"][role["seed_index"]]] if learned else matrix["seeds"]
    module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
    data = protocol["data"]
    tag = data["tag"]
    probe = lambda system, world, seed, k, d, index: domain_diagnostic(tag, system, world, seed, k, d, index)
    trials = []
    for seed in seeds:
        train_by_cell = {}
        if learned:
            tick = time.perf_counter()
            train_by_cell = {(k, d): fresh_worlds(tag, seed, "T", k, d, data["train_worlds_per_cell"], data_sink)
                             for k in matrix["knowledge_sizes"] for d in matrix["reasoning_depths"]}
            train = tuple({"statements": w.statements, "knowledge_size": k, "reasoning_depth": d}
                          for (k, d), worlds in train_by_cell.items() for w in worlds)
            data_seconds = time.perf_counter() - tick
            data_digest = sha256_json(train)
            if phase_sink:
                phase_sink("fit")
            tracemalloc.start()
            tick = time.perf_counter()
            try:
                system = module.Candidate(seed=seed, protocol={**protocol, "fit_steps_cap": role["fit_steps"]})
                digest = hashlib.sha256()
                for value in system.model.state_dict().values():
                    digest.update(value.detach().cpu().numpy().tobytes())
                report = system.fit(train, ())
                system.synchronize()
                fit_seconds = time.perf_counter() - tick
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            system.record_fit_resources(fit_seconds, peak)
            report.update(initial_parameters_sha256=digest.hexdigest(), training_worlds_sha256=data_digest,
                          data_generation_seconds=data_seconds, seed=seed, arm=role["arm"],
                          device=str(system.device), torch_version=torch.__version__,
                          gpu_name=torch.cuda.get_device_name(0), precision=str(next(system.model.parameters()).dtype),
                          tf32_matmul=torch.backends.cuda.matmul.allow_tf32, threads=torch.get_num_threads())
            if fit_seconds > protocol["fit_seconds_cap"] or report["optimizer_steps"] != role["fit_steps"]:
                raise TimeoutError("Frozen step length or fit cap failed")
            del train
        else:
            system = module.Candidate(seed=seed, protocol=protocol)
            system.record_fit_resources(0, 0)
            report = {"optimizer_steps": 0, "selection": "classical timestamped last-write map; no fit"}
        if fit_sink:
            fit_sink({"seed": seed, "candidate": candidate_name, "fit_report": report, "fit_cost": system.fit_cost_report()})
        if phase_sink:
            phase_sink("evaluation")
        for k in matrix["knowledge_sizes"]:
            for d in matrix["reasoning_depths"]:
                generated = []
                def provider():
                    worlds = fresh_worlds(tag, seed, "D", k, d, data["dev_worlds_per_cell"], data_sink)
                    generated.extend(worlds)
                    return worlds
                trial = run_trial(system, k, d, seed, report, learned, worlds_provider=provider, diagnostic_provider=probe)
                if learned:
                    tick = time.perf_counter()
                    iid = tuple(iid_namespace(w) for w in generated)
                    rename_seconds = time.perf_counter() - tick
                    iid_diagnostics = [probe(system, w, seed, k, d, i) for i, w in enumerate(iid)]
                    train_probes = train_by_cell[(k, d)][:data["train_diagnostic_worlds_per_cell"]]
                    train_diagnostics = [probe(system, w, seed, k, d, i) for i, w in enumerate(train_probes)]
                    trial["program_diagnostics"] = {"dev_iid": iid_diagnostics, "train_seen": train_diagnostics,
                                                   "dev_iid_summary": diagnostic_metrics(iid_diagnostics),
                                                   "train_seen_summary": diagnostic_metrics(train_diagnostics, worlds_expected=data["train_diagnostic_worlds_per_cell"])}
                    trial["program_costs"] = {"iid_rename_seconds": rename_seconds,
                                             "iid_rename_ops_estimate": sum(2 * len(s.encode()) for w in generated for s in w.statements)
                                                + sum(2 * len(q.text.encode()) + 2 * len(q.answer.encode()) for w in generated for q in w.questions),
                                             "additional_diagnostic_flops_estimate": sum(g["estimated_flops"] for g in iid_diagnostics + train_diagnostics),
                                             "additional_diagnostic_preparation_ops_estimate": sum(g["preparation_ops"] for g in iid_diagnostics + train_diagnostics),
                                             "additional_diagnostic_seconds": sum(g["latency_us"] for g in iid_diagnostics + train_diagnostics) / 1e6}
                    trial["dev_iid_sha256"] = sha256_json([{"statements": w.statements, "questions": [(q.text, q.answer) for q in w.questions]} for w in iid])
                trials.append(trial)
                if trial_sink:
                    trial_sink(trial)
        del system, train_by_cell
    if len(trials) != (9 if learned else 45):
        raise ValueError("Diagnostic trial coverage mismatch")
    if phase_sink:
        phase_sink("complete")
    return trials
