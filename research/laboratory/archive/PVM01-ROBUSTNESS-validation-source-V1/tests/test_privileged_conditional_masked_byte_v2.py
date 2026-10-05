import pytest

from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v11 as v11
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


def test_v11_real_run_case_routes_noncontiguous_closure_chain_privately() -> None:
    identity = tuple(range(256))
    case = v11.v9.closure_chain_case(b"([{}])", 3, 101, identity)
    row = v11._run_case(Candidate(11), "privileged_conditional_masked_byte_v2", case, 1)
    assert row["accuracy"] == row["exact"] == 1.0
    assert row["bits"] == 0.0


def test_v11_real_file_suite_completes_before_any_scoring_seed() -> None:
    plan = {
        "matrix": {
            "seeds": [1_234_567],
            "knowledge_sizes": [8],
            "reasoning_depths": [3],
            "queries_per_cell": 1,
        },
        "masked_refinement_protocol": {"state_budget_bytes": 4_194_304},
    }
    rows = v11.run_suite("privileged_conditional_masked_byte_v2", plan)
    assert len(rows) == 1
    assert rows[0]["status"] == "complete"
    assert rows[0]["accuracy"] == rows[0]["exact_span_accuracy"] == 1.0
