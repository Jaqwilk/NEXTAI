import math

from nextai_autoresearch.benchmarks import continuous_local_cellular_v1 as bench
from nextai_autoresearch.candidates.evolved_anonymous_local_rule_program import Candidate as TrueFitness
from nextai_autoresearch.candidates.population_local_rule_core import (
    CHANNELS, COEFFICIENTS, MAX_TERMS, OUTPUT_BOUND, PROGRAM_COUNT,
    PopulationLocalRule, evaluate_program, program_operation_count, term_count,
)
from nextai_autoresearch.candidates.source_identical_frozen_population_local_rule_program import Candidate as Frozen
from nextai_autoresearch.candidates.source_identical_shuffled_fitness_local_rule_program import Candidate as Shuffled


def test_all_roles_share_exact_population_language_and_proposals() -> None:
    roles = (TrueFitness(17), Shuffled(17), Frozen(17))
    assert all(isinstance(role, PopulationLocalRule) for role in roles)
    assert [role.mode for role in roles] == ["true", "shuffled", "frozen"]
    assert (PROGRAM_COUNT, MAX_TERMS, OUTPUT_BOUND) == (256, 3, 1.5)
    assert COEFFICIENTS == (-1.0, -0.5, -0.25, 0.25, 0.5, 1.0)
    assert roles[0].populations == roles[1].populations == roles[2].populations
    assert roles[0].shuffles == roles[1].shuffles == roles[2].shuffles
    assert [term_count(index) for index in (0, 63, 64, 159, 160, 255)] == [1, 1, 2, 2, 3, 3]
    for output, population in enumerate(roles[0].populations):
        assert population[0] == ((0, CHANNELS + output, 0, 1.0),)


def test_true_shuffled_and_frozen_selection_use_only_score_assignment() -> None:
    world = bench.make_world(1103)
    roles = (TrueFitness(23), Shuffled(23), Frozen(23))
    for role in roles:
        role.fit(world.training[:8], 64, 16)
    assert roles[0].scores == roles[1].scores == roles[2].scores
    for output in range(CHANNELS):
        expected = min(range(PROGRAM_COUNT), key=lambda index: (roles[0].scores[output][index], index))
        assert roles[0].selected[output] == expected
        assert sorted(roles[1].assigned_scores(output)) == sorted(roles[1].scores[output])
    assert roles[2].selected == [0] * CHANNELS
    assert roles[0].fit_ops == roles[1].fit_ops == roles[2].fit_ops


def test_program_probabilities_are_finite_clipped_and_operation_count_is_exact() -> None:
    candidate = TrueFitness(31)
    raw = tuple((index - 5) / 3 for index in range(12))
    for population in candidate.populations:
        for program in (population[0], population[64], population[160]):
            value, operations = evaluate_program(program, raw)
            assert math.isfinite(value) and abs(value) <= OUTPUT_BOUND
            assert operations == program_operation_count(program)


def test_frozen_is_persistence_zero_is_preserved_and_update_is_fully_charged() -> None:
    world = bench.make_world(1103)
    candidate = Frozen(41)
    candidate.fit(world.training[:8], 64, 16)
    vector = (0.2, -0.4, 0.6, -0.8)
    task = bench.Task(64, 7, 7, ((7, vector),))
    assert candidate.query(task, 8) == vector
    zero = bench.Task(64, 7, 7, ((7, (0.0,) * CHANNELS),))
    assert candidate.query(zero, 8) == (0.0,) * CHANNELS
    before = [scores.copy() for scores in candidate.scores]
    candidate.update(world.training[-1], None)
    assert candidate.selected == [0] * CHANNELS
    assert candidate.scores != before and candidate.update_ops > 0


def test_sparse_query_work_is_independent_of_dormant_ring_size() -> None:
    world = bench.make_world(1103)
    candidate = TrueFitness(53)
    candidate.fit(world.training[:8], 64, 16)
    work = []
    for size in (64, 256, 1024):
        candidate.query(bench.make_task(world, size, 16, 4409, 0), 16)
        work.append(candidate.last_ops)
    assert work[0] == work[1] == work[2]
