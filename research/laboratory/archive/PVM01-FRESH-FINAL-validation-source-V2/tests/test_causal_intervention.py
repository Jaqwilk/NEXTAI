from nextai_autoresearch.benchmarks.causal_intervention_v1 import (
    make_world,
    run_trial,
    training_corpus,
)
from nextai_autoresearch.causal_core import LearnedLocalCausal


def test_chain_is_identified_from_single_interventions() -> None:
    world = make_world(8, 1103)
    candidate = LearnedLocalCausal(1103)
    candidate.fit(training_corpus(world), 8, 6)
    assert (candidate.parents, candidate.biases, candidate.order) == (
        world.parents,
        world.biases,
        world.order,
    )


def test_ood_double_interventions_separate_factorization_from_lookup() -> None:
    learned = run_trial("learned_local_causal", 8, 4, 8, 1103, 6)
    observed = run_trial("observational_conditioning", 8, 4, 8, 1103, 6)
    memorized = run_trial("intervention_memorizer", 8, 4, 8, 1103, 6)
    assert learned["accuracy"] == learned["structure_accuracy"] == 1.0
    assert observed["accuracy"] == memorized["accuracy"] == 0.5


def test_local_query_ignores_irrelevant_chain_tail() -> None:
    small = run_trial("learned_local_causal", 8, 4, 4, 1103, 6)
    large = run_trial("learned_local_causal", 32, 4, 4, 1103, 6)
    dense = run_trial("learned_dense_causal", 32, 4, 4, 1103, 6)
    assert small["mean_query_ops"] == large["mean_query_ops"]
    assert small["mean_visited_nodes"] == large["mean_visited_nodes"] == 5.0
    assert large["mean_query_ops"] < dense["mean_query_ops"] * 0.4
