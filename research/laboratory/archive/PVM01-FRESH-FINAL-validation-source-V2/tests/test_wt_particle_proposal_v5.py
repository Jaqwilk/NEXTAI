import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v4 as v4
from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v5 as v5
from nextai_autoresearch.cli import _wt_prequential_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


ROLES = list(v5.ROLE_INTERVENTIONS)


def _protocol() -> dict:
    active = load_config(project_root())
    raw = copy.deepcopy(active.raw)
    raw["project"]["benchmark_version"] = v5.BENCHMARK_VERSION
    return _wt_prequential_protocol(ResearchConfig(raw, active.path))


def _plan() -> dict:
    plan = load_json(project_root() / "research/plans/EXP-20260901-0048.json")
    plan.update({"experiment_id": "EXP-20990101-9994", "parent_experiment_id": None,
                 "hypothesis_id": "HYP-9994", "benchmark": v5.BENCHMARK_VERSION,
                 "candidates": [*ROLES, *v5.BASELINES]})
    plan["wt_prequential_protocol"] = _protocol()
    return plan


def test_v5_is_role_only_and_preserves_v4_evaluator_boundary() -> None:
    assert v5.verify_static_contract is v4.verify_static_contract
    assert v5.development_smoke is v4.development_smoke
    assert v5.BASELINES == v4.BASELINES
    assert v5.TRAIN_SEEDS == v4.TRAIN_SEEDS
    assert v5.KNOWLEDGE_SIZES == v4.KNOWLEDGE_SIZES
    assert v5.HORIZONS == v4.HORIZONS


def test_v5_freezes_source_identical_future_role_lifecycle() -> None:
    protocol = _protocol()
    v5.verify_role_contract(protocol)
    assert protocol["causal_roles"] == ROLES
    assert protocol["role_implementation"] == v5.ROLE_IMPLEMENTATION
    assert set(v5.ROLE_INTERVENTIONS.values()) == {
        "learned_proposal", "bootstrap_proposal", "deterministic_posterior_mean",
    }
    candidate_dir = project_root() / "src/nextai_autoresearch/candidates"
    wrappers = [candidate_dir / f"{role}.py" for role in ROLES]
    present = [path.is_file() for path in wrappers]
    assert not any(present) or all(present)
    if all(present):
        shared_import = "from .wt_particle_proposal_predictive_state_core_v1 import Candidate"
        assert all(shared_import in path.read_text(encoding="utf-8") for path in wrappers)


def test_v5_plan_schema_is_cohort_separated_and_complete() -> None:
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    historical = load_json(project_root() / "research/plans/EXP-20260901-0048.json")
    assert historical["benchmark"] == v4.BENCHMARK_VERSION
    for role in ROLES:
        broken = copy.deepcopy(plan)
        broken["candidates"].remove(role)
        with pytest.raises(ValidationError):
            validate_document("experiment_plan", broken, project_root())


def test_v5_role_gate_rejects_mislabeled_or_split_implementation() -> None:
    protocol = _protocol()
    wrong = copy.deepcopy(protocol)
    wrong["causal_roles"][1] = "wt_rls_v1"
    with pytest.raises(RuntimeError, match="role/intervention"):
        v5.verify_role_contract(wrong)
    wrong = copy.deepcopy(protocol)
    wrong["role_implementation"] = "three_unrelated_models"
    with pytest.raises(RuntimeError, match="one implementation"):
        v5.verify_role_contract(wrong)
