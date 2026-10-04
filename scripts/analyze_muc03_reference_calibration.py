"""Recompute the final768/8192 calibration with the preregistered paired-unit analysis."""
import argparse
from collections import Counter
import math
import json
import statistics
from pathlib import Path

from nextai_autoresearch.muc02_negatives_analysis import paired_interval
from nextai_autoresearch.utils import load_json, sha256_file, sha256_json


METRICS = ("fact_top1_accuracy", "accepted_fact_accuracy", "dense_unknown_rejection", "known_false_abstention",
           "unknown_subject_rejection", "unknown_relation_rejection", "accuracy", "e2e_known_accuracy",
           "e2e_unknown_rejection", "hard_subject_fpr", "hard_relation_fpr")


def mean(values):
    return statistics.fmean(values)


def analyze(base, experiment_id):
    result_path = base / "research/results" / f"{experiment_id}.json"
    result = load_json(result_path)
    plan = load_json(base / result["plan_path"])
    protocol = plan["research_program_protocol"]
    if sha256_json(plan) != result["plan_sha256"] or sha256_file(base / protocol["study_path"]) != protocol["study_sha256"]:
        raise ValueError("Immutable preregistration does not match")
    outcomes = {item["candidate"]: item for item in result["candidates"]}
    seeds = result["evaluation_matrix"]["seeds"]
    expected = {(k, d) for k in (32, 128, 512) for d in (1, 2, 4)}
    roles, costs, pairs = {}, {}, []
    complete = result["status"] == "complete" and len(set(seeds)) == 5
    for name, binding in protocol["roles"].items():
        if binding["fit_steps"] == 0:
            continue
        item = outcomes.get(name, {})
        trials = item.get("trials", [])
        if item.get("status") != "complete" or len(trials) != 9:
            complete = False
            continue
        if ({(t["knowledge_size"], t["reasoning_depth"]) for t in trials} != expected
                or {t["seed"] for t in trials} != {seeds[binding["seed_index"]]}):
            raise ValueError("Paired trial coverage differs from preregistration")
        report = trials[0]["calibration"]["fit_report"]
        if (report["optimizer_steps"] != binding["fit_steps"] or len(report["loss_curve"]) != binding["fit_steps"]
                or report["coverage"]["worlds_covered"] != 405 or report["coverage"]["cells_covered"] != 9
                or sum(report["coverage"]["pairs_per_cell"].values()) != 4096):
            raise ValueError("Frozen training recipe or coverage changed")
        values = {m: mean(t[m] for t in trials) for m in METRICS}
        values["training_pair_accuracy"] = report["training_pair_accuracy"]
        for domain in ("dev_iid", "train_seen"):
            for metric in METRICS[:6]:
                values[f"{domain}_{metric}"] = mean(t["program_diagnostics"][f"{domain}_summary"][metric] for t in trials)
        values["namespace_top1_gap"] = values["dev_iid_fact_top1_accuracy"] - values["fact_top1_accuracy"]
        values["accepted_top1_gap"] = values["fact_top1_accuracy"] - values["accepted_fact_accuracy"]
        roles[name] = values
        execution = item["execution"]
        costs[name] = {"fit_seconds": trials[0]["fit_seconds"], "trusted_fit_seconds": execution["supervised_fit_seconds"],
                       "worker_seconds": execution["wall_seconds"], "peak_rss_bytes": execution["peak_rss_bytes"],
                       "peak_cuda_reserved_bytes": max(w["cuda_peak_reserved_bytes"] for t in trials for w in t["world_costs"]),
                       "logical_state_bytes": max(t["state_bytes"] for t in trials), "fit_ops_estimate": trials[0]["fit_ops"],
                       "fit_preprocessing_ops_estimate": trials[0]["preprocessing_ops"],
                       "diagnostic_flops_estimate": sum(t["diagnostic_flops"] + t["program_costs"]["additional_diagnostic_flops_estimate"] for t in trials),
                       "diagnostic_seconds": sum(t["diagnostic_seconds"] + t["program_costs"]["additional_diagnostic_seconds"] for t in trials),
                       "namespace_rename_seconds": sum(t["program_costs"]["iid_rename_seconds"] for t in trials),
                       "training_and_development_generation_seconds": report["data_generation_seconds"] + sum(t["development_generation_seconds"] for t in trials),
                       "e2e_query_count": sum(t["query_count"] for t in trials),
                       "e2e_latency_total_us": sum(v for t in trials for v in t["latency_samples_us"]),
                       "ingest_latency_total_us": sum(v for t in trials for v in t["ingest_latency_samples_us"]),
                       "update_latency_total_us": sum(v for t in trials for v in t["update_latency_samples_us"]),
                       "final_loss": report["loss_curve"][-1],
                       "per_k": {str(k): {"top1_accuracy": mean(t["fact_top1_accuracy"] for t in trials if t["knowledge_size"] == k),
                                           "e2e_accuracy": mean(t["accuracy"] for t in trials if t["knowledge_size"] == k),
                                           "p95_query_latency_us": mean(t["p95_latency_us"] for t in trials if t["knowledge_size"] == k)} for k in (32, 128, 512)}}
    if complete:
        for i, seed in enumerate(seeds):
            short, long = (outcomes[f"muc03_hard_{steps}_s{i}"]["trials"] for steps in (768, 8192))
            first, second = (trials[0]["calibration"]["fit_report"] for trials in (short, long))
            checks = {key: first[key] == second[key] for key in ("initial_parameters_sha256", "training_worlds_sha256")}
            checks["training_pairs"] = first["coverage"]["pairs_sha256"] == second["coverage"]["pairs_sha256"]
            checks["development_worlds"] = [t["development_sha256"] for t in short] == [t["development_sha256"] for t in long]
            checks["iid_development_worlds"] = [t["dev_iid_sha256"] for t in short] == [t["dev_iid_sha256"] for t in long]
            if not all(checks.values()):
                raise ValueError(f"Pairing failed at seed {seed}")
            pairs.append({"seed": seed, "checks": checks,
                          "first768_loss_max_abs_difference": max(abs(a-b) for a,b in zip(first["loss_curve"], second["loss_curve"][:768], strict=True))})
    symbolic = outcomes.get("symbolic_last_write_graph_v2", {})
    classical = symbolic.get("trials", [])
    control_ok = (symbolic.get("status") == "complete" and len(classical) == 45
                  and {(t["seed"], t["knowledge_size"], t["reasoning_depth"]) for t in classical} == {(s,k,d) for s in seeds for k,d in expected})
    complete = complete and control_ok and result["integrity_before"]["ok"] and result["integrity_after"]["ok"]
    arms, contrasts, diagnoses, gates = {}, {}, {}, {}
    if complete:
        for steps in (768, 8192):
            names = [f"muc03_hard_{steps}_s{i}" for i in range(5)]
            arms[str(steps)] = {metric: mean(roles[name][metric] for name in names) for metric in roles[names[0]]}
        for metric in arms["768"]:
            differences = [roles[f"muc03_hard_8192_s{i}"][metric] - roles[f"muc03_hard_768_s{i}"][metric] for i in range(5)]
            contrasts[metric] = paired_interval(differences, .975 if metric in ("training_pair_accuracy", "fact_top1_accuracy") else .95)
        d, g, long = protocol["diagnosis_gates"], protocol["reference_gates"], arms["8192"]
        diagnoses["undertraining_signal"] = contrasts["training_pair_accuracy"]["mean"] >= d["undertraining_training_gain_min"] and long["training_pair_accuracy"] >= d["undertraining_long_train_accuracy_min"]
        for steps in (768, 8192):
            gaps = [roles[f"muc03_hard_{steps}_s{i}"]["namespace_top1_gap"] for i in range(5)]
            interval = paired_interval(gaps)
            diagnoses[f"namespace_gap_{steps}"] = {"interval": interval, "gate_pass": interval["mean"] >= d["namespace_gap_min"] and interval["positive_pairs"] >= d["namespace_gap_positive_pairs_min"]}
        diagnoses["long_ranking_competent"] = long["fact_top1_accuracy"] >= d["ranking_competence_min"]
        diagnoses["long_rejection_loss_signal"] = long["accepted_top1_gap"] >= d["rejection_accepted_gap_min"]
        diagnoses["long_unknown_competent"] = long["dense_unknown_rejection"] >= d["unknown_competence_min"]
        for steps in (768, 8192):
            arm = arms[str(steps)]
            names = [f"muc03_hard_{steps}_s{i}" for i in range(5)]
            gates[str(steps)] = {
                "training_each_seed": min(roles[n]["training_pair_accuracy"] for n in names) >= g["training_each_seed_min"],
                "dev_top1_mean": arm["fact_top1_accuracy"] >= g["dev_shift_top1_mean_min"],
                "dev_top1_each_seed": min(roles[n]["fact_top1_accuracy"] for n in names) >= g["dev_shift_top1_each_seed_min"],
                "e2e_mean": arm["accuracy"] >= g["e2e_accuracy_mean_min"],
                "e2e_each_seed": min(roles[n]["accuracy"] for n in names) >= g["e2e_accuracy_each_seed_min"],
                "false_abstention_mean": arm["known_false_abstention"] <= g["known_false_abstention_mean_max"],
                "false_abstention_each_seed": max(roles[n]["known_false_abstention"] for n in names) <= g["known_false_abstention_each_seed_max"],
                "unknown_mean": arm["dense_unknown_rejection"] >= g["unknown_rejection_mean_min"],
                "symbolic_accuracy": mean(t["accuracy"] for t in classical) >= g["symbolic_accuracy_min"],
                "symbolic_parser_failure": max(t["calibration"]["parser_failures"] for t in classical) <= g["symbolic_parser_failure_max"]}
    accepted = [steps for steps in (768, 8192) if complete and all(gates[str(steps)].values())]
    workload_costs = {}
    for arm in ("768", "8192", "symbolic"):
        names = [n for n, role in protocol["roles"].items() if role["arm"] == arm]
        trials = [t for n in names for t in outcomes.get(n, {}).get("trials", [])]
        if not trials:
            continue
        ingest = [v for t in trials for v in t["ingest_latency_samples_us"]]
        updates = [v for t in trials for v in t["update_latency_samples_us"]]
        queries = sorted(v for t in trials for v in t["latency_samples_us"])
        subset = all(Counter(t["update_latency_samples_us"]) <= Counter(t["ingest_latency_samples_us"]) for t in trials)
        if not subset:
            raise ValueError("Update samples are not a subset of ingest: cost boundary inconsistent")
        warmup = sum(w["warmup_us"] for t in trials for w in t["world_costs"])
        workload_costs[arm] = {
            "query_count": len(queries), "world_count": sum(len(t["world_costs"]) for t in trials),
            "ingest_including_update_subset_seconds": sum(ingest) / 1e6,
            "update_subset_seconds_disclosed_not_added_again": sum(updates) / 1e6,
            "warmup_seconds": warmup / 1e6, "query_seconds": sum(queries) / 1e6,
            "measured_ingest_warmup_queries_seconds": (sum(ingest) + warmup + sum(queries)) / 1e6,
            "p50_query_us": statistics.median(queries),
            "p95_query_us_nearest_rank": queries[math.ceil(.95 * len(queries)) - 1],
            "updates_subset_verified": subset,
            "unmeasured_in_operation_sum": "new_session allocation; included only in complete worker wall",
            "economic_gate_certified": False}
    return {"experiment_id": experiment_id, "result_sha256": sha256_file(result_path), "plan_sha256": result["plan_sha256"],
            "study_sha256": protocol["study_sha256"], "complete_valid": complete, "seeds": seeds, "roles": roles,
            "arms": arms, "workload_costs": workload_costs, "paired_contrasts": contrasts, "pairing": pairs, "costs": costs, "diagnoses": diagnoses,
            "reference_gates": gates, "reference_accepted": bool(accepted), "selected_reference_steps": min(accepted) if accepted else None,
            "decision": "keep_dev_reference" if accepted else "inconclusive_reference_milestone_closed_no_fourth_recipe",
            "architecture_promotion": False, "economic_advantage_established": False,
            "classical_control": {"complete": control_ok, "accuracy": mean(t["accuracy"] for t in classical) if classical else None,
                                  "query_count": sum(t["query_count"] for t in classical), "worker_seconds": symbolic.get("execution", {}).get("wall_seconds")},
            "trusted_fit_seconds_total": sum(c.get("execution", {}).get("supervised_fit_seconds", 0) for c in result["candidates"]),
            "worker_seconds_total": sum(c.get("execution", {}).get("wall_seconds", 0) for c in result["candidates"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_id")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    analysis = analyze(args.root.resolve(), args.experiment_id)
    rendered = json.dumps(analysis, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
    else:
        print(rendered)
