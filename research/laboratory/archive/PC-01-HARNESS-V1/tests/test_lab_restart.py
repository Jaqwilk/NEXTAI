from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from nextai_autoresearch import cli, report
from nextai_autoresearch.gates import GateViolation, ensure_can_create_plan, ensure_can_run_plan
from nextai_autoresearch.laboratory import CONTRACT_PATH, laboratory_problems
from nextai_autoresearch.provenance import resolve_audited_source
from nextai_autoresearch.utils import load_json, project_root, sha256_bytes, sha256_file


@pytest.fixture
def report_fixture(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    shutil.copy2(project_root() / "config/research.toml", tmp_path / "config/research.toml")
    for directory in ("results", "plans"):
        (tmp_path / "research" / directory).mkdir(parents=True)
    result = tmp_path / "research/results/EXP-20990101-0001.json"
    result.write_text(json.dumps({"plan_path": "research/plans/EXP-20990101-0001.json", "value": 1}))
    (tmp_path / "research/plans/EXP-20990101-0001.json").write_text('{"value":1}')
    monkeypatch.setattr(report, "collect_rows", lambda root: [])
    report.write_report(tmp_path)
    return tmp_path


def test_report_freshness_is_content_not_mtime(report_fixture):
    root = report_fixture
    result = root / "research/results/EXP-20990101-0001.json"
    os.utime(result, (2_000_000_000, 2_000_000_000))
    os.utime(root / "research/REPORT.md", (1, 1))
    assert report.report_provenance_problems(root) == []
    # JSON whitespace/checkout line endings do not change input semantics.
    result.write_text(json.dumps(load_json(result), indent=4) + "\n", newline="\r\n")
    assert report.report_provenance_problems(root) == []


@pytest.mark.parametrize("relative", [
    "research/results/EXP-20990101-0001.json",
    "research/plans/EXP-20990101-0001.json",
])
def test_report_detects_changed_inputs_even_with_old_timestamps(report_fixture, relative):
    path = report_fixture / relative
    value = load_json(path)
    value["value"] = 2
    path.write_text(json.dumps(value))
    os.utime(path, (1, 1))
    assert any("content inputs" in p for p in report.report_provenance_problems(report_fixture))


def test_report_detects_config_corrections_and_rendered_tampering(report_fixture):
    root = report_fixture
    events = root / "research/events.jsonl"
    events.write_text('{"event":"service_note"}\n')
    assert report.report_provenance_problems(root) == []
    events.write_text('{"event":"experiment_scientific_validity_correction","experiment_id":"EXP-test","scientific_validity":"invalid"}\n')
    assert any("content inputs" in p for p in report.report_provenance_problems(root))
    report.write_report(root)
    config = root / "config/research.toml"
    config.write_text(config.read_text().replace('generation = 2', 'generation = 3'))
    assert any("content inputs" in p for p in report.report_provenance_problems(root))
    report.write_report(root)
    (root / "research/REPORT.md").write_text("tampered")
    assert any("content differs" in p for p in report.report_provenance_problems(root))


def test_missing_or_corrupt_report_receipt_fails_closed(report_fixture):
    receipt = report_fixture / "research/REPORT.provenance.json"
    receipt.write_text("not JSON")
    assert report.report_provenance_problems(report_fixture)
    receipt.unlink()
    assert report.report_provenance_problems(report_fixture)


def _lab_fixture(tmp_path):
    root = project_root()
    for relative in ("config/research.toml", "schemas/laboratory_restart.schema.json", CONTRACT_PATH):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
    for relative in load_json(root / CONTRACT_PATH)["required_documents"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)


def test_preparation_passes_but_scoring_and_status_flip_are_blocked(tmp_path):
    _lab_fixture(tmp_path)
    assert laboratory_problems(tmp_path) == []
    assert any("not authorized" in p for p in laboratory_problems(tmp_path, scoring=True))
    config = tmp_path / "config/research.toml"
    config.write_text(config.read_text().replace('benchmark_status = "maintenance"', 'benchmark_status = "active"'))
    assert any("requires benchmark_status" in p for p in laboratory_problems(tmp_path))
    contract = load_json(tmp_path / CONTRACT_PATH)
    contract["scoring_authorized"] = True
    (tmp_path / CONTRACT_PATH).write_text(json.dumps(contract))
    assert laboratory_problems(tmp_path)


def test_missing_restart_contract_is_a_blocker(tmp_path):
    _lab_fixture(tmp_path)
    (tmp_path / CONTRACT_PATH).unlink()
    assert laboratory_problems(tmp_path)


def test_actual_plan_and_run_gates_block_without_mutation():
    root = project_root()
    before = sha256_file(root / "research/plan_registry.jsonl")
    with pytest.raises(GateViolation, match="laboratory scoring is not authorized"):
        ensure_can_create_plan(root)
    with pytest.raises(GateViolation, match="laboratory scoring is not authorized"):
        ensure_can_run_plan("EXP-20990101-9999", root)
    assert sha256_file(root / "research/plan_registry.jsonl") == before


def test_lab_status_reports_preparation_not_scoring(monkeypatch, capsys):
    from nextai_autoresearch.doctor import DoctorReport
    monkeypatch.setattr(cli, "run_doctor", lambda: DoctorReport())
    monkeypatch.setattr(cli, "laboratory_progress", lambda: {
        "next_action_id": "PC-01-HARNESS", "next_action": "Verified fixture progress",
        "user_decision_required": False,
    })
    assert cli.main(["lab", "status"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["preparation_ready"] is True
    assert status["scoring_ready"] is False
    assert status["next_action_id"] == "PC-01-HARNESS"


def test_resolver_never_substitutes_current_source_for_old_hash(tmp_path):
    if not shutil.which("git"):
        pytest.skip("Git is needed for the historical blob fixture")
    relative = "src/nextai_autoresearch/candidates/example.py"
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    original = b"# old source\n"
    target.write_bytes(original)
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path).decode().strip()
    git("init", "-q")
    git("config", "core.autocrlf", "false")
    git("add", "--", relative)
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "source")
    revision = git("rev-parse", "HEAD")
    target.write_bytes(b"# different source at same path\n")
    found = resolve_audited_source(relative, sha256_bytes(original), tmp_path)
    assert found["resolved"] and found["revision"] == revision
    assert found["source"] == "git_blob"
    assert found["current_sha256"] != found["expected_sha256"]
    assert not resolve_audited_source(relative, "0" * 64, tmp_path)["resolved"]
    crlf = resolve_audited_source(relative, sha256_bytes(original.replace(b"\n", b"\r\n")), tmp_path)
    assert crlf["source"] == "git_blob_with_crlf_checkout"


@pytest.mark.parametrize("path", ["../escape.py", "/tmp/test.py", "C:/test.py", "src/nextai_autoresearch/../escape.py"])
def test_resolver_rejects_nonrepository_paths(tmp_path, path):
    with pytest.raises(ValueError):
        resolve_audited_source(path, "a" * 64, tmp_path)


def test_historical_wt_hash_and_protocol_are_preserved():
    root = project_root()
    result = load_json(root / "research/results/EXP-20260831-0007.json")
    audit = next(c for c in result["candidates"] if c["candidate"] == "wt_candidate_under_test")["audit"]
    assert audit["sha256"] == "4471f2a999f9432e9d2e6fb56d309ebe7af52cca6dff246ab1b439b38f035104"
    assert audit["sha256"] in (root / "research/LAB_PLAN.md").read_text(encoding="utf-8")
    assert sha256_file(root / "docs/archive/SCIENTIFIC_PROTOCOL_V2_2026-09-04.md") == "8e03fdd87da5b58dfbb3165c1225f862b255f2c11678c6128c0c137b6d5e15cd"


def test_bootstrap_rejects_unbounded_download_and_counts_cache():
    spec = importlib.util.spec_from_file_location("bootstrap", project_root() / "scripts/bootstrap_environment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lock = {"package": [{"name": "fixture", "wheels": [{"size": 100}, {"size": 200}]}]}
    assert module.footprint_estimate(lock) == 1200 + 2 * module.GIB
    with pytest.raises(ValueError, match="Cannot bound"):
        module.footprint_estimate({"package": [{"name": "unknown"}]})
    with pytest.raises(ValueError, match="Empty lock"):
        module.footprint_estimate({"package": []})


@pytest.mark.parametrize("blocker", ["space", "uv_missing", "none"])
def test_bootstrap_checks_space_before_mutation_and_runs_doctor(tmp_path, monkeypatch, blocker):
    from types import SimpleNamespace
    spec = importlib.util.spec_from_file_location("bootstrap", project_root() / "scripts/bootstrap_environment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "__file__", str(tmp_path / "scripts/bootstrap_environment.py"))
    (tmp_path / "uv.lock").write_text('[[package]]\nname="fixture"\nwheels=[{size=100}]\n')
    (tmp_path / "config").mkdir()
    (tmp_path / "config/bootstrap_sizes.json").write_text('{"sizes": {}}')
    checks, commands = [], []
    def disk(path):
        checks.append(path)
        return SimpleNamespace(free=module.RESERVE if blocker == "space" else 100 * module.GIB)
    monkeypatch.setattr(module.shutil, "disk_usage", disk)
    monkeypatch.setattr(module.shutil, "which", lambda name: None if blocker == "uv_missing" else "uv")
    monkeypatch.setattr(module.subprocess, "run", lambda command, **kwargs: commands.append((command, kwargs)))
    if blocker != "none":
        with pytest.raises(RuntimeError):
            module.main()
        assert len(checks) == 1
        assert commands == []
    else:
        assert module.main() == 0
        assert len(checks) == 2
        assert commands[0][0] == ["uv", "sync", "--frozen", "--extra", "dev"]
        assert commands[1][0][-2:] == ["nextai", "doctor"]
        for key in ("UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "UV_PROJECT_ENVIRONMENT"):
            assert Path(commands[0][1]["env"][key]).is_relative_to(tmp_path)


def test_actual_locked_bootstrap_footprint_is_bounded_without_network():
    import tomllib
    root = project_root()
    spec = importlib.util.spec_from_file_location("bootstrap", root / "scripts/bootstrap_environment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    sizes = load_json(root / "config/bootstrap_sizes.json")["sizes"]
    assert 2 * module.GIB < module.footprint_estimate(lock, sizes) < 64 * module.GIB
    # A new artifact hash or URL cannot silently reuse old size metadata.
    with pytest.raises(ValueError):
        module.footprint_estimate({"package": [{"name": "changed", "wheels": [{"url": "https://other.invalid", "hash": next(iter(sizes))}]}]}, sizes)
