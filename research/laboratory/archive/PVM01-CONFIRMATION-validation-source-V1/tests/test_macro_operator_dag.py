from __future__ import annotations

from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v6 as bench
from nextai_autoresearch.candidates.learned_macro_operator_dag import Candidate as Shared
from nextai_autoresearch.candidates.macro_operator_dag_core import CONSTANTS, MacroOperatorDAG
from nextai_autoresearch.candidates.source_identical_frozen_macro_operator_dag import Candidate as Frozen
from nextai_autoresearch.candidates.source_identical_rebuild_macro_operator_dag import Candidate as Rebuild
from nextai_autoresearch.operator_experience_contract import Observation, Query, Term, canonical_table


def _term(depth: int = 8):
    tables = bench._run_cell.__globals__["_tables"](1_501_103, 1103)
    return bench._run_cell.__globals__["_term"](bench.TEST_SEQUENCES[depth], tables, 91, 0)


def _copy(term: Term) -> Term:
    if term.table is not None:
        return Term(term.node_id + 7, table=tuple(list(term.table)))
    assert term.left is not None and term.right is not None
    return Term(term.node_id + 7, left=_copy(term.left), right=_copy(term.right))


def test_roles_share_one_source_constants_and_only_mode_differs() -> None:
    assert Shared.__mro__[1] is Rebuild.__mro__[1] is Frozen.__mro__[1] is MacroOperatorDAG
    assert Shared.CONSTANTS == Rebuild.CONSTANTS == Frozen.CONSTANTS == CONSTANTS
    assert {Shared.MODE, Rebuild.MODE, Frozen.MODE} == {"persist", "rebuild", "frozen"}


def test_threshold_two_admits_exact_macro_without_object_identity() -> None:
    term = _term(4)
    target = canonical_table(term)[0][7]
    learner = Shared(0)
    query = Query(term, 7)
    assert learner.query(query, 8) == target
    learner.update(Observation(query, target))
    assert learner.query(query, 8) == target
    assert not learner.last_cache_hit
    learner.update(Observation(query, target))
    copied = _copy(term)
    assert learner.query(Query(copied, 7), 8) == target
    assert learner.last_cache_hit


def test_persistence_reduces_work_while_rebuild_and_frozen_remain_exact() -> None:
    term = _term()
    target = canonical_table(term)[0][11]
    roles = [Shared(0), Rebuild(0), Frozen(0)]
    for learner in roles:
        query = Query(term, 11)
        learner.update(Observation(query, target))
        learner.update(Observation(query, target))
        assert learner.query(query, 8) == target
    shared, rebuild, frozen = roles
    assert shared.last_cache_hit and rebuild.last_cache_hit and not frozen.last_cache_hit
    assert shared.last_ops < frozen.last_ops < rebuild.last_ops
    assert shared.state_bytes() > frozen.state_bytes()
