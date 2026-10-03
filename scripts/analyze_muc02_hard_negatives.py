"""Reproduce the frozen paired-unit analysis from an immutable result JSON."""
import argparse
import json
import statistics
from pathlib import Path

from nextai_autoresearch.muc02_negatives_analysis import evaluate_gates, paired_interval
from nextai_autoresearch.utils import load_json, sha256_file

METRICS = (
    "fact_top1_accuracy", "dense_unknown_rejection", "accepted_fact_accuracy", "known_false_abstention",
    "pair_false_positive_rate", "pair_false_negative_rate", "hard_subject_fpr", "hard_relation_fpr",
    "unknown_subject_rejection", "unknown_relation_rejection", "accuracy", "e2e_known_accuracy",
    "e2e_unknown_rejection", "continual_new_fact_accuracy", "continual_retention",
)


def percentile(values, q):
    ordered = sorted(values)
    return ordered[int((len(ordered) - 1) * q)] if ordered else None


def analyze(base, experiment_id):
    result_path = base / "research/results" / f"{experiment_id}.json"
    result = load_json(result_path)
    plan = load_json(base / result["plan_path"])
    protocol = plan["muc02_negatives_protocol"]
    seeds = result["evaluation_matrix"]["seeds"]
    outcomes = {c["candidate"]: c for c in result["candidates"]}
    cells = {(k, d) for k in (32, 128, 512) for d in (1, 2, 4)}
    role_metrics, costs, pairing = {}, {}, []
    complete = result["status"] == "complete" and len(seeds) == 5
    for name, binding in protocol["roles"].items():
        item = outcomes.get(name)
        if not item or item["status"] != "complete" or len(item["trials"]) != 9:
            complete = False
            continue
        trials = item["trials"]
        if ({(t["knowledge_size"], t["reasoning_depth"]) for t in trials} != cells
                or {t["seed"] for t in trials} != {seeds[binding["seed_index"]]}):
            raise ValueError("Frozen role/seed/cell coverage changed")
        role_metrics[name] = {m: statistics.fmean(t[m] for t in trials) for m in METRICS}
        report = trials[0]["calibration"]["fit_report"]
        if (report["optimizer_steps"] != 192 or len(report["loss_curve"]) != 192
                or report["coverage"]["worlds_covered"] != 405 or report["coverage"]["cells_covered"] != 9
                or sum(report["coverage"]["pairs_per_cell"].values()) != 4096):
            raise ValueError("Frozen training coverage changed")
        latencies = [v for t in trials for v in t["latency_samples_us"]]
        diagnostic_latencies = [o["latency_us"] for t in trials for g in t["diagnostics"] for o in g["observations"]]
        costs[name] = {"fit_seconds": trials[0]["fit_seconds"], "supervised_fit_seconds": item["execution"]["supervised_fit_seconds"],
                       "worker_seconds": item["execution"]["wall_seconds"], "peak_rss_bytes": item["execution"]["peak_rss_bytes"],
                       "peak_cuda_reserved_bytes": max(c["cuda_peak_reserved_bytes"] for t in trials for c in t["world_costs"]),
                       "peak_logical_state_bytes": max(t["state_bytes"] for t in trials), "fit_ops_estimate": trials[0]["fit_ops"],
                       "fit_preprocessing_ops_estimate": trials[0]["preprocessing_ops"],
                       "dense_diagnostic_flops_estimate": sum(t["diagnostic_flops"] for t in trials),
                       "dense_diagnostic_preparation_ops_estimate": sum(t["diagnostic_preparation_ops"] for t in trials),
                       "dense_diagnostic_seconds": sum(t["diagnostic_seconds"] for t in trials),
                       "data_generation_seconds": report["data_generation_seconds"] + sum(t["development_generation_seconds"] for t in trials),
                       "e2e_b1_p50_us": percentile(latencies, .5), "e2e_b1_p95_us": percentile(latencies, .95),
                       "dense_probe_p50_us": percentile(diagnostic_latencies, .5), "dense_probe_p95_us": percentile(diagnostic_latencies, .95),
                       "training_pair_accuracy": report["training_pair_accuracy"], "final_training_loss": report["loss_curve"][-1]}
    if complete:
        for i, seed in enumerate(seeds):
            random_name, hard_name = f"muc02_random_neg_s{i}", f"muc02_hard_neg_s{i}"
            r = outcomes[random_name]["trials"][0]["calibration"]["fit_report"]
            h = outcomes[hard_name]["trials"][0]["calibration"]["fit_report"]
            checks = {name: r[name] == h[name] for name in ("initial_parameters_sha256", "training_worlds_sha256")}
            checks.update({name: r["coverage"][name] == h["coverage"][name]
                           for name in ("positive_sequence_sha256", "document_and_label_sequence_sha256")})
            checks["development_worlds"] = [t["development_sha256"] for t in outcomes[random_name]["trials"]] == [t["development_sha256"] for t in outcomes[hard_name]["trials"]]
            checks["different_negatives"] = r["coverage"]["pairs_sha256"] != h["coverage"]["pairs_sha256"]
            checks["balanced_hard_types"] = h["coverage"]["mismatch_types"] == {"same_subject": 1024, "same_relation": 1024}
            if not all(checks.values()):
                raise ValueError(f"Pairing/control integrity failed at seed {seed}")
            pairing.append({"pair_index": i, "seed": seed, "checks": checks,
                            "random_negative_types": r["coverage"]["mismatch_types"], "hard_negative_types": h["coverage"]["mismatch_types"]})
    classical = outcomes.get("symbolic_last_write_graph_v2", {})
    symbolic_trials = classical.get("trials", [])
    symbolic_ok = (classical.get("status") == "complete" and len(symbolic_trials) == 45
                   and {(t["seed"], t["knowledge_size"], t["reasoning_depth"]) for t in symbolic_trials} == {(s, k, d) for s in seeds for k, d in cells}
                   and all(t["calibration"]["parser_failures"] == 0 for t in symbolic_trials))
    complete = complete and symbolic_ok and result["integrity_before"]["ok"] and result["integrity_after"]["ok"]
    arms, contrasts, per_k = {}, {}, {}
    if complete:
        for arm in ("random", "hard"):
            arms[arm] = {m: statistics.fmean(role_metrics[f"muc02_{arm}_neg_s{i}"][m] for i in range(5)) for m in METRICS}
        for m in METRICS:
            differences = [role_metrics[f"muc02_hard_neg_s{i}"][m] - role_metrics[f"muc02_random_neg_s{i}"][m] for i in range(5)]
            contrasts[m] = paired_interval(differences, .975 if m in ("fact_top1_accuracy", "dense_unknown_rejection") else .95)
        for k in (32, 128, 512):
            per_k[str(k)] = {}
            for arm in ("random", "hard"):
                per_k[str(k)][arm] = {m: statistics.fmean(t[m] for i in range(5) for t in outcomes[f"muc02_{arm}_neg_s{i}"]["trials"] if t["knowledge_size"] == k) for m in METRICS}
        decision = evaluate_gates(contrasts, statistics.fmean(t["accuracy"] for t in symbolic_trials), protocol["decision_gates"])
    else:
        decision = {"decision": "inconclusive_partial_or_invalid", "architecture_promotion": False}
    return {"schema_version": 1, "experiment_id": experiment_id, "result_path": result_path.relative_to(base).as_posix(),
            "result_sha256": sha256_file(result_path), "immutable_plan_path": result["plan_path"], "plan_sha256": result["plan_sha256"],
            "evaluator_sha256": result["evaluator_sha256"], "analysis_script_sha256": sha256_file(Path(__file__)),
            "complete_five_pair_comparison": complete, "seeds": seeds, "role_metrics": role_metrics, "arm_means": arms,
            "paired_contrasts": contrasts, "per_K": per_k, "pairing_checks": pairing, "costs_by_role": costs, "decision": decision,
            "total_supervised_fit_seconds": sum((v.get("execution") or {}).get("supervised_fit_seconds", 0) for v in outcomes.values()),
            "total_measured_fit_seconds": sum(v["fit_seconds"] for v in costs.values()),
            "symbolic": {"complete": symbolic_ok, "accuracy": statistics.fmean(t["accuracy"] for t in symbolic_trials) if symbolic_trials else None,
                         "worker_seconds": (classical.get("execution") or {}).get("wall_seconds"),
                         "peak_rss_bytes": (classical.get("execution") or {}).get("peak_rss_bytes")},
            "experiment_seconds": sum((v.get("execution") or {}).get("wall_seconds", 0) for v in outcomes.values())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--experiment", default="EXP-20261004-0001")
    args = parser.parse_args()
    evidence = analyze(args.root.resolve(), args.experiment)
    destination = args.root / "research/reviews" / f"{args.experiment}-paired-analysis.json"
    if destination.exists():
        raise FileExistsError("Analysis evidence already exists; use an append-only addendum")
    destination.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: evidence[k] for k in ("experiment_id", "arm_means", "decision", "total_supervised_fit_seconds")}, indent=2))
