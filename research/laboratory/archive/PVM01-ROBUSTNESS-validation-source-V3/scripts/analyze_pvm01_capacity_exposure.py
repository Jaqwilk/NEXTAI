"""Frozen stored-result analysis; no model, generator or new data execution."""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t

from nextai_autoresearch.utils import atomic_write_json, sha256_file, sha256_json


def interval(values, level=.95):
    values = np.asarray(values, dtype=float)
    if len(values) != 5:
        return {"n": len(values), "mean": float(values.mean()) if len(values) else None,
                "low": None, "high": None, "values": values.tolist()}
    mean = float(values.mean())
    margin = float(t.ppf((1 + level) / 2, 4) * values.std(ddof=1) / np.sqrt(5))
    return {"n": 5, "mean": mean, "low": mean - margin, "high": mean + margin,
            "level": level, "values": values.tolist(), "positive_units": int(sum(values > 0))}


def primary_gates(contrasts, frozen):
    gates = {"five_paired_units": all(v["n"] == 5 for v in contrasts.values())}
    for name in ("small", "frozen", "shuffled"):
        value = contrasts[name]
        gates[name] = value["n"] == 5 and value["mean"] >= frozen[f"large_vs_{name}_mean_full_gain_min"] and value["low"] >= frozen["all_three_gain_ci_lower_min"] and value["positive_units"] == 5
    value = contrasts["retained"]
    gates["retention_noninferiority"] = value["n"] == 5 and value["low"] >= frozen["retained_vs_RFF2048_ci_lower_min"]
    return {key: bool(value) for key, value in gates.items()}


def analyze(base, identity):
    result_path, plan_path = (base / f"research/{folder}/{identity}.json" for folder in ("results", "plans"))
    result, plan = (json.loads(p.read_text(encoding="utf8")) for p in (result_path, plan_path))
    assert result["plan_sha256"] == sha256_json(plan)
    protocol = plan["research_program_protocol"]
    study = json.loads((base / protocol["study_path"]).read_text(encoding="utf8"))
    assert sha256_file(base / protocol["study_path"]) == protocol["study_sha256"]
    arms, costs, reports, failures, pairing, set_pairing = {}, {}, {}, [], {}, {}
    metrics = ("accuracy", "known_false_abstention", "dense_unknown_rejection",
               "nonabstaining_known_value_accuracy", "fact_top1_accuracy")
    for outcome in result["candidates"]:
        name = outcome["candidate"]
        arm, index = (protocol["roles"][name][key] for key in ("arm", "seed_index"))
        rows = outcome["trials"]
        if outcome["status"] != "complete" or len(rows) != 9:
            failures.append({"candidate": name, "status": outcome["status"], "trials": len(rows), "error": outcome.get("error")})
            continue
        report = rows[0]["fit_report"]
        assert all(row["fit_report_sha256"] == sha256_json(report) for row in rows)
        reports[(arm, index)] = report
        pairing.setdefault(index, set()).add((report["train_pairs_sha256"], report["training_validation_sha256"],
                                             report["calibration_sha256"], tuple(r["dev_sha256"] for r in rows)))
        set_pairing.setdefault(index, set()).add(sha256_json(report["training_sets_sha256"]))
        means = {key: float(np.mean([r[key] for r in rows])) if rows[0][key] is not None else None for key in metrics}
        updated = [r for r in rows if r["update_rounds"] in (1, 4)]
        means.update(updated=float(np.mean([r["updated_known_accuracy"] for r in updated])),
                     retained=float(np.mean([r["retained_known_accuracy"] for r in updated])),
                     K512_updated=float(np.mean([r["updated_known_accuracy"] for r in updated if r["knowledge_size"] == 512])),
                     threshold=report["calibration_choice"]["threshold"])
        means["by_K"] = {str(k): {key: float(np.mean([r[key] for r in rows if r["knowledge_size"] == k]))
                                 if rows[0][key] is not None else None for key in metrics} for k in (32, 128, 512)}
        arms.setdefault(arm, {})[str(index)] = means
        execution = outcome["execution"]
        costs.setdefault(arm, {})[str(index)] = {
            "fit_phase_seconds": execution["supervised_fit_seconds"],
            "charged_worker_seconds": execution["research_compute_seconds"], "peak_rss_bytes": execution["peak_rss_bytes"],
            "full_workload_seconds": sum(r["full_workload_seconds"] for r in rows),
            "p95_query_us": outcome["summary"]["p95_latency_us"],
            "logical_state_bytes": max(r["state_bytes"] for r in rows), "device": rows[0]["runtime_device"],
            "fit_seconds": report["fit_seconds"],
            **{key: sum(r["component_seconds"][key] for r in rows) for key in rows[0]["component_seconds"]}}
    def contrast(control, metric):
        indices = sorted(set(arms.get("exposure_large", {})) & set(arms.get(control, {})))
        return interval([arms["exposure_large"][i][metric] - arms[control][i][metric] for i in indices],
                        protocol["diagnosis_gates"]["simultaneous_primary_interval_level"])
    contrasts = {"small": contrast("exposure_small", "accuracy"), "frozen": contrast("exposure_frozen", "accuracy"),
                 "shuffled": contrast("exposure_shuffled", "accuracy"), "retained": contrast("delta", "retained")}
    gates = primary_gates(contrasts, protocol["diagnosis_gates"])
    competence = {}
    reference = protocol["reference_gates"]
    for arm in ("exposure_large", "dense", "dense_cached_cpu", "dense_cached_cuda"):
        units = list(arms.get(arm, {}).values())
        competence[arm] = {
            "five_units": len(units) == 5,
            "mean_accuracy": len(units) == 5 and np.mean([u["accuracy"] for u in units]) >= reference["mean_full_answer_accuracy_min"],
            "each_unit_accuracy": len(units) == 5 and min(u["accuracy"] for u in units) >= reference["each_seed_full_answer_accuracy_min"],
            "each_K_accuracy": len(units) == 5 and all(np.mean([u["by_K"][str(k)]["accuracy"] for u in units]) >= reference["each_K_mean_accuracy_min"] for k in (32, 128, 512)),
            "mean_unknown": len(units) == 5 and np.mean([u["dense_unknown_rejection"] for u in units]) >= reference["absent_identity_rejection_mean_min"],
            "each_unit_unknown": len(units) == 5 and min(u["dense_unknown_rejection"] for u in units) >= reference["each_seed_absent_identity_rejection_min"],
            "known_false_abstention": len(units) == 5 and np.mean([u["known_false_abstention"] for u in units]) <= reference["known_false_abstention_mean_max"]}
        competence[arm] = {key: bool(value) for key, value in competence[arm].items()}
    identity_checks = {}
    for index in range(5):
        group = [reports.get((a, index), {}) for a in ("exposure_large", "exposure_small", "exposure_frozen", "exposure_shuffled", "exposure_additive")]
        large, small, frozen, shuffled, additive = group
        common = all(large.get(key) is not None and all(row.get(key) == large[key] for row in group[1:])
                     for key in ("initial_parameters_sha256", "final_encoder_sha256", "alignment_losses",
                                 "compact_initial_features_sha256", "compact_precomputed_sha256"))
        fitted = all(large.get(key) is not None and large.get(key) == additive.get(key) for key in
                     ("compact_final_features_sha256", "compact_feature_losses", "compact_feature_gradient_norms", "compact_batch_value_draws_sha256"))
        draws = large.get("exposure_common_draws_sha256") is not None and all(r.get("exposure_common_draws_sha256") == large["exposure_common_draws_sha256"] for r in (small, shuffled, additive))
        unchanged = frozen.get("compact_initial_features_sha256") is not None and frozen.get("compact_final_features_sha256") == frozen["compact_initial_features_sha256"] and frozen.get("compact_feature_steps") == 0
        trained = (large, small, shuffled, additive)
        steps = all(r.get("compact_feature_steps") == protocol["recipe"]["compact_feature_steps"] for r in trained)
        changes = all(r.get("compact_final_features_sha256") != r.get("compact_initial_features_sha256") and len(r.get("compact_feature_losses", [])) == protocol["recipe"]["compact_feature_steps"] and len(r.get("compact_feature_gradient_norms", [])) == protocol["recipe"]["compact_feature_steps"] and all(np.isfinite(r.get("compact_feature_losses", []))) and all(np.isfinite(r.get("compact_feature_gradient_norms", []))) and max(r.get("compact_feature_gradient_norms", [0])) > 0 for r in trained)
        curriculum = small.get("exposure_support_sizes") == protocol["recipe"]["exposure_small_support_sizes"] and all(r.get("exposure_support_sizes") == protocol["recipe"]["exposure_large_support_sizes"] for r in (large, shuffled, additive))
        identity_checks[str(index)] = {"common_transport_and_initial_features":common, "large_additive_identical_fit":fitted,
            "optimized_arms_common_max_label_draws":draws, "frozen_features_unchanged":unchanged,
            "fixed_step_counts":steps, "features_changed_and_finite_gradient":changes, "support_curricula":curriculum}
        dense = [reports.get((a, index), {}) for a in ("dense", "dense_cached_cpu", "dense_cached_cuda")]
        identity_checks[str(index)]["dense_cache_identical_weights"] = all(dense[0].get(k) is not None and all(r.get(k) == dense[0][k] for r in dense[1:]) for k in ("final_encoder_sha256", "final_decoder_sha256", "alignment_losses", "dense_set_losses"))
        scan, tree = (reports.get((a, index), {}) for a in ("ridge_pca_scan", "ridge_pca_tree"))
        identity_checks[str(index)]["PCA_scan_tree_identical_fit"] = all(scan.get(k) is not None and tree.get(k) == scan[k] for k in ("fp32_ridge_weights_sha256", "pca_projection_sha256", "pca_choice", "pca_grid"))
    legal_pairing = len(pairing) == 5 and all(len(v) == 1 for v in pairing.values())
    legal_sets = len(set_pairing) == 5 and all(len(v) == 1 for v in set_pairing.values())
    complete = not failures and sorted(o["candidate"] for o in result["candidates"]) == sorted(study["candidates"]) and legal_pairing and legal_sets and all(all(v.values()) for v in identity_checks.values())
    if not complete or not all(all(competence[a].values()) for a in ("dense", "dense_cached_cpu", "dense_cached_cuda")):
        decision = "INCONCLUSIVE comparison"
    elif all(gates.values()) and all(competence["exposure_large"].values()):
        decision = "KEEP exact large-support exposure recipe for further validation"
    else:
        decision = "DISCARD exact K32/512 exposure RFF512/512-step recipe"
    return {"experiment_id": identity, "result_sha256": sha256_file(result_path), "plan_sha256": result["plan_sha256"],
            "study_sha256": protocol["study_sha256"], "failures": failures, "all_workers_and_trials_complete": complete,
            "identical_legal_data_across_arms": legal_pairing, "identical_training_sets": legal_sets,
            "source_fit_identity": identity_checks, "arms": arms, "costs": costs,
            "primary_simultaneous_intervals": contrasts, "primary_gates": gates, "competence_gates": competence,
            "decision": decision, "model_executed_by_analysis": False, "economic_advantage_claim": False,
            "fresh_final_executed": False, "whole_program_complete": False}


def persist(path, value):
    if path.exists():
        if json.loads(path.read_text(encoding="utf8")) != json.loads(json.dumps(value)):
            raise ValueError("Existing analysis differs; append a new correction")
    else:
        atomic_write_json(path, value)


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    output = analyze(base, sys.argv[1])
    persist(base / f"research/reviews/{sys.argv[1]}-PVM01-exposure-analysis.json", output)
    print(json.dumps({k: output[k] for k in ("experiment_id", "failures", "primary_gates", "competence_gates", "decision")}, indent=2))
