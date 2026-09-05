from __future__ import annotations

import pytest

from nextai_autoresearch.candidates.multiverse_local_core import MultiverseLocalLearner
from nextai_autoresearch.cross_family_transfer_v2_contract import (
    Example, PublicQuery, PublicTraining, TestWorld, TrainingWorld, encode,
)

TransferWorld = TestWorld
del TestWorld


def _translated_training() -> tuple[PublicTraining, PublicQuery]:
    support, _ = encode((10, 20, 30))
    query, _ = encode((10, 30))
    shifted_support, _ = encode((110, 120, 130))
    shifted_query, _ = encode((110, 130))
    facts = PublicTraining(
        (TrainingWorld(support, (Example(query, (20.0,)),)),),
        (TransferWorld(7, shifted_support),),
        len(support) + len(query) + len(shifted_support),
    )
    return facts, PublicQuery(7, shifted_query)


@pytest.mark.parametrize("mode", ["shared", "independent", "contextual", "joint", "autoregressive"])
def test_generic_candidates_are_atom_relabeling_equivariant(mode: str) -> None:
    facts, query = _translated_training()
    candidate = MultiverseLocalLearner(3, mode=mode)
    candidate.fit(facts, 8, 1)
    assert candidate.query(query, 1) == (120.0,)
    assert candidate.fit_ops > 0
    assert candidate.last_ops > 0
    assert 0 < candidate.state_bytes() < 4_194_304


def test_implementable_candidate_rejects_privileged_input() -> None:
    candidate = MultiverseLocalLearner()
    with pytest.raises(TypeError, match="PublicTraining"):
        candidate.fit(object(), 8, 1)
