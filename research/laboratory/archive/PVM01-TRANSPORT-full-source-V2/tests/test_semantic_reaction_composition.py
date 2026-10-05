from nextai_autoresearch.benchmarks.semantic_reaction_composition_v1 import (
    make_task,
    make_world,
    react_once,
    run_trial,
)
from nextai_autoresearch.reaction_core import extract_rule


def test_training_is_unlabeled_local_and_withholds_one_rule() -> None:
    world = make_world(8, 1103)
    learned = dict(extract_rule(episode)[0] for episode in world.training)
    assert len(world.rules) == 16
    assert len(world.training) == len(learned) == 15
    assert world.heldout_key not in learned
    assert learned == {key: output for key, output in world.rules.items() if key != world.heldout_key}
    assert all(react_once(episode.before, world.rules) == episode.after for episode in world.training)


def test_queries_are_unseen_compositions_without_heldout_rule() -> None:
    for size in (8, 32):
        world = make_world(size, 1103)
        training_sources = {episode.before for episode in world.training}
        for depth in (1, 4, 6):
            for index in range(8):
                task = make_task(world, size, depth, 1103, index)
                assert task.source not in training_sources
                assert world.heldout_key not in task.rule_keys
                assert len(task.rule_keys) == depth


def test_random_and_trajectory_controls_do_not_solve_compositions() -> None:
    for candidate in ("random_reaction_guess", "reaction_trajectory_memorizer"):
        for depth in (1, 4, 6):
            assert run_trial(candidate, 8, depth, 8, 1103, 6)["accuracy"] <= 0.125


def test_rule_executors_recover_every_registered_cell() -> None:
    for candidate in (
        "learned_reaction_sweep",
        "learned_reaction_recurrent",
        "rete_reaction_engine",
        "learned_semantic_reactor",
        "oracle_reaction_engine",
    ):
        for size in (8, 32):
            for depth in (1, 4, 6):
                result = run_trial(candidate, size, depth, 8, 1103, 6)
                assert result["accuracy"] == result["heldout_composition_accuracy"] == 1.0
                assert result["observed_rule_accuracy"] == 1.0
                assert result["convergence_rate"] == 1.0
                assert result["oscillation_rate"] == 0.0


def test_semantic_reactor_is_sparse_but_matches_rete() -> None:
    for depth in (4, 6):
        reactor = run_trial("learned_semantic_reactor", 32, depth, 8, 1103, 6)
        rete = run_trial("rete_reaction_engine", 32, depth, 8, 1103, 6)
        sweep = run_trial("learned_reaction_sweep", 32, depth, 8, 1103, 6)
        assert reactor["mean_active_events"] == depth
        assert reactor["mean_full_scans"] == 1.0
        assert reactor["mean_query_ops"] < 0.5 * sweep["mean_query_ops"]
        assert reactor["mean_query_ops"] == rete["mean_query_ops"]
        assert reactor["mean_bytes_scanned"] == rete["mean_bytes_scanned"]


def test_dense_update_cost_grows_with_particle_count() -> None:
    small = run_trial("learned_semantic_reactor", 8, 4, 8, 1103, 6)
    large = run_trial("learned_semantic_reactor", 32, 4, 8, 1103, 6)
    assert small["continual_new_fact_accuracy"] == large["continual_new_fact_accuracy"] == 1.0
    assert small["continual_retention"] == large["continual_retention"] == 1.0
    assert 0 < small["update_ops"] < large["update_ops"]
