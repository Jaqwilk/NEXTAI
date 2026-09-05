from nextai_autoresearch.benchmarks.routed_vsa_capacity_scaling_v2 import run_trial
from nextai_autoresearch.vsa_capacity_core import (
    BucketedVSA32, ExactTupleStoreVSA, GlobalVSA32, LearnedRoutedVSA32, OracleRoutedVSA32,
    VSAQuery,
)


def cycle(size: int) -> list[tuple[int, int]]:
    return [(index, (index + 1) % size) for index in range(size)]


def fitted(model, size=32):
    model.fit(cycle(size), size, 8)
    return model


def test_matched_r32_variants_share_codes_and_superposition() -> None:
    models = [fitted(cls()) for cls in (GlobalVSA32, BucketedVSA32, LearnedRoutedVSA32, OracleRoutedVSA32)]
    assert all((models[0].codebook == model.codebook).all() for model in models[1:])
    assert all((models[0].memory == model.memory).all() for model in models[1:])


def test_routing_reduces_cleanup_work_and_learning_is_charged() -> None:
    global_model, bucketed, learned = fitted(GlobalVSA32(), 128), fitted(BucketedVSA32(), 128), fitted(LearnedRoutedVSA32(), 128)
    global_model.query(VSAQuery(0), 1)
    bucketed.query(VSAQuery(0), 1)
    assert bucketed.last_comparisons < global_model.last_comparisons
    assert bucketed.last_ops < global_model.last_ops
    assert learned.fit_ops > bucketed.fit_ops


def test_exact_update_replaces_relation() -> None:
    model = fitted(ExactTupleStoreVSA(), 8)
    model.update(0, 4)
    assert model.query(VSAQuery(0), 1) == 4
    assert model.query(VSAQuery(1), 1) == 2


def test_benchmark_reports_noisy_and_full_cost_metrics() -> None:
    trial = run_trial("global_vsa_r32", 8, 4, 3, 1103, 8)
    assert trial["status"] == "complete"
    assert 0.0 <= trial["near_equivalent_accuracy"] <= 1.0
    assert trial["workload_ops"] > trial["fit_ops"]
    assert trial["mean_bytes_touched"] > 0
