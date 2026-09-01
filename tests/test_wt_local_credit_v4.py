import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v3 as v3
from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v4 as v4
from nextai_autoresearch.cli import _wt_prequential_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


ROLES = list(v4.ROLE_INTERVENTIONS)


def _protocol() -> dict:
    return _wt_prequential_protocol(load_config(project_root()))


def _prospective_plan() -> dict:
    root = project_root()
    plan = load_json(root / "research/plans/EXP-20260901-0024.json")
    plan["experiment_id"] = "EXP-20990101-9995"
    plan["parent_experiment_id"] = None
    plan["hypothesis_id"] = "HYP-9995"
    plan["benchmark"] = v4.BENCHMARK_VERSION
    plan["candidates"] = [*ROLES, *v4.BASELINES]
    plan["wt_prequential_protocol"] = _protocol()
    return plan


def test_v4_reuses_v3_data_evaluator_controls_and_baseline_numerics() -> None:
    assert v4.verify_static_contract is v3.verify_static_contract
    assert v4.development_smoke is v3.development_smoke
    assert v4.BASELINES == v3.BASELINES
    plan = _prospective_plan()
    runtime = copy.deepcopy(plan)
    runtime["matrix"] = {
        "knowledge_sizes": [18], "reasoning_depths": [16],
        "queries_per_cell": 18, "seeds": [117031],
        "seed_policy": plan["matrix"]["seed_policy"],
    }
    old = v3.run_suite("wt_persistence_v1", runtime)
    new = v4.run_suite("wt_persistence_v1", runtime)
    stable = lambda rows: [
        {key: value for key, value in row.items()
         if "latency" not in key and not key.endswith("_seconds")
         and key not in {"fit_peak_bytes", "peak_state_bytes"}}
        for row in rows
    ]
    assert stable(new) == stable(old)


def test_v4_freezes_four_prospective_roles_without_candidate_code() -> None:
    protocol = _protocol()
    v4.verify_role_contract(protocol)
    assert protocol["causal_roles"] == ROLES
    assert protocol["role_implementation"] == v4.ROLE_IMPLEMENTATION
    assert set(v4.ROLE_INTERVENTIONS.values()) == {
        "aligned_error_gated", "frozen_zero_trace",
        "shuffled_temporal_credit", "aligned_dense_credit",
    }
    candidate_dir = project_root() / "src/nextai_autoresearch/candidates"
    assert all(not (candidate_dir / f"{role}.py").exists() for role in ROLES)


def test_v4_prospective_plan_is_schema_valid_and_cohort_separated() -> None:
    plan = _prospective_plan()
    validate_document("experiment_plan", plan, project_root())
    historical = load_json(project_root() / "research/plans/EXP-20260901-0024.json")
    assert historical["benchmark"] == v3.BENCHMARK_VERSION
    for role in ROLES:
        broken = copy.deepcopy(plan)
        broken["candidates"].remove(role)
        with pytest.raises(ValidationError):
            validate_document("experiment_plan", broken, project_root())


def test_v4_role_contract_rejects_mislabeled_or_split_implementation() -> None:
    protocol = _protocol()
    wrong = copy.deepcopy(protocol)
    wrong["causal_roles"][2] = "wt_lms_v1"
    with pytest.raises(RuntimeError, match="role/intervention"):
        v4.verify_role_contract(wrong)
    wrong = copy.deepcopy(protocol)
    wrong["role_implementation"] = "four_unrelated_models"
    with pytest.raises(RuntimeError, match="one implementation"):
        v4.verify_role_contract(wrong)
