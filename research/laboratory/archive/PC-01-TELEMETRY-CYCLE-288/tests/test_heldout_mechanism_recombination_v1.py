from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v1 as bench
from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v2 as bench_v2
from nextai_autoresearch.benchmarks import heldout_mechanism_recombination_v3 as bench_v3
from nextai_autoresearch.mechanism_recombination_contract import PublicQuery
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


CANDIDATES = [
    "shared_latent_mechanism_library",
    "independent_latent_mechanism_library",
    "no_cross_mechanism_factorizer",
    "unigram_recombination",
    "markov5_recombination",
    "nearest_template_recombination",
    "exact_mdl_module_library",
    "oracle_composition_graph",
]
METRICS = [
    "accuracy", "minimum_combination_accuracy", "data_acquisition_ops",
    "fit_ops", "meta_fit_ops", "mean_query_ops", "update_ops",
    "state_bytes", "peak_state_bytes", "mean_bytes_touched",
    "workload_ops", "workload_ops_r16",
]


def _plan() -> dict:
    plan = copy.deepcopy(load_json(
        project_root() / "research" / "plans" / "EXP-20260830-0053.json"
    ))
    plan["benchmark"] = bench.BENCHMARK_VERSION
    plan["candidates"] = list(CANDIDATES)
    plan["primary_metrics"] = list(METRICS)
    plan["metric_directions"] = {
        metric: "maximize" if metric in {"accuracy", "minimum_combination_accuracy"}
        else "minimize"
        for metric in METRICS
    }
    plan.pop("masked_refinement_protocol")
    plan["mechanism_recombination_protocol"] = {
        "state_count": 144,
        "mechanism_source_seed": 1103,
        "source_mechanisms": [
            "program_table", "predictive_transition_outcome", "local_dynamics_rule"
        ],
        "train_compositions": [
            "A", "B", "C", "AA", "AB", "AC", "BA", "BB", "BC", "CA", "CC"
        ],
        "heldout_compositions": ["CB"],
        "runner_random_state_conjugation": True,
        "equal_public_shapes": True,
        "shared_candidate": CANDIDATES[0],
        "independent_ablation": CANDIDATES[1],
        "no_cross_mechanism_ablation": CANDIDATES[2],
        "classical_baselines": CANDIDATES[3:],
        "declared_horizons": [1, 4, 16],
        "state_budget_bytes": 4_194_304,
        "invalidation_rules": [
            "Invalidate on any training and held-out combination overlap.",
            "Invalidate on any module or source-family label exposure.",
            "Invalidate when public shapes classify composition above chance plus 0.10.",
            "Invalidate when scoring randomness exists before the runner audit.",
            "Invalidate on target leakage post-score tuning or integrity change.",
        ],
    }
    return plan


def test_public_boundary_is_balanced_anonymous_and_disjoint() -> None:
    public, privileged, queries, audit = bench._training(8, 6, 8, 1_500_001, 1103)
    assert len(public.training_worlds) == 33
    assert len(public.test_worlds) == 1
    assert all(len(world.support) == 8 and len(world.examples) == 8
               for world in public.training_worlds)
    assert len(public.test_worlds[0].support) == 8 and len(queries) == 8
    assert all(isinstance(query, PublicQuery) for query, _ in queries)
    assert set(audit["train_compositions"]).isdisjoint({audit["heldout_composition"]})
    assert not hasattr(public.test_worlds[0], "composition")
    assert not hasattr(privileged.public.test_worlds[0], "source_family")
    profiles = {
        (len(world.support), len(world.examples),
         type(world.support[0].source), type(world.support[0].target))
        for world in public.training_worlds
    }
    assert len(profiles) == 1
    assert {pair.source for pair in public.test_worlds[0].support}.isdisjoint(
        {query.source for query, _ in queries}
    )


def test_scoring_seed_changes_opaque_labels_and_partitions() -> None:
    first = bench._training(8, 4, 8, 1_500_001, 1103)
    second = bench._training(8, 4, 8, 1_500_002, 1103)
    assert first[3]["maps"][bench.HELDOUT_COMPOSITION] != second[3]["maps"][bench.HELDOUT_COMPOSITION]
    assert first[3]["support_states"] != second[3]["support_states"]
    with pytest.raises(ValueError, match="seed collision"):
        bench._training(8, 1, 8, 1103, 1103)


@pytest.mark.parametrize("size", [8, 32])
def test_development_controls_fail_and_composition_oracle_is_exact(size: int) -> None:
    for seed in (1103 + 1_000_000, 2207 + 1_000_000, 3301 + 1_000_000,
                 4409 + 1_000_000, 5519 + 1_000_000):
        gate = bench.simple_control_gate(size, 8, seed, 1103)
        assert gate["unigram"] < 0.50
        assert gate["markov_upper_bound"] < 0.50
        assert gate["nearest_template"] < 0.50
        assert gate["matching_compositions"] == 1.0
        assert gate["composition_oracle"] == 1.0


def test_plan_schema_requires_candidates_protocol_and_full_costs() -> None:
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    plan["primary_metrics"].remove("meta_fit_ops")
    del plan["metric_directions"]["meta_fit_ops"]
    with pytest.raises(ValidationError, match="does not contain"):
        validate_document("experiment_plan", plan, project_root())


def test_plan_schema_rejects_changed_holdout_or_state_count() -> None:
    plan = _plan()
    plan["mechanism_recombination_protocol"]["heldout_compositions"] = ["BC"]
    with pytest.raises(ValidationError, match="was expected"):
        validate_document("experiment_plan", plan, project_root())


def test_plan_schema_preserves_v2_roles_and_requires_v3_roles() -> None:
    historical = load_json(
        project_root() / "research" / "plans" / "EXP-20260830-0056.json"
    )
    validate_document("experiment_plan", historical, project_root())

    future = _plan()
    future["benchmark"] = bench_v3.BENCHMARK_VERSION
    replacements = {
        "shared_latent_mechanism_library": "operator_algebra_completion",
        "independent_latent_mechanism_library": "operator_algebra_independent",
        "no_cross_mechanism_factorizer": "operator_algebra_no_relations",
    }
    future["candidates"] = [replacements.get(item, item) for item in future["candidates"]]
    for role in ("shared_candidate", "independent_ablation", "no_cross_mechanism_ablation"):
        future["mechanism_recombination_protocol"][role] = replacements[
            future["mechanism_recombination_protocol"][role]
        ]
    validate_document("experiment_plan", future, project_root())

    wrong_v3 = copy.deepcopy(future)
    wrong_v3["mechanism_recombination_protocol"]["shared_candidate"] = CANDIDATES[0]
    wrong_v3["candidates"][0] = CANDIDATES[0]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", wrong_v3, project_root())

    wrong_v2 = copy.deepcopy(historical)
    wrong_v2["mechanism_recombination_protocol"]["shared_candidate"] = replacements[CANDIDATES[0]]
    wrong_v2["candidates"][0] = replacements[CANDIDATES[0]]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", wrong_v2, project_root())
    plan = _plan()
    plan["mechanism_recombination_protocol"]["state_count"] = 145
    with pytest.raises(ValidationError, match="144 was expected"):
        validate_document("experiment_plan", plan, project_root())


def test_v2_complete_result_serializes_minimum_combination_accuracy() -> None:
    result = copy.deepcopy(load_json(
        project_root() / "research" / "results" / "EXP-20260830-0053.json"
    ))
    result["benchmark"] = bench_v2.BENCHMARK_VERSION
    for candidate in result["candidates"]:
        candidate["summary"]["minimum_combination_accuracy"] = (
            candidate["summary"].get("accuracy")
        )
    validate_document("experiment_result", result, project_root())
