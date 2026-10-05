import pytest

from nextai_autoresearch.baseline_semantics import required_baseline_names
from nextai_autoresearch.benchmarks import heldout_raw_sensor_active_identification_v1 as v1
from nextai_autoresearch.benchmarks.successor_graph_v1 import load_candidate
from nextai_autoresearch.raw_sensor_acquisition_contract import (
    PrivilegedRawProbeSession, RawProbeSession, RawSensorTraining, RawSensorWorld,
)


def protocol():
    return {"support_only_ablation": "source_identical_support_only_raw_sensor_probe_v1",
            "shared_candidate": "shared_raw_sensor_probe_learner_v1",
            "frozen_representation_ablation": "source_identical_frozen_raw_sensor_probe_v1",
            "state_budget_bytes": 16_777_216}


def test_raw_sensor_world_is_reproducible_and_transform_held_out() -> None:
    assert v1._means(32, 117031).tobytes() == v1._means(32, 117031).tobytes()
    assert v1._means(32, 117031).tobytes() != v1._means(32, 117032).tobytes()
    assert 117031 not in v1.TRAIN_WORLD_SEEDS


def test_probe_session_is_bounded_and_hides_target() -> None:
    session = RawProbeSession(tuple(float(index) for index in range(v1.SENSOR_COUNT)))
    assert session.probe(3) == 3.0
    with pytest.raises(ValueError):
        session.probe(3)
    assert not hasattr(session, "target")


def test_observe_all_identifies_development_world() -> None:
    row = v1._run_trial("raw_sensor_observe_all_v1", 32, 4, 64, v1.DEVELOPMENT_SEED,
                        16_777_216, protocol())
    assert row["accuracy"] == 1.0
    assert row["mean_probe_count"] == v1.SENSOR_COUNT


def test_no_probe_does_not_solve_development_world() -> None:
    row = v1._run_trial("raw_sensor_no_probe_prior_v1", 32, 16, 128, v1.DEVELOPMENT_SEED,
                        16_777_216, protocol())
    assert row["accuracy"] < 0.10
    assert row["mean_probe_count"] == 0.0


def test_information_controls_use_only_charged_probes() -> None:
    training = v1._training(32, v1.DEVELOPMENT_SEED)
    values = v1._queries(32, 1, v1.DEVELOPMENT_SEED)[1][0]
    for name in ("raw_sensor_gaussian_information_gain_v1", "raw_sensor_kernel_information_gain_v1"):
        candidate = load_candidate(name, 7)
        candidate.fit(training, 32, 16)
        session = RawProbeSession(tuple(map(float, values)))
        candidate.query(session, 8)
        assert session.calls == 8
        assert candidate.last_input_ops == 16


def test_fisher_and_random_controls_obey_the_probe_budget() -> None:
    training = v1._training(32, v1.DEVELOPMENT_SEED)
    values = tuple(map(float, v1._queries(32, 1, v1.DEVELOPMENT_SEED)[1][0]))
    for name in ("raw_sensor_random_probe_v1", "raw_sensor_fisher_fixed_probe_v1"):
        candidate = load_candidate(name, 9)
        candidate.fit(training, 32, 16)
        session = RawProbeSession(values)
        candidate.query(session, 4)
        assert session.calls == 4
    fisher = load_candidate("raw_sensor_fisher_fixed_probe_v1", 9)
    fisher.fit(training, 32, 16)
    assert tuple(map(int, fisher.order)) != tuple(range(v1.SENSOR_COUNT))


def test_gaussian_and_kernel_controls_condition_the_second_probe() -> None:
    means = ((-1.0, -1.0, 0.0), (-1.0, 1.0, 0.0),
             (1.0, 0.0, -1.0), (1.0, 0.0, 1.0))
    world = RawSensorWorld(tuple(tuple(row for _ in range(3)) for row in means))
    training = RawSensorTraining((), world)
    for name in ("raw_sensor_gaussian_information_gain_v1", "raw_sensor_kernel_information_gain_v1"):
        candidate = load_candidate(name, 1)
        candidate.fit(training, 4, 2)
        session = RawProbeSession(means[0])
        assert candidate.query(session, 2) == 0
        assert session.used == {0, 1}


def test_privileged_target_control_is_explicit_and_probe_free() -> None:
    candidate = load_candidate("privileged_raw_sensor_target_v1", 1)
    candidate.fit(v1._training(8, v1.DEVELOPMENT_SEED), 8, 4)
    session = PrivilegedRawProbeSession(tuple(0.0 for _ in range(v1.SENSOR_COUNT)), 6)
    assert candidate.query(session, 4) == 6
    assert session.calls == 0


def test_required_raw_sensor_baselines_are_routed() -> None:
    plan = {"candidates": list(v1.BASELINES),
            "active_sensor_protocol": {"classical_baselines": list(v1.BASELINES)}}
    assert required_baseline_names(plan) == list(v1.BASELINES)


def test_only_source_identical_meta_roles_receive_meta_worlds() -> None:
    spec = protocol()
    assert v1._uses_meta_worlds(spec["shared_candidate"], spec)
    assert v1._uses_meta_worlds(spec["frozen_representation_ablation"], spec)
    assert not v1._uses_meta_worlds(spec["support_only_ablation"], spec)
    assert all(not v1._uses_meta_worlds(name, spec) for name in v1.BASELINES)


def test_development_smoke_is_discriminating() -> None:
    smoke = v1.development_smoke()
    assert smoke["decision"] == "pass"
    assert smoke["scoring_targets_read"] is False
