from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import nonstationary_online_update_battery_v1 as battery
from nextai_autoresearch.metrics import aggregate_trials
from nextai_autoresearch.online_update_contract import OnlineObservation, OnlineTraining
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


def _plan() -> dict:
    return {
        "schema_version": 1, "experiment_id": "EXP-20260830-9996",
        "parent_experiment_id": None, "created_at": "2026-08-30T12:50:00Z",
        "status": "planned", "hypothesis_id": "HYP-0014",
        "title": "Shared online update quick",
        "research_question": "Does one update rule transfer across unseen streams?",
        "architecture_family": "meta_learned_online_state_update",
        "candidates": ["shared_meta_update", "delta_lms_online"],
        "benchmark": battery.BENCHMARK_VERSION, "evaluator_sha256": "a" * 64,
        "budget": "quick",
        "matrix": {"knowledge_sizes": [8, 32], "reasoning_depths": [1, 4, 6],
                   "queries_per_cell": 8, "seed_policy": {"method": "runner_random_v1",
                   "count": 1, "minimum": 1_000_000, "maximum": 2_147_483_647}},
        "primary_metrics": ["accuracy", "worst_phase_accuracy"],
        "metric_directions": {"accuracy": "maximize", "worst_phase_accuracy": "maximize"},
        "online_update_protocol": {
            "mechanisms": list(battery.MECHANISMS), "training_stream_seeds": [1103, 2207],
            "test_stream_seed_source": "runner_scoring_seeds", "predict_then_reveal": True,
            "shared_candidate": "shared_meta_update", "classical_baselines": [
                "no_update_online", "delta_lms_online", "rls_kalman_online",
                "polynomial_rls_online", "kernel_dictionary_online"],
            "mechanism_labels": "forbidden", "test_tuning": "forbidden",
            "declared_horizons": [1, 4, 16], "state_budget_bytes_per_slot": 262144,
            "shared_state_budget_bytes": 65536,
            "invalidation_rules": ["Invalidate if prediction follows target reveal."],
        },
        "predicted_outcome": "The shared update probably remains classically dominated.",
        "falsification_criteria": ["Any mechanism falls below its registered gate."],
        "promotion_criteria": ["Only a replicated non-dominated screen may advance."],
        "alternative_explanations": ["A fixed nonlinear basis may explain any gain."],
        "confounds": ["Slots could accidentally correlate with mechanism identity."],
        "outcome_policy": {"positive": "Run an adversarial replicated screen.",
                           "null": "Return the hypothesis to dormant status.",
                           "negative": "Discard only the failed implementation."},
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }


def test_online_plan_requires_machine_readable_protocol() -> None:
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    invalid = copy.deepcopy(plan)
    del invalid["online_update_protocol"]
    with pytest.raises(ValidationError, match="online_update_protocol"):
        validate_document("experiment_plan", invalid, project_root())


def test_public_stream_has_no_regime_or_target_in_query() -> None:
    stream = battery.make_stream("mixed_linear", 8, 2, 8, 1103, 731)
    assert isinstance(stream.sequence[0].observation, OnlineObservation)
    assert not hasattr(stream.sequence[0].observation, "target")
    assert not hasattr(stream.sequence[0].observation, "phase")
    assert not hasattr(stream.sequence[0].observation, "mechanism")
    assert set(stream.phase_by_index) == {name for name, _ in battery.PHASES}


def test_evaluator_calls_predict_before_reveal(monkeypatch: pytest.MonkeyPatch) -> None:
    trace: list[str] = []

    class Probe:
        fit_ops = meta_fit_ops = update_ops = last_ops = 1
        last_bytes_touched = last_update_bytes = 8
        def fit(self, facts, universe_size, max_depth):
            assert isinstance(facts, OnlineTraining)
            trace.append("fit")
        def query(self, source, steps):
            assert isinstance(source, OnlineObservation)
            trace.append(f"q:{source.slot}")
            return 0.0
        def update(self, source, target):
            assert isinstance(source, OnlineObservation)
            assert trace[-1] == f"q:{source.slot}"
            trace.append(f"u:{source.slot}")
        def state_bytes(self): return 64

    probe = Probe()
    monkeypatch.setattr(battery, "load_candidate", lambda name, seed: probe)
    rows = battery._run_trial("probe_online", 8, 1, 3, 1_234_567, (1103,), 1, 1_000_000)
    assert len(rows) == 3
    assert trace[0] == "fit"
    assert all(trace[index][0] != trace[index + 1][0] for index in range(1, len(trace) - 1))


def test_online_metrics_preserve_weakest_phase_and_mechanism() -> None:
    base = {"status": "complete", "knowledge_size": 8, "reasoning_depth": 1,
            "mean_query_ops": 2, "mean_warm_query_ops": 2, "accuracy": .9,
            "warm_accuracy": .8, "continual_retention": .7, "p50_latency_us": 1,
            "p95_latency_us": 1, "fit_seconds": 1, "state_bytes": 64,
            "update_ops": 1, "update_latency_us": 1, "seed": 7,
            "worst_phase_accuracy": .6, "post_switch_recovery": .5,
            "recurrence_retention": .7, "prequential_loss": .1,
            "distractor_interference": .2}
    summary = aggregate_trials([dict(base, world_family="a"),
                                dict(base, world_family="b", accuracy=.7,
                                     worst_phase_accuracy=.3)])
    assert summary["minimum_family_accuracy"] == .7
    assert summary["worst_phase_accuracy"] == .3
    assert summary["post_switch_recovery"] == .5
