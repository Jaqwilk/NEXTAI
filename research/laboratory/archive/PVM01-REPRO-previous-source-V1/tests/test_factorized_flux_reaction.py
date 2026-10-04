import math

import numpy as np

from nextai_autoresearch.benchmarks import continuous_local_cellular_v1 as bench
from nextai_autoresearch.candidates.factorized_flux_reaction_core import (
    FEATURE_WIDTH, OUTPUT_BOUND, RIDGE, UPDATE_ETA, FactorizedFluxReaction,
    exchange_features, pair_features,
)
from nextai_autoresearch.candidates.learned_factorized_flux_reaction_local_rule import Candidate as Shared
from nextai_autoresearch.candidates.source_identical_frozen_flux_reaction_local_rule import Candidate as Frozen
from nextai_autoresearch.candidates.source_identical_monolithic_local_flow_rule import Candidate as Monolithic


def _transform(vector, permutation, signs):
    return tuple(signs[index] * vector[source] for index, source in enumerate(permutation))


def test_exchange_is_exactly_antisymmetric_and_monolithic_field_is_not() -> None:
    first = (0.2, -0.4, 0.7, 0.1)
    second = (-0.3, 0.5, 0.2, -0.6)
    assert np.array_equal(exchange_features(first, second), -exchange_features(second, first))
    assert not np.allclose(pair_features(first, second), -pair_features(second, first))


def test_all_roles_share_one_core_and_frozen_constants() -> None:
    roles = (Shared(1), Monolithic(1), Frozen(1))
    assert all(isinstance(role, FactorizedFluxReaction) for role in roles)
    assert [role.mode for role in roles] == ["factorized", "monolithic", "frozen"]
    assert FEATURE_WIDTH == 39 and RIDGE == 0.001 and UPDATE_ETA == 0.05 and OUTPUT_BOUND == 1.5
    assert all(role.weights.shape == (39, 4) for role in roles)


def test_shared_fit_and_query_commute_with_signed_channel_permutation() -> None:
    world = bench.make_world(1103)
    permutation, signs = (2, 0, 3, 1), (-1, 1, -1, 1)
    transformed_rows = tuple(bench.Transition(*(
        _transform(getattr(row, field), permutation, signs)
        for field in ("left", "center", "right", "target")
    )) for row in world.training)
    original, transformed = Shared(1), Shared(1)
    original.fit(world.training, 64, 16)
    transformed.fit(transformed_rows, 64, 16)
    task = bench.make_task(world, 64, 8, 2207, 3)
    changed = bench.Task(task.size, task.source, task.target, tuple(
        (position, _transform(vector, permutation, signs)) for position, vector in task.initial
    ))
    expected = _transform(original.query(task, 8), permutation, signs)
    assert np.allclose(transformed.query(changed, 8), expected, atol=1e-9)


def test_sparse_query_work_is_independent_of_dormant_world_size() -> None:
    world = bench.make_world(1103)
    candidate = Shared(1)
    candidate.fit(world.training, 64, 16)
    operations = []
    for size in (64, 256, 1024):
        candidate.query(bench.make_task(world, size, 16, 3301, 0), 16)
        operations.append(candidate.last_ops)
    slope = np.polyfit(np.log((64, 256, 1024)), np.log(operations), 1)[0]
    assert operations[0] == operations[1] == operations[2]
    assert abs(float(slope)) <= 0.10


def test_frozen_role_is_finite_and_update_does_not_learn() -> None:
    world = bench.make_world(1103)
    candidate = Frozen(1)
    candidate.fit(world.training, 64, 16)
    before = candidate.weights.copy()
    candidate.update(world.training[-1], None)
    answer = candidate.query(bench.make_task(world, 64, 16, 4409, 1), 16)
    assert np.array_equal(candidate.weights, before)
    assert all(math.isfinite(value) and abs(value) <= OUTPUT_BOUND for value in answer)
    assert candidate.fit_ops > 0 and candidate.update_ops > 0 and candidate.last_ops > 0
