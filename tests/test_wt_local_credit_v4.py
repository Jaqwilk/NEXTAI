import copy

import numpy as np
import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v3 as v3
from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v4 as v4
from nextai_autoresearch.cli import _wt_prequential_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root
from nextai_autoresearch.wt_prequential_contract import WTEpisode, WTReveal, WTTraining
from nextai_autoresearch.candidates.wt_local_credit_trace_core import (
    ERROR_GATE, FEATURE_CLIP, FEATURES, MAX_HORIZON, TRACE_DECAY, UPDATE_ETA,
    WEIGHT_CLIP, WINDOW, WIDTH, LocalCreditTrace,
)
from nextai_autoresearch.candidates.wt_error_triggered_eligibility_trace_v1 import Candidate as Gated
from nextai_autoresearch.candidates.wt_source_identical_dense_eligibility_trace_v1 import Candidate as Dense
from nextai_autoresearch.candidates.wt_source_identical_frozen_eligibility_trace_v1 import Candidate as Frozen
from nextai_autoresearch.candidates.wt_source_identical_shuffled_eligibility_trace_v1 import Candidate as Shuffled


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


def test_v4_freezes_four_roles_with_one_source_identical_core() -> None:
    protocol = _protocol()
    v4.verify_role_contract(protocol)
    assert protocol["causal_roles"] == ROLES
    assert protocol["role_implementation"] == v4.ROLE_IMPLEMENTATION
    assert set(v4.ROLE_INTERVENTIONS.values()) == {
        "aligned_error_gated", "frozen_zero_trace",
        "shuffled_temporal_credit", "aligned_dense_credit",
    }
    assert all(issubclass(role, LocalCreditTrace) for role in (Gated, Frozen, Shuffled, Dense))
    assert [role.mode for role in (Gated, Frozen, Shuffled, Dense)] == list(
        v4.ROLE_INTERVENTIONS.values()
    )
    assert (WINDOW, WIDTH, FEATURES, MAX_HORIZON) == (32, 10, 5, 96)
    assert (TRACE_DECAY, ERROR_GATE, UPDATE_ETA, FEATURE_CLIP, WEIGHT_CLIP) == (
        0.75, 0.90, 0.05, 4.0, 2.0,
    )


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


def _training() -> WTTraining:
    history = np.zeros((WINDOW, WIDTH))
    target = np.zeros((WINDOW, WIDTH))
    episode = WTEpisode(tuple(map(tuple, history)), 0.0, tuple(map(tuple, target)))
    return WTTraining((episode,), 0, 0)


def _fit(candidate: LocalCreditTrace) -> LocalCreditTrace:
    candidate.fit(_training(), 1, 96)
    return candidate


def test_v4_trace_alignment_and_seed_fixed_shuffle_are_hand_checkable() -> None:
    aligned, shuffled = _fit(Gated(17)), _fit(Shuffled(17))
    assert np.allclose(np.sort(aligned._aligned_weights), np.sort(shuffled._shuffled_weights))
    assert not np.array_equal(aligned._aligned_weights, shuffled._shuffled_weights)
    history = np.zeros((WINDOW, WIDTH))
    history[-1, 0] = 1.0
    assert not np.allclose(aligned._trace(history, 0.0), shuffled._trace(history, 0.0))


def test_v4_gate_dense_frozen_and_slot_locality_match_preregistration() -> None:
    history = tuple(map(tuple, np.zeros((WINDOW, WIDTH))))
    small = tuple(map(tuple, np.full((16, WIDTH), 0.5)))
    large = tuple(map(tuple, np.full((16, WIDTH), 2.0)))
    gated, dense, frozen = _fit(Gated(3)), _fit(Dense(3)), _fit(Frozen(3))
    gated.update(WTReveal(10, history, 0.0, small))
    dense.update(WTReveal(10, history, 0.0, small))
    frozen.update(WTReveal(10, history, 0.0, large))
    assert 10 not in gated._slots and 10 not in frozen._slots
    assert np.any(dense._slots[10])
    gated.update(WTReveal(11, history, 0.0, large))
    assert np.any(gated._slots[11]) and 10 not in gated._slots
    assert gated.update_ops > 0 and gated.last_update_bytes > 0
