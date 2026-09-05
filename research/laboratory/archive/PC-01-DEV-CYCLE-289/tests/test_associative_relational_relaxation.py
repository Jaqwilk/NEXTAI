from nextai_autoresearch.benchmarks.associative_relational_relaxation_v1 import (
    BLOCKS,
    latent_state,
    make_tasks,
    make_world,
    run_trial,
)


def test_world_is_balanced_and_queries_are_heldout_with_disjoint_corruptions() -> None:
    for size in (8, 32):
        world = make_world(size, 1103)
        for component in world.components:
            values = [pattern[component[0][0]] ^ component[0][1] for pattern in world.patterns]
            assert sum(values) == size // 2
        for depth in (1, 4, 6):
            for query, target in make_tasks(world, depth, 1103, 8):
                assert target not in world.patterns
                assert latent_state(world, target) is not None
                changed_blocks = sum(any(query.state[pos] != target[pos] for pos, _ in component) for component in world.components)
                assert changed_blocks == depth <= BLOCKS


def test_registered_leakage_controls_do_not_complete_heldout_patterns() -> None:
    for candidate in ("random_attractor_guess", "bit_majority_attractor", "nearest_stored_attractor"):
        for depth in (1, 4, 6):
            assert run_trial(candidate, 8, depth, 8, 1103, 6)["accuracy"] <= 0.125


def test_hopfield_sequential_parallel_and_oracle_recover_compositions() -> None:
    for candidate in (
        "classical_hopfield_attractor",
        "sequential_energy_repair",
        "learned_parallel_energy",
        "oracle_relational_energy",
    ):
        for size in (8, 32):
            for depth in (1, 4, 6):
                result = run_trial(candidate, size, depth, 8, 1103, 6)
                assert result["accuracy"] == result["heldout_composition_accuracy"] == 1.0
                assert result["spurious_attractor_rate"] == 0.0


def test_parallel_energy_has_registered_cost_and_dynamics_signature() -> None:
    for depth in (4, 6):
        local_small = run_trial("learned_parallel_energy", 8, depth, 8, 1103, 6)
        local_large = run_trial("learned_parallel_energy", 32, depth, 8, 1103, 6)
        hopfield = run_trial("classical_hopfield_attractor", 8, depth, 8, 1103, 6)
        sequential = run_trial("sequential_energy_repair", 8, depth, 8, 1103, 6)
        assert local_small["mean_query_ops"] == local_large["mean_query_ops"]
        assert local_small["energy_monotonic_rate"] == 1.0
        assert local_small["mean_iterations"] == 1.0
        assert local_small["mean_active_updates"] == depth
        assert local_small["mean_query_ops"] <= 0.35 * hopfield["mean_query_ops"]
        assert local_small["mean_query_ops"] <= 0.50 * sequential["mean_query_ops"]
