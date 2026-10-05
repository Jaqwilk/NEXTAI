"""Independent stored-result confirmation; no model or data generation."""
import json
from pathlib import Path
import sys

import numpy as np

from analyze_pvm01_transport import analyze, competence, interval, persist
from nextai_autoresearch.utils import sha256_file


def confirm_selected_route(analysis, study):
    contract = study["selected_classical_route_confirmation"]
    economic, domination = contract["economic_pair_family"], contract["non_domination_family"]
    candidate, reference = contract["candidate"], contract["competent_reference"]
    arms = analysis["arms"]
    noises, scales = ("0.02", "0.04"), (32, 128, 512)

    def group(arm, noise):
        return arms.get(arm, {}).get(noise, {})

    def mean(rows, k, metric):
        if set(rows) != set(map(str, range(5))):
            return float("nan")
        return float(np.mean([row["by_K"][str(k)][metric] for row in rows.values()]))

    def paired(left, right, k, metric, level, ratio=False):
        values = []
        for index in sorted(set(left) & set(right)):
            a, b = (rows[index]["by_K"][str(k)][metric] for rows in (left, right))
            values.append(a / b if ratio and b > 0 else float("nan") if ratio else a - b)
        return interval(values, level)

    competence_gates = {
        f"{noise}:{arm}": {key: bool(value) for key, value in
            competence(list(group(arm, noise).values()), study["reference_gates"]).items()}
        for noise in noises for arm in (candidate, "dense", reference, "dense_cached_cuda")
    }
    intervals, gates, guards = {}, {}, {}
    for noise in noises:
        left, right = group(candidate, noise), group(reference, noise)
        for k in scales:
            for metric in ("accuracy", "full_workload_seconds", "p95_us"):
                key = f"{noise}:K{k}:{metric}"
                value = paired(left, right, k, metric, economic["interval_level"], metric != "accuracy")
                intervals[key] = value
                threshold = (economic["quality_ci_lower_min"] if metric == "accuracy" else
                             economic["p95_ratio_ci_upper_max"] if metric == "p95_us" else
                             economic["service_ratio_ci_upper_max"])
                gates[key] = bool(value["n"] == 5 and value["low"] is not None and
                    (value["low"] >= threshold if metric == "accuracy" else value["high"] <= threshold))
            for arm in (candidate, reference):
                rows = group(arm, noise)
                guards[f"{noise}:K{k}:{arm}"] = bool(
                    mean(rows, k, "unknown") >= economic["per_cell_unknown_min"] and
                    mean(rows, k, "false_abstention") <= economic["per_cell_false_abstention_max"])
    control_intervals, control_gates = {}, {}
    for control in domination["fixed_comparators"]:
        cells = {}
        for noise in noises:
            left, right = group(control, noise), group(candidate, noise)
            for k in scales:
                key = f"{control}:{noise}:K{k}"
                quality = paired(left, right, k, "accuracy", domination["interval_level"])
                cost = paired(left, right, k, "full_workload_seconds", domination["interval_level"], True)
                control_intervals[key] = {"control_minus_candidate_accuracy": quality,
                                          "service_control_div_candidate": cost}
                cells[key] = bool(quality["n"] == cost["n"] == 5 and quality["low"] is not None and
                    cost["high"] is not None and
                    quality["low"] >= domination["quality_control_minus_candidate_ci_lower_min"] and
                    cost["high"] < domination["control_service_ratio_ci_upper_strict_max"] and
                    mean(left, k, "state_bytes") <= mean(right, k, "state_bytes") and
                    mean(left, k, "accuracy") >= domination["control_accuracy_min"] and
                    mean(left, k, "unknown") >= domination["control_unknown_min"] and
                    mean(left, k, "false_abstention") <= domination["control_false_abstention_max"])
        control_gates[control] = cells
    dominators = [name for name, cells in control_gates.items() if len(cells) == 6 and all(cells.values())]
    reference_ok = all(all(value.values()) for key, value in competence_gates.items()
                       if key.split(":")[1] != candidate)
    candidate_ok = all(all(value.values()) for key, value in competence_gates.items()
                       if key.split(":")[1] == candidate)
    family_sizes_ok = len(intervals) == economic["comparisons"] == 18 and 2 * len(control_intervals) == domination["comparisons"] == 60
    qualified = bool(analysis["valid_comparison"] and reference_ok and candidate_ok and
                     family_sizes_ok and all(gates.values()) and all(guards.values()) and not dominators)
    decision = ("INCONCLUSIVE independent comparison" if not analysis["valid_comparison"] or not reference_ok else
                "KEEP exact ridge/PCA scan route for fresh final" if qualified else
                "DISCARD exact selected-route economic qualification")
    return {"candidate": candidate, "reference": reference, "competence_gates": competence_gates,
            "economic_simultaneous_intervals": intervals, "economic_gates": gates,
            "economic_quality_guards": guards, "matched_quality_intervals": control_intervals,
            "matched_quality_gates": control_gates, "matched_quality_dominators": dominators,
            "family_sizes_ok": family_sizes_ok, "families_joint_95_percent_claim": False,
            "screen_qualified": qualified, "decision": decision,
            "economic_advantage_claim": False, "transfer_claim": False, "fresh_final_executed": False}


if __name__ == "__main__":
    root, identity = Path(__file__).resolve().parents[1], sys.argv[1]
    result = analyze(root, identity)
    study_path = root / "research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json"
    assert result["study_sha256"] == sha256_file(study_path)
    study = json.loads(study_path.read_text(encoding="utf8"))
    result["selected_classical_route_confirmation"] = confirm_selected_route(result, study)
    result["independent_previous_experiment"] = study["independent_replication"]["selecting_experiment"]
    result["previous_and_new_units_pooled"] = False
    persist(root / f"research/reviews/{identity}-PVM01-replication-analysis.json", result)
    print(json.dumps({"experiment_id": identity, "valid_comparison": result["valid_comparison"],
        "neural_decision": result["decision"], "neural_economic_screen_qualified": result["economic_screen_qualified"],
        "selected_route_decision": result["selected_classical_route_confirmation"]["decision"],
        "selected_route_screen_qualified": result["selected_classical_route_confirmation"]["screen_qualified"]}, indent=2))
