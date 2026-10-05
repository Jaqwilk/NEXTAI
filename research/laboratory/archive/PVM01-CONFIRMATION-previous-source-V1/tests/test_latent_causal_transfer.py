from nextai_autoresearch.benchmarks.latent_causal_transfer_v1 import (
    make_world,
    representation,
    run_trial,
    training_episodes,
)
from nextai_autoresearch.latent_causal_core import FactorizedLatent, OracleRepresentation


def test_unknown_targets_and_active_structure_are_identifiable_with_missing_values() -> None:
    world = make_world(8, 1103)
    learner = FactorizedLatent(1103)
    learner.fit(training_episodes(world, 1103, 8), len(world.parents), 6)
    assert learner.token_targets == {
        world.tokens[node]: world.sensors[node] for node in range(len(world.parents))
    }
    assert all(
        learner.parents[world.sensors[node]]
        == tuple(world.sensors[parent] for parent in world.parents[node])
        for node in range(20)
    )


def test_factorization_composes_unseen_paired_interventions() -> None:
    learned = run_trial("latent_factorized_causal", 8, 6, 8, 1103, 6)
    raw = run_trial("raw_episode_predictor", 8, 6, 8, 1103, 6)
    assert learned["accuracy"] == learned["ood_intervention_accuracy"] == 1.0
    assert learned["target_mapping_accuracy"] == learned["structure_accuracy"] == 1.0
    assert raw["accuracy"] <= 0.75


def test_raw_observation_cost_grows_with_distractors_but_local_dynamics_do_not() -> None:
    small = run_trial("latent_factorized_causal", 8, 6, 8, 1103, 6)
    large = run_trial("latent_factorized_causal", 32, 6, 8, 1103, 6)
    raw = run_trial("raw_episode_predictor", 32, 6, 8, 1103, 6)
    assert large["mean_perception_ops"] > small["mean_perception_ops"]
    assert large["mean_local_ops"] == small["mean_local_ops"]
    assert large["mean_query_ops"] < raw["mean_query_ops"] * 0.2


def test_oracle_representation_still_learns_dynamics() -> None:
    world = make_world(8, 1103)
    learner = OracleRepresentation(1103)
    episodes = training_episodes(world, 1103, 8)
    learner.fit((representation(world), episodes), len(world.parents), 6)
    assert learner.fit_ops > 0
    assert len(learner.biases) == 18
