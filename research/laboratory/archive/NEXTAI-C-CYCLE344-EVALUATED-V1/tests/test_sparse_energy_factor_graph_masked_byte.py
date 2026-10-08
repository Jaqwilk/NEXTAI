from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.source_identical_frozen_energy_factor_graph_masked_byte import (
    Candidate as Frozen,
)
from nextai_autoresearch.candidates.source_identical_one_sweep_energy_factor_graph_masked_byte import (
    Candidate as OneSweep,
)
from nextai_autoresearch.candidates.sparse_energy_factor_graph_core import (
    LAGS,
    LOG_FACTOR_CLIP,
    MAX_SWEEPS,
    SMOOTHING,
)
from nextai_autoresearch.candidates.sparse_learned_energy_factor_graph_masked_byte import (
    Candidate as Learned,
)
from nextai_autoresearch.masked_refinement_contract import (
    MASK,
    ByteFile,
    MaskedQuery,
    MaskedTraining,
)


def _training(data: tuple[int, ...]) -> MaskedTraining:
    return MaskedTraining((ByteFile(11, data),), (), len(data))


def test_roles_are_source_identical_and_frozen_only_skips_factor_assignment() -> None:
    assert (LAGS, SMOOTHING, LOG_FACTOR_CLIP, MAX_SWEEPS) == (
        (1, 2, 4, 8), 0.5, 4.0, 6,
    )
    data = tuple([3, 8, 3, 9, 4, 8, 4, 9] * 32)
    roles = [Learned(17), OneSweep(17), Frozen(17)]
    for role in roles:
        role.fit(_training(data), 8, 6)
    assert np.array_equal(roles[0].prior, roles[1].prior)
    assert np.array_equal(roles[0].prior, roles[2].prior)
    assert np.array_equal(roles[0].factors, roles[1].factors)
    assert np.count_nonzero(roles[0].factors) > 0
    assert np.count_nonzero(roles[2].factors) == 0
    assert len({role.fit_ops for role in roles}) == 1
    assert len({role.state_bytes() for role in roles}) == 1


def test_parallel_relaxation_requires_overlapping_factors_and_reports_monotone_energy() -> None:
    query = MaskedQuery(3, (0, MASK, MASK, MASK, MASK, 5), (1, 2, 3, 4), 0, 6)
    roles = [Learned(1), OneSweep(1)]
    for role in roles:
        role.prior[:] = 1e-12
        role.prior[:6] = 1 / 6
        role.prior /= role.prior.sum()
        for value, weight in enumerate((1.0, 2.0, 3.0, 4.0, 4.0)):
            role.factors[0, value, value + 1] = weight
    parallel = [int(np.argmax(row)) for row in roles[0].query(query, 6)]
    one_sweep = [int(np.argmax(row)) for row in roles[1].query(query, 6)]
    assert parallel == [1, 2, 3, 4]
    assert one_sweep != parallel
    assert all(after <= before for before, after in zip(
        roles[0].last_energy_trace, roles[0].last_energy_trace[1:]
    ))
    assert len(roles[0].last_energy_trace) > len(roles[1].last_energy_trace)
    assert roles[0].last_ops > roles[1].last_ops > 0
    assert roles[0].last_bytes_touched > 0
    assert not hasattr(query, "target")


def test_fit_and_query_are_equivariant_under_consistent_byte_relabeling() -> None:
    permutation = np.asarray([(73 * value + 19) % 256 for value in range(256)])
    data = tuple([2, 7, 2, 9, 4, 7, 4, 9] * 64)
    relabeled = tuple(int(permutation[value]) for value in data)
    first, second = Learned(5), Learned(5)
    first.fit(_training(data), 8, 6)
    second.fit(_training(relabeled), 8, 6)
    snapshot = (2, 7, MASK, MASK, 4, 9)
    query = MaskedQuery(1, snapshot, (2, 3), 0, 4)
    mapped_query = MaskedQuery(
        1,
        tuple(MASK if value == MASK else int(permutation[value]) for value in snapshot),
        (2, 3), 0, 4,
    )
    original = np.asarray(first.query(query, 4))
    mapped = np.asarray(second.query(mapped_query, 4))
    assert np.allclose(mapped[:, permutation], original, atol=1e-12)
