from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from nextai_autoresearch.cross_family_transfer_v2_contract import (
    Example, PublicQuery, PublicTraining, TestWorld, TrainingWorld, encode,
)
from nextai_autoresearch.utils import project_root


SHARED = "shared_relation_fragment_graph"
INDEPENDENT = "independent_relation_fragment_graph"
TransferWorld = TestWorld
del TestWorld


def _paths() -> tuple[Path, Path]:
    root = project_root() / "src" / "nextai_autoresearch" / "candidates"
    return root / f"{SHARED}.py", root / f"{INDEPENDENT}.py"


def _composition_fixture() -> tuple[PublicTraining, PublicQuery, tuple[float, ...]]:
    support, _ = encode(((10, 20, 30), (30, 40, 50)))
    first, _ = encode((10, 20))
    second, _ = encode((30, 40))
    shifted_support, _ = encode(((110, 120, 130), (130, 140, 150)))
    composed, _ = encode(((110, 120), (130, 140)))
    facts = PublicTraining(
        (TrainingWorld(support, (
            Example(first, (30.0,)), Example(second, (50.0,)),
        )),),
        (TransferWorld(7, shifted_support),),
        0,
    )
    return facts, PublicQuery(7, composed), (130.0, 150.0)


def test_v4_fixture_rejects_single_complete_example_lookup() -> None:
    facts, _, expected = _composition_fixture()
    nearest_complete_output = facts.training_worlds[0].examples[0].target
    assert len(nearest_complete_output) == 1
    assert nearest_complete_output != expected


def test_v4_future_candidates_compose_and_relabel_without_family_rules() -> None:
    paths = _paths()
    if not all(path.is_file() for path in paths):
        pytest.skip("v4 candidates are implemented only after immutable preregistration")
    shared = importlib.import_module(f"nextai_autoresearch.candidates.{SHARED}").Candidate
    independent = importlib.import_module(
        f"nextai_autoresearch.candidates.{INDEPENDENT}"
    ).Candidate
    assert shared.__bases__ == independent.__bases__
    assert shared.__bases__[0].__name__ == "RelationFragmentGraphLearner"
    facts, query, expected = _composition_fixture()
    for candidate in (shared(7), independent(7)):
        assert candidate.fragment_capacity == 64
        assert candidate.composition_rule == "typed_equality_join_then_component_emit_v1"
        candidate.fit(facts, 8, 2)
        assert candidate.query(query, 2) == expected
        assert len(candidate.last_composition_trace) >= 2
    assert shared(7).mode == "shared"
    assert independent(7).mode == "independent"
    for path in paths:
        source = path.read_text(encoding="utf-8").lower()
        assert all(value not in source for value in (
            "probabilistic", "predictive", "local", "program", "nativeworld"
        ))
