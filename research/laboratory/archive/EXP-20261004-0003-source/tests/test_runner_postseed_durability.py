from __future__ import annotations

import json
from pathlib import Path

import pytest

from nextai_autoresearch import runner
from nextai_autoresearch.audit import AuditResult
from nextai_autoresearch.config import load_config
from nextai_autoresearch.gates import plan_status
from nextai_autoresearch.ledger import ensure_layout
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_json


class _Lock:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def __enter__(self) -> "_Lock":
        return self

    def __exit__(self, *args: object) -> None:
        pass


def test_postseed_validation_failure_preserves_seed_and_invalidates_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_layout(tmp_path)
    experiment_id = "EXP-20260830-9996"
    plan = {
        "experiment_id": experiment_id,
        "hypothesis_id": "HYP-9999",
            "benchmark": load_config(project_root()).benchmark_version,
        "evaluator_sha256": "a" * 64,
        "budget": "quick",
        "candidates": ["probe_complete", "probe_timeout", "probe_crash", "probe_budget", "probe_missing"],
        "matrix": {"seed_policy": {"method": "runner_random_v1"}},
    }
    plan_path = tmp_path / "research" / "plans" / f"{experiment_id}.json"
    atomic_write_json(plan_path, plan)
    atomic_write_json(tmp_path / "research" / "eval_manifest.json", {
        "evaluator_sha256": "a" * 64,
    })
    atomic_write_json(tmp_path / "research" / "state.json", {
        "active_experiment_id": None, "cycle_number": 1,
        "completed_experiments": 0,
    })

    config = load_config(project_root())
    monkeypatch.setattr(runner, "load_config", lambda root: config)
    monkeypatch.setattr(runner, "ensure_can_run_plan", lambda *args: None)
    monkeypatch.setattr(runner, "registered_plan_hash", lambda *args: sha256_json(plan))
    monkeypatch.setattr(runner, "verify_required_baselines", lambda *args, **kwargs: None)
    monkeypatch.setattr(runner, "verify_preflight_certificate", lambda *args: {})
    monkeypatch.setattr(runner, "RunLock", _Lock)
    monkeypatch.setattr(runner, "verify_manifest", lambda root: {
        "ok": True, "benchmark_version": plan["benchmark"],
        "protocol_version": 2, "evaluator_sha256": "a" * 64,
        "candidate_bundle_sha256": "b" * 64, "problems": [],
        "checked_files": 1,
    })
    monkeypatch.setattr(runner, "audit_candidate", lambda *args: AuditResult(
        True, "probe", Path("probe.py"), "c" * 64, (), ()
    ))
    monkeypatch.setattr(runner, "_realize_evaluation_matrix", lambda plan: (
        {"knowledge_sizes": [8], "reasoning_depths": [1],
         "queries_per_cell": 1, "seeds": [1_234_567]},
        {"method": "runner_random_v1", "count": 1},
    ))

    def fake_candidate(candidate: str, *args: object) -> dict:
        failures = {
            "probe_timeout": ("timeout", "timeout"),
            "probe_crash": ("crash", "worker_crash"),
            "probe_budget": ("memory_limit", "memory_limit"),
        }
        if candidate in failures:
            status, reason = failures[candidate]
            return {
                "candidate": candidate, "status": status, "audit": {},
                "execution": {"termination_reason": reason}, "trials": [],
                "summary": {"status": "failed", "completed_trials": 0, "total_trials": 0},
            }
        output = tmp_path / "research" / "tmp" / experiment_id / f"{candidate}.json"
        atomic_write_json(output, {"candidate": candidate, "status": "complete"})
        return {
            "candidate": candidate, "status": "complete", "audit": {},
            "execution": {}, "trials": [], "summary": {
                "status": "complete", "completed_trials": 1, "total_trials": 1,
                **({} if candidate == "probe_missing" else {
                    "accuracy": 0.5, "minimum_combination_accuracy": 0.5,
                }),
            },
        }

    monkeypatch.setattr(runner, "_run_candidate", fake_candidate)
    monkeypatch.setattr(runner, "_frontier", lambda *args: ([], {
        "maximize": [], "minimize": [],
    }))
    monkeypatch.setattr(runner, "environment_fingerprint", lambda root: {})

    def fail_result_schema(name: str, document: dict, root: Path) -> None:
        if name == "experiment_result":
            raise ValueError("forced final result validation failure")

    monkeypatch.setattr(runner, "validate_document", fail_result_schema)

    with pytest.raises(ValueError, match="forced final"):
        runner.run_experiment(plan_path, tmp_path)

    events = [json.loads(line) for line in (
        tmp_path / "research" / "events.jsonl"
    ).read_text(encoding="utf-8").splitlines()]
    assert [event["event"] for event in events] == [
        "experiment_scoring_started", "experiment_runner_postseed_failure",
    ]
    assert events[0]["scoring_seeds"] == [1_234_567]
    assert events[1]["worker_artifacts"][0]["path"].endswith("probe_complete.json")
    assert len(events[1]["supervisor_artifacts"]) == 5
    supervisor = load_json(
        tmp_path / "research" / "tmp" / experiment_id / "probe_timeout.supervisor.json"
    )
    assert supervisor["status"] == "timeout"
    assert supervisor["execution"]["termination_reason"] == "timeout"
    assert {
        load_json(path)["status"]
        for path in (tmp_path / "research" / "tmp" / experiment_id).glob("*.supervisor.json")
    } == {"complete", "timeout", "crash", "memory_limit"}
    runtime = load_json(
        tmp_path / "research" / "tmp" / experiment_id / "runtime-plan.json"
    )
    assert runtime["matrix"]["seeds"] == [1_234_567]
    assert not (tmp_path / "research" / "results" / f"{experiment_id}.json").exists()
    assert load_json(tmp_path / "research" / "state.json")["active_experiment_id"] is None
    assert plan_status(experiment_id, tmp_path) == "invalidated"
