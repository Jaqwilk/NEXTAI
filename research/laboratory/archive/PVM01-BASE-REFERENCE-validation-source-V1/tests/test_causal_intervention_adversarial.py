from nextai_autoresearch.benchmarks.causal_intervention_adversarial_v2 import (
    make_world,
    run_trial,
    training_episodes,
)
from nextai_autoresearch.causal_adversarial_core import RobustLocalCausal


def test_robust_learner_recovers_main_and_abstains_on_clones() -> None:
    for seed in (1103, 2207, 3301):
        world = make_world(8, seed)
        candidate = RobustLocalCausal(seed)
        candidate.fit((world.pools, training_episodes(world, seed)), 8, 8)
        assert all(candidate.models[node] == world.models[node] for node in world.main_nodes)
        assert all(candidate.models[node] is None for node in world.ambiguous_nodes)


def test_irrelevant_k_does_not_change_main_training_data() -> None:
    small, large = make_world(8, 1103), make_world(128, 1103)
    small_data, large_data = training_episodes(small, 1103), training_episodes(large, 1103)
    assert small.models[:18] == large.models[:18]
    assert all(left[2][:18] == right[2][:18] for left, right in zip(small_data, large_data))


def test_adversarial_trial_separates_invariance_from_controls() -> None:
    robust = run_trial("robust_local_causal", 8, 6, 12, 1103, 8)
    noninvariant = run_trial("noninvariant_local_causal", 8, 6, 12, 1103, 8)
    observed = run_trial("adversarial_observational", 8, 6, 12, 1103, 8)
    assert robust["accuracy"] >= 0.95
    assert robust["main_structure_accuracy"] == robust["ambiguous_abstention_rate"] == 1.0
    assert noninvariant["main_structure_accuracy"] < robust["main_structure_accuracy"]
    assert observed["accuracy"] <= 0.75


def test_local_execution_ignores_dormant_mechanisms() -> None:
    small = run_trial("robust_local_causal", 8, 6, 6, 1103, 8)
    large = run_trial("robust_local_causal", 128, 6, 6, 1103, 8)
    dense = run_trial("robust_dense_causal", 128, 6, 6, 1103, 8)
    assert small["mean_query_ops"] == large["mean_query_ops"]
    assert small["mean_visited_nodes"] == large["mean_visited_nodes"]
    assert large["mean_query_ops"] < dense["mean_query_ops"] * 0.4
