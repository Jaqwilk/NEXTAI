from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.equality_grammar_masked_byte_core import (
    MAX_DEPTH, MAX_EXPANSION, MAX_RULES, MIN_ANCHORS, MIN_SUPPORT, SMOOTHING,
)
from nextai_autoresearch.candidates.recursive_equality_grammar_masked_byte import (
    Candidate as Recursive,
)
from nextai_autoresearch.candidates.source_identical_flat_equality_grammar_masked_byte import (
    Candidate as Flat,
)
from nextai_autoresearch.candidates.source_identical_frozen_equality_grammar_masked_byte import (
    Candidate as Frozen,
)
from nextai_autoresearch.masked_refinement_contract import (
    MASK, ByteFile, MaskedQuery, MaskedTraining,
)


def _training(raw: tuple[int, ...]) -> MaskedTraining:
    return MaskedTraining((ByteFile(7, raw),), (), len(raw))


def test_constants_roles_and_source_identity_are_frozen() -> None:
    assert (SMOOTHING, MIN_SUPPORT, MAX_RULES, MAX_DEPTH, MAX_EXPANSION, MIN_ANCHORS) == (
        0.5, 3, 64, 6, 32, 2,
    )
    assert Recursive.__mro__[1] is Flat.__mro__[1] is Frozen.__mro__[1]
    roles = [Recursive(3), Flat(3), Frozen(3)]
    for role in roles:
        role.fit(_training((1, 2, 1, 2, 1, 2, 1, 2)), 256, 6)
    assert roles[0].rules == roles[1].rules == roles[2].rules
    assert len({role.fit_ops for role in roles}) == 1
    assert len({role.state_bytes() for role in roles}) == 1


def test_recursive_fixture_requires_two_rule_levels_and_flat_cannot_solve() -> None:
    roles = [Recursive(1), Flat(1), Frozen(1)]
    training = _training((1, 2, 1, 2, 1, 2, 1, 2))
    for role in roles:
        role.fit(training, 256, 6)
    assert max(rule.depth for rule in roles[0].rules) >= 2
    query = MaskedQuery(2, (1, 2, MASK, 2, 1, 2), (2,), 0, 6)
    rows = [np.asarray(role.query(query, 6)[0]) for role in roles]
    assert rows[0][1] > rows[1][1]
    assert np.allclose(rows[1], rows[2])
    assert roles[0].last_ops > roles[1].last_ops > roles[2].last_ops
    assert roles[0].last_critical_path_steps > roles[1].last_critical_path_steps
    assert not hasattr(query, "target")


def test_fit_and_query_are_equivariant_under_consistent_byte_relabeling() -> None:
    permutation = np.asarray([(73 * value + 19) % 256 for value in range(256)])
    raw = (2, 7, 2, 7, 2, 7, 2, 7)
    first, second = Recursive(5), Recursive(5)
    first.fit(_training(raw), 256, 6)
    second.fit(_training(tuple(int(permutation[value]) for value in raw)), 256, 6)
    query = MaskedQuery(1, (2, 7, MASK, 7, 2, 7), (2,), 0, 6)
    mapped = MaskedQuery(
        1, tuple(MASK if value == MASK else int(permutation[value])
                 for value in query.snapshot), (2,), 0, 6,
    )
    original = np.asarray(first.query(query, 6))
    changed = np.asarray(second.query(mapped, 6))
    assert np.allclose(changed[:, permutation], original)
