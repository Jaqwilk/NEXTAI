"""Prospectively frozen paired-noise analysis of stored audited outcomes only."""
import copy
import json
from pathlib import Path
import sys

import numpy as np

from analyze_pvm01_transport import competence, exact_fit_checks, interval, persist, primary_gates, summarize
from analyze_pvm01_replication import confirm_selected_route
from nextai_autoresearch.utils import sha256_file, sha256_json

MIXED = ("dense_mixed", "dense_cached_cpu_mixed", "dense_cached_cuda_mixed")
BASE = ("dense", "dense_cached_cpu", "dense_cached_cuda")


def mixed_fit_checks(reports, policy, steps=2048, dense_steps=1024):
    if any(a not in reports for a in (*MIXED, "dense")):
        return {"all_mixed_reports": False}
    rows = [reports[a] for a in MIXED]
    base = reports["dense"]
    same = lambda keys: all(rows[0].get(k) is not None and all(r.get(k) == rows[0][k] for r in rows[1:]) for k in keys)
    return {"all_mixed_reports": True,
        "same_mixed_fit_and_inputs": same(("initial_parameters_sha256", "initial_decoder_sha256", "final_encoder_sha256", "final_decoder_sha256", "alignment_losses", "dense_set_losses", "effective_dense_sets_sha256", "base_dense_sets_sha256", "augmentation_policy")),
        "unchanged_alignment": all(all(r.get(k) == base.get(k) and base.get(k) is not None for k in ("initial_parameters_sha256", "final_encoder_sha256", "alignment_losses")) for r in rows),
        "fixed_steps_finite": all(r.get("optimizer_steps") == steps and len(r.get("alignment_losses", [])) == steps and len(r.get("dense_set_losses", [])) == dense_steps and np.isfinite(r["alignment_losses"]).all() and np.isfinite(r["dense_set_losses"]).all() for r in rows),
        "base_sets_preserved_effective_changed": all(r.get("base_dense_sets_sha256") == base.get("training_sets_sha256") and set(r.get("effective_dense_sets_sha256", {})) == {"32", "128"} and all(r["effective_dense_sets_sha256"][k] != base["training_sets_sha256"][k] for k in ("32", "128")) for r in rows),
        "fixed_policy_and_charged_augmentation": all(r.get("augmentation_policy") == policy and r.get("augmentation_seconds_included_in_fit", -1) >= 0 and r.get("augmentation_copied_bytes", 0) > 0 and r.get("augmentation_noise_scalar_samples", 0) > 0 for r in rows)}


def reference_selection(analysis, study):
    frozen = study["dense_noise_reference_gates"]
    arms, contrasts, gates, guards = analysis["arms"], {}, {}, {}
    competence_gates = {f"{noise}:{arm}": {k: bool(v) for k, v in competence(list(arms.get(arm, {}).get(noise, {}).values()), study["reference_gates"]).items()}
                        for noise in ("0.02", "0.04") for arm in (*BASE, *MIXED)}
    for noise in ("0.02", "0.04"):
        left, right = (arms.get(a, {}).get(noise, {}) for a in ("dense_mixed", "dense"))
        indices = sorted(set(left) & set(right))
        for metric in ("accuracy", "unknown", "false_abstention"):
            values = [(right[i][metric] - left[i][metric]) if metric == "false_abstention" else (left[i][metric] - right[i][metric]) for i in indices]
            value = interval(values, frozen["interval_level"])
            key = f"{noise}:{metric}"
            contrasts[key] = value
            minimum = frozen["false_abstention_reduction_ci_lower_min"] if metric == "false_abstention" else frozen["full_and_unknown_ci_lower_min"]
            gates[key] = bool(value["n"] == 5 and value["low"] is not None and value["low"] >= minimum)
        for i, unit in left.items():
            guards[f"{noise}:unit{i}:false_abstention"] = bool(unit["false_abstention"] <= frozen["mixed_each_unit_noise_false_abstention_max"])
    adequate = bool(analysis["valid_comparison"] and len(contrasts) == frozen["primary_comparisons"] == 6
                    and all(gates.values()) and len(guards) == 10 and all(guards.values())
                    and all(all(v.values()) for v in competence_gates.values()))
    adverse = contrasts["0.04:false_abstention"]
    base_competent = all(all(value.values()) for key, value in competence_gates.items() if key.split(":")[1] in BASE)
    mixed_competent = all(all(value.values()) for key, value in competence_gates.items() if key.split(":")[1] in MIXED)
    improved = bool(adequate and adverse["low"] is not None and adverse["low"] > frozen["causal_improvement_adverse_false_abstention_ci_lower_strict_min"]
                    and adverse["mean"] >= frozen["causal_improvement_adverse_false_abstention_mean_min"])
    return {"primary_simultaneous_intervals": contrasts, "primary_gates": gates, "competence_gates": competence_gates,
            "each_unit_false_abstention_guards": guards, "adequate_for_prospective_selection": adequate,
            "base_reference_competent": base_competent, "mixed_reference_competent": mixed_competent,
            "causal_false_abstention_improvement": improved,
            "decision": "INCONCLUSIVE comparison" if not analysis["valid_comparison"] or not base_competent else "KEEP fixed mixed-noise reference" if adequate else "DISCARD exact mixed-noise reference qualification"}


def analyze(base, identity):
    plan_path, result_path = (base / f"research/{folder}/{identity}.json" for folder in ("plans", "results"))
    plan, result = (json.loads(p.read_text(encoding="utf8")) for p in (plan_path, result_path))
    assert result["plan_sha256"] == sha256_json(plan)
    protocol = plan["research_program_protocol"]
    study_path = base / protocol["study_path"]
    assert sha256_file(study_path) == protocol["study_sha256"]
    study = json.loads(study_path.read_text(encoding="utf8"))
    arms, reports, records, failures, pairing, truth_pairing, resources = {}, {}, {}, [], {}, {}, {}
    expected = {(v["arm"], str(v["seed_index"])) for v in protocol["roles"].values()}
    for outcome in result["candidates"]:
        role = protocol["roles"][outcome["candidate"]]
        arm, index, rows = role["arm"], str(role["seed_index"]), outcome["trials"]
        if outcome["status"] != "complete" or len(rows) != 18:
            failures.append({"candidate": outcome["candidate"], "status": outcome["status"], "trials": len(rows), "error": outcome.get("error")})
            continue
        if arm in reports.get(index, {}):
            failures.append({"candidate": outcome["candidate"], "error": "Duplicate independent role"})
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
            # Ranking is separate from value correctness/absence and retained updates.
            unit["known_fact_top1_accuracy"] = float(np.mean([r["fact_top1_accuracy"] for r in selected])) if all(r.get("fact_top1_accuracy") is not None for r in selected) else None
            arms.setdefault(arm, {}).setdefault(str(noise), {})[index] = unit
    identity_checks, mixed_checks, prediction_checks = {}, {}, {}
    for index, unit in reports.items():
        identity_checks[index] = exact_fit_checks(unit)
        identity_checks[index]["strict_fit_policy"] = len(unit) == 17 and all(r.get("fit_policy_snapshot") == {
            "deterministic": True, "warn_only": False, "math_sdp": True, "efficient_sdp": False,
            "flash_sdp": False, "cudnn_sdp": False} for r in unit.values())
        mixed_checks[index] = mixed_fit_checks(unit, study["recipe"]["dense_noise_augmentation"])
        prediction_checks[index] = {}
        for family in (BASE, MIXED):
            reference = records.get((family[0], index), [])
            for arm in family[1:]:
                candidate = records.get((arm, index), [])
                same = len(reference) == len(candidate) == 5760 and all(all(a[k] == b[k] for k in ("answer", "top_handle", "top_value", "truth", "target_handle", "stratum")) for a, b in zip(reference, candidate, strict=True))
                drift = max((abs(a["decision_score"] - b["decision_score"]) for a, b in zip(reference, candidate)), default=float("inf"))
                prediction_checks[index][arm] = {"same_discrete_predictions": same, "max_score_drift": drift, "within_existing_tolerance": drift <= 1e-5}
    valid = bool(len(result["candidates"]) == len(expected) == 85 and set(records) == expected and not failures
                 and result["integrity_before"]["ok"] and result["integrity_after"]["ok"]
                 and len(pairing) == 5 and all(len(v) == 1 for v in pairing.values()) and all(all(v) for v in truth_pairing.values())
                 and all(all(v.values()) for v in (*identity_checks.values(), *mixed_checks.values()))
                 and all(all(v["same_discrete_predictions"] and v["within_existing_tolerance"] for v in row.values()) for row in prediction_checks.values()))
    output = {"experiment_id": identity, "result_sha256": sha256_file(result_path), "plan_sha256": result["plan_sha256"], "study_sha256": protocol["study_sha256"],
              "valid_comparison": valid, "failures": failures, "source_fit_identity": identity_checks, "mixed_fit_identity": mixed_checks,
              "dense_cache_predictions": prediction_checks, "arms": arms, "resources": resources,
              "previous_and_new_units_pooled": False, "model_executed_by_analysis": False, "fresh_final_executed": False,
              "economic_advantage_claim": False, "transfer_claim": False, "whole_program_complete": False}
    output["reference_selection"] = reference_selection(output, study)
    contrasts = {}
    for noise in ("0.02", "0.04"):
        for control, metric in (("transport_pca_untrained", "accuracy"), ("transport_pca_shuffled", "accuracy"), ("transport_full", "accuracy"), ("transport_full", "retained")):
            left, right = (arms.get(a, {}).get(noise, {}) for a in ("transport_pca", control))
            indices = sorted(set(left) & set(right))
            contrasts[f"{noise}:{control}:{metric}"] = interval([left[i][metric] - right[i][metric] for i in indices], study["diagnosis_gates"]["simultaneous_primary_interval_level"])
    output.update(primary_simultaneous_intervals=contrasts, primary_gates=primary_gates(contrasts, study["diagnosis_gates"]))
    addon = base / protocol["classical_economic_contract_path"]
    assert sha256_file(addon) == protocol["classical_economic_contract_sha256"]
    classical = json.loads(addon.read_text(encoding="utf8"))
    assert classical["parent_study_sha256"] == protocol["study_sha256"]
    neural_study = copy.deepcopy(study)
    neural_study["selected_classical_route_confirmation"]["candidate"] = "transport_pca"
    neural_study["selected_classical_route_confirmation"]["non_domination_family"]["fixed_comparators"] = classical["controls"]
    output["neural_economics_against_mixed_reference"] = confirm_selected_route(output, neural_study)
    output["selected_classical_route_confirmation"] = confirm_selected_route(output, study)
    for key in ("neural_economics_against_mixed_reference", "selected_classical_route_confirmation"):
        route = output[key]
        route["screen_qualified"] &= output["reference_selection"]["adequate_for_prospective_selection"] and all(output["primary_gates"].values())
        reference_ok = output["reference_selection"]["mixed_reference_competent"] and all(all(v.values()) for k, v in route["competence_gates"].items() if k.split(":")[1] != route["candidate"])
        route["decision"] = "INCONCLUSIVE comparison" if not valid or not reference_ok else f"KEEP fixed {route['candidate']} route for independent/fresh-final validation" if route["screen_qualified"] else f"DISCARD exact {route['candidate']} economic qualification"
    output["decision"] = output["reference_selection"]["decision"]
    return output


if __name__ == "__main__":
    root, identity = Path(__file__).resolve().parents[1], sys.argv[1]
    result = analyze(root, identity)
    persist(root / f"research/reviews/{identity}-PVM01-dense-noise-analysis.json", result)
    print(json.dumps({"experiment_id": identity, "valid_comparison": result["valid_comparison"], "decision": result["decision"],
                      "causal_improvement": result["reference_selection"]["causal_false_abstention_improvement"],
                      "neural_economics": result["neural_economics_against_mixed_reference"]["screen_qualified"],
                      "classical_economics": result["selected_classical_route_confirmation"]["screen_qualified"]}, indent=2))
