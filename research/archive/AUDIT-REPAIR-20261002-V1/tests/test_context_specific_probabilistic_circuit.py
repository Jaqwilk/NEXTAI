from __future__ import annotations

import importlib
import itertools

import pytest

from nextai_autoresearch.benchmarks.context_specific_probabilistic_circuit_v1 import (
    joint_probability,
    make_queries,
    make_update,
    make_world,
    oracle_probability,
)


def test_joint_distribution_is_normalized_and_oracle_matches_enumeration() -> None:
    world = make_world(8, 1103)
    rows = tuple(itertools.product((0, 1), repeat=world.public.variable_count))
    assert sum(joint_probability(row, world) for row in rows) == pytest.approx(1.0)
    query, analytic = make_queries(world, 4, 1103, 1)[0]
    compatible = [row for row in rows if all(row[index] == value for index, value in query.evidence)]
    denominator = sum(joint_probability(row, world) for row in compatible)
    numerator = sum(joint_probability(row, world) for row in compatible if row[query.target] == 1)
    assert analytic == pytest.approx(numerator / denominator)


def test_public_training_hides_selector_and_factorization_metadata() -> None:
    world = make_world(8, 1103)
    assert len(world.public.samples) == 512
    assert all(len(row) == 9 and set(row) <= {0, 1} for row in world.public.samples)
    assert not hasattr(world.public, "selector")
    assert make_world(8, 1103) == world
    assert make_world(8, 2207).public.samples != world.public.samples


def test_query_masks_charge_payload_depth_and_near_hides_selector() -> None:
    world = make_world(32, 1103)
    cold = make_queries(world, 6, 1103, 8)
    near = make_queries(world, 6, 1103, 8, near=True)
    assert all(query.target not in dict(query.evidence) for query, _ in cold + near)
    assert all(sum(index != world.selector for index, _ in query.evidence) == 6
               for query, _ in cold + near)
    assert all(world.selector not in dict(query.evidence) for query, _ in near)
    assert all(abs(cold[index][1] - 0.5) >= 0.39 for index in range(0, len(cold), 2))


def test_update_changes_one_context_and_retains_the_other() -> None:
    world = make_world(8, 1103)
    update, changed, retained = make_update(world, 1103)
    assert oracle_probability(changed, world) == pytest.approx(0.9)
    assert oracle_probability(changed, world, update.epsilons) == pytest.approx(0.75)
    assert oracle_probability(retained, world) == pytest.approx(0.9)
    assert oracle_probability(retained, world, update.epsilons) == pytest.approx(0.9)


def test_candidate_bundle_when_present() -> None:
    try:
        core = importlib.import_module("nextai_autoresearch.candidates.probabilistic_circuit_core")
    except ModuleNotFoundError:
        pytest.skip("candidate bundle is added only after protocol-v2 preregistration")
    world = make_world(8, 1103)
    query, truth = make_queries(world, 4, 1103, 1)[0]
    candidate = core.ProbabilisticCircuitCandidate(1103, "oracle")
    candidate.fit(world, 8, 6)
    assert candidate.query(query, 4) == pytest.approx(truth)
