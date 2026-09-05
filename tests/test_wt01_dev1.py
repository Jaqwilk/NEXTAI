from __future__ import annotations

import copy

import pytest

from nextai_autoresearch import wt01_dev1
from nextai_autoresearch.benchmarks import wt01_causal_factorial_diagnostic_v1 as diagnostic
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root, sha256_file


def _plan(*, runtime: bool = False):
    matrix = {
        "knowledge_sizes": [18, 36, 54],
        "reasoning_depths": [16, 32, 96],
        "queries_per_cell": 18,
    }
    if runtime:
        matrix["seeds"] = [1_234_567]
    else:
        matrix["seed_policy"] = {
            "method": "runner_random_v1", "count": 1,
            "minimum": 1_000_000, "maximum": 2_147_483_647,
        }
    return {
        "schema_version": 1,
        "experiment_id": "EXP-20990101-0001",
        "parent_experiment_id": None,
        "created_at": "2099-01-01T00:00:00Z",
        "status": "planned",
        "hypothesis_id": "HYP-0028",
        "title": "Frozen WT-01 recurrence attribution on visible development",
        "research_question": "Does recurrence have the preregistered descriptive causal effect on both visible development files?",
        "architecture_family": "source_identical_affine_factorial_diagnostic",
        "candidates": list(wt01_dev1.CANDIDATES),
        "benchmark": wt01_dev1.BENCHMARK,
        "evaluator_sha256": "a" * 64,
        "budget": "quick",
        "matrix": matrix,
        "primary_metrics": list(wt01_dev1.PRIMARY_METRICS),
        "metric_directions": {
            name: "maximize" if name == "stable_rollout_rate" else "minimize"
            for name in wt01_dev1.PRIMARY_METRICS
        },
        "predicted_outcome": "Recurrence will reduce normalized RMSE by the frozen effect threshold on aggregate and remain positive on each file.",
        "falsification_criteria": ["Reject descriptive support if the frozen aggregate or either per-file recurrence contrast fails."],
        "promotion_criteria": ["This one-seed visible-development diagnostic cannot promote an architecture or establish replication."],
        "alternative_explanations": ["The complete affine VAR(2)/ARX identity may explain the historical result without architectural novelty."],
        "confounds": ["Two visible physical files permit only descriptive uncertainty and no independent replication claim."],
        "outcome_policy": {
            "positive": "Preserve only descriptive mechanism evidence and stop for review without opening files 8-9.",
            "null": "Preserve the null result, do not tune or retry, and stop for review.",
            "negative": "Preserve the negative result, do not tune or retry, and stop for review.",
        },
        "git_before": {"commit": "a" * 40, "branch": "master", "dirty": False},
        "wt01_factorial_protocol": wt01_dev1.expected_protocol(),
    }


def test_hash_bound_authority_is_present_and_parent_receipt_unchanged():
    value = wt01_dev1.authority(project_root())
    assert value is not None
    assert value["development_attempts_authorized"] == 1
    assert value["execution"]["evaluation_files"] == [6, 7]
    assert value["execution"]["forbidden_files"] == [8, 9]


def test_exact_plan_contract_and_schema_reject_scope_drift():
    plan = _plan()
    wt01_dev1.validate_plan(plan)
    validate_document("experiment_plan", plan, project_root())

    changed = copy.deepcopy(plan)
    changed["matrix"]["seed_policy"]["count"] = 2
    with pytest.raises(ValueError, match="one-seed"):
        wt01_dev1.validate_plan(changed)

    changed = copy.deepcopy(plan)
    changed["candidates"].pop()
    with pytest.raises(ValueError, match="nine frozen roles"):
        wt01_dev1.validate_plan(changed)


def test_evaluator_routes_every_cell_only_to_visible_development(monkeypatch):
    calls = []

    def fake(candidate, knowledge, horizon, seed, evaluation, state_limit, data_role):
        calls.append((candidate, knowledge, horizon, seed, evaluation, state_limit, data_role))
        return []

    monkeypatch.setattr(diagnostic, "_run_trial", fake)
    diagnostic.run_suite(wt01_dev1.CANDIDATES[0], _plan(runtime=True))
    assert len(calls) == 9
    assert {call[4] for call in calls} == {(6, 7)}
    assert {call[6] for call in calls} == {"visible_development"}


def test_evaluator_rejects_files_8_9_and_static_check_never_hashes_them(monkeypatch):
    plan = _plan(runtime=True)
    plan["wt01_factorial_protocol"]["evaluation_files"] = [8, 9]
    with pytest.raises(ValueError, match="protocol changed"):
        diagnostic.run_suite(wt01_dev1.CANDIDATES[0], plan)

    seen = []

    def recording_hash(path):
        seen.append(path)
        return sha256_file(path)

    monkeypatch.setattr(diagnostic, "sha256_file", recording_hash)
    static = diagnostic.verify_static_contract(project_root())
    assert static["forbidden_files_opened"] is False
    assert not any(path.name in {"load_in_seed_8.csv", "load_in_seed_9.csv"} for path in seen)
