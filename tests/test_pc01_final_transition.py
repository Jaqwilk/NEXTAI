"""No corpus access or model execution: transition and synthetic series tests."""
import copy
import shutil

import pytest

from nextai_autoresearch import pc01, pc01_execution as execution, pc01_final_transition as bridge
from nextai_autoresearch.ledger import register_plan
from nextai_autoresearch.utils import project_root, load_json, atomic_write_json, sha256_file, sha256_json
from test_pc01_execution import lab, plan, install_process
from test_pc01_gpu_metadata import snapshot
from test_pc01_harness import replica


def records():
    rows = [replica(i) for i in (1, 2, 3)]
    for row in rows:
        row["gpu_metadata"] = {"before_fit": snapshot(), "after_timing": snapshot()}
    return rows


def test_v3_series_rejects_missing_metadata():
    rows = records()
    del rows[1]["gpu_metadata"]
    assert pc01.series_decision(rows, cohort=pc01.METADATA_COHORT)["decision"] == "inconclusive"


@pytest.mark.parametrize("fault", ["missing_stage", "raw_tamper", "swapped_identity", "null", "omitted", "failed", "duplicate", "unknown"])
def test_v3_series_faults_never_pass(fault):
    rows = records()
    cohort = pc01.METADATA_COHORT
    if fault == "missing_stage":
        del rows[1]["gpu_metadata"]["before_fit"]
    elif fault == "raw_tamper":
        rows[1]["gpu_metadata"]["before_fit"]["stdout"] = "bad"
    elif fault == "swapped_identity":
        rows[1]["gpu_metadata"]["after_timing"]["gpu"]["uuid"] = "GPU-other"
    elif fault == "null":
        rows[1]["gpu_metadata"] = None
    elif fault == "omitted":
        rows.pop()
    elif fault == "failed":
        rows[1]["status"] = "crashed"
    elif fault == "duplicate":
        rows[1]["seed"] = rows[0]["seed"]
    else:
        cohort = "unknown"
    assert pc01.series_decision(rows, cohort=cohort)["decision"] == "inconclusive"


@pytest.mark.parametrize("loss,expected", [(3.0, "positive_control_pass"), (3.5, "positive_control_pass"), (3.50001, "valid_negative")])
def test_v3_quality_thresholds_equal_legacy(loss, expected):
    rows = records()
    for row in rows:
        row["trained_bpb"] = loss
    old = [{k: v for k, v in row.items() if k != "gpu_metadata"} for row in rows]
    decision = pc01.series_decision(rows, cohort=pc01.METADATA_COHORT)
    assert decision == pc01.series_decision(old)
    assert decision["decision"] == expected
    assert pc01.series_decision(old, cohort=pc01.TELEMETRY_COHORT) == decision


def test_exact_real_transition_is_read_only():
    root = project_root()
    before = sha256_file(root / "research/plan_registry.jsonl")
    series_before = sha256_file(root / execution.SERIES) if (root / execution.SERIES).exists() else None
    value = bridge.selected_transition(root, "EXP-20260905-0002")
    assert value["target_cohort"] == pc01.METADATA_COHORT
    assert value["selected_evaluator_sha256"] != value["target_evaluator_sha256"]
    assert sha256_file(root / "research/plan_registry.jsonl") == before
    assert (sha256_file(root / execution.SERIES) if (root / execution.SERIES).exists() else None) == series_before


@pytest.fixture
def anchors(tmp_path, monkeypatch):
    root = project_root()
    policy = load_json(root / bridge.PLAN_PATH)
    paths = [bridge.PLAN_PATH, pc01.CONTRACT_PATH, policy["metadata_receipt"],
             "config/research.toml", "research/eval_manifest.json", "src/nextai_autoresearch/pc01.py",
             "research/plans/EXP-20260905-0002.json", "research/results/EXP-20260905-0002.json",
             *policy["source_constraints"]]
    for relative in paths:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, destination)
    monkeypatch.setattr(execution, "audit_bundle", lambda *args: {"sha256": policy["candidate_audit_sha256"]})
    return tmp_path


@pytest.mark.parametrize("relative", [bridge.PLAN_PATH, pc01.CONTRACT_PATH, "research/plans/EXP-20260905-0002.json",
    "research/results/EXP-20260905-0002.json", "research/laboratory/PC-01-GPU-METADATA-V1.receipt.json",
    "src/nextai_autoresearch/pc01_worker.py", "src/nextai_autoresearch/candidates/pc01_byte_gpt_v1.py"])
def test_transition_rejects_changed_anchors(anchors, relative):
    path = anchors / relative
    if path.suffix == ".json":
        value = load_json(path)
        value["tampered"] = True
        atomic_write_json(path, value)
    else:
        path.write_text(path.read_text() + "\n# changed\n")
    with pytest.raises(ValueError):
        bridge.selected_transition(anchors, "EXP-20260905-0002")


def test_transition_rejects_wrong_selection_and_cohort(anchors):
    with pytest.raises(ValueError, match="selected dev"):
        bridge.selected_transition(anchors, "EXP-20260905-0001")
    path = anchors / "config/research.toml"
    path.write_text(path.read_text().replace(pc01.METADATA_COHORT, pc01.TELEMETRY_COHORT))
    with pytest.raises(ValueError, match="target cohort"):
        bridge.selected_transition(anchors, "EXP-20260905-0002")


def v3_fixture(lab, monkeypatch):
    install_process(monkeypatch)
    path, _ = plan(lab)
    execution.run_diagnostic(path, lab)
    config = lab / "config/research.toml"
    config.write_text(config.read_text().replace(pc01.COHORT, pc01.METADATA_COHORT))
    # Isolate exact real selection authorization; tested against immutable anchors above.
    monkeypatch.setattr(execution, "selected_transition", lambda root, selected: {
        "selected_dev_id": selected, "target_cohort": pc01.METADATA_COHORT,
        "target_evaluator_sha256": load_json(root / "research/eval_manifest.json")["evaluator_sha256"]})
    frozen = execution.freeze_series(lab, path.stem)
    digest = sha256_json(load_json(frozen))
    install_process(monkeypatch, mutate=lambda row: row.update(gpu_metadata={"before_fit": snapshot(), "after_timing": snapshot()}))
    process = execution.supervise
    def wrapped(command, root, work):
        for stage in ("before_fit", "after_timing"):
            atomic_write_json(work / f"gpu-{stage}.json", snapshot())
        return process(command, root, work)
    monkeypatch.setattr(execution, "supervise", wrapped)
    return digest


def test_v3_authenticated_series_preserves_metadata(lab, monkeypatch):
    digest = v3_fixture(lab, monkeypatch)
    draws = iter([0, 0, 1, 1, 2])
    monkeypatch.setattr(execution.secrets, "randbelow", lambda *args: next(draws))
    for index in (1, 2, 3):
        # Fixture factory switches its constant before registration, never edits a registered plan.
        monkeypatch.setattr(pc01, "COHORT", pc01.METADATA_COHORT)
        path, _ = plan(lab, "final", index=index+1, attempt=index, series=digest)
        result = load_json(execution.run_diagnostic(path, lab))
        assert result["status"] == "complete", result.get("error")
        assert "gpu_metadata" in result["measurement"]
    decision = execution.authenticated_series_decision(lab)
    assert decision["decision"] == "positive_control_pass"
    assert decision["runner_authenticity_checked"] and not decision["architecture_promoted"]
    assert [r["seed"] for r in execution.attempt_history(lab) if r["phase"] == "final"] == [10000, 10001, 10002]
    artifact = lab / "research/tmp/EXP-20990101-0003/gpu-before_fit.json"
    artifact.unlink()
    with pytest.raises(ValueError):
        execution.authenticated_series_decision(lab)


@pytest.mark.parametrize("fault", ["missing", "evaluator", "omitted", "crashed"])
def test_v3_registered_series_fails_closed(lab, monkeypatch, fault):
    digest = v3_fixture(lab, monkeypatch)
    if fault == "evaluator":
        atomic_write_json(lab / "research/eval_manifest.json", {"evaluator_sha256": "b"*64})
    elif fault == "missing":
        series = load_json(lab / execution.SERIES)
        del series["transition"]
        atomic_write_json(lab / execution.SERIES, series)
    elif fault == "crashed":
        monkeypatch.setattr(pc01, "COHORT", pc01.METADATA_COHORT)
        path, _ = plan(lab, "final", index=2, attempt=1, series=digest)
        install_process(monkeypatch, "crash")
        execution.run_diagnostic(path, lab)
    with pytest.raises(ValueError):
        execution.authenticated_series_decision(lab)
