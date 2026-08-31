from nextai_autoresearch.candidates.relation_fragment_core import (
    CAPACITY,
    RelationFragmentGraphLearner,
    _Fragment,
)


def test_cap_can_omit_later_position_without_making_emission_partial() -> None:
    model = tuple(
        _Fragment(frozenset({(0, 0, 4, index)}), 0, 2,
                  ("scalar", float(index)), CAPACITY - index)
        for index in range(CAPACITY)
    )
    signature = model[0].edges
    for mode in ("shared", "independent"):
        candidate = RelationFragmentGraphLearner(7, mode=mode)
        assert candidate._emit(signature, model, ()) == (0.0, 0.0)
        assert len(candidate.last_composition_trace) == 2
