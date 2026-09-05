from nextai_autoresearch.candidates.learned_pushdown_masked_byte import Candidate as Full
from nextai_autoresearch.candidates.learned_pushdown_masked_byte_core import (
    BOUNDED_DEPTH, EXPECTED_SYMBOLS,
)
from nextai_autoresearch.candidates.source_identical_finite_state_pushdown_masked_byte import (
    Candidate as Bounded,
)
from nextai_autoresearch.candidates.source_identical_frozen_pushdown_masked_byte import (
    Candidate as Frozen,
)
from nextai_autoresearch.masked_refinement_contract import (
    MASK, ByteFile, MaskedQuery, MaskedTraining,
)


TRAIN = (10, 11, 9, 12, 13, 9, 14, 15, 9, 10, 12, 13, 11, 9,
         12, 14, 15, 13, 9, 14, 10, 11, 15)


def training(values=TRAIN):
    return MaskedTraining((ByteFile(7, tuple(values)),), (), len(values))


def query(values=(10, 12, 14, MASK, MASK, MASK)):
    return MaskedQuery(5, tuple(values), (3, 4, 5), 0, 1)


def predictions(candidate, source=None):
    return tuple(max(range(256), key=row.__getitem__)
                 for row in candidate.query(source or query(), 1))


def test_roles_share_core_constants_and_fit_grammar() -> None:
    assert (EXPECTED_SYMBOLS, BOUNDED_DEPTH) == (7, 2)
    assert Full.__mro__[1] is Bounded.__mro__[1] is Frozen.__mro__[1]
    roles = [Full(3), Bounded(3), Frozen(3)]
    for role in roles:
        role.fit(training(), 8, 5)
    assert roles[0].pairs == roles[1].pairs
    assert roles[0].separator == roles[1].separator == 9
    assert roles[2].pairs != roles[0].pairs or roles[2].separator != 9
    assert roles[0].fit_ops == roles[1].fit_ops > roles[2].fit_ops > 0
    assert all(role.state_bytes() > 0 for role in roles)


def test_full_stack_extrapolates_and_bounded_or_frozen_cannot_complete() -> None:
    roles = [Full(1), Bounded(1), Frozen(1)]
    for role in roles:
        role.fit(training(), 8, 5)
    truth = (15, 13, 11)
    assert predictions(roles[0]) == truth
    assert predictions(roles[1]) != truth
    assert predictions(roles[2]) != truth
    assert roles[0].last_ops == roles[1].last_ops == roles[2].last_ops
    assert roles[0].last_critical_path_steps == len(query().snapshot) + 1


def test_fit_and_query_commute_with_consistent_symbol_relabeling() -> None:
    mapping = {value: (73 * value + 19) % 256 for value in range(256)}
    first, second = Full(4), Full(4)
    first.fit(training(), 8, 5)
    second.fit(training(tuple(mapping[value] for value in TRAIN)), 8, 5)
    source = query()
    changed = MaskedQuery(
        source.slot,
        tuple(MASK if value == MASK else mapping[value] for value in source.snapshot),
        source.masked_positions, 0, 1,
    )
    assert predictions(second, changed) == tuple(mapping[value] for value in predictions(first))
    assert second.fit_ops == first.fit_ops
