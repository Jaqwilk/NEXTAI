from nextai_autoresearch.benchmarks.associative_relational_relaxation_adversarial_v2 import (
    BLOCKS,
    BLOCK_WIDTHS,
    make_tasks,
    make_world,
    relation_bounds,
    run_trial,
)


def test_adversarial_world_has_registered_noise_and_relation_gap() -> None:
    for seed in (1103, 2207, 3301):
        for size in (8, 32, 128):
            world = make_world(size, seed)
            assert tuple(map(len, world.components)) == BLOCK_WIDTHS
            assert len(set(world.latent_patterns)) == size
            assert all(sum(left != right for left, right in zip(noisy, clean)) == 2 for noisy, clean in zip(world.patterns, world.clean_patterns))
            assert any(sum(pattern[index] for pattern in world.latent_patterns) != size / 2 for index in range(BLOCKS))
            within, cross = relation_bounds(world)
            assert within >= 0.75
            assert cross <= 0.625


def test_adversarial_queries_are_clean_heldout_compositions() -> None:
    world = make_world(128, 1103)
    for depth in (1, 4, 6, 8):
        for query, target in make_tasks(world, depth, 1103, 12):
            assert target not in world.clean_patterns
            changed = [sum(query.state[position] != target[position] for position, _ in component) for component in world.components]
            assert sum(value == 1 for value in changed) == depth
            assert all(value in (0, 1) for value in changed)


def test_registered_controls_do_not_solve_noisy_heldout_compositions() -> None:
    for candidate in ("random_attractor_guess", "bit_majority_attractor", "nearest_stored_attractor"):
        for size in (8, 128):
            assert run_trial(candidate, size, 8, 12, 1103, 8)["accuracy"] <= 0.10


def test_robust_energy_recovers_and_incremental_schedule_is_counted() -> None:
    for size in (8, 128):
        parallel = run_trial("robust_parallel_energy", size, 8, 12, 1103, 8)
        sequential = run_trial("incremental_sequential_energy", size, 8, 12, 1103, 8)
        oracle = run_trial("oracle_relational_energy", size, 8, 12, 1103, 8)
        for result in (parallel, sequential, oracle):
            assert result["accuracy"] == result["heldout_composition_accuracy"] == 1.0
            assert result["spurious_attractor_rate"] == 0.0
            assert result["energy_monotonic_rate"] == 1.0
        assert parallel["mean_iterations"] == 1.0
        assert parallel["mean_active_updates"] == 8.0
        assert sequential["mean_iterations"] == 8.0
        assert sequential["mean_query_ops"] < parallel["mean_query_ops"]


def test_robust_parallel_has_registered_k_and_hopfield_signature() -> None:
    small = run_trial("robust_parallel_energy", 8, 8, 12, 1103, 8)
    large = run_trial("robust_parallel_energy", 128, 8, 12, 1103, 8)
    hopfield = run_trial("classical_hopfield_attractor", 8, 8, 12, 1103, 8)
    assert small["mean_query_ops"] == large["mean_query_ops"]
    assert small["mean_query_ops"] <= 0.12 * hopfield["mean_query_ops"]
    assert 0 < small["fit_ops"] < large["fit_ops"]
