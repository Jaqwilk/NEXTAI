from __future__ import annotations

from nextai_autoresearch.candidates.exact_mdl_module_library import Candidate as MDL
from nextai_autoresearch.candidates.independent_latent_mechanism_library import Candidate as Independent
from nextai_autoresearch.candidates.markov5_recombination import Candidate as Markov5
from nextai_autoresearch.candidates.nearest_template_recombination import Candidate as Nearest
from nextai_autoresearch.candidates.no_cross_mechanism_factorizer import Candidate as NoCross
from nextai_autoresearch.candidates.oracle_composition_graph import Candidate as Oracle
from nextai_autoresearch.candidates.shared_latent_mechanism_library import Candidate as Shared
from nextai_autoresearch.candidates.unigram_recombination import Candidate as Unigram
from nextai_autoresearch.mechanism_recombination_contract import (
    Pair, PrivilegedQuery, PrivilegedTraining, PublicQuery, PublicTraining,
    TestWorld as RecombinationTestWorld, TrainingWorld,
)


def _public(maps: list[dict[int, int]], support: dict[int, int]) -> PublicTraining:
    worlds = tuple(
        TrainingWorld(tuple(Pair(key, value) for key, value in mapping.items()), ())
        for mapping in maps
    )
    return PublicTraining(worlds, (RecombinationTestWorld(91, tuple(
        Pair(key, value) for key, value in support.items()
    )),), sum(2 * len(mapping) for mapping in maps) + 2 * len(support))


def _library_fixture() -> PublicTraining:
    first = {0: 1, 3: 4, 6: 7}
    second = {1: 2, 4: 5, 7: 8}
    distractors = [
        {0: 20 + index, 3: 30 + index, 6: 40 + index}
        for index in range(9)
    ]
    return _public([mapping for item in (first, second, *distractors)
                    for mapping in (item, item, item)], {0: 2})


def test_unigram_recombination_is_global_target_mode() -> None:
    learner = Unigram(0)
    learner.fit(_public([{0: 7, 1: 7, 2: 4}], {}), 3, 1)
    assert learner.query(PublicQuery(91, 99), 1) == 7


def test_markov5_recombination_rolls_observed_transition_five_steps() -> None:
    learner = Markov5(0)
    chain = {index: index + 1 for index in range(6)}
    learner.fit(_public([chain], {}), 7, 5)
    assert learner.query(PublicQuery(91, 0), 5) == 5
    assert learner.last_ops == 5


def test_nearest_template_uses_support_mismatch_not_world_order() -> None:
    learner = Nearest(0)
    learner.fit(_public([{0: 4, 9: 10}, {0: 5, 9: 11}], {0: 5}), 12, 1)
    assert learner.query(PublicQuery(91, 9), 1) == 11


def test_exact_mdl_search_finds_recursive_two_module_composition() -> None:
    learner = MDL(0)
    learner.fit(_library_fixture(), 144, 1)
    assert learner.query(PublicQuery(91, 3), 1) == 5
    assert learner.meta_fit_ops > learner.fit_ops


def test_shared_library_composes_while_no_cross_and_independent_do_not() -> None:
    public = _library_fixture()
    shared, independent, no_cross = Shared(0), Independent(0), NoCross(0)
    for learner in (shared, independent, no_cross):
        learner.fit(public, 144, 1)
    query = PublicQuery(91, 3)
    assert shared.query(query, 1) == 5
    assert independent.query(query, 1) != 5
    assert no_cross.query(query, 1) != 5


def test_oracle_composition_graph_is_privileged_and_exact() -> None:
    public = _public([{0: 1}], {0: 2})
    learner = Oracle(0)
    learner.fit(PrivilegedTraining(public), 144, 1)
    query = PublicQuery(91, 80)
    assert learner.query(PrivilegedQuery(query, 123), 6) == 123
