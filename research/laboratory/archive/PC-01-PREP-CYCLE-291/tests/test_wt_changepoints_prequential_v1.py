from __future__ import annotations

import numpy as np
import pytest

from nextai_autoresearch.benchmarks import heldout_wt_changepoints_prequential_v1 as bench
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root
from nextai_autoresearch.wt_prequential_contract import WTEpisode, WTQuery, WTReveal, WTTraining


def _episode(control: float, base: float, response: float) -> WTEpisode:
    history = np.full((32, 10), base, dtype=float)
    history[:, 0] += np.linspace(0.0, 0.1, 32)
    target = np.full((32, 10), base + response, dtype=float)
    return WTEpisode(tuple(map(tuple, history)), control, tuple(map(tuple, target)))


def _training() -> WTTraining:
    episodes = tuple(
        _episode(control, base, response)
        for control, base, response in (
            (-1.0, -1.0, -0.5), (1.0, -1.0, 0.5),
            (-1.0, 1.0, -0.4), (1.0, 1.0, 0.4),
        )
    )
    return WTTraining(episodes, 100, 200)


def _candidate(name: str):
    module = __import__(f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"])
    candidate = module.Candidate(7)
    candidate.fit(_training(), 4, 96)
    return candidate


def _query(control: float = 1.0, base: float = 1.0, slot: int = 11, horizon: int = 96):
    history = np.full((32, 10), base, dtype=float)
    history[:, 0] += np.linspace(0.0, 0.1, 32)
    return WTQuery(slot, tuple(map(tuple, history)), control, horizon)


def test_wt_persistence_reference_and_depth_extension() -> None:
    candidate = _candidate("wt_persistence_v1")
    query = _query(horizon=96)
    prediction = np.asarray(candidate.query(query, 96))
    assert prediction.shape == (96, 10)
    assert np.allclose(prediction, np.asarray(query.history)[-1])


def test_wt_pooled_and_exact_control_level_semantics() -> None:
    pooled = _candidate("wt_pooled_mean_v1")
    level = _candidate("wt_control_level_bank_v1")
    low, high = _query(-1.0), _query(1.0)
    assert np.allclose(pooled.query(low, 96), pooled.query(high, 96))
    assert not np.allclose(level.query(low, 96), level.query(high, 96))


@pytest.mark.parametrize("name", ["wt_lms_v1", "wt_rls_v1"])
def test_wt_adaptive_linear_update_is_slot_local(name: str) -> None:
    candidate = _candidate(name)
    first, other = _query(slot=11, horizon=32), _query(slot=22, horizon=32)
    before_first = np.asarray(candidate.query(first, 32))
    before_other = np.asarray(candidate.query(other, 32))
    target = np.asarray(first.history)[-32:] + 2.0
    candidate.update(WTReveal(first.slot, first.history, first.control, tuple(map(tuple, target))))
    assert not np.allclose(candidate.query(first, 32), before_first)
    assert np.allclose(candidate.query(other, 32), before_other)


def test_wt_ridge_fir_is_fixed_and_extends_only_by_hold_last() -> None:
    candidate = _candidate("wt_ridge_fir_v1")
    query = _query(horizon=96)
    before = np.asarray(candidate.query(query, 96))
    candidate.update(WTReveal(query.slot, query.history, query.control,
                              tuple(map(tuple, np.zeros((96, 10))))))
    after = np.asarray(candidate.query(query, 96))
    assert np.allclose(before, after)
    assert np.allclose(after[32:], after[31])


def test_wt_transition_bank_uses_prechange_signature_and_local_update() -> None:
    candidate = _candidate("wt_transition_bank_v1")
    low, high = _query(1.0, -1.0, 11, 32), _query(1.0, 1.0, 22, 32)
    assert not np.allclose(candidate.query(low, 32), candidate.query(high, 32))
    untouched = np.asarray(candidate.query(high, 32))
    candidate.update(WTReveal(low.slot, low.history, low.control,
                              tuple(map(tuple, np.full((32, 10), 5.0)))))
    assert np.allclose(candidate.query(high, 32), untouched)


def test_wt_bounded_replay_has_hard_cap_and_slot_local_state() -> None:
    candidate = _candidate("wt_bounded_replay_v1")
    query = _query(horizon=32)
    for index in range(20):
        target = np.full((32, 10), float(index))
        candidate.update(WTReveal(query.slot, query.history, query.control, tuple(map(tuple, target))))
    assert len(candidate._state[query.slot]) == 16
    assert 22 not in candidate._state


@pytest.mark.parametrize("name", bench.BASELINES)
def test_wt_baselines_are_channel_permutation_equivariant(name: str) -> None:
    training = _training()
    permutation = np.asarray([3, 1, 8, 0, 4, 9, 2, 6, 5, 7])
    permuted = WTTraining(tuple(WTEpisode(
        tuple(map(tuple, np.asarray(ep.history)[:, permutation])), ep.control,
        tuple(map(tuple, np.asarray(ep.target)[:, permutation])),
    ) for ep in training.episodes), training.acquisition_ops, training.preprocessing_ops)
    module = __import__(f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"])
    left, right = module.Candidate(7), module.Candidate(7)
    left.fit(training, 4, 96)
    right.fit(permuted, 4, 96)
    query = _query(horizon=96)
    permuted_query = WTQuery(query.slot, tuple(map(tuple, np.asarray(query.history)[:, permutation])),
                             query.control, query.horizon)
    assert np.allclose(np.asarray(left.query(query, 96))[:, permutation],
                       right.query(permuted_query, 96), atol=1e-9)


def test_wt_evaluator_freezes_complete_prediction_before_reveal(monkeypatch) -> None:
    trace = []

    class Probe:
        fit_ops = meta_fit_ops = update_ops = last_ops = 1
        last_bytes_touched = last_update_bytes = 8
        def fit(self, training, knowledge_size, max_depth): trace.append("fit")
        def query(self, query, steps):
            trace.append("query")
            return np.repeat(np.asarray(query.history)[-1][None, :], query.horizon, axis=0)
        def update(self, reveal):
            assert trace[-1] == "artifact"
            trace.append("update")
        def state_bytes(self): return 64

    original = bench._artifact
    def artifact(*args):
        result = original(*args)
        assert not result[0].flags.writeable
        trace.append("artifact")
        return result
    monkeypatch.setattr(bench, "load_candidate", lambda name, seed: Probe())
    monkeypatch.setattr(bench, "_artifact", artifact)
    rows = bench._run_trial("probe", 18, 16, 1_170_311, (6,), 1_000_000)
    assert rows[0]["prediction_artifact_count"] == 9
    assert trace[0] == "fit"
    assert trace[1:] == [value for _ in range(9) for value in ("query", "artifact", "update")]


def test_wt_static_split_and_plan_schema() -> None:
    static = bench.verify_static_contract(project_root())
    assert set(static["train"]).isdisjoint(static["development"] + static["test"])
    metrics = [
        "stable_rollout_rate", "normalized_rmse", "worst_file_normalized_rmse",
        "worst_transition_normalized_rmse", "rollout_16_nrmse", "rollout_32_nrmse",
        "rollout_96_nrmse", "data_acquisition_ops", "preprocessing_ops", "fit_ops",
        "adaptation_ops", "mean_query_ops", "update_ops", "state_bytes",
        "peak_state_bytes", "mean_bytes_touched", "workload_ops_r1", "workload_ops_r4",
        "workload_ops_r16",
    ]
    directions = {name: "maximize" if name == "stable_rollout_rate" else "minimize"
                  for name in metrics}
    protocol = {
        "corpus_id": "causal_chambers_wt_changepoints_v1",
        "manifest_sha256": static["manifest_sha256"], "split_unit": "whole_csv_file_sha256",
        "train_files": list(bench.TRAIN_SEEDS), "development_files": list(bench.DEVELOPMENT_SEEDS),
        "test_files": list(bench.TEST_SEEDS),
        "candidate_metadata": "anonymous_permuted_tensors_and_random_slot_only",
        "predict_then_atomic_artifact_then_reveal": True,
        "shared_candidate": "wt_candidate_under_test", "classical_baselines": list(bench.BASELINES),
        "knowledge_sizes": list(bench.KNOWLEDGE_SIZES), "fit_depth": 32, "fit_horizon": 32,
        "declared_horizons": list(bench.HORIZONS), "runner_random_channel_permutation": True,
        "normalization": "train_files_only_mechanical_partition", "state_budget_bytes": 16777216,
        "declared_reuses": [1, 4, 16], "minimum_meaningful_nrmse_effect": 0.1325268421060828,
        "saturation_nrmse": 0.5, "saturation_worst_file_nrmse": 0.75,
        "pareto_capability_metrics": metrics,
        "invalidation_rules": [f"Frozen invalidation rule number {index}." for index in range(8)],
    }
    plan = {
        "schema_version": 1, "experiment_id": "EXP-20990101-9999", "parent_experiment_id": None,
        "created_at": "2099-01-01T00:00:00Z", "status": "planned", "hypothesis_id": "HYP-9999",
        "title": "WT schema regression", "research_question": "Can the frozen WT contract validate?",
        "architecture_family": "test", "candidates": ["wt_candidate_under_test", *bench.BASELINES],
        "benchmark": bench.BENCHMARK_VERSION, "evaluator_sha256": "a" * 64, "budget": "quick",
        "matrix": {"knowledge_sizes": [18, 36, 54], "reasoning_depths": [16, 32, 96],
                   "queries_per_cell": 18, "seed_policy": {"method": "runner_random_v1",
                   "count": 1, "minimum": 1_000_000, "maximum": 2_147_483_647}},
        "primary_metrics": metrics, "metric_directions": directions,
        "wt_prequential_protocol": protocol,
        "predicted_outcome": "Schema-only test predicts a valid frozen contract.",
        "falsification_criteria": ["Reject malformed schema output."],
        "promotion_criteria": ["This schema test cannot promote."],
        "alternative_explanations": ["A permissive schema could hide a defect."],
        "confounds": ["No score occurs."],
        "outcome_policy": {"positive": "Permit later preregistration only.",
                           "null": "Keep benchmark in maintenance.",
                           "negative": "Repair in a new service cycle."},
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }
    validate_document("experiment_plan", plan, project_root())
