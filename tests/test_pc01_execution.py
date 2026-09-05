"""Isolated lifecycle/process fixtures, never training/scoring on the PC-01 corpus."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pytest

from nextai_autoresearch import pc01, pc01_execution as execution, pc01_worker as worker
from nextai_autoresearch.ledger import append_jsonl, register_plan
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_json, sha256_file
from test_pc01_harness import replica


FIXTURE = Path(__file__).parent / "fixtures/pc01_process_fixture.py"
REAL_SUPERVISE = execution.supervise
REAL_VERIFY_CERTIFICATE = execution.verify_certificate


@pytest.fixture
def lab(tmp_path, monkeypatch):
    for directory in ("schemas", "config", "research/plans", "research/results", "research/laboratory"):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    for path in (project_root() / "schemas").glob("*.json"):
        shutil.copy2(path, tmp_path / "schemas" / path.name)
    shutil.copy2(project_root() / "config/research.toml", tmp_path / "config/research.toml")
    config_path = tmp_path / "config/research.toml"
    config_path.write_text(config_path.read_text()
                           .replace("wt01_causal_factorial_diagnostic_v1", pc01.COHORT)
                           .replace(pc01.TELEMETRY_COHORT, pc01.COHORT)
                           .replace(pc01.METADATA_COHORT, pc01.COHORT))
    shutil.copy2(project_root() / pc01.CONTRACT_PATH, tmp_path / pc01.CONTRACT_PATH)
    atomic_write_json(tmp_path / "research/eval_manifest.json", {"evaluator_sha256": "a"*64})
    atomic_write_json(tmp_path / "research/state.json", {"active_experiment_id": None, "completed_experiments": 0,
                                                       "cycle_number": 0, "last_experiment_id": None})
    # Isolate policy activation: real production maintenance denial is tested separately.
    monkeypatch.setattr(execution, "ensure_can_create_plan", lambda root, **kwargs: None)
    monkeypatch.setattr(execution, "ensure_can_run_plan", lambda identifier, root: None)
    monkeypatch.setattr(execution, "verify_certificate", lambda root: {"fixture": True})
    monkeypatch.setattr(execution, "verify_manifest", lambda root: {"ok": True, "problems": []})
    monkeypatch.setattr(execution, "audit_bundle", lambda candidate, root: {"files": {}, "sha256": "a"*64})
    return tmp_path


def plan(root, phase="dev", index=1, attempt=1, series=None):
    value = {"schema_version": 1, "kind": "pc01_diagnostic_plan", "experiment_id": f"EXP-20990101-{index:04}",
        "created_at": "2099-01-01T00:00:00Z", "status": "planned", "benchmark": pc01.COHORT,
        "phase": phase, "candidate": "fixture_model", "contract_sha256": pc01.CONTRACT_SHA256,
        "data_sha256": pc01.DATA_SHA256, "evaluator_sha256": "a"*64, "recipe_sha256": execution.recipe_digest(root),
        "series_sha256": series, "development_seed": 1103,
        "final_seed_policy": {"method": "runner_random_v1", "minimum": 10000, "maximum": 2147483647, "count": 1},
        "architecture_promoted": False, "budget": "pc01_fixed_v1", "question": "synthetic conformance fixture",
        "attempt": attempt}
    path = root / "research/plans" / f"{value['experiment_id']}.json"
    atomic_write_json(path, value)
    register_plan(value, path, root)
    return path, value


def measurement(value, seed=1103):
    record = replica()
    for key in ("contract_sha256", "data_sha256", "evaluator_sha256", "recipe_sha256", "series_sha256", "phase", "experiment_id"):
        record[key] = value[key]
    record["seed"] = seed
    record["target_count"] = 55769 if value["phase"] == "dev" else 111539
    return record


def install_process(monkeypatch, mode="good", mutate=None):
    real = REAL_SUPERVISE
    def substitute(command, root, work):
        runtime = load_json(work / "pc01-runtime.json")
        data = measurement(runtime["plan"], runtime["seed"])
        if mutate:
            mutate(data)
        path = work / "synthetic-input.json"
        atomic_write_json(path, data)
        return real([sys.executable, str(FIXTURE), "--work", str(work), "--mode", mode, "--measurement", str(path)],
                    root, work, limits=execution.Limits(fit_seconds=1, worker_seconds=4, disk_reserve_bytes=0))
    monkeypatch.setattr(execution, "supervise", substitute)


def test_numerical_controls_and_train_only_classical_baselines():
    worker.numerical_controls()
    unigram, bigram = worker.scalar_baselines(b"ab"*200)
    assert np.exp(unigram(np.array([[97]]))).sum() == pytest.approx(1)
    assert np.exp(bigram(np.array([[97]]))).sum() == pytest.approx(1)
    assert bigram(np.array([[97]])).argmax() == 98
    # Evaluation does not fit or mutate either baseline.
    a = unigram(np.array([[97]])).copy()
    pc01.evaluate_bytes(bigram, b"baba"*10)
    assert np.array_equal(a, unigram(np.array([[97]])))


def test_frozen_learning_rate_schedule_without_optimizer_or_training():
    assert worker.learning_rate(0) == 0
    assert worker.learning_rate(99) == pytest.approx(0.00099)
    assert worker.learning_rate(100) == 0.001
    assert worker.learning_rate(4999) == pytest.approx(0.0001, abs=1e-9)
    with pytest.raises(ValueError):
        worker.learning_rate(5000)


@pytest.mark.parametrize("mode,reason", [("good", None), ("worker_hang", "worker_timeout"),
    ("fit_hang", "fit_timeout"), ("cuda", "cuda_limit"), ("payload", "payload_limit"), ("rss", "rss_limit")])
def test_real_subprocess_supervision_without_training(tmp_path, mode, reason):
    work = tmp_path / "worker"
    cap = execution.Limits(fit_seconds=0.25, worker_seconds=1.5, rss_bytes=25*1024**2 if mode == "rss" else 10*pc01.GIB,
                           payload_bytes=1024, disk_reserve_bytes=0)
    outcome = execution.supervise([sys.executable, str(FIXTURE), "--work", str(work), "--mode", mode], tmp_path, work, limits=cap)
    assert outcome["termination_reason"] == reason
    assert outcome["worker_seconds"] < 7
    assert (work / "supervisor.json").exists()
    if mode == "good":
        assert outcome["return_code"] == 0
        assert outcome["rss_bytes"] > 0
    else:
        assert outcome["fit_seconds_charged"] >= cap.fit_seconds


def test_disk_check_precedes_process_start(tmp_path):
    record = execution.supervise(["nonexistent-executable"], tmp_path, tmp_path / "work",
                                 limits=execution.Limits(disk_reserve_bytes=10**30))
    assert "disk reserve" in record["termination_reason"]
    assert record["return_code"] is None


def test_registered_diagnostic_completes_without_architecture_rows(lab, monkeypatch):
    install_process(monkeypatch)
    path, _ = plan(lab)
    result = load_json(execution.run_diagnostic(path, lab))
    assert result["status"] == "complete"
    assert result["candidates"] == result["pareto_front"] == []
    assert not result["architecture_promoted"]
    history = execution.attempt_history(lab)
    assert len(history) == 1 and history[0]["complete"]
    from nextai_autoresearch.report import collect_rows
    assert collect_rows(lab) == []
    with pytest.raises(ValueError, match="already started"):
        execution.run_diagnostic(path, lab)


@pytest.mark.parametrize("mode", ["crash", "crash_before_fit", "fit_hang"])
def test_failure_result_and_attempt_are_preserved(lab, monkeypatch, mode):
    install_process(monkeypatch, mode)
    path, _ = plan(lab)
    result = load_json(execution.run_diagnostic(path, lab))
    assert result["status"] == "inconclusive"
    assert result["error"]
    assert execution.attempt_history(lab)[0]["complete"]
    assert result["execution"]["fit_seconds_charged"] >= 1
    assert (lab / "research/tmp" / path.stem / "worker.log").exists()


@pytest.mark.parametrize("key,value", [("seed", 1104), ("updates", 4999), ("target_count", 111539),
    ("trained_bpb", float("nan")), ("trained_weights_sha256", "0"*64), ("candidate_sha256", "b"*64)])
def test_invalid_worker_output_is_terminal_inconclusive(lab, monkeypatch, key, value):
    install_process(monkeypatch, mutate=lambda record: record.__setitem__(key, value))
    path, _ = plan(lab)
    result = load_json(execution.run_diagnostic(path, lab))
    assert result["status"] == "inconclusive"
    assert "invalid_worker_output" in result["error"]
    assert execution.attempt_history(lab)[0]["complete"]


def test_source_audit_precedes_final_seed(lab, monkeypatch):
    path, _ = plan(lab, "final", series="a"*64)
    monkeypatch.setattr(execution, "audit_bundle", lambda *a: (_ for _ in ()).throw(ValueError("audit rejected")))
    monkeypatch.setattr(execution.secrets, "randbelow", lambda *a: pytest.fail("seed drawn before audit"))
    with pytest.raises(ValueError, match="audit rejected"):
        execution.run_diagnostic(path, lab)
    assert not (lab / execution.ATTEMPTS).exists()


def test_unresolved_parent_interrupt_blocks_retry(lab, monkeypatch):
    path, value = plan(lab)
    runtime = {"plan": value, "seed": 1103, "audit": {"sha256": "a"*64}}
    relative = f"research/tmp/{path.stem}/pc01-runtime.json"
    atomic_write_json(lab / relative, runtime)
    append_jsonl(lab / execution.ATTEMPTS, {"event": "started", "experiment_id": path.stem,
        "plan_sha256": sha256_json(value), "runtime_path": relative, "runtime_sha256": sha256_json(runtime), "seed": 1103})
    assert execution.attempt_history(lab)[0]["fit_seconds_charged"] == 1200
    with pytest.raises(ValueError, match="unresolved"):
        execution.run_diagnostic(path, lab)


def test_plan_schema_has_no_k_d_or_custom_budget(lab):
    _, value = plan(lab)
    execution.validate_plan(value, lab)
    for key, bad in (("matrix", {}), ("development_seed", 1104), ("budget", "deep"), ("attempt", 4)):
        edited = {**value, key: bad}
        with pytest.raises(Exception):
            execution.validate_plan(edited, lab)


def test_changed_preregistered_plan_and_duplicate_attempt_fail(lab):
    path, value = plan(lab)
    atomic_write_json(path, {**value, "question": "changed"})
    with pytest.raises(ValueError, match="changed"):
        execution.registered_plans(lab)
    atomic_write_json(path, value)
    plan(lab, index=2, attempt=1)
    with pytest.raises(ValueError, match="reset/duplicated"):
        execution.registered_plans(lab)


def test_real_maintenance_blocks_new_diagnostic_and_series_without_mutation(tmp_path):
    from nextai_autoresearch.gates import GateViolation
    from test_lab_restart import _lab_fixture
    _lab_fixture(tmp_path)
    root = tmp_path
    (root / "research/plan_registry.jsonl").write_text("")
    before = sha256_file(root / "research/plan_registry.jsonl")
    with pytest.raises(GateViolation, match="blocked"):
        execution.create_plan(root, candidate="fixture_model", phase="dev", question="must be blocked")
    with pytest.raises(GateViolation, match="blocked"):
        execution.freeze_series(root, "EXP-20990101-0001")
    assert sha256_file(root / "research/plan_registry.jsonl") == before


def test_cli_diagnostic_does_not_require_fictitious_hypothesis():
    from nextai_autoresearch.cli import build_parser
    args = build_parser().parse_args(["plan", "new", "--pc01-phase", "dev", "--candidates", "fixture_model", "--question", "fixture"])
    assert args.pc01_phase == "dev" and args.hypothesis is None


def test_real_worker_denies_unregistered_or_maintenance_runtime_before_torch(lab):
    path, value = plan(lab)
    runtime = lab / "research/tmp" / path.stem / "pc01-runtime.json"
    atomic_write_json(runtime, {"plan": value, "seed": 1103, "audit": {}})
    with pytest.raises(Exception, match="blocked"):
        worker.validate_runtime(runtime, lab)


def final_series_fixture(lab, monkeypatch):
    install_process(monkeypatch)
    path, _ = plan(lab)
    execution.run_diagnostic(path, lab)
    frozen = execution.freeze_series(lab, path.stem)
    return sha256_json(load_json(frozen))


def test_complete_authenticated_series_uses_three_distinct_runner_seeds(lab, monkeypatch):
    series_digest = final_series_fixture(lab, monkeypatch)
    draws = iter([0, 0, 1, 1, 2])  # Deliberate collisions must be retried before launch.
    monkeypatch.setattr(execution.secrets, "randbelow", lambda *args: next(draws))
    for index in (1, 2, 3):
        path, _ = plan(lab, "final", index=index+1, attempt=index, series=series_digest)
        execution.run_diagnostic(path, lab)
    decision = execution.authenticated_series_decision(lab)
    assert decision["decision"] == "positive_control_pass"
    assert decision["runner_authenticity_checked"]
    assert not decision["architecture_promoted"] and not decision["scientific_result_created"]
    assert [r["seed"] for r in execution.attempt_history(lab) if r["phase"] == "final"] == [10000, 10001, 10002]


@pytest.mark.parametrize("tamper", ["source", "evaluator", "development", "series", "omission"])
def test_final_series_rejects_changed_or_missing_evidence(lab, monkeypatch, tamper):
    digest = final_series_fixture(lab, monkeypatch)
    if tamper == "source":
        monkeypatch.setattr(execution, "audit_bundle", lambda *a: {"files": {}, "sha256": "b"*64})
    elif tamper == "evaluator":
        atomic_write_json(lab / "research/eval_manifest.json", {"evaluator_sha256": "b"*64})
    elif tamper == "development":
        plan(lab, index=2, attempt=2)
    elif tamper == "series":
        value = load_json(lab / execution.SERIES)
        value["replicates"] = 2
        atomic_write_json(lab / execution.SERIES, value)
    if tamper == "omission":
        with pytest.raises(ValueError, match="three registered"):
            execution.authenticated_series_decision(lab)
    else:
        with pytest.raises(ValueError):
            execution.verify_series(lab)


def test_failed_final_cannot_be_omitted_or_rescue_tuned(lab, monkeypatch):
    digest = final_series_fixture(lab, monkeypatch)
    install_process(monkeypatch, "crash")
    path, _ = plan(lab, "final", index=2, attempt=1, series=digest)
    execution.run_diagnostic(path, lab)
    with pytest.raises(ValueError, match="three registered"):
        execution.authenticated_series_decision(lab)
    path, _ = plan(lab, "dev", index=3, attempt=2)
    with pytest.raises(ValueError, match="no dev runs"):
        execution.run_diagnostic(path, lab)


def test_attempt_receipt_tampering_is_detected(lab, monkeypatch):
    install_process(monkeypatch)
    path, _ = plan(lab)
    result_path = execution.run_diagnostic(path, lab)
    value = load_json(result_path)
    value["execution"]["fit_seconds_charged"] = 0
    atomic_write_json(result_path, value)
    with pytest.raises(ValueError, match="result missing/changed"):
        execution.attempt_history(lab)


def test_stop_is_enforced_by_parent_during_fixture(tmp_path):
    (tmp_path / "STOP").touch()
    result = execution.supervise([sys.executable, str(FIXTURE), "--work", str(tmp_path / "work"), "--mode", "fit_hang"],
        tmp_path, tmp_path / "work", limits=execution.Limits(worker_seconds=2, disk_reserve_bytes=0))
    assert result["termination_reason"] == "stop_gate"


def layout_fixture():
    """Meta tensors validate shape/recipe only: no forward, optimizer, data or storage."""
    import torch
    from torch import nn
    with torch.device("meta"):
        model = nn.Module()
        blocks = []
        for _ in range(6):
            block = nn.Module()
            block.ln_1 = nn.LayerNorm(384, bias=False)
            block.ln_2 = nn.LayerNorm(384, bias=False)
            block.attn = nn.Module()
            block.attn.n_head = 6
            block.attn.c_attn = nn.Linear(384, 1152, bias=False)
            block.attn.c_proj = nn.Linear(384, 384, bias=False)
            block.attn.attn_dropout = nn.Dropout(0.2)
            block.attn.resid_dropout = nn.Dropout(0.2)
            block.mlp = nn.ModuleDict({"c_fc": nn.Linear(384, 1536, bias=False), "c_proj": nn.Linear(1536, 384, bias=False),
                                       "gelu": nn.GELU(), "dropout": nn.Dropout(0.2)})
            blocks.append(block)
        model.transformer = nn.ModuleDict({"wte": nn.Embedding(256, 384), "wpe": nn.Embedding(256, 384),
            "drop": nn.Dropout(0.2), "h": nn.ModuleList(blocks), "ln_f": nn.LayerNorm(384, bias=False)})
        model.lm_head = nn.Linear(384, 256, bias=False)
        model.lm_head.weight = model.transformer.wte.weight
    return model


def test_model_layout_is_checked_without_instantiating_storage_or_training():
    model = layout_fixture()
    worker.verify_model_layout(model, pc01.contract()["model"])
    assert all(p.is_meta for p in model.parameters())


@pytest.mark.parametrize("fault", ["dropout", "heads", "untied", "norm", "gelu", "frozen"])
def test_wrong_model_recipe_is_rejected_without_training(fault):
    import torch
    from torch import nn
    model = layout_fixture()
    if fault == "dropout":
        model.transformer.drop.p = 0.1
    elif fault == "heads":
        model.transformer.h[0].attn.n_head = 8
    elif fault == "untied":
        model.lm_head.weight = nn.Parameter(torch.empty((256, 384), device="meta"))
    elif fault == "norm":
        model.transformer.ln_f.eps = 1e-3
    elif fault == "gelu":
        model.transformer.h[0].mlp.gelu.approximate = "tanh"
    elif fault == "frozen":
        model.transformer.wte.weight.requires_grad_(False)
    with pytest.raises(ValueError):
        worker.verify_model_layout(model, pc01.contract()["model"])


def test_extension_cannot_reset_original_cap_or_repeat(tmp_path):
    from nextai_autoresearch.laboratory import _authorized_extension
    relative = "research/laboratory/PC-01-EXTENSION-20260905-V1.json"
    (tmp_path / relative).parent.mkdir(parents=True)
    shutil.copy2(project_root() / relative, tmp_path / relative)
    progress = {"service_cycles_used": 2, "next_action_id": "PC-01-DECISION"}
    event = {"event": "laboratory_maintenance_started", "action_id": "PC-01-INTEGRATION",
             "authorization_sha256": sha256_file(tmp_path / relative)}
    with pytest.raises(ValueError, match="missing/repeated"):
        _authorized_extension(tmp_path, progress)
    append_jsonl(tmp_path / "research/events.jsonl", event)
    result = _authorized_extension(tmp_path, progress)
    assert result["service_cycles_used"] == 2 and result["extension_cycles_cap"] == 1
    with pytest.raises(ValueError, match="original budget"):
        _authorized_extension(tmp_path, {**progress, "service_cycles_used": 0})
    append_jsonl(tmp_path / "research/events.jsonl", event)
    with pytest.raises(ValueError, match="missing/repeated"):
        _authorized_extension(tmp_path, progress)


@pytest.mark.parametrize("fault", [None, "missing_source", "changed_source", "failed_test", "missing_test", "unregistered"])
def test_execution_certificate_requires_hashes_and_actual_report_structure(lab, fault):
    import xml.etree.ElementTree as ET
    files = {}
    for relative in execution.CERTIFICATE_FILES:
        destination = lab / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project_root() / relative, destination)
        files[relative] = sha256_file(destination)
    xml = ET.Element("testsuites")
    suite = ET.SubElement(xml, "testsuite", tests=str(len(execution.CERTIFICATE_TESTS)), failures="0", errors="0", skipped="0")
    for name in execution.CERTIFICATE_TESTS:
        if fault == "missing_test" and name == execution.CERTIFICATE_TESTS[0]:
            continue
        ET.SubElement(suite, "testcase", name=name)
    if fault == "failed_test":
        suite.set("failures", "1")
    report = lab / "research/laboratory/synthetic-conformance.xml"
    ET.ElementTree(xml).write(report, encoding="utf-8")
    value = {"kind": "pc01_execution_conformance", "all_required_checks_passed": True,
             "contract_sha256": pc01.CONTRACT_SHA256, "evaluator_sha256": "a"*64, "files": files,
             "test_report": report.relative_to(lab).as_posix(), "test_report_sha256": sha256_file(report)}
    if fault == "missing_source":
        value["files"].pop(execution.CERTIFICATE_FILES[0])
    atomic_write_json(lab / execution.CERTIFICATE, value)
    if fault != "unregistered":
        append_jsonl(lab / "research/events.jsonl", {"event": "pc01_execution_certificate_created",
                                                   "certificate_path": execution.CERTIFICATE, "evaluator_sha256": "a"*64,
                                                   "certificate_sha256": sha256_file(lab / execution.CERTIFICATE)})
    if fault == "changed_source":
        (lab / execution.CERTIFICATE_FILES[0]).write_text("# changed fixture bytes")
    if fault is None:
        assert REAL_VERIFY_CERTIFICATE(lab)["all_required_checks_passed"]
    else:
        with pytest.raises(ValueError):
            REAL_VERIFY_CERTIFICATE(lab)
