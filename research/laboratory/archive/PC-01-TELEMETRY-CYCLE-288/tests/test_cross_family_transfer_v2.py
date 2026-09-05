from __future__ import annotations

import copy
from dataclasses import dataclass

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import cross_family_shared_representation_v2 as bench
from nextai_autoresearch.cross_family_transfer_v2_contract import encode
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


@dataclass(frozen=True)
class NamedShape:
    long_public_value: tuple[int, ...]


def test_v2_encoding_is_lossless_and_omits_names() -> None:
    values = tuple(range(70_000))
    encoded, operations = encode(NamedShape(values))
    assert operations == len(encoded) > 65_536
    assert encoded[-9::2] == values[-5:]
    assert hash("NamedShape") not in encoded
    assert hash("long_public_value") not in encoded


def test_v2_world_split_is_anonymous_complete_and_seed_disjoint() -> None:
    public, privileged, cold, near = bench._training(
        32, 6, 2, 1_500_001, (1103, 2207, 3301)
    )
    assert len(public.training_worlds) == 12
    assert len(public.test_worlds) == 4
    assert len({world.slot for world in public.test_worlds}) == 4
    assert set(cold) == set(bench.FAMILIES) == set(near)
    assert all(len(rows) == 2 for rows in cold.values())
    assert max(len(world.support) for world in public.test_worlds) > 65_536
    assert {world.family for world in privileged.native_worlds} == set(bench.FAMILIES)
    assert all(not hasattr(world, "family") for world in public.test_worlds)


def test_v2_rejects_derived_seed_collision() -> None:
    with pytest.raises(ValueError, match="derived training/test seed collision"):
        bench._training(8, 1, 1, 1103, (1103,))


def test_v2_plan_requires_lossless_transfer_commitments() -> None:
    plan = load_json(project_root() / "research" / "plans" / "EXP-20260830-0042.json")
    plan = copy.deepcopy(plan)
    plan["benchmark"] = bench.BENCHMARK_VERSION
    plan["transfer_protocol"].update({
        "representation_interface": "lossless_family_neutral_structural_tokens_v2",
        "test_result_access_during_fit": "forbidden",
        "state_budget_bytes": 4_194_304,
    })
    validate_document("experiment_plan", plan, project_root())
    del plan["transfer_protocol"]["representation_interface"]
    with pytest.raises(ValidationError, match="representation_interface"):
        validate_document("experiment_plan", plan, project_root())
