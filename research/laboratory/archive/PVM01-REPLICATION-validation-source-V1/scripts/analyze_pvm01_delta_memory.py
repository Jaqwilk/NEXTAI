"""Stored-result-only preregistered PVM delta-memory analysis; never executes models."""
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
    update, retain = contrasts["updated"], contrasts["retained"]
    return {
        "five_paired_units": all(v["n"] == 5 for v in contrasts.values()),
        "updated_mean": update["n"] == 5 and update["mean"] >= frozen["updated_gain_mean_min"],
        "updated_lower": update["n"] == 5 and update["low"] >= frozen["updated_gain_ci_lower_min"],
        "all_updated_positive": update["n"] == 5 and update["positive_units"] == 5,
        "retention_noninferiority": retain["n"] == 5 and retain["low"] >= frozen["retained_difference_ci_lower_min"],
        **{name: value["n"] == 5 and value["mean"] >= frozen[f"delta_vs_{name}_mean_full_answer_gain_min"]
           and value["low"] >= frozen["both_learning_ci_lower_min"]
           for name, value in contrasts.items() if name in {"untrained", "shuffled"}},
    }


def analyze(base, identity):
    result_path, plan_path = (base / f"research/{folder}/{identity}.json" for folder in ("results", "plans"))
    result, plan = (json.loads(p.read_text(encoding="utf8")) for p in (result_path, plan_path))
    assert result["plan_sha256"] == sha256_json(plan)
    protocol = plan["research_program_protocol"]
    study = json.loads((base / protocol["study_path"]).read_text(encoding="utf8"))
    assert sha256_file(base / protocol["study_path"]) == protocol["study_sha256"]
    arms, costs, reports, failures, pairing = {}, {}, {}, [], {}
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
        means = {key: float(np.mean([r[key] for r in rows])) if rows[0][key] is not None else None for key in metrics}
        updated = [r for r in rows if r["update_rounds"] in (1, 4)]
        means.update(updated=float(np.mean([r["updated_known_accuracy"] for r in updated])),
                     retained=float(np.mean([r["retained_known_accuracy"] for r in updated])),
                     threshold=report["calibration_choice"]["threshold"])
        means["by_K"] = {str(k): {key: float(np.mean([r[key] for r in rows if r["knowledge_size"] == k]))
                                 if rows[0][key] is not None else None for key in metrics} for k in (32, 128, 512)}
        arms.setdefault(arm, {})[str(index)] = means
        execution = outcome["execution"]
        costs.setdefault(arm, {})[str(index)] = {
            "fit_phase_seconds": execution["supervised_fit_seconds"],
            "charged_worker_seconds": execution["research_compute_seconds"],
            "peak_rss_bytes": execution["peak_rss_bytes"],
            "full_workload_seconds": sum(r["full_workload_seconds"] for r in rows),
            "p95_query_us": outcome["summary"]["p95_latency_us"],
            "logical_state_bytes": max(r["state_bytes"] for r in rows),
            "device": rows[0]["runtime_device"], "fit_seconds": report["fit_seconds"],
            **{key: sum(r["component_seconds"][key] for r in rows) for key in rows[0]["component_seconds"]},
        }
    def contrast(control, metric):
        indices = sorted(set(arms.get("delta", {})) & set(arms.get(control, {})))
        return interval([arms["delta"][i][metric] - arms[control][i][metric] for i in indices],
                        protocol["diagnosis_gates"]["simultaneous_primary_interval_level"])
    contrasts = {"updated": contrast("additive", "updated"), "retained": contrast("additive", "retained"),
                 "untrained": contrast("delta_untrained", "accuracy"), "shuffled": contrast("delta_shuffled", "accuracy")}
    gates = primary_gates(contrasts, protocol["diagnosis_gates"])
    competence = {}
    for arm in ("delta", "dense"):
        units = list(arms.get(arm, {}).values())
        competence[arm] = {
            "five_units": len(units) == 5,
            "mean_accuracy": len(units) == 5 and np.mean([u["accuracy"] for u in units]) >= .95,
            "each_unit_accuracy": len(units) == 5 and min(u["accuracy"] for u in units) >= .9,
            "each_K_accuracy": len(units) == 5 and all(np.mean([u["by_K"][str(k)]["accuracy"] for u in units]) >= .9 for k in (32, 128, 512)),
            "mean_unknown": len(units) == 5 and np.mean([u["dense_unknown_rejection"] for u in units]) >= .95,
            "each_unit_unknown": len(units) == 5 and min(u["dense_unknown_rejection"] for u in units) >= .9,
            "known_false_abstention": len(units) == 5 and np.mean([u["known_false_abstention"] for u in units]) <= .02,
        }
        competence[arm] = {k: bool(v) for k, v in competence[arm].items()}
    identity_checks = {i: all(
        reports.get(("delta", i), {}).get(key) == reports.get(("additive", i), {}).get(key)
        and reports.get(("delta", i), {}).get(key) is not None
        for key in ("initial_parameters_sha256", "final_encoder_sha256", "alignment_losses", "memory_projection_sha256")) for i in range(5)}
    legal_pairing = len(pairing) == 5 and all(len(v) == 1 for v in pairing.values())
    complete = not failures and len(result["candidates"]) == len(study["candidates"]) and legal_pairing and all(identity_checks.values())
    if not complete or not all(competence["dense"].values()):
        decision = "INCONCLUSIVE comparison"
    elif all(gates.values()) and all(competence["delta"].values()):
        decision = "KEEP narrow delta mechanism for further validation"
    elif gates["updated_mean"] and gates["updated_lower"] and gates["all_updated_positive"]:
        decision = "KEEP narrow update effect; DISCARD this economic recipe"
    else:
        decision = "DISCARD exact RFF2048/sigma0.35/beta1 recipe"
    return {"experiment_id": identity, "result_sha256": sha256_file(result_path),
            "plan_sha256": result["plan_sha256"], "study_sha256": protocol["study_sha256"],
            "failures": failures, "all_workers_and_trials_complete": complete,
            "identical_legal_data_across_arms": legal_pairing, "delta_additive_source_fit_identity": identity_checks,
            "arms": arms, "costs": costs, "primary_simultaneous_intervals": contrasts,
            "primary_gates": gates, "competence_gates": competence, "decision": decision,
            "model_executed_by_analysis": False, "economic_advantage_claim": False,
            "fresh_final_executed": False, "whole_program_complete": False}


def persist(path, value):
    if path.exists():
        if json.loads(path.read_text(encoding="utf8")) != json.loads(json.dumps(value)):
            raise ValueError("Existing analysis differs; append a new correction, do not overwrite")
    else:
        atomic_write_json(path, value)


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    output = analyze(base, sys.argv[1])
    persist(base / f"research/reviews/{sys.argv[1]}-PVM01-delta-analysis.json", output)
    print(json.dumps({k: output[k] for k in ("experiment_id", "failures", "primary_gates", "competence_gates", "decision")}, indent=2))
