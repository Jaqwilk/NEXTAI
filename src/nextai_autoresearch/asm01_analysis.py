"""Frozen paired writer-level source, competence and full-cost decision rules."""
import math
import statistics

from scipy.stats import t


ARMS = ("source_trained", "source_untrained", "source_shuffled", "source_ridge", "target_dense",
        "target_ridge_pca", "target_kernel", "native_raw", "native_dtw")
CLASSICS = ("source_ridge", "target_ridge_pca", "target_kernel", "native_raw", "native_dtw", "target_dense")
QUALITY = ("accuracy", "fact_top1_accuracy", "source_attribution_accuracy", "dense_unknown_rejection",
           "known_false_abstention", "updated_known_accuracy", "retained_known_accuracy", "value_accuracy")


def paired_interval(values, family_size=1):
    if len(values) != 5 or any(not math.isfinite(value) for value in values):
        raise ValueError("Five finite independent writer pairs required")
    mean = statistics.mean(values)
    half = float(t.ppf(1 - .05 / (2 * family_size), 4)) * statistics.stdev(values) / math.sqrt(5)
    return {"n": 5, "mean": mean, "lower": mean - half, "upper": mean + half,
            "positive_pairs": sum(value > 0 for value in values), "pairs": values,
            "confidence": 1 - .05 / family_size, "family_size": family_size}


def unit_cells(trials):
    grouped = {}
    for trial in trials:
        key = trial["condition"], trial["knowledge_size"]
        grouped.setdefault(key, []).append(trial)
    result = {}
    for key, rows in grouped.items():
        if len(rows) != 3 or {row["update_rounds"] for row in rows} != {0, 1, 4}:
            raise ValueError("Every native cell must retain all three update conditions")
        measurements = [m for row in rows for m in row["measurements"]]
        latency = sorted(sample for row in rows for sample in row["latency_samples_us"])
        if not latency:
            raise ValueError("Missing actual end-to-end latency samples")
        values = {metric: statistics.mean(row[metric] for row in rows if row[metric] is not None)
                  for metric in QUALITY}
        values.update(full_workload_seconds=sum(row["full_workload_seconds"] for row in rows),
                      p95_latency_us=latency[int(.95 * (len(latency) - 1))],
                      p50_latency_us=latency[(len(latency) - 1) // 2],
                      state_bytes=max(row["state_bytes"] for row in rows),
                      service_state_restore_seconds=sum(row["service_state_restore_seconds"] for row in rows),
                      raw_query_samples=len(latency),
                      write_preprocessing_seconds=sum(m["write_preprocessing_seconds"] for m in measurements))
        result[key] = values
    if set(result) != {(condition, size) for condition in ("nominal", "adverse") for size in (16, 32, 64)}:
        raise ValueError("Missing native condition or one of three preregistered scales")
    return result


def qualification(cells, arm):
    gates = {}
    for condition in ("nominal", "adverse"):
        for size in (16, 32, 64):
            key = condition, size
            rows = [cells[arm][unit][key] for unit in range(5)]
            ref = [cells["target_dense"][unit][key] for unit in range(5)]
            checks = {}
            for metric in ("accuracy", "full_workload_seconds", "p95_latency_us"):
                values = [a[metric] - b[metric] if metric == "accuracy" else a[metric] / b[metric]
                          for a, b in zip(rows, ref, strict=True)]
                interval = paired_interval(values, 18)
                limit = -.02 if metric == "accuracy" else .8 if metric == "full_workload_seconds" else .9
                checks[metric] = {**interval, "limit": limit,
                                  "pass": interval["lower"] >= limit if metric == "accuracy" else interval["upper"] <= limit}
            checks["competence"] = statistics.mean(row["accuracy"] for row in rows) >= .95 and all(row["accuracy"] >= .90 for row in rows)
            checks["unknown"] = all(row["dense_unknown_rejection"] >= .95 for row in rows)
            checks["false_abstention"] = all(row["known_false_abstention"] <= .02 for row in rows)
            gates[f"{condition}:K{size}"] = checks
    comparisons, dominators = {}, []
    for comparator in CLASSICS:
        per_cell = {}
        dominates_all = True
        for condition in ("nominal", "adverse"):
            for size in (16, 32, 64):
                key = condition, size
                candidate = [cells[arm][unit][key] for unit in range(5)]
                control = [cells[comparator][unit][key] for unit in range(5)]
                quality = paired_interval([a["accuracy"] - b["accuracy"] for a, b in zip(control, candidate, strict=True)], 108)
                service = paired_interval([a["full_workload_seconds"] / b["full_workload_seconds"] for a, b in zip(control, candidate, strict=True)], 108)
                latency = paired_interval([a["p95_latency_us"] / b["p95_latency_us"] for a, b in zip(control, candidate, strict=True)], 108)
                competent = (statistics.mean(row["accuracy"] for row in control) >= .95
                             and all(row["accuracy"] >= .90 and row["dense_unknown_rejection"] >= .95
                                     and row["known_false_abstention"] <= .02 for row in control))
                dominates = (competent and quality["lower"] >= -.02 and service["upper"] <= 1
                             and latency["upper"] <= 1 and min(service["upper"], latency["upper"]) < 1)
                per_cell[f"{condition}:K{size}"] = {"quality": quality, "service_ratio": service,
                                                     "p95_ratio": latency, "competent": competent, "dominates": dominates}
                dominates_all &= dominates
        comparisons[comparator] = per_cell
        if dominates_all:
            dominators.append(comparator)
    passed = all(all(check["pass"] if isinstance(check, dict) else check for check in checks.values()) for checks in gates.values())
    return {"gates": gates, "comparisons": comparisons, "fixed_matched_quality_dominators": dominators,
            "individual_economic_gates_pass": passed, "qualified": passed and not dominators}


def analyze(result, study):
    problems, cells, reports = [], {arm: {} for arm in ARMS}, {}
    expected = set(study["candidates"])
    outcomes = result["candidates"]
    if len(outcomes) != 45 or {row["candidate"] for row in outcomes} != expected:
        problems.append("Missing/duplicate mandatory native workers")
    for outcome in outcomes:
        name = outcome["candidate"]
        if name not in study["roles"]:
            problems.append("Unexpected native role")
            continue
        role = study["roles"][name]
        arm, index = role["arm"], role["seed_index"]
        if outcome["status"] != "complete" or len(outcome.get("trials", [])) != 18:
            problems.append(f"Incomplete role {name}")
            continue
        report = outcome["trials"][0]["fit_report"]
        if (report["seed_index"] != index or report["train_writer"] != index + 1
                or report["dev_writer"] != index + 16 or report["source_replayed"] is not False):
            problems.append(f"Native unit/writer binding failed {name}")
        if arm.startswith("source_") and (report["source_frozen"] is not True
                or report["source_before"] != report["source_after"] or report["optimizer_steps"] != 0
                or report["source_provenance"]["source_unit"] != index):
            problems.append(f"Actual frozen source guard failed {name}")
        if arm == "target_dense" and (report["optimizer_steps"] != 2048 or len(report["dense_set_losses"]) != 1024):
            problems.append(f"Target reference fixed-step fit failed {name}")
        try:
            cells[arm][index] = unit_cells(outcome["trials"])
            reports[(arm, index)] = report
        except (ValueError, KeyError, ZeroDivisionError) as exc:
            problems.append(f"Native cell validity failed {name}: {exc}")
    for index in range(5):
        current = [reports.get((arm, index)) for arm in ARMS]
        if any(report is None for report in current):
            problems.append(f"Incomplete five-pair unit {index}")
            continue
        for field in ("train_pairs_sha256", "training_validation_sha256", "calibration_sha256", "scaler_sha256",
                      "native_dataset_sha256", "private_data_sha256"):
            if len({report[field] for report in current}) != 1:
                problems.append(f"Paired legal data/scaler mismatch {index}:{field}")
        for condition in ("nominal", "adverse"):
            for size in (16, 32, 64):
                for update in (0, 1, 4):
                    hashes = {next(row["dev_sha256"] for row in outcome["trials"]
                        if row["condition"] == condition and row["knowledge_size"] == size and row["update_rounds"] == update)
                        for outcome in outcomes if outcome["candidate"] in expected
                        and study["roles"][outcome["candidate"]]["seed_index"] == index and len(outcome.get("trials", [])) == 18}
                    if len(hashes) != 1:
                        problems.append(f"Paired native episodes mismatch {index}:{condition}:{size}:{update}")
    if result.get("integrity_before", {}).get("ok") is not True or result.get("integrity_after", {}).get("ok") is not True:
        problems.append("Evaluation integrity did not pass before and after")
    analysis = {"id": result["experiment_id"], "valid": not problems, "problems": problems,
                "source_information_transfer": "INCONCLUSIVE" if problems else None,
                "economic_decision": "INCONCLUSIVE" if problems else None,
                "independent_units": 5, "independence_unit": "disjoint native writer/source-seed pairs",
                "replication_or_final": False, "unseen_numeric_reserved_writers": list(range(6, 16)) + list(range(21, 31)),
                "decision_scope": "Exact frozen source/readout/native-view recipe; no architecture/LLM/general-intelligence or blinded-holdout claim"}
    if problems:
        return analysis
    reference = {}
    for condition in ("nominal", "adverse"):
        for size in (16, 32, 64):
            rows = [cells["target_dense"][unit][condition, size] for unit in range(5)]
            reference[f"{condition}:K{size}"] = {
                "accuracy_mean": statistics.mean(row["accuracy"] for row in rows),
                "accuracy_each_unit": [row["accuracy"] for row in rows],
                "unknown_each_unit": [row["dense_unknown_rejection"] for row in rows],
                "false_abstention_each_unit": [row["known_false_abstention"] for row in rows],
                "pass": statistics.mean(row["accuracy"] for row in rows) >= .95
                    and all(row["accuracy"] >= .90 and row["dense_unknown_rejection"] >= .95
                            and row["known_false_abstention"] <= .02 for row in rows)}
    primary = {}
    for control in ("source_untrained", "source_shuffled"):
        for metric in ("fact_top1_accuracy", "dense_unknown_rejection"):
            values = [statistics.mean(cells["source_trained"][unit]["nominal", size][metric]
                                     - cells[control][unit]["nominal", size][metric] for size in (16, 32, 64))
                      for unit in range(5)]
            interval = paired_interval(values, 4)
            primary[f"trained_minus_{control}:{metric}"] = {**interval,
                "pass": interval["mean"] >= .02 and interval["lower"] > 0 and interval["positive_pairs"] == 5}
    competent = all(row["pass"] for row in reference.values())
    means = {}
    for arm in ARMS:
        means[arm] = {}
        for condition in ("nominal", "adverse"):
            for size in (16, 32, 64):
                rows = [cells[arm][unit][condition, size] for unit in range(5)]
                means[arm][f"{condition}:K{size}"] = {
                    metric: statistics.mean(row[metric] for row in rows)
                    for metric in (*QUALITY, "full_workload_seconds", "p95_latency_us", "state_bytes")}
    economics = {arm: qualification(cells, arm) for arm in ARMS}
    learned_pass = all(row["pass"] for row in primary.values())
    analysis.update(reference=reference, reference_competent=competent, primary=primary, means=means,
                    economics=economics, qualified_routes=[arm for arm in ARMS if competent and economics[arm]["qualified"]],
                    source_information_transfer="KEEP" if learned_pass else "DISCARD",
                    economic_decision="INCONCLUSIVE" if not competent else "KEEP" if any(row["qualified"] for row in economics.values()) else "DISCARD",
                    primary_family_confidence=.95, primary_endpoint_confidence=.9875,
                    economic_family_confidence_separate=.95,
                    caution="Family confidence is separate, not a joint95% statement across all families. Repeated windows/queries are not independent data units.")
    return analysis
