"""Versioned lifecycle and exact second-dev scope; synthetic workers only."""
import shutil

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch import laboratory, pc01, pc01_execution as execution
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.schemas import validate_document, load_schema
from nextai_autoresearch.utils import load_json, project_root, sha256_file
from test_pc01_execution import lab, plan, install_process


@pytest.fixture
def scope(tmp_path, monkeypatch):
    root = project_root()
    authority = load_json(root / laboratory.DEV2_PATH)
    original = load_json(root / "research/plans/EXP-20260905-0001.json")
    plans = [original]
    (tmp_path / "config").mkdir()
    shutil.copy2(root / "config/research.toml", tmp_path / "config/research.toml")
    monkeypatch.setattr(laboratory, "dev2_authority", lambda base: authority)
    monkeypatch.setattr(execution, "registered_plans", lambda base: plans)
    return tmp_path, plans, authority


def second_plan(original):
    return {**original, "experiment_id": "EXP-20990101-0002", "attempt": 2,
            "benchmark": pc01.TELEMETRY_COHORT}


def test_second_dev_is_single_use_and_cannot_reset_history(scope):
    root, plans, authority = scope
    kwargs = {"candidate": authority["candidate"], "phase": "dev"}
    assert laboratory.pc01_scope_problems(root, **kwargs) == []
    for candidate, phase in ((None, None), (authority["candidate"], "final"), ("other", "dev")):
        assert laboratory.pc01_scope_problems(root, candidate=candidate, phase=phase)
    new = second_plan(plans[0])
    plans.append(new)
    assert laboratory.pc01_scope_problems(root, experiment_id=new["experiment_id"]) == []
    assert laboratory.pc01_scope_problems(root, experiment_id=plans[0]["experiment_id"])
    assert laboratory.pc01_scope_problems(root, **kwargs)
    append_jsonl(root / "research/plan_status_events.jsonl", {
        "experiment_id": new["experiment_id"], "status": "invalidated", "reason": "fixture"})
    assert laboratory.pc01_scope_problems(root, **kwargs)
    plans.append({**new, "experiment_id": "EXP-20990101-0003", "attempt": 3})
    assert laboratory.pc01_scope_problems(root, **kwargs)
    plans[:] = [new]
    assert laboratory.pc01_scope_problems(root, experiment_id=new["experiment_id"])


@pytest.mark.parametrize("key,value", [("attempt", 1), ("candidate", "other"), ("phase", "final"),
    ("benchmark", pc01.COHORT), ("development_seed", 1104), ("series_sha256", "f"*64), ("recipe_sha256", "f"*64)])
def test_second_dev_rejects_scope_drift(scope, key, value):
    root, plans, _ = scope
    new = second_plan(plans[0])
    new[key] = value
    plans.append(new)
    assert laboratory.pc01_scope_problems(root, experiment_id=new["experiment_id"])


@pytest.fixture
def authority_files(tmp_path, monkeypatch):
    root = project_root()
    authority = load_json(root / laboratory.DEV2_PATH)
    files = [laboratory.DEV2_PATH, authority["design_path"],
             "src/nextai_autoresearch/candidates/pc01_byte_gpt_v1.py", *authority["historical_anchors"]]
    for relative in files:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
    append_jsonl(tmp_path / "research/events.jsonl", {"event": "pc01_dev2_authorized",
                 "authorization_path": laboratory.DEV2_PATH, "authorization_sha256": laboratory.DEV2_SHA256})
    monkeypatch.setattr(laboratory, "activation_authority", lambda base: {"historical": True})
    monkeypatch.setattr(laboratory, "telemetry_repair_status", lambda base: {"complete": True})
    return tmp_path


def test_second_authority_hashes_historical_anchors_and_unchanged_model(authority_files):
    assert laboratory.dev2_authority(authority_files)["global_attempt"] == 2
    candidate = authority_files / "src/nextai_autoresearch/candidates/pc01_byte_gpt_v1.py"
    candidate.write_text(candidate.read_text()+"\n# changed\n")
    with pytest.raises(ValueError, match="unchanged candidate"):
        laboratory.dev2_authority(authority_files)


@pytest.mark.parametrize("fault", ["missing", "changed", "duplicate", "anchor", "incomplete_repair", "no_first_authority"])
def test_second_authority_fails_closed(authority_files, monkeypatch, fault):
    root = authority_files
    path = root / laboratory.DEV2_PATH
    if fault == "missing":
        path.unlink()
    elif fault == "changed":
        path.write_text(path.read_text()+" ")
    elif fault == "duplicate":
        append_jsonl(root / "research/events.jsonl", {"event": "pc01_dev2_authorized"})
    elif fault == "anchor":
        original = root / "research/results/EXP-20260905-0001.json"
        original.write_text(original.read_text().replace('"fit_seconds_charged": 1200', '"fit_seconds_charged": 0'))
    elif fault == "incomplete_repair":
        monkeypatch.setattr(laboratory, "telemetry_repair_status", lambda base: {"complete": False})
    else:
        monkeypatch.setattr(laboratory, "activation_authority", lambda base: None)
    with pytest.raises(ValueError):
        laboratory.dev2_authority(root)


def test_schema_dispatch_preserves_v1_and_rejects_unknown_version(lab):
    _, original = plan(lab)
    before = load_schema("pc01_plan", lab)
    for version in pc01.COHORTS:
        validate_document("experiment_plan", {**original, "benchmark": version}, lab)
    assert load_schema("pc01_plan", lab) == before
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", {**original, "benchmark": "pc01_byte_lm_learning_measurement_v3"}, lab)
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", {**original, "benchmark": pc01.TELEMETRY_COHORT, "budget": "unlimited"}, lab)


def test_v2_diagnostic_retains_identity_and_prior_fit_charge(lab, monkeypatch):
    # The synthetic supervisor reduces fit allowance to 1 s (production: 1200).
    # Its failed v1 fit consumes that full reservation; v2 cannot reset it.
    first, _ = plan(lab)
    install_process(monkeypatch, mode="crash")
    first_result = execution.run_diagnostic(first, lab)
    original_hash = sha256_file(first_result)
    assert execution.attempt_history(lab)[0]["fit_seconds_charged"] == 1
    config = lab / "config/research.toml"
    config.write_text(config.read_text().replace(pc01.COHORT, pc01.TELEMETRY_COHORT))
    second = execution.create_plan(lab, candidate="fixture_model", phase="dev", question="v2 synthetic")
    assert load_json(second)["attempt"] == 2
    install_process(monkeypatch)
    result = load_json(execution.run_diagnostic(second, lab))
    assert result["status"] == "complete"
    assert result["benchmark"] == pc01.TELEMETRY_COHORT
    assert result["candidates"] == [] and result["pareto_front"] == []
    history = execution.attempt_history(lab)
    assert len(history) == 2 and sum(row["fit_seconds_charged"] for row in history) >= 1
    assert sha256_file(first_result) == original_hash
