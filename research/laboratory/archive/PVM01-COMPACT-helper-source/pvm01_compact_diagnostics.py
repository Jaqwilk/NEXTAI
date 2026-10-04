"""Descriptive stored-result diagnostics; no generator or candidate execution."""
import json
from pathlib import Path
import sys

import numpy as np

from nextai_autoresearch.utils import atomic_write_json, sha256_file, sha256_json, utc_now

b = Path.cwd()
sys.path.insert(0, str(b / "scripts"))
from analyze_pvm01_compact_features import interval

identity = "EXP-20261004-0007"
primary_path = b / f"research/reviews/{identity}-PVM01-compact-analysis.json"
a = json.loads(primary_path.read_text(encoding="utf8"))
r = json.loads((b / f"research/results/{identity}.json").read_text(encoding="utf8"))
p = json.loads((b / f"research/plans/{identity}.json").read_text(encoding="utf8"))
assert a["result_sha256"] == sha256_file(b / f"research/results/{identity}.json")
assert r["plan_sha256"] == sha256_json(p) == a["plan_sha256"]
assert a["all_workers_and_trials_complete"] and len(r["candidates"]) == 75
roles = p["research_program_protocol"]["roles"]
outcomes = {(roles[c["candidate"]]["arm"], str(roles[c["candidate"]]["seed_index"])): c for c in r["candidates"]}
reports = {key: c["trials"][0]["fit_report"] for key, c in outcomes.items()}
summary = {}
for arm, values in a["arms"].items():
    units = list(values.values())
    costs = list(a["costs"][arm].values())
    summary[arm] = {key: interval([u[key] for u in units]) for key in
                    ("accuracy", "dense_unknown_rejection", "known_false_abstention", "updated", "retained")}
    summary[arm]["costs"] = {key: interval([u[key] for u in costs]) for key in costs[0] if key != "device"}
    summary[arm]["by_K"] = {str(k): {key: interval([u["by_K"][str(k)][key] for u in units])
                                     for key in ("accuracy", "dense_unknown_rejection", "known_false_abstention")}
                            for k in (32, 128, 512)}
    summary[arm]["by_K_and_round"] = {}
    for k in (32, 128, 512):
        for rounds in (0, 1, 4):
            rows = [next(row for row in outcomes[(arm, str(i))]["trials"]
                         if row["knowledge_size"] == k and row["update_rounds"] == rounds) for i in range(5)]
            summary[arm]["by_K_and_round"][f"K{k}/updates{rounds}"] = {
                key: interval([row[key] for row in rows]) if rows[0][key] is not None else None
                for key in ("accuracy", "updated_known_accuracy", "retained_known_accuracy", "dense_unknown_rejection", "known_false_abstention")}

identity_checks, cache_checks, feature_traces, gpu = {}, {}, {}, {}
neural = ("compact_learned", "compact_frozen", "compact_shuffled", "compact_additive",
          "delta", "dense", "dense_cached_cpu", "dense_cached_cuda", "exact_nn_cpu")
for i in map(str, range(5)):
    group = [reports[(arm, i)] for arm in neural]
    identity_checks[i] = {key: all(row.get(key) == group[0][key] for row in group) for key in
                          ("initial_parameters_sha256", "final_encoder_sha256", "alignment_losses")}
    scan, tree = reports[("ridge_pca_scan", i)], reports[("ridge_pca_tree", i)]
    identity_checks[i]["PCA_scan_tree_common_fit"] = all(scan.get(key) is not None and scan[key] == tree.get(key)
        for key in ("ridge_weights_sha256", "projection_sha256", "pca_choice"))
    # Show actual fields too: an absent field is not evidence of inequality.
    identity_checks[i]["PCA_report_fields"] = {key: scan[key] for key in scan
        if any(token in key for token in ("weights", "projection", "pca"))}
    cache_checks[i] = {}
    for arm in ("dense_cached_cpu", "dense_cached_cuda"):
        dense = outcomes[("dense", i)]
        cached = outcomes[(arm, i)]
        score_difference, same, count = [], True, 0
        for dr, cr in zip(dense["trials"], cached["trials"], strict=True):
            for de, ce in zip(dr["measurements"], cr["measurements"], strict=True):
                for dq, cq in zip(de["predictions"], ce["predictions"], strict=True):
                    same &= all(dq[key] == cq[key] for key in ("answer", "top_handle", "top_value", "truth", "target_handle"))
                    score_difference.append(abs(dq["decision_score"] - cq["decision_score"]))
                    count += 1
        loss_difference = np.max(np.abs(np.asarray(reports[("dense", i)]["dense_set_losses"])
                                     - np.asarray(reports[(arm, i)]["dense_set_losses"])))
        cache_checks[i][arm] = {"predictions_handles_values_equal": bool(same), "count": count,
            "max_decision_score_absolute_difference": max(score_difference),
            "max_set_loss_absolute_difference": float(loss_difference), "decoder_weight_sha256": "not_collected"}
    for arm in ("compact_learned", "compact_shuffled", "compact_additive"):
        report = reports[(arm, i)]
        losses = np.asarray(report["compact_feature_losses"])
        grads = np.asarray(report["compact_feature_gradient_norms"])
        assert len(losses) == len(grads) == 512 and np.isfinite(losses).all() and np.isfinite(grads).all()
        feature_traces[f"{arm}/{i}"] = {"steps": len(losses), "first_loss": float(losses[0]),
            "first50_mean": float(losses[:50].mean()), "last_loss": float(losses[-1]),
            "last50_mean": float(losses[-50:].mean()), "loss_min": float(losses.min()), "loss_max": float(losses.max()),
            "gradient_mean": float(grads.mean()), "gradient_max": float(grads.max()),
            "features_changed": report["compact_initial_features_sha256"] != report["compact_final_features_sha256"]}
for key, outcome in outcomes.items():
    journal = b / f"research/laboratory/archive/{identity}-runtime/research/tmp/{identity}/{outcome['candidate']}.device.json"
    device = json.loads(journal.read_text(encoding="utf8"))
    gpu[outcome["candidate"]] = {"allocated_bytes": device["allocated"], "reserved_bytes": device["reserved"],
                                "journal_sha256": sha256_file(journal)}
comparisons = {}
for control in ("dense_cached_cpu", "delta", "exact_nn_cpu", "ridge", "ridge_pca_scan"):
    comparisons[control] = {
        "accuracy_difference": interval([a["arms"]["compact_learned"][i]["accuracy"] - a["arms"][control][i]["accuracy"] for i in map(str, range(5))]),
        **{f"{metric}_ratio": interval([a["costs"]["compact_learned"][i][metric] / a["costs"][control][i][metric]
                                       for i in map(str, range(5))]) for metric in ("full_workload_seconds", "p95_query_us", "logical_state_bytes")}}
result = {"created_at": utc_now(), "experiment_id": identity, "result_sha256": a["result_sha256"],
    "plan_sha256": r["plan_sha256"], "study_sha256": a["study_sha256"], "primary_analysis_sha256": sha256_file(primary_path),
    "started_at": r["started_at"], "completed_at": r["completed_at"], "descriptive_95_percent_intervals": summary,
    "identity_checks": identity_checks, "cache_checks": cache_checks, "feature_training_traces": feature_traces,
    "descriptive_paired_comparisons": comparisons, "whole_worker_cuda_allocator_peaks": gpu,
    "total_supervised_fit_phase_seconds": sum(c["execution"]["supervised_fit_seconds"] for c in r["candidates"]),
    "total_internal_algorithm_fit_seconds": sum(report["fit_seconds"] for report in reports.values()),
    "full_charged_worker_seconds": sum(c["execution"]["research_compute_seconds"] for c in r["candidates"]),
    "independent_units": 5, "primary_gates_unchanged": True, "models_or_generator_executed": False,
    "decoder_hash_not_collected": True, "cuda_inference_only_memory_not_collected": True,
    "descriptive_intervals_not_primary_decision_tests": True}
target = b / f"research/reviews/{identity}-PVM01-full-diagnostics-V1.json"
assert not target.exists()
atomic_write_json(target, result)
for arm, row in summary.items():
    print(arm, "full%", round(row["accuracy"]["mean"]*100,4), "Kfull/U%",
          {k: [round(row["by_K"][k][m]["mean"]*100,4) for m in ("accuracy", "dense_unknown_rejection")] for k in row["by_K"]},
          "fit/service/p95/RSS", {k: round(row["costs"][k]["mean"],6) for k in ("fit_phase_seconds", "full_workload_seconds", "p95_query_us", "peak_rss_bytes")})
print("Totals", {key: result[key] for key in result if key.startswith("total_") or key == "full_charged_worker_seconds"})
print("Feature traces", {key: value for key, value in feature_traces.items() if key.startswith("compact_learned/")})
print("Identities", identity_checks)
print("Cache max", max(v["max_decision_score_absolute_difference"] for row in cache_checks.values() for v in row.values()))
print("Paired compact vs cache", comparisons["dense_cached_cpu"])
