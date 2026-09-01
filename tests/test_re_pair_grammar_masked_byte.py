from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.re_pair_grammar_masked_byte import Candidate
from nextai_autoresearch.masked_refinement_contract import ByteFile, MASK, MaskedQuery, MaskedTraining


def _training(raw: tuple[int, ...]) -> MaskedTraining:
    return MaskedTraining((ByteFile(0, raw),), (), len(raw))


def test_re_pair_builds_recursive_rules_and_uses_them_for_completion() -> None:
    model = Candidate()
    model.fit(_training((1, 2, 1, 2, 1, 2, 1, 2)), 256, 8)
    assert model.max_rule_depth >= 2
    assert any(len(expansion) >= 4 for expansion in model.expansions)

    query = MaskedQuery(0, (1, 2, MASK, 2, 1, 2), (2,), 0, 1)
    row = np.asarray(model.query(query, 1)[0])
    assert np.isclose(row.sum(), 1.0)
    assert row[1] > row[3]


def test_re_pair_is_equivariant_under_consistent_byte_relabeling() -> None:
    raw = (7, 9, 7, 9, 7, 9, 7, 9)
    query = MaskedQuery(0, (7, 9, MASK, 9, 7, 9), (2,), 0, 1)
    first = Candidate()
    first.fit(_training(raw), 256, 8)
    original = np.asarray(first.query(query, 1)[0])

    mapping = np.arange(256)
    mapping[[7, 9, 41, 73]] = mapping[[41, 73, 7, 9]]
    relabeled = tuple(int(mapping[value]) for value in raw)
    second = Candidate()
    second.fit(_training(relabeled), 256, 8)
    changed_query = MaskedQuery(0, tuple(MASK if v == MASK else int(mapping[v]) for v in query.snapshot), (2,), 0, 1)
    changed = np.asarray(second.query(changed_query, 1)[0])
    assert np.allclose(changed[mapping], original)


def test_flat_digram_alias_cannot_pass_recursive_re_pair_fixture() -> None:
    model = Candidate()
    model.fit(_training((1, 2, 1, 2, 1, 2, 1, 2)), 256, 8)
    flat_digrams = {(1, 2)}
    assert model.max_rule_depth >= 2
    assert not any(len(rule) >= 4 for rule in flat_digrams)
