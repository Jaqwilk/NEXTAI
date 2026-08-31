from __future__ import annotations

import importlib
import copy

import numpy as np
import pytest

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.benchmarks.heldout_three_family_continuous_transfer_v1 import (
    FAMILIES, ROLE, _assignment, build_worlds,
)
from nextai_autoresearch.config import load_config
from nextai_autoresearch.three_family_tensor_contract import (
    Training, World, fit_normalizer, masked_mse, pad,
)
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.runner import _apply_continuous_transfer_comparisons
from nextai_autoresearch.utils import load_json, project_root


BASELINES = (
    "tensor_persistence_v1", "tensor_ridge_arx_v1", "tensor_rls_arx_v1",
    "tensor_empirical_gaussian_joint_v1", "tensor_contextual_gaussian_chow_liu_v1",
    "tensor_autoregressive_v1", "privileged_tensor_support_v1",
)


def _synthetic(rows: int = 108) -> World:
    x = np.linspace(-1, 1, rows, dtype=np.float32)
    support_input = np.column_stack((x, np.sin(x), np.cos(x)))
    support_target = np.column_stack((2 * x + 0.25, -x))
    history_x = np.linspace(-0.5, 0.1, 32, dtype=np.float32)
    history = np.column_stack((history_x, np.sin(history_x), 2 * history_x + 0.25))
    future_x = np.linspace(0.11, 0.6, 50, dtype=np.float32)[:, None]
    output = np.column_stack((2 * future_x[:, 0] + 0.25, -future_x[:, 0]))
    return World(1, pad(support_input, 108), pad(support_target, 108),
                 pad(history, 32), pad(future_x, 50), pad(output, 50))


def test_tensor_adapter_is_exact_masked_upper_left_and_finite() -> None:
    native = np.arange(18, dtype=np.float64).reshape(6, 3)
    tensor = pad(native, 6)
    assert tensor.values.shape == tensor.mask.shape == (6, 32)
    assert tensor.mask.sum() == 18
    assert np.array_equal(tensor.values[:, :3], native.astype(np.float32))
    assert not tensor.values[:, 3:].any()
    with pytest.raises(ValueError, match="finite"):
        pad(np.full((6, 1), np.nan), 6)


def test_training_only_normalization_preserves_masks_and_ignores_holdout() -> None:
    world = _synthetic()
    normalizer = fit_normalizer((world,))
    before = tuple(value.copy() for value in normalizer.means)
    changed = World(world.slot, world.support_input, world.support_target, world.history,
                    world.future_public, pad(np.full((50, 2), 1e9), 50))
    normalized = normalizer.apply(changed)
    assert all(np.array_equal(left, right) for left, right in zip(before, normalizer.means))
    assert np.array_equal(normalized.output.mask, changed.output.mask)
    assert not normalized.output.values[:, 2:].any()


def test_four_causal_assignments_are_exact_and_family_private() -> None:
    worlds = {family: [_synthetic()] for family in FAMILIES}
    assert len(_assignment("shared", FAMILIES[0], worlds)) == 3
    assert len(_assignment("independent", FAMILIES[0], worlds)) == 1
    assert len(_assignment("cross_family_only", FAMILIES[0], worlds)) == 2
    assert _assignment("support_only", FAMILIES[0], worlds) == ()


@pytest.mark.parametrize("name", BASELINES)
def test_tensor_baselines_are_auditable_and_complete_reference_contract(name: str) -> None:
    audit = audit_candidate(name, load_config())
    assert audit.ok, audit.problems
    candidate = importlib.import_module(f"nextai_autoresearch.candidates.{name}").Candidate(7)
    world = _synthetic()
    candidate.fit(Training((world,)))
    session = candidate.adapt(world.support_input, world.support_target)
    prediction = candidate.predict(session, world.history, world.future_public)
    assert prediction.shape == (50, 32)
    assert np.isfinite(prediction).all()
    assert np.isfinite(masked_mse(prediction, world.output))


def test_rls_matches_scalar_predict_gain_update_reference() -> None:
    module = importlib.import_module("nextai_autoresearch.candidates.tensor_rls_arx_v1")
    candidate = module.Candidate(1)
    world = _synthetic(108)
    candidate.fit(Training(()))
    session = candidate.adapt(world.support_input, world.support_target)
    design = np.column_stack((np.ones(108), world.support_input.values[:, :3]))
    values = world.support_target.values[:, 0]
    weight, precision = np.zeros(4), np.eye(4) * 1000.0
    for row, value in zip(design, values):
        gain = precision @ row / (1 + row @ precision @ row)
        weight += gain * (value - row @ weight)
        precision -= np.outer(gain, row @ precision)
    assert np.allclose(session["weights"][:, 0], weight)


@pytest.mark.parametrize("name", ["tensor_ridge_arx_v1", "tensor_autoregressive_v1"])
def test_ridge_and_recursive_arx_match_affine_reference(name: str) -> None:
    world = _synthetic()
    x = np.linspace(-1, 1, 108, dtype=np.float32)
    support_x = pad(x[:, None], 108)
    support_y = pad(np.column_stack((2 * x + .25, -x)), 108)
    candidate = importlib.import_module(f"nextai_autoresearch.candidates.{name}").Candidate(1)
    candidate.fit(Training(()))
    session = candidate.adapt(support_x, support_y)
    assert session["weights"][0, 0] == pytest.approx(.25, abs=2e-3)
    assert session["weights"][1, 0] == pytest.approx(2.0, abs=2e-3)
    prediction = candidate.predict(session, world.history, world.future_public)
    assert prediction[0, 0] != pytest.approx(prediction[-1, 0])


def test_empirical_joint_matches_gaussian_conditional_reference() -> None:
    world = _synthetic()
    x = np.linspace(-1, 1, 108, dtype=np.float32)
    support_x = pad(x[:, None], 108)
    support_y = pad(np.column_stack((2 * x + .25, -x)), 108)
    module = importlib.import_module("nextai_autoresearch.candidates.tensor_empirical_gaussian_joint_v1")
    candidate = module.Candidate(1)
    candidate.fit(Training(()))
    session = candidate.adapt(support_x, support_y)
    assert session["weights"][0, 0] == pytest.approx(.25, abs=2e-3)
    assert session["weights"][1, 0] == pytest.approx(2.0, abs=2e-3)


def test_persistence_repeats_last_mechanically_located_state() -> None:
    world = _synthetic()
    module = importlib.import_module("nextai_autoresearch.candidates.tensor_persistence_v1")
    candidate = module.Candidate(1)
    candidate.fit(Training(()))
    prediction = candidate.predict(
        candidate.adapt(world.support_input, world.support_target),
        world.history, world.future_public,
    )
    assert np.allclose(prediction[0, :2], world.history.values[-1, 1:3])


def test_gaussian_chow_liu_propagates_context_through_tree() -> None:
    rng = np.random.default_rng(17)
    x = rng.normal(size=108)
    y1 = x + rng.normal(scale=.2, size=108)
    y2 = y1 + rng.normal(scale=.2, size=108)
    world = _synthetic()
    support_x, support_y = pad(x[:, None], 108), pad(np.column_stack((y1, y2)), 108)
    module = importlib.import_module("nextai_autoresearch.candidates.tensor_contextual_gaussian_chow_liu_v1")
    candidate = module.Candidate(1)
    candidate.fit(Training(()))
    session = candidate.adapt(support_x, support_y)
    r_xy1 = np.corrcoef(x, y1)[0, 1]
    r_y1y2 = np.corrcoef(y1, y2)[0, 1]
    expected = y2.std() * r_xy1 * r_y1y2 / x.std()
    assert session["weights"][1, 1] == pytest.approx(expected, rel=.03)
    assert abs(session["weights"][1, 1]) > .5


def test_real_files_map_all_three_families_to_exact_contract() -> None:
    training, testing = build_worlds(4, 1, 1_500_001)
    assert set(training) == set(testing) == set(FAMILIES)
    expected_masks = {"ncmapss_ds08a": 700, "dronepropa": 300, "continuous_event": 50}
    for family in FAMILIES:
        assert len(training[family]) == 4 and len(testing[family]) == 1
        world = testing[family][0]
        assert world.support_input.values.shape == (108, 32)
        assert world.history.values.shape == (32, 32)
        assert world.future_public.values.shape == world.output.values.shape == (50, 32)
        assert int(world.output.mask.sum()) == expected_masks[family]


def test_frozen_role_names_do_not_alias_causal_controls() -> None:
    assert ROLE["independent_tensor_dynamics_v1"] == "independent"
    assert ROLE["cross_family_only_tensor_dynamics_v1"] == "cross_family_only"
    assert ROLE["support_only_tensor_dynamics_v1"] == "support_only"


def test_future_plan_schema_locks_causal_roles_costs_and_matrix() -> None:
    root = project_root()
    plan = copy.deepcopy(load_json(root / "research/plans/EXP-20260830-0057.json"))
    plan["benchmark"] = "heldout_three_family_continuous_transfer_v2"
    plan["matrix"]["knowledge_sizes"] = [4, 9]
    plan["matrix"]["reasoning_depths"] = [1]
    plan.pop("mechanism_recombination_protocol")
    plan["candidates"] = [
        "shared_tensor_dynamics_v1", "independent_tensor_dynamics_v1",
        "cross_family_only_tensor_dynamics_v1", "support_only_tensor_dynamics_v1",
        *BASELINES,
    ]
    plan["continuous_transfer_protocol"] = {
        "families": list(FAMILIES),
        "tensor_contract_sha256": "63c0e64273a1ffb2d4fd2fd6f24fc2d8701066ef9fd07d46eafeefa73fbf0296",
        "shared_candidate": "shared_tensor_dynamics_v1",
        "independent_ablation": "independent_tensor_dynamics_v1",
        "cross_family_only_ablation": "cross_family_only_tensor_dynamics_v1",
        "support_only_ablation": "support_only_tensor_dynamics_v1",
        "classical_baselines": list(BASELINES),
        "privileged_support_control": "privileged_tensor_support_v1",
        "family_labels": "evaluator_private", "semantic_channel_alignment": "forbidden",
        "normalization": "masked_training_worlds_only",
        "loss": "family_balanced_masked_normalized_mse",
        "state_budget_bytes": 67_108_864, "declared_reuses": [1, 4, 16],
        "pareto_capability_metrics": [
            "transfer_accuracy", "minimum_family_accuracy", "stable_rollout_rate",
            "normalized_rmse", "data_acquisition_ops", "preprocessing_ops", "fit_ops",
            "adaptation_ops", "mean_query_ops", "state_bytes", "peak_state_bytes",
            "mean_bytes_touched", "workload_ops_r1", "workload_ops_r4", "workload_ops_r16",
        ],
        "causal_promotion_gates": [
            "shared_vs_independent_gain", "cross_family_transfer_gain",
        ],
        "invalidation_rules": ["Invalidate any family label or semantic channel alignment."] * 7,
    }
    plan["primary_metrics"] = [
        "transfer_accuracy", "minimum_family_accuracy", "stable_rollout_rate", "normalized_rmse",
        "shared_vs_independent_gain", "cross_family_transfer_gain",
        "data_acquisition_ops", "preprocessing_ops", "fit_ops", "adaptation_ops",
        "mean_query_ops", "state_bytes", "peak_state_bytes", "mean_bytes_touched",
        "workload_ops_r1", "workload_ops_r4", "workload_ops_r16",
    ]
    plan["metric_directions"] = {
        name: ("maximize" if name in {"transfer_accuracy", "minimum_family_accuracy", "stable_rollout_rate",
                                      "shared_vs_independent_gain", "cross_family_transfer_gain"}
               else "minimize") for name in plan["primary_metrics"]
    }
    validate_document("experiment_plan", plan, root)
    invalid = copy.deepcopy(plan)
    invalid["continuous_transfer_protocol"]["cross_family_only_ablation"] = "support_only_tensor_dynamics_v1"
    with pytest.raises(Exception, match="cross_family_only_tensor_dynamics_v1"):
        validate_document("experiment_plan", invalid, root)


def test_cross_candidate_gains_are_derived_per_family_before_aggregation() -> None:
    def row(name: str, errors: tuple[float, float, float]) -> dict:
        trials = [{
            "status": "complete", "world_family": family, "seed": 7,
            "knowledge_size": 4, "reasoning_depth": 1, "accuracy": 1 / (1 + error),
            "warm_accuracy": 1 / (1 + error), "continual_retention": 1.0,
            "normalized_rmse": error, "mean_query_ops": 1, "mean_warm_query_ops": 1,
            "p50_latency_us": 1, "p95_latency_us": 1, "fit_seconds": 1,
            "state_bytes": 1, "update_ops": 0, "update_latency_us": 0,
        } for family, error in zip(FAMILIES, errors)]
        return {"candidate": name, "status": "complete", "trials": trials, "summary": {}}
    rows = [
        row("shared", (.2, .3, .4)), row("independent", (.4, .5, .6)),
        row("cross", (.5, .6, .7)), row("support", (.8, .9, 1.0)),
    ]
    _apply_continuous_transfer_comparisons(rows, {
        "shared_candidate": "shared", "independent_ablation": "independent",
        "cross_family_only_ablation": "cross", "support_only_ablation": "support",
    })
    assert rows[0]["summary"]["shared_vs_independent_gain"] == pytest.approx(.2)
    assert rows[2]["summary"]["cross_family_transfer_gain"] == pytest.approx(.3)
