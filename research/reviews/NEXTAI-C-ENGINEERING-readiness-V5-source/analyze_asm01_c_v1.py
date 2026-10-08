"""Saved C outcomes and trusted journals; unchanged ASM scientific calculations.

No native arrays are loaded, no model is instantiated and no fit is replayed.
Missing evidence produces a durable INCONCLUSIVE analysis, not a rescued study.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import sys

from nextai_autoresearch.asm01_analysis import ARMS, QUALITY, analyze
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.pc01_telemetry import read_device_sample
from nextai_autoresearch.research_program_c import CONTRACT, CONTRACT_SHA256, EVENTS, PROGRAM_ID
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, sha256_json
from nextai_autoresearch.worker_resource_peaks import validate_peak_record

STUDY = "research/plans/ASM01-C-STABILIZED-SCREEN-V1.json"
STUDY_SHA256 = "297357e54f271bebe8fdf8da0d6a31c6d2c7a3fea5251ad9f1008eb9b26b8c1d"
TASK = "research/plans/ASM01-C-SIGNED-SERIAL-TASK-V1.json"
TASK_SHA256 = "66cb7521a72e3485c8738d0f46cfe64bad3d773755fcc15c5db23a4cde9afa85"
MATH_SOURCE = "src/nextai_autoresearch/asm01_analysis.py"
MATH_SHA256 = "7f42f0f1a66c7de3332c99592f868284d6bb032fbd457b6b85919ae46b69d47d"
INTAKE = "research/data_manifests/ASM01-C-ACQUISITION-V1.json"
COHORT = "asm01_native_memory_v4"
_CELLS = {(condition, k, update) for condition in ("nominal", "adverse")
          for k in (16, 32, 64) for update in (0, 1, 4)}
_ERRORS = (OSError, ValueError, KeyError, TypeError, AssertionError, IndexError, ZeroDivisionError)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _trials(outcome):
    value = outcome.get("trials")
    return value if isinstance(value, list) else []


def _reuse(candidate_cold, reference_cold, candidate_service, reference_service):
    """Same descriptive R1/R4/R16 arithmetic as analyze_pvm01_confirmation."""
    _require(all(_finite(value) for value in (candidate_cold, reference_cold, candidate_service, reference_service)),
             "Invalid descriptive cold/service cost")
    savings = reference_service - candidate_service
    return {"by_reuse": {str(r): {"candidate_seconds": candidate_cold + r * candidate_service,
                                  "reference_seconds": reference_cold + r * reference_service} for r in (1, 4, 16)},
            "faster_service_break_even_workloads": max(0., (candidate_cold - reference_cold) / savings) if savings > 0 else None}


def _sanitize(value, nonfinite, path="analysis"):
    """Invalid raw evidence remains hashed separately; unknown numbers stay null."""
    if isinstance(value, float) and not math.isfinite(value):
        nonfinite.append(path)
        return None
    if isinstance(value, dict):
        return {key: _sanitize(item, nonfinite, f"{path}.{key}") for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item, nonfinite, f"{path}[{index}]") for index, item in enumerate(value)]
    return value


def _local(root, relative):
    _require(isinstance(relative, str) and bool(relative), "Missing evidence path")
    path = (root / relative).resolve()
    _require(path.is_relative_to(root.resolve()), "Evidence path escapes checkout")
    return path


def _input(root, relative, hashes, problems, *, expected=None, default=None):
    try:
        path = _local(root, relative)
        digest = sha256_file(path)
        if expected:
            _require(digest == expected, f"Frozen hash mismatch {relative}")
        hashes[relative] = digest
        value = load_json(path)
        _require(isinstance(value, dict), f"Expected object {relative}")
        return value
    except _ERRORS as exc:
        problems.append(f"Input evidence failed {relative}: {type(exc).__name__}: {exc}")
        return default if default is not None else {}


def _fallback(identity, problems):
    return {"id": identity, "valid": False, "problems": list(problems),
            "source_information_transfer": "INCONCLUSIVE", "economic_decision": "INCONCLUSIVE",
            "qualified_routes": [], "independent_units": 5,
            "independence_unit": "disjoint development writer/source-seed pairs",
            "replication_or_final": False, "whole_goal_complete": False}


def _trusted_role(root, identity, outcome, protocol, study, runtime, intake, intake_hash):
    """The HAR journal/resource contract, bound to C writer/data identities."""
    name = outcome["candidate"]
    directory = root / "research/tmp" / identity
    execution, trials = outcome["execution"], outcome["trials"]
    index = study["roles"][name]["seed_index"]
    seed = runtime["matrix"]["seeds"][index]
    _require(outcome["status"] == "complete" and outcome["audit"]["ok"] is True,
             "Mandatory audited worker did not complete")
    _require(len(trials) == 18 and { (r["condition"], r["knowledge_size"], r["update_rounds"]) for r in trials } == _CELLS,
             "Missing/duplicate fixed condition/K/update trials")
    for row in trials:
        _require(all(row[key] is None or _finite(row[key]) and row[key] <= 1 for key in QUALITY),
                 "Quality metric is missing/nonfinite/boolean/outside probability range")
        _require(isinstance(row["latency_samples_us"], list) and bool(row["latency_samples_us"])
                 and all(_finite(value) for value in row["latency_samples_us"])
                 and _finite(row["p95_latency_us"]) and type(row["state_bytes"]) is int and row["state_bytes"] > 0,
                 "Query latency/state telemetry is missing or nonfinite")
    _require(execution["return_code"] == 0 and execution["termination_reason"] is None,
             "Worker exit or termination invalid")
    _require(execution["research_compute_charge_basis"] == "full_worker_wall_v1"
             and execution["environment_sanitized"] is True
             and execution.get("fit_charge_conservative", False) is False,
             "Trusted worker clock/environment boundary invalid")
    full, fit, rss = execution["research_compute_seconds"], execution["supervised_fit_seconds"], execution["peak_rss_bytes"]
    _require(_finite(full) and 0 < full == execution["wall_seconds"] <= study["resources"]["worker_charge_ceiling_with_monitor_margin"]
             and _finite(fit) and fit <= full and fit <= protocol["fit_seconds_cap"]
             and type(rss) is int and 0 < rss <= protocol["max_rss_bytes"],
             "Full worker, fit or sampled tree RSS exceeds frozen cap/is missing")
    device = read_device_sample(directory / f"{name}.device.json")
    _require(device is not None and 0 <= device["allocated"] <= device["reserved"] <= protocol["max_cuda_reserved_bytes"],
             "Trusted cumulative CUDA allocator high-water sample missing/invalid")
    phase = load_json(directory / f"{name}.phase.json")
    _require(set(phase) == {"phase", "fit_started", "fit_elapsed"} and phase["phase"] == "complete"
             and _finite(phase["fit_elapsed"]) and phase["fit_elapsed"] == fit
             and _finite(phase["fit_started"]), "Trusted complete phase/fit clock missing or differs")
    fitted = read_jsonl(directory / f"{name}.fits.jsonl")
    _require(len(fitted) == 1 and fitted[0]["candidate"] == name and fitted[0]["seed"] == seed,
             "One matching fit journal is required")
    report = fitted[0]["fit_report"]
    _require(all(row["fit_report"] == report and row["seed"] == seed and row["seed_index"] == index
                 and row["status"] == "complete" for row in trials), "Fit/seed/trial journal identities differ")
    _require(report["seed"] == seed and report["seed_index"] == index
             and report["train_writer"] == index + 1 and report["dev_writer"] == index + 16
             and report["native_dataset_sha256"] == intake["dataset_sha256"]
             and report["native_intake_sha256"] == intake_hash
             and report["private_data_sha256"] == runtime["asm01_private_data_sha256"],
             "Native writer/dataset/intake/private-unit fit binding differs")
    data = read_jsonl(directory / f"{name}.data.jsonl")
    _require(len(data) == 19 and data[0]["split"] == "T" and data[0]["seed_index"] == index,
             "Exactly one T and eighteen D data journal records required")
    for field in ("train_pairs_sha256", "training_validation_sha256", "calibration_sha256", "scaler_sha256",
                  "native_dataset_sha256", "private_data_sha256"):
        _require(data[0][field] == report[field], f"T fit/data identity differs:{field}")
    dev = {(row["condition"], row["K"], row["update_rounds"]): row for row in data[1:]}
    _require(set(dev) == _CELLS and len(dev) == 18, "D journal cells missing or duplicated")
    for row in data[1:]:
        _require(row["split"] == "D" and row["seed_index"] == index and row["fixed_writer"] == index + 16
                 and row["episode_count"] == 4 and row["no_structural_resampling"] is True,
                 "D writer/episode identity differs")
    for row in trials:
        _require(dev[row["condition"], row["knowledge_size"], row["update_rounds"]]["episodes_sha256"] == row["dev_sha256"],
                 "D episode and trial hash differs")
    _require(read_jsonl(directory / f"{name}.trials.jsonl") == trials, "Trial journal differs from saved outcomes")
    _require(load_json(directory / f"{name}.supervisor.json") == outcome, "Trusted supervisor differs from saved outcome")
    suffixes = ["fits.jsonl", "data.jsonl", "trials.jsonl", "device.json", "phase.json", "supervisor.json"]
    resources = {"supervised_fit_seconds": fit, "full_worker_seconds": full,
                 "sampled_tree_peak_rss_bytes": rss, "cuda_allocator_peak_allocated_bytes": device["allocated"],
                 "cuda_allocator_peak_reserved_bytes": device["reserved"], "phase_fit_elapsed_seconds": phase["fit_elapsed"]}
    if protocol.get("resource_measurement_version") == "cumulative_cuda_phase_peaks_v1":
        path = _local(root, execution["resource_peaks_path"])
        _require(path == (directory / f"{name}.resources.json").resolve()
                 and sha256_file(path) == execution["resource_peaks_sha256"], "Trusted resource peak path/hash differs")
        record = load_json(path)
        _require(record == execution["resource_peaks"], "Trusted resource snapshots differ from supervisor")
        validate_peak_record(record, protocol)
        _require(all(row["process_rss_bytes"] <= protocol["max_rss_bytes"] for row in record["snapshots"]),
                 "Resource phase RSS exceeds frozen cap")
        resources["cumulative_phase_peaks"] = record
        suffixes.append("resources.json")
    hashes = {f"research/tmp/{identity}/{name}.{suffix}": sha256_file(directory / f"{name}.{suffix}") for suffix in suffixes}
    return resources, hashes, report


def _source_history(root, name, report, study, hashes):
    provenance = report.get("source_provenance")
    if not provenance:
        _require(not study["roles"][name]["arm"].startswith("source_"), "Source role has no source provenance")
        return {"historical_source_fit_seconds": 0., "source_replayed": False,
                "charged_to_C_again": False, "charged_to_B_again": False}
    _require(provenance["no_source_refit"] is True and report["source_replayed"] is False
             and report["source_frozen"] is True and report["source_before"] == report["source_after"]
             and report["optimizer_steps"] == 0, "Source weights changed or source fit was replayed")
    publication_path = study["source_evidence"]["publication_path"]
    publication = load_json(_local(root, publication_path))
    _require(sha256_file(_local(root, publication_path)) == study["source_evidence"]["publication_sha256"]
             and publication["exports"] == 25 and publication["before_final_data"] is True,
             "Incomplete/leaky frozen source publication")
    source_name = f"pvm01_tc_{provenance['source_arm']}_s{provenance['source_unit']}"
    for suffix, field in (("metadata.json", "metadata_sha256"), ("parameters.npz", "parameters_sha256")):
        _require(provenance[field] == publication["files"][f"{source_name}/{suffix}"]["sha256"],
                 "Used source identity differs from immutable publication")
    relative = f"research/laboratory/archive/EXP-20261005-0006-runtime/research/tmp/EXP-20261005-0006/{source_name}.supervisor.json"
    original = load_json(_local(root, relative))
    _require(original["status"] == "complete" and _finite(original["execution"]["supervised_fit_seconds"]),
             "Historical source fit cost is not complete/finite")
    hashes[relative] = sha256_file(_local(root, relative))
    hashes[publication_path] = sha256_file(_local(root, publication_path))
    return {"historical_source_fit_seconds": original["execution"]["supervised_fit_seconds"],
            "source_receipt_path": relative, "source_receipt_sha256": hashes[relative],
            "metadata_sha256": provenance["metadata_sha256"], "parameters_sha256": provenance["parameters_sha256"],
            "source_before": report["source_before"], "source_after": report["source_after"],
            "source_replayed": False, "charged_to_C_again": False, "charged_to_B_again": False}


def _descriptive_costs(root, outcomes, study, intake, reports, hashes, problems):
    acquisition = intake.get("full_intake_wall_seconds")
    if not _finite(acquisition):
        problems.append("Current shared C acquisition/intake timing missing or nonfinite")
        acquisition = None
    rows, history, services = {}, {}, {}
    for outcome in outcomes:
        name = outcome.get("candidate", "unknown")
        if name not in reports:
            continue
        try:
            trials, report = outcome["trials"], reports[name]
            component_names = ("allocation_seconds", "write_preprocessing_seconds", "query_preprocessing_seconds_subset",
                               "ingest_seconds", "update_seconds_subset_of_ingest", "warmup_seconds", "query_seconds",
                               "unattributed_python_output_seconds")
            for trial in trials:
                _require(_finite(trial["full_workload_seconds"]) and trial["full_workload_seconds"] > 0
                         and _finite(trial["service_state_restore_seconds"])
                         and all(_finite(trial["component_seconds"][key]) for key in component_names),
                         "Missing/nonfinite full service component costs")
                _require(len(trial["measurements"]) == 4, "Expected four actual native episode measurements")
                expected = trial["service_state_restore_seconds"] + sum(item["full_workload_seconds"] for item in trial["measurements"])
                _require(math.isclose(trial["full_workload_seconds"], expected, abs_tol=1e-9, rel_tol=1e-12),
                         "Full service omits restore or actual episode measurements")
                for key in component_names:
                    _require(all(_finite(item[key]) for item in trial["measurements"])
                             and math.isclose(trial["component_seconds"][key], sum(item[key] for item in trial["measurements"]),
                                              abs_tol=1e-9, rel_tol=1e-12), "Service component journal aggregate differs")
            full_service = sum(row["full_workload_seconds"] for row in trials)
            full_worker = outcome["execution"]["research_compute_seconds"]
            _require(full_service <= full_worker + 1e-9, "Nested service exceeds enclosing worker wall")
            non_service = max(0., full_worker - full_service)
            source = _source_history(root, name, report, study, hashes)
            history[name] = source
            _require(all(_finite(report[key]) for key in ("fit_seconds", "native_preparation_seconds", "source_load_seconds", "calibration_seconds")),
                     "Missing/nonfinite offline component costs")
            rows[name] = {"full_worker_seconds": full_worker, "all_18_service_workloads_seconds": full_service,
                          "worker_non_service_seconds": non_service,
                          "offline_components_nested_within_worker": {key: report[key] for key in
                              ("fit_seconds", "native_preparation_seconds", "source_load_seconds", "calibration_seconds")},
                          "service_components_including_nested_subsets": {key: sum(row["component_seconds"][key] for row in trials)
                              for key in component_names},
                          "service_state_restore_seconds": sum(row["service_state_restore_seconds"] for row in trials),
                          "shared_current_C_intake_seconds": acquisition,
                          "current_C_cold_seconds": non_service + acquisition if acquisition is not None else None,
                          "cold_seconds_with_historical_source_fit": non_service + acquisition + source["historical_source_fit_seconds"]
                              if acquisition is not None else None}
            services[name] = {condition: sum(row["full_workload_seconds"] for row in trials if row["condition"] == condition)
                              for condition in ("nominal", "adverse")}
        except _ERRORS as exc:
            problems.append(f"Descriptive full-cost evidence failed {name}: {type(exc).__name__}: {exc}")
    reuse = {}
    if acquisition is not None:
        for name, service in services.items():
            reference = f"asm01_target_dense_s{study['roles'][name]['seed_index']}"
            if reference not in services:
                continue
            reuse[name] = {condition: {
                "current_C_costs": _reuse(rows[name]["current_C_cold_seconds"], rows[reference]["current_C_cold_seconds"],
                                             service[condition], services[reference][condition]),
                "including_historical_source_fit": _reuse(rows[name]["cold_seconds_with_historical_source_fit"],
                                             rows[reference]["cold_seconds_with_historical_source_fit"], service[condition],
                                             services[reference][condition])}
                for condition in ("nominal", "adverse")}
    return {"per_role": rows, "historical_source_costs": history, "descriptive_reuse_costs": reuse,
            "shared_actual_C_acquisition_intake_seconds": acquisition, "intake_count_in_aggregate": 1,
            "component_cost_roles_observed": len(rows), "component_cost_roles_required": 45,
            "component_cost_aggregate_complete": len(rows) == 45,
            "observed_partial_worker_nonservice_sum_seconds": sum(row["worker_non_service_seconds"] for row in rows.values()),
            "current_C_aggregate_worker_nonservice_plus_shared_intake_seconds":
                sum(row["worker_non_service_seconds"] for row in rows.values()) + acquisition
                    if acquisition is not None and len(rows) == 45 else None,
            "component_boundary": "Worker includes fit/preparation/source-load/calibration/generation/service/serialization; these components are not added again. Updates are a subset of ingest; query preprocessing is a subset of query. Shared actual C intake is counted once in aggregate and attributed once per route for descriptive cold/reuse comparisons. Historical source fit is sunk A cost, shown separately without replay or a second C/B charge. Research-wide C tests/failures/admin/analysis/archive/publication stay in the separate inclusive outer-wall completion report.",
            "reuse_used_as_scientific_gate": False}


def collect_analysis(root, identity):
    root = Path(root).resolve()
    _require(re.fullmatch(r"EXP-\d{8}-\d{4}", identity) is not None, "Expected registered experiment identity")
    hashes, problems = {}, []
    study = _input(root, STUDY, hashes, problems, expected=STUDY_SHA256)
    _input(root, TASK, hashes, problems, expected=TASK_SHA256)
    _input(root, CONTRACT, hashes, problems, expected=CONTRACT_SHA256)
    try:
        _require(sha256_file(root / MATH_SOURCE) == MATH_SHA256, "Frozen ASM analysis math changed")
        hashes[MATH_SOURCE] = MATH_SHA256
    except _ERRORS as exc:
        problems.append(f"Scientific calculation source failed: {exc}")
    plan_path, result_path = f"research/plans/{identity}.json", f"research/results/{identity}.json"
    plan = _input(root, plan_path, hashes, problems)
    result = _input(root, result_path, hashes, problems, default={"experiment_id": identity, "candidates": []})
    outcomes = result.get("candidates", [])
    if not isinstance(outcomes, list) or any(not isinstance(row, dict) for row in outcomes):
        problems.append("Saved scientific candidates are malformed")
        outcomes = []
        result = {**result, "candidates": outcomes}
    protocol = plan.get("research_program_protocol", {})
    try:
        _require(plan["experiment_id"] == result["experiment_id"] == identity and plan["benchmark"] == study["cohort"] == COHORT
                 and protocol["study_path"] == STUDY and protocol["study_sha256"] == STUDY_SHA256
                 and protocol["task_contract_path"] == TASK and protocol["task_contract_sha256"] == TASK_SHA256
                 and protocol["program_id"] == PROGRAM_ID and protocol["program_contract_path"] == CONTRACT
                 and protocol["program_contract_sha256"] == CONTRACT_SHA256,
                 "Exact C plan/study/task/program binding differs")
        _require(result["status"] == "complete", "Saved result is not complete")
        _require(protocol["fit_seconds_total_cap"] == protocol["full_worker_total_cap"] == 9000
                 and protocol["supervised_fit_total_cap"] == 3600, "C full-worker/fit caps differ")
        _require(len(outcomes) == 45 and sum(len(_trials(row)) for row in outcomes) == 810,
                 "Expected exactly45 mandatory roles and810 trials")
    except _ERRORS as exc:
        problems.append(f"Scientific binding/completeness failed: {exc}")
    pins_verified = all(hashes.get(path) == expected for path, expected in
                        ((STUDY, STUDY_SHA256), (TASK, TASK_SHA256), (CONTRACT, CONTRACT_SHA256), (MATH_SOURCE, MATH_SHA256)))
    try:
        _require(pins_verified, "Scientific authority/task/study/calculation pins did not pass")
        analysis = analyze(result, study)  # Exactly the unchanged frozen scientific math.
    except _ERRORS as exc:
        analysis = _fallback(identity, [f"Frozen analysis cannot evaluate saved outcomes: {type(exc).__name__}: {exc}"])
    analysis.setdefault("problems", []).extend(problems)
    runtime = _input(root, f"research/tmp/{identity}/runtime-plan.json", hashes, analysis["problems"])
    intake = _input(root, INTAKE, hashes, analysis["problems"])
    try:
        _require(runtime["experiment_id"] == identity and runtime["research_program_protocol"] == protocol
                 and runtime["benchmark"] == COHORT and len(runtime["matrix"]["seeds"]) == 5
                 and len(set(runtime["matrix"]["seeds"])) == 5
                 and all(type(seed) is int for seed in runtime["matrix"]["seeds"]), "Runtime seed/protocol identity differs")
        private_path = f"research/tmp/{identity}/asm01-private-data.json"
        private = _input(root, private_path, hashes, analysis["problems"], expected=runtime["asm01_private_data_sha256"])
        _require(_local(root, runtime["asm01_private_data_path"]) == _local(root, private_path)
                 and private["experiment_id"] == identity and len(private["unit_nonces"]) == 5
                 and len(set(private["unit_nonces"])) == 5, "Runtime private-unit identities differ")
        _require(intake["complete"] is True and intake["study_sha256"] == STUDY_SHA256
                 and intake["task_contract_sha256"] == TASK_SHA256
                 and intake["converted_writers"] == [1, 2, 3, 4, 5, 16, 17, 18, 19, 20]
                 and tuple(intake[key] for key in ("native_files_attempted", "native_files_converted", "validated_files",
                     "old74_compared", "previous1171_compared", "D_samples_opened")) == (1830, 1830, 1830, 74, 1171, 915)
                 and intake["no_future_writer_coordinates_read"] is True, "C complete native/history/intake scope differs")
    except _ERRORS as exc:
        analysis["problems"].append(f"Runtime/native-manifest metadata binding failed: {exc}")
    checks, resource_values, journal_hashes, reports = {}, {}, {}, {}
    for position, outcome in enumerate(outcomes):
        name = outcome.get("candidate", "unknown")
        if not isinstance(name, str) or not name:
            checks[f"malformed-worker-{position}"] = False
            analysis["problems"].append(f"Malformed mandatory worker identity at saved position{position}")
            continue
        try:
            values, journals, report = _trusted_role(root, identity, outcome, protocol, study, runtime, intake, hashes[INTAKE])
            _require(name not in checks, "Duplicate mandatory worker")
            checks[name], resource_values[name], reports[name] = True, values, report
            journal_hashes.update(journals)
        except _ERRORS as exc:
            checks[name] = False
            analysis["problems"].append(f"Trusted resource/journal check failed {name}: {type(exc).__name__}: {exc}")
    totals = {}
    for field in ("research_compute_seconds", "supervised_fit_seconds"):
        values = [(row.get("execution") if isinstance(row.get("execution"), dict) else {}).get(field) for row in outcomes]
        totals[field] = sum(values) if values and all(_finite(value) for value in values) else None
    _require(isinstance(analysis["problems"], list), "Analysis problem evidence must remain a list")
    cost_path = "research/reviews/NEXTAI-C-SCIENCE-V1.cost.json"
    cost = _input(root, cost_path, hashes, analysis["problems"])
    try:
        _require(cost["program_id"] == PROGRAM_ID and cost["contract_sha256"] == CONTRACT_SHA256
                 and cost["study_path"] == STUDY and cost["study_sha256"] == STUDY_SHA256 and cost["experiment_id"] == identity,
                 "Actual C cost receipt covers another study/EXP")
        worker, fit = cost["full_worker_seconds"], cost["supervised_fit_seconds"]
        _require(_finite(worker) and _finite(fit) and fit <= worker and worker <= 9000 and fit <= 3600,
                 "Actual C full-worker/supervised-fit receipt is missing/nonfinite/over cap")
        _require(totals["research_compute_seconds"] is not None and totals["supervised_fit_seconds"] is not None
                 and math.isclose(worker, totals["research_compute_seconds"], abs_tol=1e-9, rel_tol=1e-12)
                 and math.isclose(fit, totals["supervised_fit_seconds"], abs_tol=1e-9, rel_tol=1e-12)
                 and cost.get("conservative_uncovered_failed_runner_seconds", 0) == 0 and cost.get("telemetry_error") is None,
                 "C cost receipt and trusted completed worker totals differ or recovery/telemetry is incomplete")
        events = read_jsonl(root / EVENTS)
        recorded = [event for event in events if event.get("event") == "scientific_cost" and event.get("experiment_id") == identity]
        registered = [event for event in events if event.get("event") == "registered" and event.get("experiment_id") == identity]
        _require(len(recorded) == 1 and len(registered) == 1 and registered[0]["plan_sha256"] == sha256_json(plan)
                 and recorded[0]["receipt_path"] == cost_path and recorded[0]["receipt_sha256"] == hashes[cost_path]
                 and recorded[0]["full_worker_seconds"] == worker and recorded[0]["supervised_fit_seconds"] == fit,
                 "Actual C registration/cost event and immutable receipts differ")
    except _ERRORS as exc:
        analysis["problems"].append(f"Actual C scientific cost crosscheck failed: {exc}")
    costs = _descriptive_costs(root, outcomes, study, intake, reports, hashes, analysis["problems"])
    analysis.update(trusted_resource_journal_checks=checks, resource_measurements=resource_values,
                    journal_sha256=journal_hashes, input_sha256=hashes, descriptive_full_costs=costs,
                    actual_C_cost_receipt=cost, reported_supervised_fit_seconds=totals["supervised_fit_seconds"],
                    reported_full_worker_seconds=totals["research_compute_seconds"],
                    full_worker_seconds=cost.get("full_worker_seconds"), supervised_fit_seconds=cost.get("supervised_fit_seconds"),
                    completed_workers=sum(row.get("status") == "complete" for row in outcomes),
                    recorded_workers=len(outcomes), recorded_trials=sum(len(_trials(row)) for row in outcomes),
                    program_id=PROGRAM_ID, study_sha256=STUDY_SHA256, task_sha256=TASK_SHA256,
                    model_metrics_thresholds_unchanged=pins_verified, no_paid_retry=True, no_prototype=True,
                    whole_goal_complete=False, previous_HAR_decision="DISCARD unchanged",
                    source_sunk_fit_recharged_to_C_or_B=False,
                    hardware_boundary="Cumulative PyTorch allocated/reserved peaks from trusted sampler; driver/context VRAM and energy unmeasured. Parent CPU process-tree RSS is sampled. Phase snapshots are validated only if requested by protocol. Timing does not establish an algorithmic complexity bound.")
    nonfinite = []
    analysis = _sanitize(analysis, nonfinite)
    if nonfinite:
        analysis["problems"].append("Nonfinite saved numeric evidence (preserved by input hash): " + ", ".join(nonfinite))
    analysis["valid"] = bool(analysis.get("valid") and len(checks) == 45 and all(checks.values()) and not analysis["problems"])
    if not analysis["valid"]:
        analysis.update(source_information_transfer="INCONCLUSIVE", economic_decision="INCONCLUSIVE", qualified_routes=[])
    return analysis, result, study


def report_text(analysis):
    def seconds(value):
        return f"{value:.6f}s" if _finite(value) else "unknown"
    def percent(value):
        return f"{100 * value:.3f}" if _finite(value) else "unknown"
    def number(value, precision):
        return f"{value:.{precision}f}" if _finite(value) else "unknown"
    lines = [f"# {analysis['id']} — C frozen-source native ASM development screen", "",
             f"Source information: **{analysis['source_information_transfer']}**. Economic qualification: **{analysis['economic_decision']}**. Valid complete comparison: {analysis['valid']}.", "",
             f"Recorded workers {analysis['recorded_workers']}/45; complete {analysis['completed_workers']}/45; trials {analysis['recorded_trials']}/810. Actual full-worker cost {seconds(analysis['full_worker_seconds'])}; supervised fit {seconds(analysis['supervised_fit_seconds'])}.",
             "Five fixed development writer/source-seed pairs, T1–5/D16–20. Views, queries and repeated updates from the same acquisition are dependent. All1830 members are development data; prior75 attempted/74 converted and later1172 attempted/1171 converted exposures remain disclosed. This is not a blind final or independent replication.", "",
             "Full answers require value AND actual current source. Ranking, source attribution, current values, retained/updated known facts, UNKNOWN and known false abstention remain distinct.", "",
             "| Arm | Condition | K | Full / rank / source / UNKNOWN / false abstention % | Updated / retained / value % | Service s | p95 us | State bytes |",
             "|---|---|---:|---|---|---:|---:|---:|"]
    for arm in ARMS:
        for condition in ("nominal", "adverse"):
            for k in (16, 32, 64):
                row = analysis.get("means", {}).get(arm, {}).get(f"{condition}:K{k}")
                if row:
                    first = " / ".join(percent(row[key]) for key in
                        ("accuracy", "fact_top1_accuracy", "source_attribution_accuracy", "dense_unknown_rejection", "known_false_abstention"))
                    other = " / ".join(percent(row[key]) for key in ("updated_known_accuracy", "retained_known_accuracy", "value_accuracy"))
                    lines.append(f"| {arm} | {condition} | {k} | {first} | {other} | {number(row['full_workload_seconds'], 6)} | {number(row['p95_latency_us'], 2)} | {number(row['state_bytes'], 0)} |")
    if not analysis.get("means"):
        lines.append("| unavailable: incomplete/invalid five-pair comparison | — | — | — | — | — | — | — |")
    lines += ["", "Four preregistered nominal source-information endpoints use paired Student t(df4),98.75% per endpoint and Bonferroni95% for this four-endpoint family:", ""]
    for control in ("source_untrained", "source_shuffled"):
        for metric in ("fact_top1_accuracy", "dense_unknown_rejection"):
            key = f"trained_minus_{control}:{metric}"
            row = analysis.get("primary", {}).get(key)
            lines.append(f"- {key}: {100*row['mean']:.4f}pp, CI[{100*row['lower']:.4f},{100*row['upper']:.4f}]pp; positive {row['positive_pairs']}/5; pass={row['pass']}." if row else f"- {key}: unavailable; required paired evidence incomplete.")
    costs = analysis["descriptive_full_costs"]
    lines += ["", f"Competent dense reference at all six condition/K cells: {analysis.get('reference_competent', False)}. Qualified routes: {analysis.get('qualified_routes', [])}.",
              "The unchanged18 economic guards and108 fixed strong-comparator contrasts per route are retained in the machine JSON. Reference competence failure makes economic qualification INCONCLUSIVE. A target-only fitted readout does not establish transfer; no result here falsifies an architectural family.", "",
              f"Actual shared C acquisition/intake: {seconds(costs['shared_actual_C_acquisition_intake_seconds'])}, counted once in aggregate. Machine JSON separates full worker non-service costs, every service component, and descriptive R1/R4/R16 reuse with and without historical source fit. Original source fit is sunk A expenditure; it is disclosed without replay or recharging C/B. Component fit/service times are nested within worker and outer C time; updates are a subset of ingest and query preprocessing a subset of query.",
              "C stage setup, profiling, tests/failures, analysis, archive and publication belong to the separate final C outer-wall accounting report, including the600s inherited uncertain administrative allowance. This scientific analysis is not final wallet closure. Protected B allocations remain untouched.", "",
              f"Trusted resource/journal checks: {sum(analysis['trusted_resource_journal_checks'].values())}/45. {analysis['hardware_boundary']}", "",
              "Integrity and evidence problems:", ""]
    lines.extend(f"- {problem}" for problem in analysis["problems"])
    if not analysis["problems"]:
        lines.append("- None.")
    lines += ["", "Decision applies only to this exact frozen source/readout/native-view development recipe. No paid retry, source refit, new architecture, WT8–9, external model/API, prototype or schedule change. Previous HAR DISCARD remains unchanged; independent replication, fresh finals and the broader prototype objective remain open.", "",
              "Dataset: UCI Online Handwritten Assamese Characters, Baruah and Hazarika(2015), DOI10.24432/C50C8Q, CC BY4.0. Native instance memory uses pen trajectories, without character labels; future writers6–15/21–30/31–45 and Data_Table remain closed.", ""]
    return "\n".join(lines)


def main(identity, root=None):
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    analysis, _, _ = collect_analysis(root, identity)
    target = root / f"research/analyses/{identity}-asm01-c.json"
    if target.exists():
        _require(load_json(target) == analysis, "Immutable C machine analysis already differs")
    else:
        atomic_write_json(target, analysis)
    report = root / f"research/analyses/{identity}.md"
    text = report_text(analysis)
    if report.exists():
        _require(report.read_text(encoding="utf-8") == text, "Immutable C scientific report already differs")
    else:
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    print(json.dumps({key: analysis[key] for key in ("id", "valid", "source_information_transfer", "economic_decision",
                                         "full_worker_seconds", "supervised_fit_seconds", "problems")}, allow_nan=False), flush=True)
    return 0 if analysis["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
