from __future__ import annotations

import math

import numpy as np

from nextai_autoresearch.candidates.born_mps_masked_byte_core import (
    FLOOR, Candidate as Parallel,
)
from nextai_autoresearch.candidates.source_identical_frozen_born_mps_masked_byte import (
    Candidate as Frozen,
)
from nextai_autoresearch.candidates.source_identical_sequential_born_mps_masked_byte import (
    Candidate as Sequential,
)
from nextai_autoresearch.masked_refinement_contract import (
    MASK, ByteFile, MaskedQuery, MaskedTraining,
)


def _training() -> MaskedTraining:
    data = tuple(([7, 1, 2, 7, 1, 3] * 40) + ([8, 4, 5, 8, 4, 6] * 40))
    return MaskedTraining((ByteFile(11, data),), (), len(data))


def test_source_identical_roles_share_tensor_and_probabilities() -> None:
    parallel, sequential = Parallel(7), Sequential(7)
    parallel.fit(_training(), 8, 6)
    sequential.fit(_training(), 8, 6)
    assert np.array_equal(parallel.tensor, sequential.tensor)
    query = MaskedQuery(3, (7, 1, MASK, 7, MASK, 3), (2, 4), 0, 6)
    first, second = parallel.query(query, 6), sequential.query(query, 6)
    assert np.allclose(first, second, rtol=0.0, atol=1e-12)
    assert parallel.last_critical_path_steps == 2 * math.ceil(math.log2(6)) + 3
    assert sequential.last_critical_path_steps == 2 * 6 + 3


def test_query_matches_direct_born_probability_for_one_mask() -> None:
    candidate = Parallel(9)
    candidate.fit(_training(), 8, 6)
    snapshot = (7, 1, MASK, 7)
    observed = candidate.query(MaskedQuery(2, snapshot, (2,), 0, 1), 1)[0]
    direct = []
    boundary = np.ones(2) / math.sqrt(2)
    for token in range(256):
        product = np.eye(2)
        for value in (7, 1, token, 7):
            product = product @ candidate.tensor[value]
        direct.append(float(boundary @ product @ boundary) ** 2)
    direct = np.asarray(direct) / sum(direct)
    direct = (direct + FLOOR) / sum(direct + FLOOR)
    assert np.allclose(observed, direct, rtol=0.0, atol=1e-12)


def test_frozen_role_charges_fit_but_retains_uniform_tensor() -> None:
    learned, frozen = Parallel(4), Frozen(4)
    learned.fit(_training(), 8, 6)
    frozen.fit(_training(), 8, 6)
    expected = math.sqrt(1 / 256) * np.eye(2)
    assert np.allclose(frozen.tensor, np.repeat(expected[None], 256, axis=0))
    assert not np.allclose(learned.tensor, frozen.tensor)
    assert learned.fit_ops == frozen.fit_ops
