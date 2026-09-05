from __future__ import annotations

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v4 as bench
from nextai_autoresearch.candidates.experience_operator_compiler_core import (
    CONSTANTS, ExperienceOperatorCompiler,
)
from nextai_autoresearch.config import load_config
from nextai_autoresearch.operator_experience_contract import Mutation, Query, canonical_table


SEED = 1_501_103


def _fit(scope: str = "pooled") -> ExperienceOperatorCompiler:
    candidate = ExperienceOperatorCompiler(SEED)
    candidate.SCOPE = scope
    candidate.fit(bench.make_training(32, SEED, 1103), 32, 16)
    return candidate


def test_probe_learning_validates_pairs_and_covers_training_negatives() -> None:
    candidate = _fit()
    training = bench.make_training(32, SEED, 1103)
    assert len(candidate.probes) == CONSTANTS[0]
    for pair in training.pairs:
        left, right = canonical_table(pair.left)[0], canonical_table(pair.right)[0]
        if pair.equivalent:
            assert left == right
        else:
            assert any(left[state] != right[state] for state in candidate.probes)


def test_shared_compiler_has_exact_declining_experience_curve() -> None:
    curves = []
    for size in (8, 32, 128):
        rows = [bench._run_cell("experience_operator_compiler", size, exposure, 8,
                                SEED, 1103, 4_194_304)
                for exposure in bench.EXPOSURES]
        assert all(row["minimum_combination_accuracy"] == 1.0 for row in rows)
        assert all(row["false_reuse_rate"] == 0.0 for row in rows)
        assert rows[0]["mean_warm_query_ops"] > rows[1]["mean_warm_query_ops"] > rows[2]["mean_warm_query_ops"]
        curves.append([row["mean_warm_query_ops"] for row in rows])
    assert curves[0] == curves[1] == curves[2]


def test_scope_ablations_share_core_and_do_not_pool_raw_reencodings() -> None:
    assert CONSTANTS == (3, (4, 16))
    for name in ("experience_operator_independent", "experience_operator_no_pairing"):
        rows = [bench._run_cell(name, 8, exposure, 2, SEED, 1103, 4_194_304)
                for exposure in bench.EXPOSURES]
        assert all(row["minimum_combination_accuracy"] == 1.0 for row in rows)
        assert all(row["reuse_coverage"] == 0.0 for row in rows)
        assert len({row["mean_warm_query_ops"] for row in rows}) == 1


def test_mutation_adds_new_operator_and_retains_old_without_global_refit() -> None:
    tables = bench._tables(SEED, 1103)
    old = bench._term(bench.TEST_SEQUENCE, tables, 91, 0)
    new = bench._term((*bench.TEST_SEQUENCE[:-1], "A"), tables, 93, 1)
    candidate = _fit()
    candidate.update(Mutation(old, new))
    state = 17
    assert candidate.query(Query(new, state), 16) == canonical_table(new)[0][state]
    assert candidate.query(Query(old, state), 16) == canonical_table(old)[0][state]
    assert candidate.update_ops > 0


def test_all_three_candidate_entries_pass_transitive_audit() -> None:
    config = load_config()
    for name in (
        "experience_operator_compiler", "experience_operator_independent",
        "experience_operator_no_pairing",
    ):
        result = audit_candidate(name, config)
        assert result.ok, result.problems
        assert any(path.name == "experience_operator_compiler_core.py" for path, _ in result.dependencies)
