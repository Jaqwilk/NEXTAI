from nextai_autoresearch.benchmarks.noisy_nonexhaustive_causal_transfer_v3 import (
    make_tasks,
    make_world,
    run_trial,
    training_data,
)
from nextai_autoresearch.benchmarks.latent_causal_transfer_adversarial_v2 import (
    oracle_model,
    training_episodes,
)
from nextai_autoresearch.noisy_causal_core import learn_factorization


def test_training_is_noisy_sparse_and_contains_no_intervention_pairs() -> None:
    world = make_world(8, 1103)
    bundle, metrics = training_data(world, 1103, 6)
    episodes, examples = bundle
    assert 0.08 <= metrics["training_noise_rate"] <= 0.12
    assert metrics["intervention_context_coverage"] == 0.25
    assert metrics["intervention_target_coverage"] < 1.0
    assert metrics["training_pair_rate"] == 0.0
    assert all(len(query.interventions) <= 1 for query, _ in examples)
    assert any(episode.intervention_code is None for episode in episodes)


def test_scored_tasks_are_balanced_unseen_pairs() -> None:
    world = make_world(8, 1103)
    tasks = make_tasks(world, 6, 1103, 8)
    assert sum(target for _, target in tasks) == 4
    assert all(len(query.interventions) == 2 for query, _ in tasks)


def test_factorization_still_recovers_the_old_clean_complete_calibration() -> None:
    world = make_world(8, 1103)
    targets, parents, _, models, _ = learn_factorization(training_episodes(world, 1103, 8))
    true_parents, true_models, true_targets, _ = oracle_model(world)
    assert targets == dict(true_targets)
    assert parents == dict(true_parents)
    assert models == dict(true_models)


def test_full_oracle_is_exact_and_accounting_sums() -> None:
    result = run_trial("oracle_noisy_causal", 8, 6, 8, 1103, 6)
    assert result["accuracy"] == result["ood_intervention_accuracy"] == 1.0
    assert result["target_mapping_accuracy"] == result["structure_accuracy"] == result["gate_accuracy"] == 1.0
    assert result["mean_query_ops"] == result["mean_encoding_ops"] + result["mean_representation_ops"] + result["mean_local_ops"]


def test_dense_baseline_is_learned_and_returns_binary_answers() -> None:
    result = run_trial("dense_random_feature_causal", 8, 1, 8, 1103, 6)
    assert 0.0 <= result["accuracy"] <= 1.0
    assert result["fit_ops"] > 0
    assert result["mean_representation_ops"] > result["mean_encoding_ops"]
    assert result["state_bytes"] > 0
