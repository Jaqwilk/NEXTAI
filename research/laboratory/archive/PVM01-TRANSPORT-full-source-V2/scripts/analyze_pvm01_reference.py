"""Stored-result-only analysis of preregistered PVM01 reference and learning gates."""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t

from nextai_autoresearch.utils import atomic_write_json, sha256_file, sha256_json


def interval(values, level=.95):
    values = np.array(values, dtype=float)
    if len(values) != 5:
        return {"n": len(values), "mean": float(values.mean()) if len(values) else None, "low": None, "high": None}
    mean = float(values.mean())
    margin = float(t.ppf((1 + level) / 2, 4) * values.std(ddof=1) / np.sqrt(5))
    return {"n": 5, "mean": mean, "low": mean - margin, "high": mean + margin, "level": level,
            "values": values.tolist(), "positive_units": int(sum(values > 0))}


def analyze(base, experiment_id):
    path = base / "research/results" / f"{experiment_id}.json"
    result = json.loads(path.read_text(encoding="utf8"))
    plan = json.loads((base / "research/plans" / f"{experiment_id}.json").read_text(encoding="utf8"))
    assert sha256_json(plan) == result["plan_sha256"]
    protocol = plan["research_program_protocol"]
    study = json.loads((base / protocol["study_path"]).read_text(encoding="utf8"))
    assert sha256_file(base / protocol["study_path"]) == protocol["study_sha256"]
    roles = protocol["roles"]
    arms = {}
    costs = {}
    failures = []
    data_hashes, encoder_hashes = {}, {}
    for outcome in result["candidates"]:
        name = outcome["candidate"]
        arm, index = roles[name]["arm"], roles[name]["seed_index"]
        if outcome["status"] != "complete" or len(outcome["trials"]) != 9:
            failures.append({"candidate": name, "status": outcome["status"], "error": outcome.get("error"), "completed_trials": len(outcome["trials"])})
            continue
        rows = outcome["trials"]
        report = rows[0]["fit_report"]
        data_hashes.setdefault(index, set()).add((report["train_pairs_sha256"], report["training_validation_sha256"], report["calibration_sha256"], tuple(r["dev_sha256"] for r in rows)))
        encoder_hashes[(arm, index)] = report["final_encoder_sha256"]
        arms.setdefault(arm, {})[index] = {key: float(np.mean([r[key] for r in rows])) for key in
                                         ("accuracy", "fact_top1_accuracy", "known_false_abstention", "dense_unknown_rejection")}
        arms[arm][index]["by_K"] = {str(k): {key: float(np.mean([r[key] for r in rows if r["knowledge_size"] == k])) for key in
                                            ("accuracy", "fact_top1_accuracy", "dense_unknown_rejection", "known_false_abstention")}
                                            for k in (32, 128, 512)}
        arms[arm][index].update(threshold=report["calibration_choice"]["threshold"], stale_errors=sum(r["stale_or_value_errors_at_correct_handle"] for r in rows))
        execution = outcome["execution"]
        costs.setdefault(arm, []).append({"seed_index": index, "trusted_fit_seconds": execution["supervised_fit_seconds"],
          "charged_worker_seconds": execution["research_compute_seconds"], "peak_rss_bytes": execution["peak_rss_bytes"],
          "fit_operations_estimate": report["fit_operations_estimate"], "full_workload_seconds": sum(r["full_workload_seconds"] for r in rows),
          "allocation_seconds": sum(r["component_seconds"]["allocation_seconds"] for r in rows),
          "ingest_seconds": sum(r["component_seconds"]["ingest_seconds"] for r in rows),
          "updates_seconds_subset": sum(r["component_seconds"]["update_seconds_subset_of_ingest"] for r in rows),
          "warmup_seconds": sum(r["component_seconds"]["warmup_seconds"] for r in rows),
          "queries_seconds": sum(r["component_seconds"]["query_seconds"] for r in rows),
          "logical_state_bytes": max(r["state_bytes"] for r in rows), "p95_query_us": outcome["summary"]["p95_latency_us"],
          "query_count": sum(r["query_count"] for r in rows), "device": rows[0]["runtime_device"]})
    summaries = {arm: {key: interval([units[i][key] for i in sorted(units)]) for key in
                      ("accuracy", "fact_top1_accuracy", "known_false_abstention", "dense_unknown_rejection")} for arm, units in arms.items()}
    contrasts = {}
    for control in ("untrained", "shuffled"):
        indices = sorted(set(arms.get("pointer", {})) & set(arms.get(control, {})))
        contrasts[control] = interval([arms["pointer"][i]["accuracy"] - arms[control][i]["accuracy"] for i in indices], .975)
    learning = len(failures) == 0 and all(v["n"] == 5 and v["mean"] >= .20 and v["low"] >= .10 for v in contrasts.values())
    gates = {}
    for arm in ("dense", "pointer"):
        units = list(arms.get(arm, {}).values())
        gates[arm] = {"five_units": len(units) == 5,
            "mean_accuracy": len(units) == 5 and np.mean([u["accuracy"] for u in units]) >= .95,
            "each_seed_accuracy": len(units) == 5 and min(u["accuracy"] for u in units) >= .90,
            "each_K_accuracy": len(units) == 5 and all(np.mean([u["by_K"][str(k)]["accuracy"] for u in units]) >= .90 for k in (32, 128, 512)),
            "known_false_abstention": len(units) == 5 and np.mean([u["known_false_abstention"] for u in units]) <= .02,
            "mean_unknown": len(units) == 5 and np.mean([u["dense_unknown_rejection"] for u in units]) >= .95,
            "each_seed_unknown": len(units) == 5 and min(u["dense_unknown_rejection"] for u in units) >= .90}
        gates[arm] = {key: bool(value) for key, value in gates[arm].items()}
    pairing = all(len(v) == 1 for v in data_hashes.values()) and len(data_hashes) == 5
    encoder_identity = all(encoder_hashes.get(("pointer", i)) == encoder_hashes.get(("exact_nn", i)) and encoder_hashes.get(("pointer", i)) is not None for i in range(5))
    keep = not failures and learning and pairing and encoder_identity and all(gates["dense"].values())
    return {"experiment_id": experiment_id, "result_sha256": sha256_file(path), "plan_sha256": result["plan_sha256"],
            "study_sha256": protocol["study_sha256"], "model_executed_by_analysis": False, "failures": failures,
            "all_40_workers_and_360_trials_complete": not failures and len(result["candidates"]) == 40,
            "arms": arms, "summaries": summaries, "costs": costs, "learning_contrasts_97_5": contrasts,
            "learning_gate": bool(learning), "competence_gates": gates, "identical_legal_data_across_arms": pairing,
            "pointer_exact_nn_encoder_identity": encoder_identity, "decision": "KEEP scoped screening cohort" if keep else "INCONCLUSIVE reference; diagnose and examine alternatives",
            "economic_advantage_claim": False, "fresh_final_executed": False, "whole_program_complete": False,
            "limitations": ["Five combined seed/data units, synthetic visible local development; not independent blinded final.",
              "Updated history label is not recursive reasoning depth; no language capability or transfer claim.",
              "Neural CUDA and classical CPU on same computer are disclosed deployments, not same-device algorithmic complexity.",
              "Logical storage and operations are estimates; full synchronized workload times and parent peak RSS measured; energy not measured.",
              "No memory mechanism, source-identical memory ablation, adverse test or final in this reference-only study."]}


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    result = analyze(base, sys.argv[1])
    destination = base / "research/reviews" / f"{sys.argv[1]}-PVM01-reference-analysis.json"
    if destination.exists():
        assert json.loads(destination.read_text(encoding="utf8")) == result
    else:
        atomic_write_json(destination, result)
    print(json.dumps({key: result[key] for key in ("experiment_id", "failures", "learning_gate", "competence_gates", "decision")}, indent=2))
