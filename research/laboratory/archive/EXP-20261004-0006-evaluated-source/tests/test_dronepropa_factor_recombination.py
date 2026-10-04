from __future__ import annotations

import hashlib
import struct
import zlib

import numpy as np
import pytest

from nextai_autoresearch.benchmarks import heldout_dronepropa_factor_recombination_v1 as bench
from nextai_autoresearch.benchmarks import heldout_dronepropa_factor_recombination_v2 as bench_v2
from nextai_autoresearch.candidates.dronepropa_baselines import (
    ConditionOracle,
    ConditionSpecialist,
    ContextualGaussianChowLiu,
    EmpiricalGaussianJoint,
    IndependentARX,
    NearestOperatorTemplate,
    Persistence,
    PooledARX,
    RLSARX,
    affine_predict,
    affine_ridge,
    chow_liu_tree,
)
from nextai_autoresearch.dronepropa_contract import FlightExamples
from nextai_autoresearch.utils import project_root


def _element(kind: int, payload: bytes) -> bytes:
    return struct.pack("<II", kind, len(payload)) + payload + b"\0" * (-len(payload) % 8)


def _mat_file(matrix: np.ndarray) -> bytes:
    flags = _element(6, struct.pack("<II", 6, 0))
    dimensions = _element(5, struct.pack("<ii", *matrix.shape))
    name = _element(1, b"QDrone_data")
    numeric = _element(9, np.asarray(matrix, dtype="<f8").tobytes(order="F"))
    inner = _element(14, flags + dimensions + name + numeric)
    compressed = zlib.compress(inner)
    header = b"MATLAB 5.0 MAT-file, NEXTAI semantic fixture".ljust(124, b" ") + b"\0\1IM"
    return header + struct.pack("<II", 15, len(compressed)) + compressed


def test_static_split_is_anonymous_whole_flight_and_frozen() -> None:
    result = bench.verify_static_contract(project_root())
    assert result["files"] == 130
    assert result["roles"] == bench.ROLE_COUNTS
    assert result["split_sha256"] == bench.SPLIT_MANIFEST_SHA256


def test_v2_split_reuses_files_and_reserves_t4_only_for_privileged_controls() -> None:
    result = bench_v2.verify_static_contract(project_root())
    assert result["roles"] == bench_v2.ROLE_COUNTS
    v1 = bench._corpus_rows(project_root())
    v2 = bench._corpus_rows(project_root(), bench_v2.SPLIT_MANIFEST)
    assert [row["source_sha256"] for row in v1] == [row["source_sha256"] for row in v2]
    support = [row for row in v2 if row["role"] == "privileged_oracle_support"]
    assert len(support) == 26 and {row["trajectory"] for row in support} == {"t4"}


def test_selected_loader_excludes_bad_esc_and_verifies_hash(tmp_path) -> None:
    matrix = np.zeros((56, 1000))
    matrix[0] = np.arange(1000) / 1000
    for index, row in enumerate(bench.SELECTED_ROWS):
        matrix[row] = index + np.arange(1000) / 100
    matrix[47] = np.nan
    matrix[49] = np.inf
    raw = _mat_file(matrix)
    path = tmp_path / "fixture.mat"
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    controls, states = bench.load_selected_flight(path, digest)
    assert controls.shape == (1000, 4)
    assert states.shape == (1000, 6)
    assert np.isfinite(controls).all() and np.isfinite(states).all()
    with pytest.raises(ValueError, match="hash mismatch"):
        bench.load_selected_flight(path, "0" * 64)


def test_adaptation_and_evaluation_windows_are_disjoint_and_guarded() -> None:
    adaptation = bench.adaptation_anchors(80_000)
    evaluation = bench.evaluation_anchors(80_000, 1234567)
    assert len(adaptation) == 32 and len(evaluation) == 128
    assert max(adaptation) < min(evaluation)
    assert min(right - left for left, right in zip(evaluation, evaluation[1:])) >= 82
    controls = np.arange(80_000 * 4, dtype=float).reshape(80_000, 4)
    states = np.arange(80_000 * 6, dtype=float).reshape(80_000, 6)
    features, targets = bench.arx_examples(controls, states, adaptation)
    assert features.shape == (32, 320) and targets.shape == (32, 6)


def test_full_cost_charges_acquisition_and_r1_r4_r16() -> None:
    fixed = bench.ARCHIVE_BYTES + bench.EXTRACTED_BYTES + 100
    assert bench.full_cost(100, 10, 20, 5, 1) == fixed + 35
    assert bench.full_cost(100, 10, 20, 5, 4) == fixed + 140
    assert bench.full_cost(100, 10, 20, 5, 16) == fixed + 560


def _synthetic_flight(slot: int, phase: float) -> bench._Flight:
    time = np.arange(20_000, dtype=float) / 1000
    controls = np.column_stack([np.sin(time * (index + 1) + phase) for index in range(4)])
    states = np.column_stack([
        np.sin(time * (index + 1) / 3 + phase) + 0.1 * controls[:, index % 4]
        for index in range(6)
    ])
    return bench._Flight(slot, controls, states, "fixture", "t1", controls.nbytes + states.nbytes)


def test_synthetic_end_to_end_runtime_reports_all_horizons_and_costs() -> None:
    result = bench._run_cell(
        "persistence_state_v1", 1_234_567, 1, 1,
        [_synthetic_flight(0, 0.0)], [_synthetic_flight(1, 0.2)],
        evaluation_count=4,
    )
    assert result["status"] == "complete"
    assert all(np.isfinite(result[name]) for name in (
        "teacher_forced_nrmse", "rollout_10_nrmse", "rollout_50_nrmse",
        "worst_flight_normalized_rmse", "workload_ops_r1", "workload_ops_r16",
    ))
    assert result["workload_ops_r16"] > result["workload_ops_r1"]


@pytest.mark.parametrize("candidate", [
    "persistence_state_v1", "ridge_arx_v1", "rls_arx_v1",
    "nearest_operator_template_v1", "source_identical_independent_arx_v1",
    "no_sharing_pooled_arx_v1", "empirical_gaussian_joint_v1",
    "contextual_gaussian_chow_liu_v1",
])
def test_all_implementable_controls_complete_same_synthetic_adapter_e2e(candidate) -> None:
    rng = np.random.default_rng(7)
    features = rng.normal(size=(32, 10))
    targets = features[:, :6] + 0.1 * features[:, 4:10]
    training = (FlightExamples(0, features, targets),)
    normalizer = bench._Normalization(np.zeros(10), np.ones(10), np.zeros(6), np.ones(6))
    runtime = bench._Runtime(candidate, 0, training, ("fixture",), normalizer)
    runtime.retain_training(training)
    session = runtime.adapt(FlightExamples(1, features[:16], targets[:16]), "fixture")
    prediction = runtime.predict(session, features[16])
    assert prediction.mean.shape == (1, 6)
    assert np.isfinite(prediction.mean).all()


def test_real_flight_loader_to_runtime_examples_smoke() -> None:
    row = next(row for row in bench._corpus_rows(project_root()) if row["role"] == "train")
    flight = bench._load_flights([row])[0]
    examples = bench._examples(flight, bench.training_anchors(len(flight.states)))
    assert examples.features.shape == (128, 320)
    assert examples.targets.shape == (128, 6)


def test_all_implementable_controls_real_file_one_step_smoke() -> None:
    rows = bench._corpus_rows(project_root(), bench_v2.SPLIT_MANIFEST)
    train_row = next(row for row in rows if row["role"] == "train")
    test_row = next(row for row in rows if row["role"] == "test")
    train, test = bench._load_flights([train_row, test_row])
    full_training = bench._examples(train, bench.training_anchors(len(train.states)))
    raw_training = (FlightExamples(
        full_training.slot, full_training.features[:, :10], full_training.targets,
    ),)
    normalizer = bench._normalization(raw_training)
    training = tuple(normalizer.examples(row) for row in raw_training)
    full_adaptation = bench._examples(test, bench.adaptation_anchors(len(test.states)))
    adaptation = normalizer.examples(FlightExamples(
        full_adaptation.slot, full_adaptation.features[:, :10], full_adaptation.targets,
    ))
    feature = adaptation.features[0]
    for candidate in (
        "persistence_state_v1", "ridge_arx_v1", "rls_arx_v1",
        "nearest_operator_template_v1", "source_identical_independent_arx_v1",
        "no_sharing_pooled_arx_v1", "empirical_gaussian_joint_v1",
        "contextual_gaussian_chow_liu_v1",
    ):
        runtime = bench._Runtime(
            candidate, 0, training, (train.condition,), normalizer,
        )
        runtime.retain_training(training)
        session = runtime.adapt(adaptation, test.condition)
        assert np.isfinite(runtime.predict(session, feature).mean).all()


def test_exact_heldout_conditions_are_absent_from_training() -> None:
    rows = bench._corpus_rows(project_root())
    training = {row["condition"] for row in rows if row["role"] == "train"}
    testing = {row["condition"] for row in rows if row["role"] == "test"}
    assert testing == {"F1_SV3", "F2_SV2", "F3_SV1"}
    assert training.isdisjoint(testing)


def test_exact_condition_control_refuses_undefined_heldout_condition() -> None:
    features = np.arange(4, dtype=float)[:, None]
    targets = np.column_stack([features[:, 0] + offset for offset in range(6)])
    examples = FlightExamples(0, features, targets)
    normalizer = bench._Normalization(np.zeros(1), np.ones(1), np.zeros(6), np.ones(6))
    runtime = bench._Runtime(
        "oracle_charged_condition_specialist_arx_v1", 0, (examples,),
        ("F1_SV1",), normalizer,
    )
    with pytest.raises(RuntimeError, match="absent from training"):
        runtime.adapt(examples, "F1_SV3")


@pytest.mark.parametrize(
    "candidate", [
        "oracle_charged_condition_specialist_arx_v2",
        "privileged_same_condition_oracle_arx_v2",
        "privileged_all_condition_support_arx_v3",
        "privileged_same_condition_support_arx_v3",
    ],
)
def test_v2_privileged_controls_use_t4_support_without_test_targets(candidate) -> None:
    rng = np.random.default_rng(11)
    features = rng.normal(size=(32, 10))
    targets = features[:, :6]
    examples = FlightExamples(0, features, targets)
    normalizer = bench._Normalization(np.zeros(10), np.ones(10), np.zeros(6), np.ones(6))
    runtime = bench._Runtime(
        candidate, 0, (examples,), ("train-only",), normalizer,
        (examples,), ("F1_SV3",),
    )
    session = runtime.adapt(examples, "F1_SV3")
    prediction = runtime.predict(session, features[0])
    assert prediction.mean.shape == (1, 6)
    assert np.isfinite(prediction.mean).all()


@pytest.mark.parametrize("candidate", [
    "oracle_charged_condition_specialist_arx_v2",
    "privileged_same_condition_oracle_arx_v2",
    "privileged_all_condition_support_arx_v3",
    "privileged_same_condition_support_arx_v3",
])
def test_v2_privileged_controls_real_file_one_step_smoke(candidate) -> None:
    rows = bench._corpus_rows(project_root(), bench_v2.SPLIT_MANIFEST)
    train_row = next(row for row in rows if row["role"] == "train")
    test_row = next(row for row in rows if row["role"] == "test")
    support_row = next(
        row for row in rows
        if row["role"] == "privileged_oracle_support"
        and row["condition"] == test_row["condition"]
    )
    train, test, support = bench._load_flights([train_row, test_row, support_row])
    full_training = bench._examples(train, bench.training_anchors(len(train.states)))
    raw_training = (FlightExamples(
        full_training.slot, full_training.features[:, :10], full_training.targets,
    ),)
    normalizer = bench._normalization(raw_training)
    training = tuple(normalizer.examples(row) for row in raw_training)
    full_support = bench._examples(support, bench.training_anchors(len(support.states)))
    privileged = (normalizer.examples(FlightExamples(
        full_support.slot, full_support.features[:, :10], full_support.targets,
    )),)
    runtime = bench._Runtime(
        candidate, 0, training, (train.condition,), normalizer,
        privileged, (support.condition,),
    )
    full_adaptation = bench._examples(test, bench.adaptation_anchors(len(test.states)))
    adaptation = normalizer.examples(FlightExamples(
        full_adaptation.slot, full_adaptation.features[:, :10], full_adaptation.targets,
    ))
    session = runtime.adapt(adaptation, test.condition)
    anchor = bench.evaluation_anchors(len(test.states), 1_234_567)[0]
    raw_feature = bench._feature(
        test.controls[anchor - bench.HISTORY + 1 : anchor + 1],
        test.states[anchor - bench.HISTORY + 1 : anchor + 1],
    )[:10]
    prediction = runtime.predict(
        session, (raw_feature - normalizer.feature_mean) / normalizer.feature_scale
    )
    assert prediction.mean.shape == (1, 6)
    assert np.isfinite(prediction.mean).all()


def test_persistence_and_affine_ridge_reference() -> None:
    state = np.arange(6, dtype=float)
    assert np.array_equal(Persistence().predict(state), state)
    x = np.arange(4, dtype=float)[:, None]
    y = np.column_stack([2 * x[:, 0] + offset for offset in range(6)])
    coefficients = affine_ridge(x, y, ridge=0.0)
    assert np.allclose(affine_predict(coefficients, np.array([[4.0]])), np.arange(6) + 8)


def test_rls_uses_predict_then_fixed_covariance_update() -> None:
    model = RLSARX(1, outputs=1, covariance=1000.0)
    assert model.predict(np.array([[0.0]])).item() == 0.0
    model.update(np.array([0.0]), np.array([2.0]))
    assert model.predict(np.array([[0.0]])).item() == pytest.approx(2000 / 1001)


def test_nearest_template_uses_operator_not_label_or_order() -> None:
    x = np.arange(5, dtype=float)[:, None]
    first = np.column_stack([x[:, 0]] * 6)
    second = -first
    model = NearestOperatorTemplate()
    model.fit([(x, first), (x, second)])
    assert model.select(x, second) == 1


def test_independent_and_no_sharing_are_distinct_source_identical_modes() -> None:
    assert issubclass(IndependentARX, PooledARX.__bases__[0])
    assert IndependentARX is not PooledARX


def test_empirical_gaussian_joint_matches_analytic_linear_conditional() -> None:
    x = np.arange(-20, 21, dtype=float)[:, None]
    y = np.column_stack([2 * x[:, 0] + offset for offset in range(6)])
    model = EmpiricalGaussianJoint(ridge=1e-9)
    model.fit(x, y)
    mean, covariance = model.conditional(np.array([[3.0]]))
    assert np.allclose(mean[0], np.arange(6) + 6, atol=1e-7)
    assert np.linalg.eigvalsh(covariance).min() > 0


def test_chow_liu_has_recursive_context_edge_and_markov_alias_cannot_pass() -> None:
    base = np.linspace(-1, 1, 64)
    residuals = np.column_stack((base, base + np.sin(np.arange(64)) * 0.01, (-1.0) ** np.arange(64)))
    tree = chow_liu_tree(residuals)
    assert (0, 1) in tree and len(tree) == 2
    model = ContextualGaussianChowLiu()
    x = np.arange(64, dtype=float)[:, None]
    targets = np.column_stack([2 * x[:, 0] + residuals[:, index % 3] for index in range(6)])
    model.fit(x, targets)
    assert len(model.tree) == 5
    assert not hasattr(PooledARX(), "tree")


def test_specialist_and_oracle_require_privileged_condition() -> None:
    x = np.arange(4, dtype=float)[:, None]
    rows = [(1, x, np.ones((4, 6))), (2, x, np.ones((4, 6)) * 2)]
    specialist, oracle = ConditionSpecialist(), ConditionOracle()
    specialist.fit(rows)
    oracle.fit(rows)
    assert np.allclose(specialist.predict(1, np.array([[9.0]])), 1)
    assert np.allclose(oracle.predict(2, np.array([[9.0]])), 2)
    assert specialist.privileged and oracle.privileged
