"""Final activation authorization only; no training or corpus access."""
import copy
import shutil

import pytest

from nextai_autoresearch import pc01_execution as execution, pc01_final_authority as final, laboratory, gates
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import project_root, load_json, sha256_file


@pytest.fixture
def policy():
    return {**load_json(project_root() / final.PATH), "finals": [], "completed": 0,
            "terminal": False, "failed": False, "series_frozen": False}


def test_final_scope_is_exact_and_single_use(policy):
    root = project_root()
    assert final.scope(root, policy, series_freeze=True) == []
    for kwargs in ({}, {"candidate": policy["candidate"], "phase": "dev"},
                   {"candidate": "other", "phase": "final"}, {"experiment_id": "EXP-20260905-0002"},
                   {"candidate": policy["candidate"], "phase": "final"}):
        assert final.scope(root, policy, **kwargs)
    policy["series_frozen"] = True
    assert final.scope(root, policy, series_freeze=True)
    assert final.scope(root, policy, candidate=policy["candidate"], phase="final") == []
    policy["finals"] = [{"experiment_id": f"final-{i}"} for i in (1, 2, 3)]
    assert final.scope(root, policy, candidate=policy["candidate"], phase="final")
    assert final.scope(root, policy, experiment_id="final-3") == []
    policy["terminal"] = True
    assert final.scope(root, policy, experiment_id="final-3")
    assert final.scope(root, policy, series_freeze=True)


@pytest.fixture
def authority_files(tmp_path, monkeypatch):
    root = project_root()
    policy = load_json(root / final.PATH)
    plans = execution.registered_plans(root)
    history = execution.attempt_history(root)
    # Preserve the historical dev fixture even after real final replicas exist.
    plans = [p for p in plans if p["phase"] == "dev"]
    history = [a for a in history if a["phase"] == "dev"]
    for relative in (final.PATH, policy["preparation_receipt"]):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, path)
    append_jsonl(tmp_path / "research/events.jsonl", dict(event="pc01_final_authorized",
                 authorization_path=final.PATH, authorization_sha256=final.SHA256))
    monkeypatch.setattr(laboratory, "final_preparation_status", lambda root: {"complete": True})
    from nextai_autoresearch import pc01_final_transition
    monkeypatch.setattr(pc01_final_transition, "selected_transition", lambda *args: {})
    monkeypatch.setattr(execution, "registered_plans", lambda root: plans)
    monkeypatch.setattr(execution, "attempt_history", lambda root: history)
    return tmp_path, plans, history


@pytest.mark.parametrize("fault", ["none", "missing", "changed", "event", "receipt", "dev_added", "dev_omitted", "charge", "not_complete"])
def test_final_authority_hashes_and_history_fail_closed(authority_files, monkeypatch, fault):
    root, plans, history = authority_files
    if fault == "none":
        assert final.authority(root)["completed"] == 0
        return
    if fault == "missing":
        (root / final.PATH).unlink()
    elif fault == "changed":
        path = root / final.PATH
        path.write_text(path.read_text()+" ")
    elif fault == "event":
        append_jsonl(root / "research/events.jsonl", {"event": "pc01_final_authorized"})
    elif fault == "receipt":
        path = root / load_json(root / final.PATH)["preparation_receipt"]
        path.write_text(path.read_text()+" ")
    elif fault == "dev_added":
        plans.append({**plans[-1], "experiment_id": "third-dev"})
    elif fault == "dev_omitted":
        plans.pop(0)
    elif fault == "charge":
        history[0]["fit_seconds_charged"] = 0
    else:
        monkeypatch.setattr(laboratory, "final_preparation_status", lambda root: {"complete": False})
    with pytest.raises((ValueError, OSError)):
        final.authority(root)


def test_real_final_authority_keeps_dev_and_replay_closed():
    root = project_root()
    before = sha256_file(root / "research/plan_registry.jsonl")
    assert final.authority(root)["id"] == "PC-01-FINAL-ACTIVATION-20260905-V1"
    with pytest.raises(gates.GateViolation):
        execution.create_plan(root, candidate="pc01_byte_gpt_v1", phase="dev", question="denial only")
    with pytest.raises(gates.GateViolation):
        gates.ensure_can_run_plan("EXP-20260905-0002", root)
    assert laboratory.pc01_scope_problems(root, candidate="other", phase="final")
    assert sha256_file(root / "research/plan_registry.jsonl") == before


@pytest.mark.parametrize("fault", ["STOP", "PAUSE", "maintenance", "integrity"])
def test_final_activation_does_not_bypass_normal_gates(tmp_path, monkeypatch, policy, fault):
    root = project_root()
    config = tmp_path / "config/research.toml"
    config.parent.mkdir()
    config.write_text((root / "config/research.toml").read_text().replace('benchmark_status = "maintenance"', 'benchmark_status = "active"'))
    benchmark = tmp_path / "src/nextai_autoresearch/benchmarks" / f"{policy['cohort']}.py"
    benchmark.parent.mkdir(parents=True)
    benchmark.write_text("")
    policy["series_frozen"] = True
    monkeypatch.setattr(final, "authority", lambda root: policy)
    monkeypatch.setattr(gates, "lifecycle_problems", lambda root: [])
    monkeypatch.setattr(gates, "laboratory_problems", lambda root, **kwargs: [])
    monkeypatch.setattr(gates, "verify_manifest", lambda root: {"ok": fault != "integrity", "problems": ["changed"]})
    if fault in ("STOP", "PAUSE"):
        (tmp_path / fault).touch()
    elif fault == "maintenance":
        config.write_text(config.read_text().replace('benchmark_status = "active"', 'benchmark_status = "maintenance"'))
    with pytest.raises(gates.GateViolation):
        gates.ensure_can_create_plan(tmp_path, pc01_candidate=policy["candidate"], pc01_phase="final")
