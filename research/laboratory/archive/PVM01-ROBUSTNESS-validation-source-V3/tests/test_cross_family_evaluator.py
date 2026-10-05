from __future__ import annotations

from dataclasses import dataclass

from nextai_autoresearch.benchmarks import cross_family_shared_representation_v1 as bench
from nextai_autoresearch.cross_family_contract import QUERY_WIDTH, SUPPORT_WIDTH, pack


@dataclass(frozen=True)
class PublicShape:
    values: tuple[int, ...]
    label: int


def test_public_pack_is_fixed_width_and_ignores_field_names() -> None:
    support, operations = pack(PublicShape((4, 5), 6), SUPPORT_WIDTH)
    query, _ = pack(((4, 5), 6), QUERY_WIDTH)
    assert len(support) == SUPPORT_WIDTH
    assert len(query) == QUERY_WIDTH
    assert operations > 0
    assert all(isinstance(token, int) for token in support)
    assert hash("values") not in support and hash("label") not in support


def test_four_unseen_worlds_are_anonymous_and_seed_disjoint() -> None:
    public, privileged, cold, near = bench._training(8, 1, 2, 1_500_001, (1103,))
    assert len(public.meta_worlds) == 4
    assert len(public.test_worlds) == 4
    assert len({world.slot for world in public.test_worlds}) == 4
    assert set(cold) == set(bench.FAMILIES) == set(near)
    assert all(len(rows) == 2 for rows in cold.values())
    assert all(len(world.support) == SUPPORT_WIDTH for world in public.test_worlds)
    assert all(len(case.public.tokens) == QUERY_WIDTH for rows in cold.values() for case in rows)
    assert {world.family for world in privileged.native_worlds} == set(bench.FAMILIES)


def test_scoring_seed_cannot_be_a_training_seed() -> None:
    try:
        bench._training(8, 1, 1, 1103, (1103,))
    except ValueError as error:
        assert "collision" in str(error)
    else:
        raise AssertionError("seed collision was accepted")
