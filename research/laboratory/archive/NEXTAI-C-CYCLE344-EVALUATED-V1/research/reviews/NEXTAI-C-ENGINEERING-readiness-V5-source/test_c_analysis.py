"""Synthetic scalar receipts; no native payloads, models, fits or registrations."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from nextai_autoresearch import asm01_analysis
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, sha256_json

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "EXP-20990101-9999"
SOURCE_ARMS = {"source_trained": "transport_pca", "source_untrained": "transport_pca_untrained",
               "source_shuffled": "transport_pca_shuffled", "source_ridge": "ridge_pca_scan"}


@pytest.fixture
def analyzer():
    spec = importlib.util.spec_from_file_location("c_analysis_fixture", ROOT / "scripts/analyze_asm01_c_v1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(base, relative, value):
    path = base / relative
    atomic_write_json(path, value)
    return sha256_file(path)


def _copy(base, relative):
    path = base / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / relative, path)


def _fixture(base, a, monkeypatch):
    study = deepcopy(load_json(ROOT / a.STUDY))
    publication = {"exports": 25, "before_final_data": True, "files": {}}
    for name, role in study["roles"].items():
        if role["arm"] not in SOURCE_ARMS:
            continue
        source_name = f"pvm01_tc_{SOURCE_ARMS[role['arm']]}_s{role['seed_index']}"
        for suffix in ("metadata.json", "parameters.npz"):
            publication["files"][f"{source_name}/{suffix}"] = {"sha256": "a" * 64, "bytes": 1}
        source = f"research/laboratory/archive/EXP-20261005-0006-runtime/research/tmp/EXP-20261005-0006/{source_name}.supervisor.json"
        _write(base, source, {"status": "complete", "execution": {"supervised_fit_seconds": 1.}})
    digest = _write(base, study["source_evidence"]["publication_path"], publication)
    study["source_evidence"]["publication_sha256"] = digest
    monkeypatch.setattr(a, "STUDY_SHA256", _write(base, a.STUDY, study))
    for path in (a.TASK, a.CONTRACT, a.MATH_SOURCE):
        _copy(base, path)
    dataset_hash = "d" * 64
    intake = {"complete": True, "study_sha256": a.STUDY_SHA256, "task_contract_sha256": a.TASK_SHA256,
              "converted_writers": [1, 2, 3, 4, 5, 16, 17, 18, 19, 20], "dataset_sha256": dataset_hash,
              "native_files_attempted": 1830, "native_files_converted": 1830, "validated_files": 1830,
              "old74_compared": 74, "previous1171_compared": 1171, "D_samples_opened": 915,
              "no_future_writer_coordinates_read": True, "full_intake_wall_seconds": 5.}
    intake_hash = _write(base, a.INTAKE, intake)
    seeds = [101, 102, 103, 104, 105]
    private_path = f"research/tmp/{IDENTITY}/asm01-private-data.json"
    private_hash = _write(base, private_path, {"experiment_id": IDENTITY, "unit_nonces": [str(i).zfill(64) for i in range(5)]})
    protocol = {"study_path": a.STUDY, "study_sha256": a.STUDY_SHA256, "task_contract_path": a.TASK,
                "task_contract_sha256": a.TASK_SHA256, "program_id": a.PROGRAM_ID,
                "program_contract_path": a.CONTRACT, "program_contract_sha256": a.CONTRACT_SHA256,
                "fit_seconds_total_cap": 9000, "full_worker_total_cap": 9000, "supervised_fit_total_cap": 3600,
                "fit_seconds_cap": 120, "max_rss_bytes": 4294967296, "max_cuda_reserved_bytes": 4294967296}
    plan = {"experiment_id": IDENTITY, "benchmark": a.COHORT, "research_program_protocol": protocol}
    _write(base, f"research/plans/{IDENTITY}.json", plan)
    _write(base, f"research/tmp/{IDENTITY}/runtime-plan.json", {**plan, "matrix": {"seeds": seeds},
        "asm01_private_data_path": str(base / private_path), "asm01_private_data_sha256": private_hash})
    outcomes = []
    for name, role in study["roles"].items():
        index, arm = role["seed_index"], role["arm"]
        report = {"arm": arm, "seed": seeds[index], "seed_index": index, "train_writer": index + 1,
                  "dev_writer": index + 16, "source_replayed": False, "source_frozen": True,
                  "source_before": {"sha": "unchanged"}, "source_after": {"sha": "unchanged"},
                  "optimizer_steps": 2048 if arm == "target_dense" else 0,
                  "dense_set_losses": [1.] * 1024 if arm == "target_dense" else [], "source_provenance": None,
                  "native_dataset_sha256": dataset_hash, "native_intake_sha256": intake_hash,
                  "private_data_sha256": private_hash, "fit_seconds": .1, "native_preparation_seconds": .02,
                  "source_load_seconds": .01, "calibration_seconds": .02}
        for key in ("train_pairs_sha256", "training_validation_sha256", "calibration_sha256", "scaler_sha256"):
            report[key] = str(index).zfill(64)
        if arm in SOURCE_ARMS:
            report["source_provenance"] = {"source_arm": SOURCE_ARMS[arm], "source_unit": index,
                "no_source_refit": True, "metadata_sha256": "a" * 64, "parameters_sha256": "a" * 64}
        trials, data = [], [{"split": "T", "seed_index": index, **{key: report[key] for key in
                            ("train_pairs_sha256", "training_validation_sha256", "calibration_sha256", "scaler_sha256",
                             "native_dataset_sha256", "private_data_sha256")}}]
        for condition in ("nominal", "adverse"):
            for k in (16, 32, 64):
                for update in (0, 1, 4):
                    components = {"allocation_seconds": .0001, "write_preprocessing_seconds": .0001,
                                  "query_preprocessing_seconds_subset": .0001, "ingest_seconds": .0002,
                                  "update_seconds_subset_of_ingest": .0001, "warmup_seconds": .0001,
                                  "query_seconds": .0003, "unattributed_python_output_seconds": .0002}
                    measurements = [{**components, "full_workload_seconds": .001} for _ in range(4)]
                    trial = {"status": "complete", "seed": seeds[index], "seed_index": index,
                             "fit_report": report, "condition": condition, "knowledge_size": k,
                             "update_rounds": update, "dev_sha256": str(index).zfill(64),
                             "measurements": measurements, "latency_samples_us": [1., 2.], "p95_latency_us": 1.,
                             "full_workload_seconds": .005, "state_bytes": 1024, "service_state_restore_seconds": .001,
                             "component_seconds": {key: 4 * value for key, value in components.items()}}
                    trial.update({key: .99 for key in asm01_analysis.QUALITY})
                    trial.update(known_false_abstention=0., fact_top1_accuracy=.9 if arm == "source_trained" else .4,
                                 dense_unknown_rejection=.5 if arm in ("source_untrained", "source_shuffled") else .99)
                    trials.append(trial)
                    data.append({"split": "D", "seed_index": index, "K": k, "update_rounds": update,
                                 "condition": condition, "episodes_sha256": trial["dev_sha256"], "episode_count": 4,
                                 "fixed_writer": index + 16, "no_structural_resampling": True})
        execution = {"return_code": 0, "termination_reason": None, "research_compute_charge_basis": "full_worker_wall_v1",
                     "environment_sanitized": True, "research_compute_seconds": 2., "wall_seconds": 2.,
                     "supervised_fit_seconds": .25, "peak_rss_bytes": 1024}
        outcome = {"candidate": name, "status": "complete", "trials": trials, "audit": {"ok": True}, "execution": execution}
        outcomes.append(outcome)
        prefix = base / f"research/tmp/{IDENTITY}/{name}"
        for row in trials:
            append_jsonl(Path(str(prefix) + ".trials.jsonl"), row)
        for row in data:
            append_jsonl(Path(str(prefix) + ".data.jsonl"), row)
        append_jsonl(Path(str(prefix) + ".fits.jsonl"), {"candidate": name, "seed": seeds[index], "fit_report": report})
        _write(base, f"research/tmp/{IDENTITY}/{name}.device.json", {"allocated": 0, "reserved": 0})
        _write(base, f"research/tmp/{IDENTITY}/{name}.phase.json", {"phase": "complete", "fit_started": 1., "fit_elapsed": .25})
        _write(base, f"research/tmp/{IDENTITY}/{name}.supervisor.json", outcome)
    result = {"experiment_id": IDENTITY, "status": "complete", "candidates": outcomes,
              "integrity_before": {"ok": True}, "integrity_after": {"ok": True}}
    _write(base, f"research/results/{IDENTITY}.json", result)
    cost_path = "research/reviews/NEXTAI-C-SCIENCE-V1.cost.json"
    cost = {"program_id": a.PROGRAM_ID, "contract_sha256": a.CONTRACT_SHA256, "study_path": a.STUDY,
            "study_sha256": a.STUDY_SHA256, "experiment_id": IDENTITY, "full_worker_seconds": 90.,
            "supervised_fit_seconds": 11.25, "conservative_uncovered_failed_runner_seconds": 0, "telemetry_error": None}
    cost_hash = _write(base, cost_path, cost)
    append_jsonl(base / a.EVENTS, {"event": "registered", "experiment_id": IDENTITY, "plan_sha256": sha256_json(plan)})
    append_jsonl(base / a.EVENTS, {"event": "scientific_cost", "experiment_id": IDENTITY,
                 "receipt_path": cost_path, "receipt_sha256": cost_hash, "full_worker_seconds": 90., "supervised_fit_seconds": 11.25})
    return study, result


def test_complete_public_fixture_preserves_frozen_math_and_cost_nesting(analyzer, tmp_path, monkeypatch):
    study, result = _fixture(tmp_path, analyzer, monkeypatch)
    saved = deepcopy(result)
    answer, _, _ = analyzer.collect_analysis(tmp_path, IDENTITY)
    parent = asm01_analysis.analyze(result, study)
    assert result == saved and answer["valid"] and not answer["problems"]
    for key in ("primary", "means", "reference", "economics", "source_information_transfer", "economic_decision"):
        assert answer[key] == parent[key]
    assert answer["full_worker_seconds"] == 90 and answer["supervised_fit_seconds"] == 11.25
    costs = answer["descriptive_full_costs"]
    assert costs["intake_count_in_aggregate"] == 1 and costs["shared_actual_C_acquisition_intake_seconds"] == 5
    assert answer["source_sunk_fit_recharged_to_C_or_B"] is False
    assert len(costs["historical_source_costs"]) == 45


def test_partial_or_missing_result_saves_inconclusive_without_retry(analyzer, tmp_path, monkeypatch):
    _, result = _fixture(tmp_path, analyzer, monkeypatch)
    result["candidates"].pop()
    result["status"] = "complete_with_failures"
    _write(tmp_path, f"research/results/{IDENTITY}.json", result)
    assert analyzer.main(IDENTITY, tmp_path) == 1
    machine = load_json(tmp_path / f"research/analyses/{IDENTITY}-asm01-c.json")
    assert not machine["valid"] and machine["source_information_transfer"] == machine["economic_decision"] == "INCONCLUSIVE"
    assert machine["recorded_workers"] == 44 and machine["problems"]
    assert (tmp_path / f"research/analyses/{IDENTITY}.md").is_file()


def test_missing_trusted_telemetry_overrides_passed_source_contrast(analyzer, tmp_path, monkeypatch):
    _, result = _fixture(tmp_path, analyzer, monkeypatch)
    name = result["candidates"][0]["candidate"]
    (tmp_path / f"research/tmp/{IDENTITY}/{name}.phase.json").unlink()
    answer, _, _ = analyzer.collect_analysis(tmp_path, IDENTITY)
    assert not answer["valid"] and answer["primary"] and all(row["pass"] for row in answer["primary"].values())
    assert answer["source_information_transfer"] == answer["economic_decision"] == "INCONCLUSIVE"
    assert not answer["trusted_resource_journal_checks"][name] and not answer["qualified_routes"]


def test_source_identity_drift_and_math_pin_failure_are_inconclusive(analyzer, tmp_path, monkeypatch):
    _, result = _fixture(tmp_path, analyzer, monkeypatch)
    report = next(row for row in result["candidates"] if row["candidate"].startswith("asm01_source_trained"))["trials"][0]["fit_report"]
    report["source_after"] = {"sha": "changed"}
    _write(tmp_path, f"research/results/{IDENTITY}.json", result)
    answer, _, _ = analyzer.collect_analysis(tmp_path, IDENTITY)
    assert not answer["valid"] and any("source" in problem.lower() for problem in answer["problems"])
    path = tmp_path / analyzer.MATH_SOURCE
    path.write_bytes(path.read_bytes() + b"\n# changed fixture bytes\n")
    answer, _, _ = analyzer.collect_analysis(tmp_path, IDENTITY)
    assert not answer["model_metrics_thresholds_unchanged"] and answer["source_information_transfer"] == "INCONCLUSIVE"


def test_actual_cost_mismatch_cannot_qualify_scientific_recipe(analyzer, tmp_path, monkeypatch):
    _fixture(tmp_path, analyzer, monkeypatch)
    path = "research/reviews/NEXTAI-C-SCIENCE-V1.cost.json"
    cost = load_json(tmp_path / path)
    cost["full_worker_seconds"] = 91.
    _write(tmp_path, path, cost)
    answer, _, _ = analyzer.collect_analysis(tmp_path, IDENTITY)
    assert not answer["valid"] and any("cost" in problem.lower() for problem in answer["problems"])
    assert answer["economic_decision"] == "INCONCLUSIVE"


def test_malformed_saved_results_and_nonfinite_cost_still_preserve_report(analyzer, tmp_path, monkeypatch):
    _fixture(tmp_path, analyzer, monkeypatch)
    _write(tmp_path, f"research/results/{IDENTITY}.json", {"experiment_id": IDENTITY, "status": "failed",
        "candidates": [{"candidate": "malformed", "trials": None, "execution": "missing"}]})
    path = "research/reviews/NEXTAI-C-SCIENCE-V1.cost.json"
    cost = load_json(tmp_path / path)
    cost["supervised_fit_seconds"] = float("nan")
    _write(tmp_path, path, cost)
    assert analyzer.main(IDENTITY, tmp_path) == 1
    raw = (tmp_path / f"research/analyses/{IDENTITY}-asm01-c.json").read_text(encoding="utf-8")
    assert "NaN" not in raw
    saved = json.loads(raw)
    assert saved["supervised_fit_seconds"] is None and saved["problems"]
    assert "INCONCLUSIVE" in (tmp_path / f"research/analyses/{IDENTITY}.md").read_text(encoding="utf-8")


def test_missing_result_remains_unknown_not_zero_and_reports_all_four_unavailable(analyzer, tmp_path, monkeypatch):
    _fixture(tmp_path, analyzer, monkeypatch)
    (tmp_path / f"research/results/{IDENTITY}.json").unlink()
    assert analyzer.main(IDENTITY, tmp_path) == 1
    saved = load_json(tmp_path / f"research/analyses/{IDENTITY}-asm01-c.json")
    assert saved["reported_full_worker_seconds"] is None and saved["reported_supervised_fit_seconds"] is None
    report = (tmp_path / f"research/analyses/{IDENTITY}.md").read_text(encoding="utf-8")
    assert report.count("unavailable; required paired evidence incomplete") == 4
