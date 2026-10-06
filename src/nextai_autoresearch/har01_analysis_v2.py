"""Replication binding adapter; all statistical computations remain in V1."""
import copy

from .har01_analysis import ARMS, CLASSICS, QUALITY, analyze as analyze_parent


def analyze(result, study):
    if study.get("cohort") != "har01_native_memory_v2" or study.get("stage") != "independent_replication":
        raise ValueError("Exact independent HAR replication scope required")
    mapped = copy.deepcopy(result)
    seen = set()
    for outcome in mapped["candidates"]:
        role = study["roles"].get(outcome["candidate"])
        if role is None:
            continue
        index = role["seed_index"]
        for trial in outcome.get("trials", []):
            report = trial.get("fit_report", {})
            if id(report) in seen:
                continue
            seen.add(id(report))
            if (report.get("train_subject"), report.get("dev_subject")) == (index + 6, index + 21):
                report.update(train_subject=index + 1, dev_subject=index + 16)
            else:
                # Prevent old screen bindings from passing the parent's checks.
                report.update(train_subject=-1, dev_subject=-1)
    analysis = analyze_parent(mapped, study)
    analysis.update(replication_or_final=True, stage="independent_replication",
        train_subjects=list(range(6, 11)), dev_subjects=list(range(21, 26)),
        unseen_numeric_reserved_subjects=list(range(11, 16)) + list(range(26, 31)),
        parent_results_pooled=False, source_units_reused_as_fixed_controls=True)
    return analysis
