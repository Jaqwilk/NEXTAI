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
    for name in ("frozen", "shuffled"):
        value = contrasts[name]
        gates[name] = value["n"] == 5 and value["mean"] >= frozen[f"feature_vs_{name}_mean_full_gain_min"] and value["low"] >= frozen["both_feature_gain_ci_lower_min"] and value["positive_units"] == 5
    value = contrasts["K512_updated"]
    gates["K512_updated"] = value["n"] == 5 and value["mean"] >= frozen["K512_updated_gain_mean_min"] and value["low"] >= frozen["K512_updated_gain_ci_lower_min"] and value["positive_units"] == 5
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
        if arm.startswith(("dense", "compact_")):
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
        indices = sorted(set(arms.get("compact_learned", {})) & set(arms.get(control, {})))
        return interval([arms["compact_learned"][i][metric] - arms[control][i][metric] for i in indices],
                        protocol["diagnosis_gates"]["simultaneous_primary_interval_level"])
    contrasts = {"frozen": contrast("compact_frozen", "accuracy"), "shuffled": contrast("compact_shuffled", "accuracy"),
                 "K512_updated": contrast("compact_frozen", "K512_updated"), "retained": contrast("delta", "retained")}
    gates = primary_gates(contrasts, protocol["diagnosis_gates"])
    competence = {}
    reference = protocol["reference_gates"]
    for arm in ("compact_learned", "dense", "dense_cached_cpu", "dense_cached_cuda"):
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
        group = [reports.get((a, index), {}) for a in ("compact_learned", "compact_frozen", "compact_shuffled", "compact_additive")]
        common = all(group[0].get(key) is not None and all(row.get(key) == group[0][key] for row in group[1:])
                     for key in ("initial_parameters_sha256", "final_encoder_sha256", "alignment_losses",
                                 "compact_initial_features_sha256", "compact_precomputed_sha256"))
        learned, additive, shuffled, frozen = group[0], group[3], group[2], group[1]
        fitted = all(learned.get(key) is not None and learned.get(key) == additive.get(key) for key in
                     ("compact_final_features_sha256", "compact_feature_losses", "compact_feature_gradient_norms", "compact_batch_value_draws_sha256"))
        draws = learned.get("compact_batch_value_draws_sha256") == shuffled.get("compact_batch_value_draws_sha256")
        unchanged = frozen.get("compact_final_features_sha256") == frozen.get("compact_initial_features_sha256") and frozen.get("compact_feature_steps") == 0
        steps = all(r.get("compact_feature_steps") == protocol["recipe"]["compact_feature_steps"] for r in (learned, additive, shuffled))
        identity_checks[str(index)] = {"common_transport_and_initial_features": common, "learned_additive_identical_fit": fitted,
                                      "learned_shuffled_identical_draws": draws, "frozen_features_unchanged": unchanged, "fixed_step_counts": steps}
    legal_pairing = len(pairing) == 5 and all(len(v) == 1 for v in pairing.values())
    legal_sets = len(set_pairing) == 5 and all(len(v) == 1 for v in set_pairing.values())
    complete = not failures and len(result["candidates"]) == len(study["candidates"]) and legal_pairing and legal_sets and all(all(v.values()) for v in identity_checks.values())
    if not complete or not all(all(competence[a].values()) for a in ("dense", "dense_cached_cpu", "dense_cached_cuda")):
        decision = "INCONCLUSIVE comparison"
    elif all(gates.values()) and all(competence["compact_learned"].values()):
        decision = "KEEP compact feature recipe for further validation"
    else:
        decision = "DISCARD exact RFF512/512-step learned feature recipe"
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
    persist(base / f"research/reviews/{sys.argv[1]}-PVM01-compact-analysis.json", output)
    print(json.dumps({k: output[k] for k in ("experiment_id", "failures", "primary_gates", "competence_gates", "decision")}, indent=2))
