from nextai_autoresearch.benchmarks.heterogeneous_module_composition_v1 import make_tasks, make_world, run_trial
from nextai_autoresearch.modular_composition_core import FEATURE_BITS, PROBES


def test_world_is_k_stable_and_features_have_disjoint_radius_one_codes() -> None:
    small, large = make_world(8, 1103), make_world(32, 1103)
    assert small.specs == large.specs[:8]
    assert small.features == large.features[:8]
    assert min(sum(a != b for a, b in zip(left, right)) for i, left in enumerate(large.features) for right in large.features[i + 1:]) >= 5


def test_queries_hold_out_inputs_features_and_compositions() -> None:
    world = make_world(8, 1103)
    for depth in (1, 4, 6):
        for query, _ in make_tasks(world, depth, 1103, 8):
            assert query.source not in PROBES
            assert len(query.features) == len(query.route_ids) == depth
            assert all(sum(a != b for a, b in zip(feature, world.features[route])) == 1 for feature, route in zip(query.features, query.route_ids))
            assert all(route < 6 for route in query.route_ids)


def test_sparse_and_direct_are_exact_but_direct_is_no_worse() -> None:
    sparse = run_trial("learned_sparse_modules", 8, 6, 8, 1103, 6)
    direct = run_trial("direct_program_index", 8, 6, 8, 1103, 6)
    assert sparse["accuracy"] == sparse["routing_accuracy"] == sparse["expert_induction_accuracy"] == 1.0
    assert sparse["mean_active_modules"] == 6
    assert direct["accuracy"] == direct["routing_accuracy"] == 1.0
    assert direct["mean_query_ops"] <= sparse["mean_query_ops"]
    assert direct["mean_bytes_loaded"] <= sparse["mean_bytes_loaded"]
    assert direct["state_bytes"] <= sparse["state_bytes"]


def test_sparse_query_is_k_stable_while_dense_sweep_scales() -> None:
    sparse_small = run_trial("learned_sparse_modules", 8, 4, 8, 1103, 6)
    sparse_large = run_trial("learned_sparse_modules", 32, 4, 8, 1103, 6)
    dense_small = run_trial("dense_expert_sweep", 8, 4, 8, 1103, 6)
    dense_large = run_trial("dense_expert_sweep", 32, 4, 8, 1103, 6)
    assert sparse_small["mean_query_ops"] == sparse_large["mean_query_ops"]
    assert sparse_small["mean_bytes_loaded"] == sparse_large["mean_bytes_loaded"]
    assert dense_large["mean_full_expert_evaluations"] == 4 * dense_small["mean_full_expert_evaluations"]
    assert dense_large["mean_query_ops"] > dense_small["mean_query_ops"]


def test_dense_shared_control_is_learned_and_bounded() -> None:
    result = run_trial("dense_shared_transform", 8, 1, 8, 1103, 6)
    assert 0 <= result["accuracy"] <= 1
    assert result["fit_ops"] > 0
    assert result["state_bytes"] > FEATURE_BITS
