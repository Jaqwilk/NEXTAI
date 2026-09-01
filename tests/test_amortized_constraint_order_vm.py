from nextai_autoresearch.benchmarks.program_induction_from_whole_io_v2 import make_tasks, training_corpus
from nextai_autoresearch.candidates.amortized_constraint_order_vm_core import AmortizedConstraintOrderVM
from nextai_autoresearch.candidates.enumerative_mdl_vm import Candidate as Enumerative
from nextai_autoresearch.candidates.learned_amortized_constraint_order_vm import Candidate as Meta
from nextai_autoresearch.candidates.source_identical_frozen_constraint_order_vm import Candidate as Frozen
from nextai_autoresearch.candidates.source_identical_support_only_constraint_order_vm import Candidate as Support
from nextai_autoresearch.whole_io_vm_core import PROGRAMS, support_key


def _fit(candidate, seed=1103):
    candidate.fit(training_corpus(8, 8, seed), 8, 6)
    return candidate


def test_all_roles_share_one_complete_core_and_frozen_constants() -> None:
    assert all(issubclass(role, AmortizedConstraintOrderVM) for role in (Meta, Support, Frozen))
    assert {Meta(0).mode, Support(0).mode, Frozen(0).mode} == {"meta", "support", "frozen"}


def test_all_orders_match_complete_mdl_on_reference_and_adversarial_supports() -> None:
    tasks = make_tasks(8, 6, 2207, 6)
    for task in tasks:
        key, _ = support_key(task.query.support)
        expected, _ = Enumerative._induce(key)
        for role in (Meta, Support, Frozen):
            candidate = _fit(role(1103))
            candidate.query(task.query, 6)
            assert candidate.last_program == expected
            assert candidate.last_program in PROGRAMS


def test_first_incumbent_cannot_replace_the_proven_optimum() -> None:
    task = make_tasks(8, 6, 3301, 1)[0]
    candidate = _fit(Frozen(1103))
    candidate.query(task.query, 6)
    key, _ = support_key(task.query.support)
    expected, _ = Enumerative._induce(key)
    assert candidate.last_program == expected
    assert candidate.last_program != PROGRAMS[0]
    assert candidate.last_nodes > 9


def test_preregistered_orders_change_search_nodes_on_development_fixture() -> None:
    tasks = make_tasks(8, 6, 4409, 8)
    counts = []
    for role in (Meta, Support, Frozen):
        candidate = _fit(role(1103))
        role_counts = []
        for task in tasks:
            candidate.query(task.query, 6)
            role_counts.append(candidate.last_nodes)
        counts.append(tuple(role_counts))
    assert len(set(counts)) > 1
