from __future__ import annotations

from pathlib import Path
import json
import shutil

import pytest

from nextai_autoresearch.gates import (
    GateViolation,
    _continuous_transfer_promotion_problems,
    _review_gate_problems,
    enforce_hypothesis_transition,
    lifecycle_problems,
    pending_plan_ids,
    stop_gate_problems,
)
from nextai_autoresearch.ledger import append_plan_status, ensure_layout
from nextai_autoresearch.scientific_validity import invalid_experiment_ids
from nextai_autoresearch.config import load_config
from nextai_autoresearch.baseline_semantics import verify_required_baselines
from nextai_autoresearch.runner import _realize_evaluation_matrix
from nextai_autoresearch.utils import project_root


def test_pause_and_stop_are_hard_gate_inputs(tmp_path: Path) -> None:
    (tmp_path / "PAUSE").write_text("maintenance\n", encoding="utf-8")
    (tmp_path / "STOP").write_text("stop\n", encoding="utf-8")
    assert stop_gate_problems(tmp_path) == [
        "STOP gate is present",
        "PAUSE gate is present",
    ]


def test_plan_invalidation_is_append_only_and_removes_pending_state(
    tmp_path: Path,
) -> None:
    ensure_layout(tmp_path)
    plan_path = tmp_path / "research" / "plans" / "EXP-20260830-9999.json"
    plan_path.write_text("{}\n", encoding="utf-8")
    assert pending_plan_ids(tmp_path) == ["EXP-20260830-9999"]
    append_plan_status(
        "EXP-20260830-9999", "invalidated", "invalid test plan", tmp_path
    )
    assert plan_path.is_file()
    assert pending_plan_ids(tmp_path) == []


def test_runner_realizes_blind_scoring_seeds_without_mutating_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DeterministicRandom:
        def sample(self, population: range, count: int) -> list[int]:
            return [population.start + index for index in range(count)]

    monkeypatch.setattr(
        "nextai_autoresearch.runner.secrets.SystemRandom",
        lambda: DeterministicRandom(),
    )
    plan = {
        "matrix": {
            "knowledge_sizes": [8, 32],
            "reasoning_depths": [1, 4, 6],
            "queries_per_cell": 8,
            "seed_policy": {
                "method": "runner_random_v1",
                "count": 3,
                "minimum": 100,
                "maximum": 200,
            },
        }
    }
    matrix, policy = _realize_evaluation_matrix(plan)
    assert matrix["seeds"] == [100, 101, 102]
    assert policy == plan["matrix"]["seed_policy"]
    assert "seeds" not in plan["matrix"]


def test_promising_transition_cannot_bypass_candidate_gate() -> None:
    previous = {
        "hypothesis_id": "HYP-9999",
        "evidence_experiment_ids": [],
        "prior_art": [{"title": "x", "url": "https://example.com", "relationship": "x"}],
    }
    with pytest.raises(GateViolation, match="requires --candidate"):
        enforce_hypothesis_transition(
            previous, "promising", [], None, project_root()
        )


def test_scientifically_invalid_result_cannot_falsify(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    shutil.copy2(
        project_root() / "config" / "research.toml",
        tmp_path / "config" / "research.toml",
    )
    ensure_layout(tmp_path)
    experiment_id = "EXP-20260830-9997"
    (tmp_path / "research" / "results" / f"{experiment_id}.json").write_text(
        "{}\n", encoding="utf-8"
    )
    (tmp_path / "research" / "analyses" / f"{experiment_id}.md").write_text(
        "# OBSERVATION\n", encoding="utf-8"
    )
    event = {
        "event": "experiment_scientific_validity_correction",
        "experiment_id": experiment_id,
        "scientific_validity": "invalid",
        "reason": "missing mandatory control",
    }
    (tmp_path / "research" / "events.jsonl").write_text(
        json.dumps(event) + "\n", encoding="utf-8"
    )
    assert invalid_experiment_ids(tmp_path) == {experiment_id}
    with pytest.raises(GateViolation, match="scientifically invalid evidence"):
        enforce_hypothesis_transition(
            {"hypothesis_id": "HYP-9999"},
            "falsified",
            [experiment_id],
            None,
            tmp_path,
        )
    with pytest.raises(GateViolation, match="scientifically invalid evidence"):
        enforce_hypothesis_transition(
            {"hypothesis_id": "HYP-9999"},
            "testing",
            [experiment_id],
            None,
            tmp_path,
        )


def test_semantic_gate_rejects_changed_baseline_before_seed(tmp_path: Path) -> None:
    root = project_root()
    (tmp_path / "config").mkdir()
    shutil.copy2(root / "config" / "baseline_semantics.json", tmp_path / "config")
    registry = json.loads((tmp_path / "config" / "baseline_semantics.json").read_text())
    record = registry["baselines"]["left_to_right_ppm_masked_byte"]
    for relative in record["implementation_files"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
    for test in record["conformance_tests"]:
        target = tmp_path / test["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / test["path"], target)
    implementation = next(iter(record["implementation_files"]))
    (tmp_path / implementation).write_text("# intentionally false baseline\n")
    plan = {
        "candidates": ["left_to_right_ppm_masked_byte"],
        "masked_refinement_protocol": {
            "classical_baselines": ["left_to_right_ppm_masked_byte"]
        },
    }
    with pytest.raises(RuntimeError, match="implementation hash mismatch"):
        verify_required_baselines(plan, tmp_path, run_tests=False)


def test_review_cadence_is_machine_enforced() -> None:
    config = load_config(project_root())
    problems = _review_gate_problems(
        {
            "completed_experiments": 12,
            "last_reflection_completed_experiments": 0,
            "last_literature_review_completed_experiments": 6,
        },
        config,
    )
    assert any("reflection is due" in problem for problem in problems)
    assert any("literature review is due" in problem for problem in problems)


def test_promising_requires_replicated_implementable_frontier(
    tmp_path: Path,
) -> None:
    (tmp_path / "config").mkdir()
    shutil.copy2(project_root() / "config" / "research.toml", tmp_path / "config" / "research.toml")
    result_dir = tmp_path / "research" / "results"
    analysis_dir = tmp_path / "research" / "analyses"
    result_dir.mkdir(parents=True)
    analysis_dir.mkdir(parents=True)
    experiment_id = "EXP-20260830-9998"
    source = {
        "url": "https://example.com/primary",
        "primary_source": True,
    }
    (tmp_path / "research" / "sources.jsonl").write_text(
        json.dumps(source) + "\n", encoding="utf-8"
    )
    trials = [
        {"status": "complete", "seed": seed, "accuracy": 1.0}
        for seed in (101, 202, 303)
    ]
    result = {
        "experiment_id": experiment_id,
        "hypothesis_id": "HYP-9999",
        "budget": "screen",
        "benchmark": "screen_a",
        "integrity_before": {"ok": True},
        "integrity_after": {"ok": True},
        "pareto_front_implementable": ["learned_candidate"],
        "candidates": [
            {
                "candidate": "learned_candidate",
                "status": "complete",
                "trials": trials,
            }
        ],
    }
    (result_dir / f"{experiment_id}.json").write_text(
        json.dumps(result), encoding="utf-8"
    )
    (analysis_dir / f"{experiment_id}.md").write_text(
        "OBSERVATION\n", encoding="utf-8"
    )
    previous = {
        "hypothesis_id": "HYP-9999",
        "evidence_experiment_ids": [],
        "prior_art": [
            {
                "title": "Primary",
                "url": source["url"],
                "relationship": "direct",
            }
        ],
    }
    enforce_hypothesis_transition(
        previous,
        "promising",
        [experiment_id],
        "learned_candidate",
        tmp_path,
    )
    result["pareto_front_implementable"] = []
    (result_dir / f"{experiment_id}.json").write_text(
        json.dumps(result), encoding="utf-8"
    )
    with pytest.raises(GateViolation, match="not on the implementable Pareto front"):
        enforce_hypothesis_transition(
            previous,
            "promising",
            [experiment_id],
            "learned_candidate",
            tmp_path,
        )


def test_mandatory_control_timeout_blocks_promotion(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    shutil.copy2(project_root() / "config" / "research.toml", tmp_path / "config" / "research.toml")
    ensure_layout(tmp_path)
    experiment_id = "EXP-20260830-9995"
    plan_path = tmp_path / "research" / "plans" / f"{experiment_id}.json"
    plan_path.write_text(json.dumps({
        "dronepropa_protocol": {"classical_baselines": ["mandatory_control"]}
    }), encoding="utf-8")
    source = {"url": "https://example.com/primary", "primary_source": True}
    (tmp_path / "research" / "sources.jsonl").write_text(json.dumps(source) + "\n", encoding="utf-8")
    result = {
        "experiment_id": experiment_id,
        "hypothesis_id": "HYP-9999",
        "budget": "screen",
        "benchmark": "screen_a",
        "plan_path": f"research/plans/{experiment_id}.json",
        "integrity_before": {"ok": True},
        "integrity_after": {"ok": True},
        "pareto_front_implementable": ["learned_candidate"],
        "candidates": [
            {"candidate": "learned_candidate", "status": "complete", "trials": [
                {"status": "complete", "seed": seed, "accuracy": 1.0}
                for seed in (101, 202, 303)
            ]},
            {"candidate": "mandatory_control", "status": "timeout", "trials": []},
        ],
    }
    (tmp_path / "research" / "results" / f"{experiment_id}.json").write_text(json.dumps(result), encoding="utf-8")
    (tmp_path / "research" / "analyses" / f"{experiment_id}.md").write_text("OBSERVATION\n", encoding="utf-8")
    previous = {
        "hypothesis_id": "HYP-9999", "evidence_experiment_ids": [],
        "prior_art": [{"title": "Primary", "url": source["url"], "relationship": "direct"}],
    }
    with pytest.raises(GateViolation, match="mandatory control did not complete"):
        enforce_hypothesis_transition(previous, "promising", [experiment_id], "learned_candidate", tmp_path)


def test_three_family_v2_causal_gains_are_hard_promotion_gates() -> None:
    plan = {"continuous_transfer_protocol": {
        "shared_candidate": "shared",
        "cross_family_only_ablation": "cross",
        "causal_promotion_gates": [
            "shared_vs_independent_gain", "cross_family_transfer_gain",
        ],
    }}
    result = {
        "benchmark": "heldout_three_family_continuous_transfer_v2",
        "candidates": [
            {"candidate": "shared", "status": "complete",
             "summary": {"shared_vs_independent_gain": .1}},
            {"candidate": "cross", "status": "complete",
             "summary": {"cross_family_transfer_gain": .2}},
        ],
    }
    assert _continuous_transfer_promotion_problems(result, plan, "shared") == []
    result["candidates"][1]["summary"]["cross_family_transfer_gain"] = 0.0
    assert _continuous_transfer_promotion_problems(result, plan, "shared") == [
        "causal promotion gate cross_family_transfer_gain must be positive in every family"
    ]


def test_checked_in_research_lifecycle_is_consistent() -> None:
    assert lifecycle_problems(project_root()) == []
