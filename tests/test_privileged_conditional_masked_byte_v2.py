import pytest

from nextai_autoresearch.candidates.privileged_conditional_masked_byte_v2 import Candidate
from nextai_autoresearch.masked_refinement_contract import (
    MASK, MaskedQuery, PrivilegedMaskedQuery,
)


def test_privileged_support_maps_noncontiguous_targets_by_masked_position_order() -> None:
    public = MaskedQuery(7, (4, MASK, 5, MASK, 6, 7, MASK), (1, 3, 6), 0, 1)
    candidate = Candidate(11)
    rows = candidate.query(PrivilegedMaskedQuery(public, (31, 47, 59)), 1)
    assert [row.index(1.0) for row in rows] == [31, 47, 59]
    assert all(sum(row) == 1.0 for row in rows)
    assert candidate.last_ops == candidate.last_bytes_touched == 3


def test_privileged_support_rejects_target_alignment_mismatch() -> None:
    public = MaskedQuery(7, (MASK, 4, MASK), (0, 2), 0, 1)
    with pytest.raises(ValueError, match="align"):
        Candidate(11).query(PrivilegedMaskedQuery(public, (31,)), 1)
