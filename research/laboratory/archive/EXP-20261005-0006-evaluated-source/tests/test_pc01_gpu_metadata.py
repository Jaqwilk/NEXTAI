"""Metadata-only fixtures and bounded real probes; never model training."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from nextai_autoresearch import pc01, pc01_execution as execution, pc01_gpu_metadata as gpu
from nextai_autoresearch import pc01_worker as worker, laboratory
from nextai_autoresearch.runner import _sanitized_environment
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file
from nextai_autoresearch.ledger import append_jsonl
from test_pc01_execution import lab, plan, measurement, install_process
from test_lab_restart import _lab_fixture

CSV = "0, GPU-00000000-0000-0000-0000-000000000001, NVIDIA GeForce RTX 4070, 551.78, 210, 405, 25, 644\n"


def snapshot():
    return dict(schema_version=1, kind="pc01_gpu_metadata", status="complete", executable=str(Path(sys.executable).resolve()),
                arguments=list(gpu.ARGS), environment_policy="nvidia_child_only_registry_ProgramW6432", return_code=0,
                stdout=CSV, stderr="", gpu=gpu.parse_gpu(CSV), error=None,
                started_at="2026-09-05T00:00:00Z", completed_at="2026-09-05T00:00:00Z", elapsed_seconds=0.1)


def test_probe_environment_is_child_only(monkeypatch):
    monkeypatch.setattr(gpu, "_program_files_64", lambda: "C:/Program Files")
    before = dict(os.environ)
    child, policy = gpu.probe_environment()
    assert dict(os.environ) == before and child is not os.environ
    if os.name == "nt":
        assert child["ProgramW6432"] == "C:/Program Files"
        assert {k:v for k,v in child.items() if k.upper() != "PROGRAMW6432"} == {
            k:v for k,v in before.items() if k.upper() != "PROGRAMW6432"}
    assert "ProgramW6432" not in _sanitized_environment(project_root())


@pytest.mark.parametrize("text", ["", CSV+CSV, CSV.replace("551.78", "N/A"), CSV.replace("210", "0"),
    CSV.replace("405", "-1"), CSV.replace("25, 644", "101, 644"), CSV.replace("644", "nan"),
    CSV.replace("644", "inf"), CSV.replace("644", "-1"), CSV.replace("0, GPU", "1, GPU"),
    CSV.replace("GPU-00000000-0000-0000-0000-000000000001", "unknown"), CSV.rsplit(",",1)[0]])
def test_malformed_metadata_is_not_accepted(text):
    with pytest.raises(ValueError):
        gpu.parse_gpu(text)


@pytest.mark.parametrize("fault", ["missing", "nvml", "timeout", "malformed", "registry"])
def test_probe_failures_retain_explicit_evidence(monkeypatch, fault):
    monkeypatch.setattr(gpu.shutil, "which", lambda name: None if fault == "missing" else sys.executable)
    def environment():
        if fault == "registry":
            raise OSError("registry unavailable")
        return {}, "nvidia_child_only_registry_ProgramW6432"
    monkeypatch.setattr(gpu, "probe_environment", environment)
    def query(command, **kwargs):
        assert kwargs["timeout"] == 5 and kwargs["env"] == {}
        if fault == "timeout":
            raise subprocess.TimeoutExpired(command, 5, output=b"partial", stderr=b"delayed")
        return subprocess.CompletedProcess(command, 255 if fault == "nvml" else 0,
                                           "NVML failed" if fault == "nvml" else "malformed", "fixture error")
    monkeypatch.setattr(gpu.subprocess, "run", query)
    record = gpu.probe_gpu()
    assert record["status"] == "error" and record["error"]
    if fault == "timeout":
        assert record["stdout"] == "partial" and record["stderr"] == "delayed"
    with pytest.raises(ValueError):
        gpu.validate_snapshot(record)


@pytest.mark.parametrize("key,value", [("gpu", None), ("return_code", True), ("status", "error"),
    ("arguments", []), ("elapsed_seconds", float("nan")), ("elapsed_seconds", -1),
    ("completed_at", "2025-01-01T00:00:00Z"), ("started_at", "2026-09-05T00:00:00"),
    ("executable", "relative.exe"), ("stdout", CSV.replace("210", "220"))])
def test_snapshot_completeness_and_raw_binding(key, value):
    record = snapshot()
    gpu.validate_snapshot(record)
    record[key] = value
    with pytest.raises(ValueError):
        gpu.validate_snapshot(record)


def test_pair_requires_matching_identity_and_order():
    pair = {"before_fit": snapshot(), "after_timing": snapshot()}
    gpu.validate_pair(pair)
    for key, replacement in (("551.78", "552.00"), ("000000000001", "000000000002")):
        changed = copy.deepcopy(pair)
        changed["after_timing"]["stdout"] = CSV.replace(key,replacement)
        changed["after_timing"]["gpu"] = gpu.parse_gpu(changed["after_timing"]["stdout"])
        with pytest.raises(ValueError, match="identity/driver"):
            gpu.validate_pair(changed)
    with pytest.raises(ValueError):
        gpu.validate_pair({"before_fit": snapshot()})


def test_failed_prefit_probe_preserves_error_without_model_or_training(tmp_path, monkeypatch):
    work = tmp_path / "research/tmp/EXP-20990101-0001"
    work.mkdir(parents=True)
    runtime = {"plan": {"benchmark": pc01.METADATA_COHORT}, "seed": 1103}
    monkeypatch.setattr(worker, "validate_runtime", lambda *args: runtime)
    monkeypatch.setattr(gpu, "probe_gpu", lambda: {"status": "error", "error": "NVML fixture failure"})
    monkeypatch.setattr(worker.importlib, "import_module", lambda *args: pytest.fail("Candidate must not be imported"))
    with pytest.raises(ValueError, match="missing, failed or incomplete"):
        worker.run(work / "runtime.json", tmp_path)
    assert load_json(work / "gpu-before_fit.json")["error"] == "NVML fixture failure"
    assert not (work / "fit-request.json").exists()
    assert not (tmp_path / "research/pc01_payload").exists()


def test_stop_prevents_probe_and_error_file(tmp_path, monkeypatch):
    (tmp_path / "STOP").touch()
    monkeypatch.setattr(gpu, "probe_gpu", lambda: pytest.fail("STOP must precede probe"))
    with pytest.raises(ValueError, match="STOP"):
        gpu.capture_required(tmp_path, "before_fit", tmp_path)
    assert not (tmp_path / "gpu-before_fit.json").exists()


def test_v3_parent_rejects_missing_metadata_but_preserves_v2(lab):
    _, value = plan(lab)
    runtime = {"plan": value, "seed": 1103, "audit": {"sha256": "a"*64}}
    record = measurement(value)
    value["benchmark"] = pc01.TELEMETRY_COHORT
    execution.validate_measurement(record, runtime, lab)
    value["benchmark"] = pc01.METADATA_COHORT
    with pytest.raises(ValueError, match="gpu_metadata"):
        execution.validate_measurement(record, runtime, lab)
    pair = {"before_fit": snapshot(), "after_timing": snapshot()}
    record["gpu_metadata"] = pair
    work = lab / "research/tmp" / value["experiment_id"]
    for stage, data in pair.items():
        atomic_write_json(work / f"gpu-{stage}.json", data)
    execution.validate_measurement(record, runtime, lab)
    (work / "gpu-after_timing.json").unlink()
    with pytest.raises(ValueError, match="Missing GPU metadata"):
        execution.validate_measurement(record, runtime, lab)
    atomic_write_json(work / "gpu-after_timing.json", {"changed": True})
    with pytest.raises(ValueError, match="immutable worker artifact"):
        execution.validate_measurement(record, runtime, lab)


def test_v3_runner_preserves_failed_postfit_metadata(lab, monkeypatch):
    config = lab / "config/research.toml"
    config.write_text(config.read_text().replace(pc01.COHORT, pc01.METADATA_COHORT))
    path = execution.create_plan(lab, candidate="fixture_model", phase="dev", question="synthetic v3 invalid metadata")
    install_process(monkeypatch, mutate=lambda record: record.update(gpu_metadata={"before_fit": snapshot()}))
    result = load_json(execution.run_diagnostic(path, lab))
    assert result["status"] == "inconclusive" and result["measurement"] is None
    assert "Both GPU metadata snapshots" in result["error"]
    assert "measurement.json" in result["execution"]["worker_artifacts"]
    assert execution.attempt_history(lab)[0]["complete"]


def test_metadata_maintenance_cannot_grant_scoring(tmp_path):
    _lab_fixture(tmp_path)
    for relative in (laboratory.GPU_METADATA_PATH, "research/laboratory/PC-01-DEV-CYCLE-289-V1.receipt.json"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project_root() / relative, target)
    assert laboratory.laboratory_problems(tmp_path)
    append_jsonl(tmp_path / "research/events.jsonl", dict(event="laboratory_maintenance_started",
        action_id="PC-01-GPU-METADATA", plan_path=laboratory.GPU_METADATA_PATH,
        plan_sha256=laboratory.GPU_METADATA_SHA256))
    assert laboratory.laboratory_problems(tmp_path) == []
    assert laboratory.laboratory_problems(tmp_path, scoring=True)
    assert laboratory.pc01_scope_problems(tmp_path, candidate="pc01_byte_gpt_v1", phase="dev")
    config = tmp_path / "config/research.toml"
    config.write_text(config.read_text().replace('benchmark_status = "maintenance"','benchmark_status = "active"'))
    assert laboratory.laboratory_problems(tmp_path)


def test_real_sanitized_probe_pair_without_training(record_property):
    # One paired observation per test invocation; at most three authorized calls
    # in this maintenance cycle (targeted, full conformance, optional correction).
    code = """import json,os,subprocess,shutil
from nextai_autoresearch.pc01_gpu_metadata import probe_gpu,ARGS
before=dict(os.environ)
p=subprocess.run([shutil.which('nvidia-smi'),*ARGS],capture_output=True,text=True,timeout=5)
new=probe_gpu()
assert dict(os.environ)==before
print(json.dumps(dict(original=dict(return_code=p.returncode,stdout=p.stdout,stderr=p.stderr),repaired=new,environment_unchanged=True)))
"""
    process = subprocess.run([sys.executable, "-c", code], cwd=project_root(),
                             env=_sanitized_environment(project_root()), capture_output=True, text=True, timeout=20)
    assert process.returncode == 0, process.stderr
    pair = json.loads(process.stdout)
    record_property("paired_probe", json.dumps(pair, sort_keys=True))
    gpu.validate_snapshot(pair["repaired"])
    assert pair["environment_unchanged"]
    # Preserve the old probe's actual outcome; success is not required to fail
    # on every future machine. Only the repaired complete snapshot is mandatory.
