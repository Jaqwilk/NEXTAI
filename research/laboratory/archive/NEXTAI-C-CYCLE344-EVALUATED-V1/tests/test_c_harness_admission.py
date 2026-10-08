"""Engineering-only regression of historical lifecycle memory and C routing."""
import gc
from pathlib import Path
from types import SimpleNamespace
import weakref

from nextai_autoresearch import gates, laboratory, research_program
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, sha256_json


def _history(tmp_path, monkeypatch):
    codex = {"reflection_every_completed_experiments": 1000,
             "literature_review_every_completed_experiments": 1000}
    monkeypatch.setattr(gates, "load_config", lambda _: SimpleNamespace(raw={"codex": codex}))
    monkeypatch.setattr(gates, "report_provenance_problems", lambda _: [])
    for index in range(1, 6):
        identity = f"EXP-20200101-{index:04d}"
        plan = {"experiment_id": identity}
        atomic_write_json(tmp_path / f"research/plans/{identity}.json", plan)
        append_jsonl(tmp_path / "research/plan_registry.jsonl",
                     {"experiment_id": identity, "plan_sha256": sha256_json(plan)})
        atomic_write_json(tmp_path / f"research/results/{identity}.json",
                          {"experiment_id": identity, "plan_sha256": sha256_json(plan),
                           "completed_at": "2020-01-01T00:00:00Z", "large_trial_payload": "x" * 65536})
        analysis = tmp_path / f"research/analyses/{identity}.md"
        analysis.parent.mkdir(parents=True, exist_ok=True)
        analysis.write_text("Synthetic fixture only", encoding="utf-8")
    atomic_write_json(tmp_path / "research/state.json",
                      {"completed_experiments": 5, "last_experiment_id": "EXP-20200101-0001",
                       "active_experiment_id": None, "last_reflection_completed_experiments": 5,
                       "last_literature_review_completed_experiments": 5})


def test_lifecycle_releases_each_historical_result_and_preserves_timestamp_tie(tmp_path, monkeypatch):
    _history(tmp_path, monkeypatch)
    original = gates.load_json
    retained = []
    class Payload(dict):
        pass
    def watched(path):
        value = original(path)
        if Path(path).parent.name == "results":
            gc.collect()
            assert sum(ref() is not None for ref in retained) <= 1, "Historical trial payloads accumulate"
            value = Payload(value)
            retained.append(weakref.ref(value))
        return value
    monkeypatch.setattr(gates, "load_json", watched)
    assert gates.lifecycle_problems(tmp_path) == []
    gc.collect()
    assert not any(ref() is not None for ref in retained)


def test_lifecycle_metadata_still_rejects_count_and_newest_state_errors(tmp_path, monkeypatch):
    _history(tmp_path, monkeypatch)
    atomic_write_json(tmp_path / "research/state.json",
                      {"completed_experiments": 4, "last_experiment_id": "EXP-20200101-0005",
                       "active_experiment_id": None, "last_reflection_completed_experiments": 4,
                       "last_literature_review_completed_experiments": 4})
    problems = gates.lifecycle_problems(tmp_path)
    assert "state completed_experiments differs from immutable result count" in problems
    assert "state last_experiment_id differs from newest result" in problems


def test_active_c_scope_never_enters_historical_pc01_ladder(tmp_path, monkeypatch):
    calls = []
    owner = SimpleNamespace(scope_problems=lambda base, identity, **kwargs: calls.append((base, identity, kwargs)) or [])
    monkeypatch.setattr(research_program, "_c_owner", lambda _: owner)
    assert laboratory.pc01_scope_problems(tmp_path, prospective=True) == []
    assert calls == [(tmp_path, None, {"prospective": True})]
    assert laboratory.pc01_scope_problems(tmp_path, candidate="historical") == [
        "C does not reopen historical PC-01 or final-series operations"]


def test_c_wallet_dispatch_never_falls_back_to_b(tmp_path, monkeypatch):
    owner = SimpleNamespace(status=lambda _: {"id": "fixture-C", "credit": 43200})
    monkeypatch.setattr(research_program, "_c_owner", lambda _: owner)
    monkeypatch.setattr(research_program, "legacy_status", lambda _: (_ for _ in ()).throw(AssertionError("B fallback")))
    assert research_program.status(tmp_path) == {"id": "fixture-C", "credit": 43200}
