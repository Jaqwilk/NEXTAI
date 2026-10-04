from __future__ import annotations

import pytest

from nextai_autoresearch.benchmarks.successor_graph_v1 import make_world, oracle_answer
from nextai_autoresearch.candidates.compiled_jump import Candidate as CompiledJump
from nextai_autoresearch.candidates.dense_recurrent import Candidate as DenseRecurrent
from nextai_autoresearch.candidates.indexed_graph import Candidate as IndexedGraph
from nextai_autoresearch.candidates.linear_scan import Candidate as LinearScan
from nextai_autoresearch.candidates.memoized_graph import Candidate as MemoizedGraph


EXACT_CANDIDATES = [LinearScan, IndexedGraph, MemoizedGraph, CompiledJump, DenseRecurrent]


@pytest.mark.parametrize("candidate_class", EXACT_CANDIDATES)
def test_exact_candidates_match_oracle_and_preserve_old_facts(candidate_class) -> None:
    world = make_world(32, seed=1103)
    candidate = candidate_class(seed=1103)
    candidate.fit(world.facts, universe_size=32, max_depth=64)

    for source in (0, 3, 17, 31):
        for steps in (1, 2, 7, 31, 64):
            assert candidate.query(source, steps) == oracle_answer(
                world.oracle, source, steps
            )

    before = candidate.query(3, 7)
    candidate.update(32, 32)
    assert candidate.query(32, 7) == 32
    assert candidate.query(3, 7) == before


def _ordered_cycle(size: int) -> list[tuple[int, int]]:
    return [(index, (index + 1) % size) for index in range(size)]


def test_operation_counters_recover_expected_scaling_signatures() -> None:
    small_scan = LinearScan()
    small_scan.fit(_ordered_cycle(16), 16, 32)
    assert small_scan.query(15, 1) == 0
    small_scan_ops = small_scan.last_ops

    large_scan = LinearScan()
    large_scan.fit(_ordered_cycle(64), 64, 32)
    assert large_scan.query(63, 1) == 0
    assert large_scan.last_ops == 4 * small_scan_ops

    indexed = IndexedGraph()
    indexed.fit(_ordered_cycle(64), 64, 32)
    assert indexed.query(0, 16) == 16
    assert indexed.last_ops == 16

    compiled = CompiledJump()
    compiled.fit(_ordered_cycle(64), 64, 32)
    assert compiled.query(0, 16) == 16
    assert compiled.last_ops == 1
    assert compiled.query(0, 31) == 31
    assert compiled.last_ops == 5

    dense = DenseRecurrent()
    dense.fit(_ordered_cycle(16), 16, 32)
    dense.query(0, 4)
    dense_small_ops = dense.last_ops
    dense.fit(_ordered_cycle(32), 32, 32)
    dense.query(0, 4)
    assert dense.last_ops == 4 * dense_small_ops


def test_memoization_reduces_warm_operations_and_update_invalidates_cache() -> None:
    candidate = MemoizedGraph()
    candidate.fit(_ordered_cycle(64), 64, 32)
    assert candidate.query(0, 16) == 16
    assert candidate.last_ops == 16
    assert candidate.query(0, 16) == 16
    assert candidate.last_ops == 1

    candidate.update(0, 2)
    assert candidate.update_ops >= 2
    assert candidate.query(0, 16) == 17
    assert candidate.last_ops == 16


def test_world_generation_is_seeded_and_forms_one_cycle() -> None:
    left = make_world(128, seed=42)
    right = make_world(128, seed=42)
    other = make_world(128, seed=43)
    assert left == right
    assert left != other
    assert set(left.oracle) == set(range(128))
    assert set(left.oracle.values()) == set(range(128))
    assert oracle_answer(left.oracle, 0, 128) == 0

