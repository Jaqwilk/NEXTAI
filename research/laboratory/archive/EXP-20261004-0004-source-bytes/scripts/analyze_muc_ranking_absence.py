"""Posthoc separation using immutable saved predictions; no model execution."""
import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

from nextai_autoresearch.utils import load_json, sha256_file, sha256_json


def summarize(observations):
    known = [o for o in observations if o["known"]]
    unknown = [o for o in observations if not o["known"]]
    result = {"known_count": len(known), "unknown_count": len(unknown)}
    for name, predicate in {
        "known_top1_correct": lambda o: o["top1_correct"],
        "known_accepted_correct": lambda o: o["accepted_correct"],
        "known_rejected": lambda o: o["rejected"],
        "known_wrong_key": lambda o: not o["top1_correct"] and o["query"] != o["selected_key"],
        "known_right_key_wrong_timestamp": lambda o: not o["top1_correct"] and o["query"] == o["selected_key"],
        "known_correct_but_rejected": lambda o: o["top1_correct"] and o["rejected"],
    }.items():
        count = sum(predicate(o) for o in known)
        result[name] = count
        result[name + "_rate"] = count / len(known) if known else None
    for kind in ("all", "subject", "relation"):
        group = unknown if kind == "all" else [o for o in unknown if o["unknown_type"] == kind]
        result[f"unknown_{kind}_count"] = len(group)
        result[f"unknown_{kind}_rejected"] = sum(o["rejected"] for o in group)
        result[f"unknown_{kind}_rejection_rate"] = sum(o["rejected"] for o in group) / len(group) if group else None
    for group_name, group in (("known", known), ("unknown", unknown)):
        result[f"{group_name}_rows_scored"] = sum(o["rows_scored"] for o in group)
        for kind in ("pair", "subject", "relation"):
            negatives = sum(o[f"{kind}_negatives"] for o in group)
            fp = sum(o[f"{kind}_fp"] for o in group)
            result[f"{group_name}_{kind}_negative_pairs"] = negatives
            result[f"{group_name}_{kind}_false_positive_pairs"] = fp
            result[f"{group_name}_{kind}_false_positive_rate"] = fp / negatives if negatives else None
    return result


def analyze(root, experiment_id):
    path = root / "research/results" / f"{experiment_id}.json"
    result = load_json(path)
    continuation = root / "research/plans/NEXTAI-CONTINUATION-PROGRAM-V1.json"
    if continuation.is_file():
        bound = load_json(continuation)["carry_forward"]["document_sha256"]
        if bound.get(path.relative_to(root).as_posix()) != sha256_file(path):
            raise ValueError("Completed result differs from immutable carry-forward hash")
    plan = load_json(root / result["plan_path"])
    if sha256_json(plan) != result["plan_sha256"]:
        raise ValueError("Completed plan hash differs from preserved result")
    roles = plan["research_program_protocol"]["roles"]
    arms = defaultdict(list)
    outcomes = []
    for candidate in result["candidates"]:
        binding = roles[candidate["candidate"]]
        outcomes.append({"candidate": candidate["candidate"], "status": candidate["status"], "error": candidate.get("error")})
        if binding["fit_steps"] == 0 or candidate["status"] != "complete":
            continue
        by_k = defaultdict(list)
        for trial in candidate["trials"]:
            for world in trial["diagnostics"]:
                by_k[trial["knowledge_size"]].extend(world["observations"])
        arms[str(binding["fit_steps"])].append({
            "seed_index": binding["seed_index"], "seed": candidate["trials"][0]["seed"],
            "overall": summarize([o for group in by_k.values() for o in group]),
            "by_K": {str(k): summarize(v) for k, v in sorted(by_k.items())},
        })
    aggregates = {}
    for arm, units in arms.items():
        units.sort(key=lambda u: u["seed_index"])
        aggregates[arm] = {"independent_units": len(units), "seeds": units,
            "mean_top1_accuracy": statistics.fmean(u["overall"]["known_top1_correct_rate"] for u in units),
            "mean_unknown_rejection": statistics.fmean(u["overall"]["unknown_all_rejection_rate"] for u in units)}
    return {"experiment_id": experiment_id, "result_sha256": sha256_file(path),
            "plan_sha256": result["plan_sha256"], "posthoc": True, "model_executed": False,
            "completed_metrics_thresholds_or_decisions_changed": False,
            "uncertainty_unit": "five seed/data units; nested queries and pair counts are descriptive, not independent replications",
            "outcomes_including_failures": outcomes, "arms": aggregates}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--experiment", default="EXP-20261004-0003")
    args = parser.parse_args()
    print(json.dumps(analyze(args.root, args.experiment), indent=2, sort_keys=True))
