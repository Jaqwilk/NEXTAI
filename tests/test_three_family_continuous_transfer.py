from __future__ import annotations

import importlib
import copy

import numpy as np
import pytest

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.benchmarks.heldout_three_family_continuous_transfer_v1 import (
    BASE_IMPLEMENTATION, FAMILIES, ROLE, _assignment, build_worlds,
)
from nextai_autoresearch.benchmarks import heldout_three_family_continuous_transfer_v6 as v6_benchmark
from nextai_autoresearch.benchmarks import heldout_three_family_continuous_transfer_v7 as v7_benchmark
from nextai_autoresearch.benchmarks import heldout_three_family_continuous_transfer_v8 as v8_benchmark
from nextai_autoresearch.benchmarks import heldout_three_family_continuous_transfer_v1 as shared_evaluator
from nextai_autoresearch.benchmarks import heldout_three_family_continuous_transfer_v2 as v2_benchmark
from nextai_autoresearch.benchmarks import heldout_three_family_continuous_transfer_v3 as v3_benchmark
from nextai_autoresearch.benchmarks import heldout_three_family_continuous_transfer_v4 as v4_benchmark
from nextai_autoresearch.benchmarks import heldout_three_family_continuous_transfer_v5 as v5_benchmark
from nextai_autoresearch.config import load_config
from nextai_autoresearch.candidates.tensor_indexed_local_operator_core import (
    BUCKET_CAP, BUCKET_COUNT, CODE_BITS, RIDGE,
)
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
INDEX_BASELINES = (
    "tensor_raw_window_local_linear_v1", "tensor_random_projection_hash_v1",
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


def test_v6_registers_four_source_identical_recurrent_residual_roles() -> None:
    roles = {
        "shared_bounded_recurrent_residual_v1": "shared",
        "independent_bounded_recurrent_residual_v1": "independent",
        "cross_family_only_bounded_recurrent_residual_v1": "cross_family_only",
        "support_only_bounded_recurrent_residual_v1": "support_only",
    }
    assert v6_benchmark.BENCHMARK_VERSION == "heldout_three_family_continuous_transfer_v6"
    assert {name: ROLE[name] for name in roles} == roles
    assert {
        BASE_IMPLEMENTATION[name] for name in roles if name != "shared_bounded_recurrent_residual_v1"
    } == {"shared_bounded_recurrent_residual_v1"}


def test_v7_registers_four_source_identical_local_update_law_roles() -> None:
    roles = {
        "shared_local_update_law_v1": "shared",
        "independent_local_update_law_v1": "independent",
        "cross_family_only_local_update_law_v1": "cross_family_only",
        "support_only_local_update_law_v1": "support_only",
    }
    assert v7_benchmark.BENCHMARK_VERSION == "heldout_three_family_continuous_transfer_v7"
    assert {name: ROLE[name] for name in roles} == roles
    assert {
        BASE_IMPLEMENTATION[name] for name in roles if name != "shared_local_update_law_v1"
    } == {"shared_local_update_law_v1"}
    worlds = {family: [_synthetic()] for family in FAMILIES}
    assert [len(_assignment(ROLE[name], FAMILIES[0], worlds)) for name in roles] == [3, 1, 2, 0]


def test_v8_registers_invariant_module_roles_without_changing_assignments() -> None:
    transfer_roles = {
        "shared_invariant_residual_module_v1": "shared",
        "independent_invariant_residual_module_v1": "independent",
        "cross_family_only_invariant_residual_module_v1": "cross_family_only",
        "support_only_invariant_residual_module_v1": "support_only",
    }
    assert v8_benchmark.BENCHMARK_VERSION == "heldout_three_family_continuous_transfer_v8"
    assert {name: ROLE[name] for name in transfer_roles} == transfer_roles
    assert {
        BASE_IMPLEMENTATION[name] for name in transfer_roles
        if name != "shared_invariant_residual_module_v1"
    } == {"shared_invariant_residual_module_v1"}
    assert ROLE["pooled_without_invariance_residual_module_v1"] == "shared"
    assert ROLE["frozen_partition_invariant_residual_module_v1"] == "shared"
    worlds = {family: [_synthetic()] for family in FAMILIES}
    assert [len(_assignment(ROLE[name], FAMILIES[0], worlds)) for name in transfer_roles] == [3, 1, 2, 0]


def test_v7_reports_local_adaptation_as_update_without_changing_old_roles() -> None:
    assert shared_evaluator._reported_update_ops("shared_local_update_law_v1", 36.0, 9) == 4.0
    for name in tuple(ROLE):
        if name not in shared_evaluator.UPDATE_LAW_ROLES:
            assert shared_evaluator._reported_update_ops(name, 36.0, 9) == 0.0


def test_v6_role_extension_preserves_all_v1_through_v5_role_semantics() -> None:
    expected = {
        "shared_tensor_dynamics_v1": "shared",
        "independent_tensor_dynamics_v1": "independent",
        "cross_family_only_tensor_dynamics_v1": "cross_family_only",
        "support_only_tensor_dynamics_v1": "support_only",
        "tensor_persistence_v1": "shared",
        "tensor_ridge_arx_v1": "shared",
        "tensor_rls_arx_v1": "shared",
        "tensor_empirical_gaussian_joint_v1": "shared",
        "tensor_contextual_gaussian_chow_liu_v1": "shared",
        "tensor_autoregressive_v1": "shared",
        "privileged_tensor_support_v1": "privileged",
        "tensor_raw_window_local_linear_v1": "shared",
        "tensor_random_projection_hash_v1": "shared",
        "shared_predictive_index_v1": "shared",
        "independent_predictive_index_v1": "independent",
        "cross_family_only_predictive_index_v1": "cross_family_only",
        "support_only_predictive_index_v1": "support_only",
    }
    assert {name: ROLE[name] for name in expected} == expected
    assert {name: BASE_IMPLEMENTATION[name] for name in BASE_IMPLEMENTATION if name in expected} == {
        "independent_tensor_dynamics_v1": "shared_tensor_dynamics_v1",
        "cross_family_only_tensor_dynamics_v1": "shared_tensor_dynamics_v1",
        "support_only_tensor_dynamics_v1": "shared_tensor_dynamics_v1",
        "independent_predictive_index_v1": "shared_predictive_index_v1",
        "cross_family_only_predictive_index_v1": "shared_predictive_index_v1",
        "support_only_predictive_index_v1": "shared_predictive_index_v1",
    }
    assert all(
        benchmark.run_suite is shared_evaluator.run_suite
        for benchmark in (
            v2_benchmark, v3_benchmark, v4_benchmark, v5_benchmark, v6_benchmark,
            v7_benchmark, v8_benchmark,
        )
    )


def test_v6_roles_resolve_one_candidate_and_only_assignment_scope_differs(monkeypatch) -> None:
    loaded = []

    class Module:
        class Candidate:
            CONSTANTS = (0.001, 4.0)

            def __init__(self, seed):
                self.seed = seed

    def fake_import(name):
        loaded.append(name)
        return Module

    monkeypatch.setattr(shared_evaluator.importlib, "import_module", fake_import)
    names = (
        "shared_bounded_recurrent_residual_v1",
        "independent_bounded_recurrent_residual_v1",
        "cross_family_only_bounded_recurrent_residual_v1",
        "support_only_bounded_recurrent_residual_v1",
    )
    candidates = [shared_evaluator._load(name, 17) for name in names]
    assert len(set(loaded)) == 1
    assert loaded[0].endswith(".shared_bounded_recurrent_residual_v1")
    assert {candidate.CONSTANTS for candidate in candidates} == {(0.001, 4.0)}
    worlds = {family: [_synthetic()] for family in FAMILIES}
    assert [len(_assignment(ROLE[name], FAMILIES[0], worlds)) for name in names] == [3, 1, 2, 0]


@pytest.mark.parametrize("name", BASELINES + INDEX_BASELINES)
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


def _index_arrays() -> tuple[np.ndarray, ...]:
    x = np.zeros((40, 32), dtype=np.float64)
    x[:, :4] = np.column_stack((
        np.linspace(-2, 2, 40), np.sin(np.linspace(-2, 2, 40)),
        np.cos(np.linspace(-2, 2, 40)), np.linspace(1, 3, 40),
    ))
    y = np.zeros((40, 32), dtype=np.float64)
    y[:, :2] = np.column_stack((x[:, 0] + x[:, 2], 2 * x[:, 1] - x[:, 3]))
    xm, ym = np.zeros_like(x, dtype=bool), np.zeros_like(y, dtype=bool)
    xm[:, :4], ym[:, :2] = True, True
    return x, y, xm, ym


@pytest.mark.parametrize("name,variant", [
    ("tensor_raw_window_local_linear_v1", "raw"),
    ("tensor_random_projection_hash_v1", "random"),
])
def test_index_controls_share_cap_operator_and_reference_key(name: str, variant: str) -> None:
    candidate = importlib.import_module(f"nextai_autoresearch.candidates.{name}").Candidate(17)
    x, y, xm, ym = _index_arrays()
    model = candidate._build(x, y, xm, ym)
    assert (BUCKET_COUNT, BUCKET_CAP, CODE_BITS, RIDGE) == (32, 8, 5, 1e-3)
    assert len(model["buckets"]) == BUCKET_COUNT
    assert max(len(bucket["x"]) for bucket in model["buckets"]) <= BUCKET_CAP
    query, mask = x[11], xm[11]
    bucket = candidate._bucket(query, mask, model)
    if variant == "raw":
        distances = np.square(np.where(model["prototype_masks"] & mask,
                                       model["prototypes"] - query, 0.0)).sum(axis=1)
        distances += 1e6 * np.logical_xor(model["prototype_masks"], mask).sum(axis=1)
        assert bucket == int(np.argmin(distances))
    else:
        key = np.sort(np.where(mask, query, np.inf))
        key = np.where(np.isfinite(key), key, 0.0)
        bits = model["projection"] @ key >= 0.0
        assert bucket == sum((1 << index) for index, value in enumerate(bits) if value)


@pytest.mark.parametrize("name", INDEX_BASELINES)
def test_index_controls_ignore_slots_world_order_and_equivariantly_permute_channels(name: str) -> None:
    module = importlib.import_module(f"nextai_autoresearch.candidates.{name}")
    first, second = _synthetic(), _synthetic()
    second = World(999, second.support_input, second.support_target, second.history,
                   second.future_public, second.output)
    left, right = module.Candidate(23), module.Candidate(23)
    left.fit(Training((first, second)))
    right.fit(Training((second, first)))
    assert np.array_equal(left._model["prototypes"], right._model["prototypes"])
    for a, b in zip(left._model["buckets"], right._model["buckets"]):
        assert np.allclose(a["weights"], b["weights"])

    x, y, xm, ym = _index_arrays()
    input_perm = np.r_[np.array([2, 0, 3, 1]), np.arange(4, 32)]
    output_perm = np.r_[np.array([1, 0]), np.arange(2, 32)]
    base, permuted = module.Candidate(23), module.Candidate(23)
    base_model = base._build(x, y, xm, ym)
    permuted_model = permuted._build(x[:, input_perm], y[:, output_perm],
                                     xm[:, input_perm], ym[:, output_perm])
    query = x[13]
    base_bucket = base._bucket(query, xm[13], base_model)
    permuted_bucket = permuted._bucket(query[input_perm], xm[13, input_perm], permuted_model)
    assert base_bucket == permuted_bucket
    base_prediction = np.r_[1.0, query] @ base_model["buckets"][base_bucket]["weights"]
    permuted_prediction = (np.r_[1.0, query[input_perm]]
                           @ permuted_model["buckets"][permuted_bucket]["weights"])
    assert np.allclose(permuted_prediction, base_prediction[output_perm], atol=1e-8)


def test_predictive_equivalence_fixture_defeats_raw_proximity() -> None:
    observations = np.array([[0.0], [0.1], [2.0]])
    future_operator = np.array([1, -1, 1])
    query = np.array([0.06])
    raw_choice = int(np.argmin(np.square(observations - query).sum(axis=1)))
    equivalent = np.flatnonzero(future_operator == future_operator[0])
    assert raw_choice == 1
    assert set(equivalent) == {0, 2}
    assert raw_choice not in equivalent


@pytest.mark.parametrize("name", INDEX_BASELINES)
def test_index_support_insert_is_local_bounded_and_global_model_is_unchanged(name: str) -> None:
    candidate = importlib.import_module(f"nextai_autoresearch.candidates.{name}").Candidate(31)
    world = _synthetic()
    candidate.fit(Training((world,)))
    before = [bucket["weights"].copy() for bucket in candidate._model["buckets"]]
    session = candidate.adapt(world.support_input, world.support_target)
    assert all(np.array_equal(weight, bucket["weights"])
               for weight, bucket in zip(before, candidate._model["buckets"]))
    assert max(len(bucket["x"]) for bucket in session["buckets"]) <= BUCKET_CAP
    assert candidate.state_bytes() < 67_108_864
    prediction = candidate.predict(session, world.history, world.future_public)
    assert np.isfinite(prediction).all()
    first_ops = candidate.last_ops
    candidate.fit(Training((world,) * 9))
    session = candidate.adapt(world.support_input, world.support_target)
    candidate.predict(session, world.history, world.future_public)
    assert candidate.last_ops == first_ops


def test_index_candidate_source_has_no_private_routing_tokens() -> None:
    root = project_root()
    forbidden = ("ncmapss", "dronepropa", "continuous_event", "world_family",
                 "source_path", "native_type", "semantic_channel", "test_output")
    for relative in (
        "src/nextai_autoresearch/candidates/tensor_indexed_local_operator_core.py",
        "src/nextai_autoresearch/candidates/tensor_raw_window_local_linear_v1.py",
        "src/nextai_autoresearch/candidates/tensor_random_projection_hash_v1.py",
    ):
        source = (root / relative).read_text(encoding="utf-8").lower()
        assert not any(token in source for token in forbidden)


def test_index_controls_real_file_smoke_and_fixed_query_work() -> None:
    training, testing = build_worlds(4, 1, 1_500_003)
    pooled = Training(tuple(world for family in FAMILIES for world in training[family]))
    for name in INDEX_BASELINES:
        candidate = importlib.import_module(f"nextai_autoresearch.candidates.{name}").Candidate(41)
        candidate.fit(pooled)
        observed = []
        for family in FAMILIES:
            world = testing[family][0]
            prediction = candidate.predict(
                candidate.adapt(world.support_input, world.support_target),
                world.history, world.future_public,
            )
            assert prediction.shape == (50, 32) and np.isfinite(prediction).all()
            observed.append(candidate.last_ops)
        assert all(value > 0 for value in observed)
        assert candidate.state_bytes() < 67_108_864


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

    v3 = copy.deepcopy(plan)
    v3["benchmark"] = "heldout_three_family_continuous_transfer_v3"
    v3["matrix"]["knowledge_sizes"] = [4, 6, 9]
    v3["candidates"] = [
        "shared_predictive_index_v1", "independent_predictive_index_v1",
        "cross_family_only_predictive_index_v1", "support_only_predictive_index_v1",
        *BASELINES[:-1], *INDEX_BASELINES, BASELINES[-1],
    ]
    protocol = v3["continuous_transfer_protocol"]
    protocol.update(
        shared_candidate="shared_predictive_index_v1",
        independent_ablation="independent_predictive_index_v1",
        cross_family_only_ablation="cross_family_only_predictive_index_v1",
        support_only_ablation="support_only_predictive_index_v1",
        classical_baselines=[*BASELINES[:-1], *INDEX_BASELINES, BASELINES[-1]],
    )
    validate_document("experiment_plan", v3, root)

    v6 = copy.deepcopy(v3)
    v6["benchmark"] = "heldout_three_family_continuous_transfer_v6"
    v6_roles = [
        "shared_bounded_recurrent_residual_v1",
        "independent_bounded_recurrent_residual_v1",
        "cross_family_only_bounded_recurrent_residual_v1",
        "support_only_bounded_recurrent_residual_v1",
    ]
    v6["candidates"] = [*v6_roles, *BASELINES[:-1], *INDEX_BASELINES, BASELINES[-1]]
    v6["continuous_transfer_protocol"].update(
        shared_candidate=v6_roles[0], independent_ablation=v6_roles[1],
        cross_family_only_ablation=v6_roles[2], support_only_ablation=v6_roles[3],
    )
    validate_document("experiment_plan", v6, root)
    v6["candidates"].remove(v6_roles[2])
    with pytest.raises(Exception, match="does not contain"):
        validate_document("experiment_plan", v6, root)

    v3["candidates"].remove("tensor_random_projection_hash_v1")
    with pytest.raises(Exception, match="does not contain"):
        validate_document("experiment_plan", v3, root)


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
