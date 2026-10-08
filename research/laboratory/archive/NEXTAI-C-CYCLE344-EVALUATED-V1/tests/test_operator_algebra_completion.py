from __future__ import annotations

from nextai_autoresearch.candidates.operator_algebra_core import (
    close_relations, infer_equations,
)
from nextai_autoresearch.candidates.operator_algebra_completion import Candidate
from nextai_autoresearch.candidates.operator_algebra_no_relations import (
    Candidate as NoRelations,
)
from nextai_autoresearch.mechanism_recombination_contract import (
    Pair, PublicQuery, PublicTraining, TestWorld as RecombinationTestWorld,
    TrainingWorld,
)


def _relabel(mapping: dict[int, int], permutation: tuple[int, ...]) -> dict[int, int]:
    return {permutation[source]: permutation[target] for source, target in mapping.items()}


def test_relation_closure_recovers_two_missing_composition_edges_equivariantly() -> None:
    # AA=A(A(.)) reveals A(7); AB=B(A(.)) then reveals B(0).
    a = (1, 2, 3, 4, 5, 6, 7, 0)
    b = (2, 5, 7, 0, 6, 1, 3, 4)
    compose = lambda first, second: tuple(second[first[x]] for x in range(8))
    maps = [
        {x: a[x] for x in range(7)},
        {x: b[x] for x in range(1, 8)},
        dict(enumerate(compose(a, a))),
        dict(enumerate(compose(a, b))),
    ]
    assert 7 not in maps[0] and 0 not in maps[1]
    equations = infer_equations(maps)
    assert (0, 0, 2) in equations and (0, 1, 3) in equations
    closed, _ = close_relations(maps, equations)
    assert closed[0][7] == 0 and closed[1][0] == 2
    assert closed[1][closed[0][7]] == 2

    permutation = (5, 2, 7, 0, 6, 3, 1, 4)
    relabeled = [_relabel(mapping, permutation) for mapping in maps]
    relabeled_closed, _ = close_relations(relabeled, infer_equations(relabeled))
    assert relabeled_closed == [_relabel(mapping, permutation) for mapping in closed]

    order = (3, 1, 0, 2)
    shuffled = [maps[index] for index in order]
    shuffled_closed, _ = close_relations(shuffled, infer_equations(shuffled))
    assert shuffled_closed == [closed[index] for index in order]

    worlds = tuple(
        TrainingWorld(tuple(Pair(source, target) for source, target in mapping.items()), ())
        for mapping in maps
    )
    facts = PublicTraining(
        worlds, (RecombinationTestWorld(9, (Pair(0, 3), Pair(1, 7))),), 0
    )
    query = PublicQuery(9, 7)
    learner, control = Candidate(), NoRelations()
    learner.fit(facts, 8, 1)
    control.fit(facts, 8, 1)
    assert learner.query(query, 1) == 2
    assert control.query(query, 1) != 2
