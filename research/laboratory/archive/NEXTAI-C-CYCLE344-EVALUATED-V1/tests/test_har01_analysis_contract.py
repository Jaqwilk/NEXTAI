"""No data or models: exercise the frozen source/economic decision separation."""
import copy
import json
from pathlib import Path

from nextai_autoresearch.har01_analysis import analyze, QUALITY


ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT / "research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json").read_text(encoding="utf-8"))


def fixture_result(reference_good=False, source_effect=True):
    outcomes = []
    for name, role in STUDY["roles"].items():
        index, arm = role["seed_index"], role["arm"]
        quality = .99 if arm != "target_dense" or reference_good else .4
        ranking = .9 if arm == "source_trained" or not source_effect else .4
        rejection = .99 if arm == "source_trained" or not source_effect else .1
        report = {"arm": arm, "seed_index": index, "train_subject": index + 1, "dev_subject": index + 16,
            "source_replayed": False, "source_frozen": True, "source_before": {"sha": "same"},
            "source_after": {"sha": "same"}, "optimizer_steps": 2048 if arm == "target_dense" else 0,
            "dense_set_losses": [1.] * 1024 if arm == "target_dense" else [], "source_provenance": {"source_unit": index}}
        for key in ("train_pairs_sha256", "training_validation_sha256", "calibration_sha256", "scaler_sha256",
                    "native_dataset_sha256", "private_data_sha256"):
            report[key] = str(index).zfill(64)
        rows = []
        for condition in ("nominal", "adverse"):
            for size in (16, 32, 64):
                for update in (0, 1, 4):
                    row = {"fit_report": report, "condition": condition, "knowledge_size": size,
                        "update_rounds": update, "dev_sha256": str(index).zfill(64),
                        "measurements": [{"write_preprocessing_seconds": .001}], "latency_samples_us": [1., 2.],
                        "full_workload_seconds": .01, "state_bytes": 1024, "service_state_restore_seconds": .001}
                    row.update({key: quality for key in QUALITY})
                    row.update(fact_top1_accuracy=ranking, dense_unknown_rejection=rejection if arm.startswith("source_") else .99,
                               known_false_abstention=0.)
                    rows.append(row)
        outcomes.append({"candidate": name, "status": "complete", "trials": rows})
    return {"experiment_id": "EXP-20990101-9999", "candidates": outcomes,
        "integrity_before": {"ok": True}, "integrity_after": {"ok": True}}


def test_failed_target_reference_blocks_economics_without_erasing_valid_source_contrasts():
    result = analyze(fixture_result(), STUDY)
    assert result["valid"] and all(row["pass"] for row in result["primary"].values())
    assert result["source_information_transfer"] == "KEEP"
    assert result["reference_competent"] is False and result["economic_decision"] == "INCONCLUSIVE"
    assert result["qualified_routes"] == []


def test_valid_null_source_contrast_discards_only_exact_transfer_recipe():
    result = analyze(fixture_result(reference_good=True, source_effect=False), STUDY)
    assert result["valid"] and result["reference_competent"]
    assert result["source_information_transfer"] == "DISCARD"
    assert all(row["mean"] == 0 and not row["pass"] for row in result["primary"].values())


def test_missing_pair_or_source_weight_drift_is_inconclusive_before_decision():
    result = fixture_result(reference_good=True)
    missing = copy.deepcopy(result)
    missing["candidates"].pop()
    drift = copy.deepcopy(result)
    drift["candidates"][0]["trials"][0]["fit_report"]["source_after"] = {"sha": "changed"}
    for bad in (missing, drift):
        outcome = analyze(bad, STUDY)
        assert outcome["valid"] is False and outcome["problems"]
        assert outcome["source_information_transfer"] == outcome["economic_decision"] == "INCONCLUSIVE"
