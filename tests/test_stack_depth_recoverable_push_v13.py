from collections import Counter

import pytest

from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v11 as v11
from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v12 as v12
from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v13 as v13
from nextai_autoresearch.masked_refinement_contract import MASK


def test_literal_missing_push_chain_is_suffix_recoverable_not_top_copyable() -> None:
    case = v13.recoverable_push_chain_case(
        b"([{}])", 3, 7, tuple(range(256))
    )
    _, snapshot, positions, target = case
    assert positions == (1, 2)
    assert target == tuple(map(ord, "[{"))
    assert snapshot[0] == ord("(")
    assert all(snapshot[position] == MASK for position in positions)
    assert tuple(snapshot[position] for position in (3, 4)) == tuple(map(ord, "}]"))
    inverse = {ord(")"): ord("("), ord("]"): ord("["), ord("}"): ord("{")}
    assert tuple(inverse[snapshot[position]] for position in (4, 3)) == target
    assert tuple([snapshot[0]] * len(target)) != target


def test_copyable_single_type_chain_is_rejected() -> None:
    with pytest.raises(ValueError, match="copyable"):
        v13.recoverable_push_chain_case(
            b"((()))", 3, 7, tuple(range(256))
        )


def test_real_v12_corpus_supplies_identifiable_v13_cases_at_all_depths() -> None:
    _, tests, permutation = v12.make_stack_training(8, 123)
    counts = Counter()
    for depth in (3, 4, 5):
        cases = v13._repair_cases(tests, depth, 8, 123, permutation)
        assert len(cases) == 8
        for _, snapshot, positions, target in cases:
            counts[depth] += 1
            assert len(positions) == len(target) == depth - 1
            assert all(snapshot[position] == MASK for position in positions)
            assert any(value != snapshot[0] for value in target)
    assert counts == {3: 8, 4: 8, 5: 8}


def test_v13_changes_only_case_transform_and_reuses_v12_data_and_v11_route() -> None:
    assert v13.BENCHMARK_VERSION == "heldout_parallel_masked_infilling_v13"
    assert v13.make_stack_training is v12.make_stack_training
    assert v13._run_case is v11._run_case
