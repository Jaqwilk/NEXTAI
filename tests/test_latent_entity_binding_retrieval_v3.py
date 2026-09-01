from pathlib import Path

import numpy as np

from nextai_autoresearch.baseline_semantics import required_baseline_names
from nextai_autoresearch.benchmarks import latent_entity_binding_retrieval_v3 as v3
from nextai_autoresearch.benchmarks.successor_graph_v1 import load_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.entity_addressing_contract import HIERARCHICAL_ROLE_CONTRACT, RawQuery


def _valid_hierarchical_bundle(paths: tuple[Path, ...]) -> bool:
    if not any(path.exists() for path in paths):
        return True
    shared = "from nextai_autoresearch.candidates.learned_hierarchical_routing_v1 import"
    return all(path.exists() for path in paths) and all(
        shared in path.read_text(encoding="utf-8") for path in paths
    )


def test_v3_reuses_worlds_but_has_separate_contract() -> None:
    assert v3.BENCHMARK_VERSION == "latent_entity_binding_retrieval_v3"
    world = v3.make_world(32, 1103)
    assert len(world.records) == 32
    assert tuple(HIERARCHICAL_ROLE_CONTRACT) == (
        "learned_balanced_hierarchical_router_v1",
        "source_identical_dense_hierarchical_representation_v1",
        "source_identical_frozen_hierarchical_router_v1",
        "source_identical_shuffled_hierarchical_router_v1",
        "raw_balanced_kd_tree_v1", "raw_nearest_neighbour_scan_v1",
        "local_dense_transition_gru_v1", "privileged_exact_entity_key_v1",
    )


def test_v3_plan_contract_is_hierarchical_not_flat_addressing() -> None:
    protocol = load_config().raw["hierarchical_addressing"]
    assert protocol["tree_depth_rule"] == "balanced_recursive_median_until_singleton"
    assert protocol["visited_node_cap"] == 64 and protocol["fallback_candidates"] == 0
    assert protocol["shared_candidate"] == tuple(HIERARCHICAL_ROLE_CONTRACT)[0]
    assert "key_bits" not in protocol and "probes" not in protocol
    assert required_baseline_names({"entity_addressing_protocol": protocol}) == list(tuple(HIERARCHICAL_ROLE_CONTRACT)[-4:])


def test_hierarchical_roles_are_absent_or_one_complete_shared_core(tmp_path: Path) -> None:
    roles = tuple(HIERARCHICAL_ROLE_CONTRACT)[:4]
    repository = Path(__file__).parents[1] / "src/nextai_autoresearch/candidates"
    assert _valid_hierarchical_bundle(tuple(repository / f"{role}.py" for role in roles))
    paths = tuple(tmp_path / f"{role}.py" for role in roles)
    assert _valid_hierarchical_bundle(paths)
    paths[0].write_text("pass\n", encoding="utf-8")
    assert not _valid_hierarchical_bundle(paths)
    for path in paths:
        path.write_text("from nextai_autoresearch.candidates.learned_hierarchical_routing_v1 import Base\n", encoding="utf-8")
    assert _valid_hierarchical_bundle(paths)


def test_raw_kd_tree_matches_full_scan_and_uses_node_conditional_axes() -> None:
    world = v3.make_world(32, 1103)
    tree, scan = load_candidate("raw_balanced_kd_tree_v1", 1103), load_candidate("raw_nearest_neighbour_scan_v1", 1103)
    tree.fit(world.records, 32, 8)
    scan.fit(world.records, 32, 8)
    assert len(set(map(int, tree.axis[:tree.count]))) > 1
    assert not hasattr(tree, "thresholds") and not hasattr(tree, "buckets")
    for depth in (1, 4, 8):
        for task in v3.make_tasks(world, depth, 1103, 8):
            assert tree.query(task.public, depth) == scan.query(task.public, depth) == task.expected


def test_raw_kd_tree_insert_is_path_local_and_semantically_complete() -> None:
    world = v3.make_world(32, 1103)
    tree = load_candidate("raw_balanced_kd_tree_v1", 1103)
    tree.fit(world.records, 32, 8)
    root, axes = tree.root, tree.axis[:tree.count].copy()
    links = np.concatenate((tree.left[:tree.count], tree.right[:tree.count])).copy()
    record = world.records[0]
    tree.update(record, record.value)
    changed = np.count_nonzero(links != np.concatenate((tree.left[:32], tree.right[:32])))
    assert tree.root == root and np.array_equal(tree.axis[:32], axes)
    assert tree.count == 33 and changed == 1 and tree.update_ops < 1_000
    source = RawQuery(tuple(record.observations[0]), 1)
    assert isinstance(tree.query(source, 1), int)


def test_raw_kd_tree_real_trial_is_exact_and_locally_updatable() -> None:
    result = v3.run_trial("raw_balanced_kd_tree_v1", 32, 8, 8, 1103, 8)
    assert result["accuracy"] == result["continual_new_fact_accuracy"] == 1.0
    assert 0 < result["mean_comparisons"] <= 32 * 8
    assert result["update_ops"] < 1_000
