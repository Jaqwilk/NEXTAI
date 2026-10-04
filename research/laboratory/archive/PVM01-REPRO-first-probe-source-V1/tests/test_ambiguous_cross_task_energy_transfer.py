from nextai_autoresearch.benchmarks.ambiguous_cross_task_energy_transfer_v1 import (
    WIDTH, make_tasks, make_world, run_trial,
)
from nextai_autoresearch.parity_energy_core import ExactAffineSpan, ParallelParityEnergy


def test_world_is_a_hidden_distance_32_affine_family() -> None:
    world = make_world(8, 1103)
    assert len(world.full_codebook) == 64
    assert len(world.factors) == 651
    distances = [sum(a != b for a, b in zip(left, right))
                 for index, left in enumerate(world.codewords)
                 for right in world.codewords[index + 1:]]
    assert set(distances) == {32}


def test_queries_are_unstored_and_have_exact_registered_corruption() -> None:
    world = make_world(32, 1103)
    for depth in (1, 4, 6):
        for task in make_tasks(world, depth, 1103, 8):
            assert task.target not in world.patterns
            assert sum(a != b for a, b in zip(task.query.state, task.target)) == depth
            assert sum(a != b for a, b in zip(task.near_query.state, task.target)) == depth


def test_training_recovers_rank_and_all_true_factors() -> None:
    world = make_world(8, 1103)
    exact, energy = ExactAffineSpan(), ParallelParityEnergy()
    exact.fit(world.patterns, WIDTH, 6)
    energy.fit(world.patterns, WIDTH, 6)
    assert exact.affine_rank == 6 and len(exact.codes) == 64
    assert energy.factor_count == len(world.factors) == 651
    assert energy.factors == world.factors


def test_parallel_and_exact_recover_deep_heldout_codes() -> None:
    exact = run_trial("exact_affine_span_decoder", 8, 6, 8, 1103, 6)
    parallel = run_trial("learned_parallel_parity_energy", 8, 6, 8, 1103, 6)
    for result in (exact, parallel):
        assert result["accuracy"] == result["near_equivalent_accuracy"] == 1.0
        assert result["spurious_attractor_rate"] == 0.0
    assert parallel["mean_iterations"] == 1.0
    assert exact["state_bytes"] < parallel["state_bytes"]
    assert exact["workload_ops"] < parallel["workload_ops"]


def test_nearest_memory_cannot_return_unstored_targets() -> None:
    assert run_trial("nearest_code_memory", 32, 6, 8, 1103, 6)["accuracy"] == 0.0
