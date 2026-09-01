import os
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

from nextai_autoresearch.benchmarks.latent_entity_binding_retrieval_v2 import make_tasks, make_world, run_trial
from nextai_autoresearch.baseline_semantics import required_baseline_names
from nextai_autoresearch.entity_addressing_contract import KNOWLEDGE_SIZES, ROLE_CONTRACT
from nextai_autoresearch.entity_addressing_core import split_burst


def test_raw_contract_has_no_key_or_entity_field() -> None:
    world = make_world(32, 1103)
    assert set(world.records[0].__dataclass_fields__) == {"observations", "value"}
    assert set(make_tasks(world, 1, 1103, 1)[0].public.__dataclass_fields__) == {"observation", "signature"}


def test_three_scales_cover_exactly_one_hundred_fold() -> None:
    assert KNOWLEDGE_SIZES == (32, 320, 3200)
    assert KNOWLEDGE_SIZES[-1] / KNOWLEDGE_SIZES[0] == 100


def test_dense_nonlinear_encoder_uses_every_latent_coordinate() -> None:
    world = make_world(32, 1103)
    assert all(all(abs(weight) > 1e-9 for weight in row) for row in world.encoder_a)
    assert all(all(abs(weight) > 1e-9 for weight in row) for row in world.encoder_b)


def test_development_change_points_and_exact_key_are_identifiable() -> None:
    world = make_world(32, 1103)
    assert all(len(record.observations) == 7 for record in world.records)
    assert all(left.shape == right.shape == (24,) for left, right in map(split_burst, world.records))
    privileged = run_trial("privileged_exact_entity_key_v1", 32, 8, 8, 1103, 8)
    assert privileged["accuracy"] == privileged["continual_new_fact_accuracy"] == 1.0


def test_classical_dense_scan_is_complete_and_k_linear() -> None:
    small = run_trial("raw_nearest_neighbour_scan_v1", 32, 4, 8, 1103, 8)
    medium = run_trial("raw_nearest_neighbour_scan_v1", 320, 4, 8, 1103, 8)
    assert small["accuracy"] == medium["accuracy"] == 1.0
    assert medium["mean_query_ops"] > 9 * small["mean_query_ops"]


def test_local_dense_neural_control_completes_without_external_index() -> None:
    result = run_trial("local_dense_transition_gru_v1", 32, 1, 2, 1103, 8)
    assert result["fit_ops"] > result["mean_query_ops"] > 0
    assert 0 < result["state_bytes"] < 1_000_000
    assert result["mean_comparisons"] == 0


def test_future_roles_are_frozen_but_main_sources_do_not_exist() -> None:
    assert tuple(ROLE_CONTRACT) == (
        "learned_discrete_address_index_v1", "source_identical_dense_scan_v1",
        "source_identical_frozen_encoder_index_v1", "source_identical_shuffled_representation_index_v1",
        "raw_nearest_neighbour_scan_v1", "local_dense_transition_gru_v1", "privileged_exact_entity_key_v1",
    )
    candidates = Path(__file__).parents[1] / "src/nextai_autoresearch/candidates"
    assert not any((candidates / f"{name}.py").exists() for name in tuple(ROLE_CONTRACT)[:4])


def test_entity_addressing_controls_are_required_by_pre_seed_gate() -> None:
    controls = list(tuple(ROLE_CONTRACT)[-3:])
    plan = {
        "entity_addressing_protocol": {
            "classical_baselines": controls,
        }
    }
    assert required_baseline_names(plan) == controls
