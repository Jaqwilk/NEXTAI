"""Frozen stored-result analysis, with exact validity gates before decisions."""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t

from nextai_autoresearch.utils import atomic_write_json, sha256_file, sha256_json


def interval(values, level=.95):
    values = np.asarray(values, dtype=float)
    if len(values) != 5 or not np.isfinite(values).all():
        return {"n": len(values), "values": values.tolist(), "mean": None, "low": None, "high": None}
    mean = float(values.mean())
    margin = float(t.ppf((1 + level) / 2, 4) * values.std(ddof=1) / np.sqrt(5))
    return {"n": 5, "mean": mean, "low": mean - margin, "high": mean + margin,
            "values": values.tolist(), "level": level, "positive_units": int(sum(values > 0))}


def primary_gates(contrasts, frozen):
    result = {}
    for key, value in contrasts.items():
        learning = "untrained" in key or "shuffled" in key
        result[key] = value["n"] == 5 and value["low"] is not None and value["low"] >= (
            frozen["learning_ci_lower_min"] if learning else frozen["compression_full_and_retained_ci_lower_min"])
        if learning:
            result[key] &= value["mean"] >= frozen["learning_mean_gain_min"] and value["positive_units"] == 5
    result["all_eight_endpoints"] = len(contrasts) == 8
    return {k: bool(v) for k, v in result.items()}


def exact_fit_checks(reports, steps=2048, dense_steps=1024):
    required = ("transport_pca", "transport_full", "transport_pca_untrained", "transport_pca_shuffled",
                "dense", "dense_cached_cpu", "dense_cached_cuda", "delta", "ridge32", "ridge_pca_scan", "ridge_pca_tree")
    if any(a not in reports for a in required):
        return {"all_required_reports": False}
    trained = [reports[a] for a in ("transport_pca", "transport_full", "dense", "dense_cached_cpu", "dense_cached_cuda", "delta")]
    pca = [reports[a] for a in ("transport_pca", "transport_pca_untrained", "transport_pca_shuffled")]
    dense = [reports[a] for a in ("dense", "dense_cached_cpu", "dense_cached_cuda")]
    frozen, shuffled = reports["transport_pca_untrained"], reports["transport_pca_shuffled"]
    def same(rows, keys):
        return all(rows[0].get(k) is not None and all(r.get(k) == rows[0][k] for r in rows[1:]) for k in keys)
    return {"all_required_reports": True,
            "same_trained_transport": same(trained, ("initial_parameters_sha256", "final_encoder_sha256", "alignment_losses")),
            "exact_steps_and_finite_losses": all(len(r.get("alignment_losses", [])) == steps and r.get("optimizer_steps") == steps and np.isfinite(r["alignment_losses"]).all() and r["initial_parameters_sha256"] != r["final_encoder_sha256"] for r in trained),
            "exact_dense_cache_fit": same(dense, ("final_decoder_sha256", "dense_set_losses")) and all(len(r.get("dense_set_losses", [])) == dense_steps and np.isfinite(r["dense_set_losses"]).all() for r in dense),
            "same_write_only_PCA": same(pca, ("pca_projection_sha256", "pca_grid", "pca_choice")),
            "frozen_no_optimizer": frozen.get("optimizer_steps") == 0 and frozen.get("alignment_losses") == [] and frozen.get("initial_parameters_sha256") == frozen.get("final_encoder_sha256"),
            "shuffled_same_initialization": shuffled.get("initial_parameters_sha256") == pca[0].get("initial_parameters_sha256") and shuffled.get("optimizer_steps") == steps,
            "same_classical_PCA": same([reports[a] for a in ("ridge_pca_scan", "ridge_pca_tree")], ("pca_projection_sha256", "pca_choice", "pca_grid", "fp32_ridge_weights_sha256")),
            "same_classical_transport": same([reports[a] for a in ("ridge32", "ridge_pca_scan", "ridge_pca_tree")], ("fp32_ridge_weights_sha256",))}


def summarize(rows):
    updated = [r for r in rows if r["update_rounds"] in (1, 4)]
    latency = sorted(v for r in rows for v in r["latency_samples_us"])
    return {"accuracy": float(np.mean([r["accuracy"] for r in rows])),
            "unknown": float(np.mean([r["dense_unknown_rejection"] for r in rows])),
            "false_abstention": float(np.mean([r["known_false_abstention"] for r in rows])),
            "retained": float(np.mean([r["retained_known_accuracy"] for r in updated])),
            "updated": float(np.mean([r["updated_known_accuracy"] for r in updated])),
            "full_workload_seconds": sum(r["full_workload_seconds"] for r in rows),
            "p95_us": latency[int(.95 * (len(latency) - 1))], "state_bytes": max(r["state_bytes"] for r in rows)}


def competence(units, gates):
    if len(units) != 5:
        return {"five_units": False}
    return {"five_units": True,
            "mean_accuracy": np.mean([u["accuracy"] for u in units]) >= gates["mean_full_answer_accuracy_min"],
            "each_unit_accuracy": min(u["accuracy"] for u in units) >= gates["each_seed_full_answer_accuracy_min"],
            "each_K_accuracy": all(np.mean([u["by_K"][str(k)]["accuracy"] for u in units]) >= gates["each_K_mean_accuracy_min"] for k in (32, 128, 512)),
            "mean_unknown": np.mean([u["unknown"] for u in units]) >= gates["absent_identity_rejection_mean_min"],
            "each_unit_unknown": min(u["unknown"] for u in units) >= gates["each_seed_absent_identity_rejection_min"],
            "false_abstention": np.mean([u["false_abstention"] for u in units]) <= gates["known_false_abstention_mean_max"]}


def analyze(base, identity):
    plan_path, result_path = (base / f"research/{folder}/{identity}.json" for folder in ("plans", "results"))
    plan, result = (json.loads(p.read_text(encoding="utf8")) for p in (plan_path, result_path))
    assert result["plan_sha256"] == sha256_json(plan)
    protocol = plan["research_program_protocol"]
    study = json.loads((base / protocol["study_path"]).read_text(encoding="utf8"))
    assert sha256_file(base / protocol["study_path"]) == protocol["study_sha256"]
    arms, reports, records, failures, pairing, truth_pairing, resources = {}, {}, {}, [], {}, {}, {}
    for outcome in result["candidates"]:
        role = protocol["roles"][outcome["candidate"]]
        arm, index, rows = role["arm"], str(role["seed_index"]), outcome["trials"]
        if outcome["status"] != "complete" or len(rows) != 18:
            failures.append({"candidate": outcome["candidate"], "status": outcome["status"], "trials": len(rows), "error": outcome.get("error")})
            continue
        report = rows[0]["fit_report"]
        assert all(r["fit_report_sha256"] == sha256_json(report) for r in rows)
        assert {(r["observation_noise"], r["knowledge_size"], r["update_rounds"]) for r in rows} == {(n, k, u) for n in (.02, .04) for k in (32, 128, 512) for u in (0, 1, 4)}
        reports.setdefault(index, {})[arm] = report
        resources.setdefault(arm, {})[index] = outcome["execution"]
        pairing.setdefault(index, set()).add((report["train_pairs_sha256"], report["training_validation_sha256"], report["calibration_sha256"], sha256_json(report["training_sets_sha256"]), tuple(r["dev_sha256"] for r in rows)))
        truth_pairing.setdefault(index, []).append(all(a["truth_pair_sha256"] == b["truth_pair_sha256"] for a, b in zip(rows[:9], rows[9:], strict=True)))
        records[(arm, index)] = [p for r in rows for m in r["measurements"] for p in m["predictions"]]
        for noise in (.02, .04):
            selected = [r for r in rows if r["observation_noise"] == noise]
            unit = summarize(selected)
            unit["by_K"] = {str(k): summarize([r for r in selected if r["knowledge_size"] == k]) for k in (32, 128, 512)}
            arms.setdefault(arm, {}).setdefault(str(noise), {})[index] = unit
    identity_checks, prediction_checks = {}, {}
    for index in map(str, range(5)):
        group = reports.get(index, {})
        identity_checks[index] = exact_fit_checks(group, protocol["recipe"]["alignment_steps"], protocol["recipe"]["dense_set_steps"])
        identity_checks[index]["strict_fit_policy"] = len(group) == 14 and all(r.get("fit_policy_snapshot") == {"deterministic": True, "warn_only": False, "math_sdp": True, "efficient_sdp": False, "flash_sdp": False, "cudnn_sdp": False} for r in group.values())
        reference = records.get(("dense", index), [])
        prediction_checks[index] = {}
        for arm in ("dense_cached_cpu", "dense_cached_cuda"):
            candidate = records.get((arm, index), [])
            same = len(reference) == len(candidate) == 5760 and all(all(a[k] == b[k] for k in ("answer", "top_handle", "top_value", "truth", "target_handle", "stratum")) for a, b in zip(reference, candidate))
            drift = max((abs(a["decision_score"] - b["decision_score"]) for a, b in zip(reference, candidate)), default=float("inf"))
            prediction_checks[index][arm] = {"same_discrete_predictions": same, "max_score_drift": drift, "within_existing_tolerance": drift <= 1e-5}
    contrasts, economic, competence_gates = {}, {}, {}
    for noise in ("0.02", "0.04"):
        for control, metric in (("transport_pca_untrained", "accuracy"), ("transport_pca_shuffled", "accuracy"), ("transport_full", "accuracy"), ("transport_full", "retained")):
            units = sorted(set(arms.get("transport_pca", {}).get(noise, {})) & set(arms.get(control, {}).get(noise, {})))
            contrasts[f"{noise}:{control}:{metric}"] = interval([arms["transport_pca"][noise][i][metric] - arms[control][noise][i][metric] for i in units], protocol["diagnosis_gates"]["simultaneous_primary_interval_level"])
        for arm in ("transport_pca", "dense", "dense_cached_cpu", "dense_cached_cuda"):
            competence_gates[f"{noise}:{arm}"] = {k: bool(v) for k, v in competence(list(arms.get(arm, {}).get(noise, {}).values()), protocol["reference_gates"]).items()}
        for k in (32, 128, 512):
            for metric in ("accuracy", "full_workload_seconds", "p95_us"):
                units = sorted(set(arms.get("transport_pca", {}).get(noise, {})) & set(arms.get("dense_cached_cpu", {}).get(noise, {})))
                values = []
                for i in units:
                    a, b = (arms[arm][noise][i]["by_K"][str(k)][metric] for arm in ("transport_pca", "dense_cached_cpu"))
                    values.append(a - b if metric == "accuracy" else a / b)
                economic[f"{noise}:K{k}:{metric}"] = interval(values, study["economic_measurement"]["simultaneous_interval_level"])
    economic_contract_path = base / protocol["classical_economic_contract_path"]
    assert sha256_file(economic_contract_path) == protocol["classical_economic_contract_sha256"]
    classical_contract = json.loads(economic_contract_path.read_text(encoding="utf8"))
    assert classical_contract["parent_study_sha256"] == protocol["study_sha256"]
    classical_intervals, classical_gates = {}, {}
    for control in classical_contract["controls"]:
        cells = {}
        for noise in ("0.02", "0.04"):
            for k in (32, 128, 512):
                candidate, other = (arms.get(a, {}).get(noise, {}) for a in ("transport_pca", control))
                units = sorted(set(candidate) & set(other))
                quality = interval([other[i]["by_K"][str(k)]["accuracy"] - candidate[i]["by_K"][str(k)]["accuracy"] for i in units], classical_contract["interval_level"])
                cost = interval([other[i]["by_K"][str(k)]["full_workload_seconds"] / candidate[i]["by_K"][str(k)]["full_workload_seconds"] for i in units], classical_contract["interval_level"])
                key = f"{control}:{noise}:K{k}"
                classical_intervals[key] = {"control_minus_candidate_accuracy": quality, "service_control_div_candidate": cost}
                means = lambda group, metric: np.mean([v["by_K"][str(k)][metric] for v in group.values()])
                cells[key] = bool(len(units) == 5 and quality["low"] >= classical_contract["quality_control_minus_candidate_lower_min"] and cost["high"] < classical_contract["full_service_control_div_candidate_upper_strict_max"] and means(other, "state_bytes") <= means(candidate, "state_bytes") and means(other, "accuracy") >= classical_contract["control_mean_accuracy_min"] and means(other, "unknown") >= classical_contract["control_unknown_min"] and means(other, "false_abstention") <= classical_contract["control_false_abstention_max"])
        classical_gates[control] = cells
    matched_quality_classical_dominators = [name for name, cells in classical_gates.items() if len(cells) == 6 and all(cells.values())]
    gates = primary_gates(contrasts, protocol["diagnosis_gates"])
    valid = len(result["candidates"]) == 70 and not failures and len(pairing) == 5 and all(len(v) == 1 for v in pairing.values()) and all(all(v) for v in truth_pairing.values()) and all(all(v.values()) for v in identity_checks.values()) and all(all(v["same_discrete_predictions"] and v["within_existing_tolerance"] for v in row.values()) for row in prediction_checks.values())
    reference_ok = all(all(v.values()) for k, v in competence_gates.items() if "transport_pca" not in k)
    candidate_ok = all(all(v.values()) for k, v in competence_gates.items() if "transport_pca" in k)
    economic_gates = {key: bool(value["n"] == 5 and value["low"] is not None and
        (value["low"] >= study["economic_gates"]["candidate_quality_difference_simultaneous_lower_min"] if key.endswith(":accuracy") else
         value["high"] <= study["economic_gates"]["p95_ratio_upper_max"] if key.endswith(":p95_us") else
         value["high"] <= study["economic_gates"]["full_workload_latency_ratio_simultaneous_upper_max"])) for key, value in economic.items()}
    economic_quality_guards = {f"{noise}:K{k}:{arm}": bool(len(arms.get(arm, {}).get(noise, {})) == 5 and np.mean([u["by_K"][str(k)]["unknown"] for u in arms.get(arm, {}).get(noise, {}).values()]) >= study["economic_gates"]["unknown_rejection_min"] and np.mean([u["by_K"][str(k)]["false_abstention"] for u in arms.get(arm, {}).get(noise, {}).values()]) <= study["economic_gates"]["known_false_abstention_max"]) for noise in ("0.02", "0.04") for k in (32, 128, 512) for arm in ("transport_pca", "dense_cached_cpu")}
    descriptive_dominators = []
    for arm in ("ridge", "ridge32", "ridge_pca_scan", "ridge_pca_tree", "kernel"):
        dominated, strict = True, False
        for noise in ("0.02", "0.04"):
            for k in (32, 128, 512):
                candidate, control = (arms.get(a, {}).get(noise, {}) for a in ("transport_pca", arm))
                if len(candidate) != 5 or len(control) != 5:
                    dominated = False
                    continue
                means = lambda units, metric: np.mean([v["by_K"][str(k)][metric] for v in units.values()])
                dominated &= means(control, "accuracy") >= means(candidate, "accuracy") and means(control, "full_workload_seconds") <= means(candidate, "full_workload_seconds") and means(control, "state_bytes") <= means(candidate, "state_bytes")
                strict |= means(control, "full_workload_seconds") < means(candidate, "full_workload_seconds")
        if dominated and strict: descriptive_dominators.append(arm)
    decision = "INCONCLUSIVE comparison" if not valid or not reference_ok else "KEEP exact transport/PCA recipe for independent validation" if candidate_ok and all(gates.values()) else "DISCARD exact transport/PCA recipe"
    return {"experiment_id": identity, "result_sha256": sha256_file(result_path), "plan_sha256": result["plan_sha256"], "study_sha256": protocol["study_sha256"], "failures": failures, "valid_comparison": valid, "source_fit_identity": identity_checks, "dense_cache_predictions": prediction_checks, "arms": arms, "resources": resources, "primary_simultaneous_intervals": contrasts, "primary_gates": gates, "competence_gates": competence_gates, "economic_simultaneous_intervals": economic, "economic_gates": economic_gates, "economic_quality_guards": economic_quality_guards, "descriptive_classical_dominators": descriptive_dominators, "matched_quality_classical_intervals": classical_intervals, "matched_quality_classical_gates": classical_gates, "matched_quality_classical_dominators": matched_quality_classical_dominators, "economic_screen_qualified": bool(valid and reference_ok and candidate_ok and all(gates.values()) and len(economic_gates) == 18 and all(economic_gates.values()) and all(economic_quality_guards.values()) and not descriptive_dominators and not matched_quality_classical_dominators), "decision": decision, "model_executed_by_analysis": False, "economic_advantage_claim": False, "fresh_final_executed": False, "whole_program_complete": False}


def persist(path, value):
    if path.exists():
        if json.loads(path.read_text(encoding="utf8")) != value:
            raise ValueError("Existing analysis differs; append correction")
    else:
        atomic_write_json(path, value)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    output = analyze(root, sys.argv[1])
    persist(root / f"research/reviews/{sys.argv[1]}-PVM01-transport-analysis.json", output)
    print(json.dumps({k: output[k] for k in ("experiment_id", "valid_comparison", "failures", "primary_gates", "competence_gates", "decision")}, indent=2))
