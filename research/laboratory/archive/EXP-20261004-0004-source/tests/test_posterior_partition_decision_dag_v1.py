from __future__ import annotations

import numpy as np

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.benchmarks import heldout_raw_sensor_active_identification_v1 as v1
from nextai_autoresearch.benchmarks.successor_graph_v1 import load_candidate
from nextai_autoresearch.candidates.posterior_partition_decision_dag_core_v1 import (
    FROZEN_WEIGHTS, MAX_DEPTH, RIDGE, VARIANCE_FLOOR, PosteriorPartitionDecisionDAG,
)
from nextai_autoresearch.config import load_config
from nextai_autoresearch.raw_sensor_acquisition_contract import RawProbeSession, RawSensorTraining, RawSensorWorld
from nextai_autoresearch.utils import project_root


ROLES = (
    "shared_posterior_partition_decision_dag_v1",
    "source_identical_support_only_partition_dag_v1",
    "source_identical_frozen_partition_dag_v1",
)


def test_three_roles_share_one_core_and_frozen_constants() -> None:
    candidates = [load_candidate(name, 3) for name in ROLES]
    assert all(isinstance(candidate, PosteriorPartitionDecisionDAG) for candidate in candidates)
    assert [candidate.mode for candidate in candidates] == ["shared", "support_only", "frozen"]
    assert VARIANCE_FLOOR == 0.04 and RIDGE == 0.01 and MAX_DEPTH == 16
    assert np.array_equal(FROZEN_WEIGHTS, (0.5, 0.5))


def test_utility_is_invariant_to_class_sensor_and_sign_relabeling() -> None:
    world = v1._support(8, v1.DEVELOPMENT_SEED)
    samples = np.asarray(world.samples)
    class_order = np.asarray((3, 1, 6, 0, 7, 4, 2, 5))
    sensor_order = np.arange(47, -1, -1)
    signs = np.where(np.arange(48) % 2, -1.0, 1.0)
    transformed = RawSensorWorld(tuple(tuple(tuple(map(float, row)) for row in label)
                                       for label in samples[class_order][:, :, sensor_order] * signs))
    left = PosteriorPartitionDecisionDAG(1)
    left.mode = "support_only"
    left.fit(RawSensorTraining((), world), 8, 16)
    right = PosteriorPartitionDecisionDAG(1)
    right.mode = "support_only"
    right.fit(RawSensorTraining((), transformed), 8, 16)
    assert np.allclose(left.weights, right.weights, atol=1e-12)


def test_compiled_graph_uses_unique_charged_probes_and_stops_at_singleton() -> None:
    candidate = load_candidate("source_identical_frozen_partition_dag_v1", 5)
    training = v1._training(8, v1.DEVELOPMENT_SEED, include_meta=True)
    candidate.fit(training, 8, 16)
    row = tuple(map(float, v1._queries(8, 1, v1.DEVELOPMENT_SEED)[1][0]))
    session = RawProbeSession(row)
    answer = candidate.query(session, 16)
    assert 0 <= answer < 8
    assert session.calls <= 3
    assert session.calls == len(session.used)
    assert candidate.last_input_ops == 2 * session.calls


def test_all_roles_complete_a_tiny_real_evaluator_cell() -> None:
    protocol = {
        "shared_candidate": ROLES[0], "support_only_ablation": ROLES[1],
        "frozen_representation_ablation": ROLES[2], "state_budget_bytes": 16_777_216,
    }
    for role in ROLES:
        row = v1._run_trial(role, 8, 4, 8, v1.DEVELOPMENT_SEED, 16_777_216, protocol)
        assert row["status"] == "complete"
        assert 0.0 <= row["accuracy"] <= 1.0
        assert row["mean_probe_count"] <= 3.0


def test_all_roles_pass_transitive_candidate_audit() -> None:
    config, root = load_config(), project_root()
    for role in ROLES:
        result = audit_candidate(role, config, root)
        assert result.ok, result.problems
