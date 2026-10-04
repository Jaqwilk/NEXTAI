from nextai_autoresearch.benchmarks.latent_entity_binding_retrieval_v1 import make_tasks, make_world, run_trial
from nextai_autoresearch.entity_binding_core import ContrastiveHash, HashIndex, stable_dimensions


def test_raw_facts_expose_no_entity_identifiers() -> None:
    world = make_world(8, 1103)
    assert set(world.facts[0].__dataclass_fields__) == {"source", "target", "value"}
    assert len({fact.value for fact in world.facts}) == 8


def test_analytic_and_contrastive_fit_recover_the_hidden_subspace() -> None:
    world = make_world(32, 1103)
    analytic, learned = HashIndex(), ContrastiveHash()
    analytic.fit(world.facts, 32, 6)
    learned.fit(world.facts, 32, 6)
    assert set(stable_dimensions(world.facts)) == set(world.stable)
    assert set(analytic.dimensions) == set(learned.dimensions) == set(world.stable)


def test_fresh_and_stronger_nuisance_views_preserve_hidden_target() -> None:
    world = make_world(32, 1103)
    for depth in (1, 4, 6):
        tasks = make_tasks(world, depth, 1103, 8)
        assert all(task.query.view != task.near.view for task in tasks)


def test_full_learners_are_exact_and_raw_hash_is_not() -> None:
    for candidate in ("probabilistic_linkage_scan", "paired_stability_index", "contrastive_hash_index"):
        result = run_trial(candidate, 32, 6, 8, 1103, 6)
        assert result["accuracy"] == result["near_equivalent_accuracy"] == 1.0
        assert result["continual_new_fact_accuracy"] == result["continual_retention"] == 1.0
    assert run_trial("raw_sign_lsh", 32, 6, 8, 1103, 6)["accuracy"] < 1.0


def test_classical_hash_matches_learned_query_and_has_lower_workload() -> None:
    analytic = run_trial("paired_stability_index", 32, 6, 8, 1103, 6)
    learned = run_trial("contrastive_hash_index", 32, 6, 8, 1103, 6)
    assert analytic["mean_query_ops"] == learned["mean_query_ops"]
    assert analytic["workload_ops"] < learned["workload_ops"]
