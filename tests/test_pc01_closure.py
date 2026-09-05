"""No-training tests for the terminal PC-01 lifecycle migration."""
import ast
from pathlib import Path
import types

import pytest

from nextai_autoresearch import laboratory, pc01_closure
from nextai_autoresearch.pc01_execution import authenticated_series_decision
from nextai_autoresearch.pc01_telemetry import read_device_sample
from nextai_autoresearch.utils import project_root, sha256_file


def test_real_git_backed_closure_preserves_terminal_decision():
    root = project_root()
    value = pc01_closure.closure(root)
    assert value["git_commit"] == "f08cd02fb1cc80ed169b63c1917eb1b979c0b238"
    assert value["terminal_decision"]["decision"] == "positive_control_pass"
    decision = authenticated_series_decision(root)
    for key, expected in value["terminal_decision"].items():
        assert decision[key] == expected


def test_closure_rejects_substituted_git_bytes(monkeypatch):
    root = project_root()
    actual = pc01_closure.git_bytes
    pc01_closure._verify_git_bundle.cache_clear()

    def substituted(base, commit, relative):
        value = actual(base, commit, relative)
        return value + b"substitution" if relative.endswith("pc01_telemetry.py") else value

    monkeypatch.setattr(pc01_closure, "git_bytes", substituted)
    with pytest.raises(ValueError, match="historical Git evidence changed"):
        pc01_closure.closure(root)


def test_closure_rejects_mutated_current_evidence(monkeypatch):
    root = project_root()
    actual = pc01_closure.sha256_file
    target = (root / "research/laboratory/PC-01-FINAL-SERIES-V1.json").resolve()

    def changed(path: Path):
        return "0" * 64 if path.resolve() == target else actual(path)

    monkeypatch.setattr(pc01_closure, "sha256_file", changed)
    with pytest.raises(ValueError, match="current immutable PC-01 evidence changed"):
        pc01_closure.closure(root)


def test_append_only_registry_accepts_complete_records(monkeypatch, tmp_path):
    historical = b'{"experiment_id":"EXP-1"}\n'
    relative = "research/plan_registry.jsonl"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(historical + b'{"experiment_id":"EXP-2"}\n')
    monkeypatch.setattr(pc01_closure, "git_bytes",
                        lambda _root, _commit, _relative: historical)
    assert pc01_closure._verify_append_only_jsonl(tmp_path, "a" * 40, relative) == 1


@pytest.mark.parametrize("changed", [
    b'{"experiment_id":"CHANGED"}\n',
    b'{"experiment_id":"EXP-1"',
    b'{"experiment_id":"EXP-0"}\n{"experiment_id":"EXP-1"}\n',
])
def test_append_only_registry_rejects_prefix_mutation_truncation_or_reorder(
    monkeypatch, tmp_path, changed
):
    historical = b'{"experiment_id":"EXP-1"}\n'
    relative = "research/plan_registry.jsonl"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(changed)
    monkeypatch.setattr(pc01_closure, "git_bytes",
                        lambda _root, _commit, _relative: historical)
    with pytest.raises(ValueError, match="historical prefix changed"):
        pc01_closure._verify_append_only_jsonl(tmp_path, "a" * 40, relative)


@pytest.mark.parametrize("appended", [b'{"experiment_id":"EXP-2"}', b'not-json\n', b'\n'])
def test_append_only_registry_rejects_partial_malformed_or_blank_records(
    monkeypatch, tmp_path, appended
):
    historical = b'{"experiment_id":"EXP-1"}\n'
    relative = "research/plan_registry.jsonl"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(historical + appended)
    monkeypatch.setattr(pc01_closure, "git_bytes",
                        lambda _root, _commit, _relative: historical)
    with pytest.raises(ValueError, match="incomplete|malformed"):
        pc01_closure._verify_append_only_jsonl(tmp_path, "a" * 40, relative)


def _function(source: str, name: str) -> str:
    node = next(item for item in ast.parse(source).body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name)
    return ast.dump(node, include_attributes=False)


def test_historical_v1_failure_is_preserved_while_live_v2_handles_absence(tmp_path):
    root = project_root()
    value = pc01_closure.closure(root)
    historical = pc01_closure.git_bytes(
        root, value["git_commit"], "src/nextai_autoresearch/pc01_telemetry.py"
    ).decode("utf-8")
    current = (root / "src/nextai_autoresearch/pc01_telemetry.py").read_text(encoding="utf-8")
    assert _function(historical, "write_device_sample") == _function(current, "write_device_sample")

    module = types.ModuleType("historical_pc01_telemetry_v1")
    exec(compile(historical.replace(
        "from .utils import atomic_write_json, load_json",
        "from nextai_autoresearch.utils import atomic_write_json, load_json",
    ), "historical_pc01_telemetry_v1.py", "exec"), module.__dict__)

    def missing(_path):
        raise FileNotFoundError("deterministic historical transient absence")

    module.load_json = missing
    with pytest.raises(FileNotFoundError, match="historical transient absence"):
        module.read_device_sample(tmp_path / "missing.json")
    assert read_device_sample(tmp_path / "missing.json") is None


def test_migrated_laboratory_identity_advances_only_through_verified_wt_contract():
    root = project_root()
    contract = laboratory.laboratory_contract(root)
    progress = laboratory.laboratory_progress(root)
    from nextai_autoresearch.wt01_dev1 import status as wt01_dev1_status
    dev1 = wt01_dev1_status(root)
    assert contract["status"] == ("preparation_only" if dev1["terminal"] else "dev_authorized")
    assert contract["scoring_authorized"] is (not dev1["terminal"])
    assert contract["lifecycle_migration_complete"] is True
    assert contract["wt01_contract_ready"] is True
    assert progress["wt01_contract"]["artifacts_ready"] is True
    if progress["wt01_contract"]["complete"]:
        if progress.get("wt01_dev1") is not None:
            review = progress.get("review01")
            expected = ("REVIEW-01-DECISION" if review and review["complete"] else "WT-01-DECISION") \
                if dev1["terminal"] else "WT-01-DEV-1"
            assert progress["next_action_id"] == expected
            assert progress["user_decision_required"] is dev1["terminal"]
            assert progress["scoring_authorized"] is (not dev1["terminal"])
            assert progress["wt01_dev1"]["registrations_cap"] == 1
        elif progress.get("wt01_harness") is not None:
            assert progress["next_action_id"] in {"WT-01-DATA-HARNESS", "WT-01-DEV-1"}
            assert progress["user_decision_required"] is progress["wt01_harness"]["complete"]
        else:
            assert progress["next_action_id"] == "WT-01-DATA-HARNESS"
            assert progress["user_decision_required"] is True
    else:
        assert progress["next_action_id"] == "WT-01-CONTRACT"
        assert progress["user_decision_required"] is False
    assert progress["final_access_authorized"] is False
    assert sha256_file(root / pc01_closure.PATH) == pc01_closure.SHA256
