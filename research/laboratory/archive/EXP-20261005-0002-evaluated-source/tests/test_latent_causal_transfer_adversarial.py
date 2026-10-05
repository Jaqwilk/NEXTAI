from nextai_autoresearch.benchmarks.latent_causal_transfer_adversarial_v2 import (
    make_tasks,
    make_world,
    run_trial,
)


def test_codes_are_unique_nonarithmetic_and_active_codes_are_k_stable() -> None:
    small, large = make_world(8, 1103), make_world(32, 1103)
    assert len(set(large.sensors)) == len(large.sensors)
    assert len(set(large.tokens)) == len(large.tokens)
    assert small.sensors[:20] == large.sensors[:20]
    assert small.tokens[:20] == large.tokens[:20]
    assert len(set(right - left for left, right in zip(small.sensors, small.sensors[1:]))) > 1


def test_every_cell_is_balanced_and_registered_shortcuts_are_bounded() -> None:
    for size in (8, 32):
        world = make_world(size, 1103)
        for depth in (1, 4, 6):
            tasks = make_tasks(world, depth, 1103, 8)
            assert sum(target for _, target in tasks) == 4
            for candidate in ("random_latent_independent", "latent_majority_guess", "latent_parity_shortcut"):
                assert run_trial(candidate, size, depth, 8, 1103, 6)["accuracy"] <= 0.625


def test_mixed_factorization_recovers_targets_structure_gates_and_ood_answers() -> None:
    for depth in (1, 4, 6):
        result = run_trial("latent_factorized_mixed", 8, depth, 8, 1103, 6)
        assert result["accuracy"] == result["ood_intervention_accuracy"] == 1.0
        assert result["target_mapping_accuracy"] == 1.0
        assert result["structure_accuracy"] == result["gate_accuracy"] == 1.0


def test_perception_grows_with_k_while_mixed_local_execution_is_stable() -> None:
    small = run_trial("latent_factorized_mixed", 8, 6, 8, 1103, 6)
    large = run_trial("latent_factorized_mixed", 32, 6, 8, 1103, 6)
    assert large["mean_perception_ops"] > small["mean_perception_ops"]
    assert large["mean_local_ops"] == small["mean_local_ops"]
