"""Frozen paired-unit uncertainty and gates, not query-level pseudo-replication."""
import math
import statistics
from scipy.stats import t


def paired_interval(differences, confidence=0.95):
    if len(differences) != 5 or any(not math.isfinite(v) for v in differences):
        raise ValueError("Exactly five finite paired units required")
    mean = statistics.fmean(differences)
    margin = float(t.ppf((1 + confidence) / 2, 4)) * statistics.stdev(differences) / math.sqrt(5)
    return {"mean": mean, "lower": mean - margin, "upper": mean + margin,
            "confidence": confidence, "df": 4, "positive_pairs": sum(v > 0 for v in differences), "differences": differences}


def evaluate_gates(contrasts, symbolic_accuracy, thresholds):
    first, second = contrasts["fact_top1_accuracy"], contrasts["dense_unknown_rejection"]
    gates = {
        "fact_selection_effect": first["mean"] >= thresholds["fact_top1_gain_min"],
        "unknown_effect": second["mean"] >= thresholds["unknown_rejection_gain_min"],
        "simultaneous_intervals": min(first["lower"], second["lower"]) > thresholds["both_primary_simultaneous_ci_lower_gt"],
        "sign_consistency": min(first["positive_pairs"], second["positive_pairs"]) >= thresholds["positive_pairs_min"],
        "accepted_known_guard": contrasts["accepted_fact_accuracy"]["mean"] >= thresholds["known_accepted_and_e2e_accuracy_gain_min"],
        "e2e_known_guard": contrasts["e2e_known_accuracy"]["mean"] >= thresholds["known_accepted_and_e2e_accuracy_gain_min"],
        "false_abstention_guard": contrasts["known_false_abstention"]["mean"] <= thresholds["known_false_abstention_gain_max"],
        "symbolic_control": symbolic_accuracy >= thresholds["symbolic_accuracy_min"],
    }
    return {"gates": gates, "decision": "keep_dev_recipe" if all(gates.values()) else "discard_proposed_recipe",
            "architecture_promotion": False}
