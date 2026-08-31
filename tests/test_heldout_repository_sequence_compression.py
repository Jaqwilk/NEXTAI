from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v1 as bench
from nextai_autoresearch.cli import _compression_protocol
from nextai_autoresearch.config import load_config
from nextai_autoresearch.metrics import aggregate_trials
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import project_root


def _plan() -> dict:
    return {
        "schema_version": 1, "experiment_id": "EXP-20260830-9995",
        "parent_experiment_id": "EXP-20260830-0043", "created_at": "2026-08-30T13:11:38Z",
        "status": "planned", "hypothesis_id": "HYP-0016",
        "title": "Held-out repository sequence compression quick",
        "research_question": "Can reusable motifs improve fully charged held-out byte compression?",
        "architecture_family": "hierarchical_adaptive_sequence_compression",
        "candidates": ["hierarchical_motif_compressor", "ppm_byte"],
        "benchmark": bench.BENCHMARK_VERSION, "evaluator_sha256": "a" * 64, "budget": "quick",
        "matrix": {"knowledge_sizes": [8, 32], "reasoning_depths": [1, 4, 6],
                   "queries_per_cell": 8, "seed_policy": {"method": "runner_random_v1",
                   "count": 1, "minimum": 1_000_000, "maximum": 2_147_483_647}},
        "primary_metrics": ["bits_per_byte", "cold_bits_per_byte", "workload_ops_r16"],
        "metric_directions": {"bits_per_byte": "minimize", "cold_bits_per_byte": "minimize",
                              "workload_ops_r16": "minimize"},
        "compression_protocol": {
            "corpus_id": "nextai_local_repository_sha256_v1",
            "split_unit": "whole_files_sha256", "test_file_access": "evaluator_only",
            "predict_then_reveal": True, "shared_candidate": "hierarchical_motif_compressor",
            "classical_baselines": ["empirical_unigram_byte", "ppm_byte",
                                    "context_tree_weighting_byte", "lz_dictionary_byte",
                                    "dense_autoregressive_byte"],
            "shared_slow_state_updates": "forbidden", "test_tuning": "forbidden",
            "declared_horizons": [1, 4, 16], "state_budget_bytes": 4_194_304,
            "invalidation_rules": ["Invalidate on any immutable corpus mismatch."],
        },
        "predicted_outcome": "Classical universal compressors are likely to remain stronger.",
        "falsification_criteria": ["A mandatory baseline matches or dominates the learner."],
        "promotion_criteria": ["Only replicated non-dominated transfer can advance."],
        "alternative_explanations": ["Ordinary context mixing may explain any improvement."],
        "confounds": ["Repository boilerplate may cross file roles."],
        "outcome_policy": {"positive": "Replicate on a larger hidden corpus.",
                           "null": "Keep only if uncertainty remains material.",
                           "negative": "Make the motif route dormant without tuning."},
        "git_before": {"commit": None, "branch": "master", "dirty": True},
    }


def test_corpus_is_whole_file_disjoint_and_matches_hashes() -> None:
    training, test = bench.make_training(8, 1103)
    assert sum(size for _, _, size, _ in bench.CORPUS) == 367_255
    assert {role for role, *_ in bench.CORPUS} == {"train", "validation", "test"}
    assert len(training.train_files) == 33
    assert len(training.validation_files) == 5
    assert len(test) == 5
    assert training.acquisition_ops == 367_255


def test_byte_distribution_boundary_is_strict() -> None:
    assert bench._distribution([1.0] * 256)[0] == pytest.approx(1 / 256)
    with pytest.raises(ValueError, match="256"):
        bench._distribution([1.0] * 255)
    with pytest.raises(ValueError, match="nonnegative"):
        bench._distribution([-1.0] + [1.0] * 255)


def test_compression_plan_requires_machine_readable_protocol() -> None:
    plan = _plan()
    validate_document("experiment_plan", plan, project_root())
    invalid = copy.deepcopy(plan)
    del invalid["compression_protocol"]
    with pytest.raises(ValidationError, match="compression_protocol"):
        validate_document("experiment_plan", invalid, project_root())


def test_official_plan_generator_builds_compression_protocol() -> None:
    plan = _plan()
    plan["compression_protocol"] = _compression_protocol(load_config(project_root()))
    validate_document("experiment_plan", plan, project_root())
    assert plan["compression_protocol"]["split_unit"] == "whole_files_sha256"
    assert plan["compression_protocol"]["test_file_access"] == "evaluator_only"
    assert plan["compression_protocol"]["shared_slow_state_updates"] == "forbidden"


def test_compression_metrics_preserve_worst_file() -> None:
    base = {"status": "complete", "knowledge_size": 8, "reasoning_depth": 1,
            "mean_query_ops": 2, "mean_warm_query_ops": 2, "accuracy": .2,
            "warm_accuracy": .2, "continual_retention": .2, "p50_latency_us": 1,
            "p95_latency_us": 1, "fit_seconds": 1, "state_bytes": 64,
            "update_ops": 1, "update_latency_us": 1, "seed": 7,
            "bits_per_byte": 4.0, "cold_bits_per_byte": 5.0,
            "worst_file_bits_per_byte": 4.0, "compression_ratio": .5}
    summary = aggregate_trials([dict(base, world_family="a"),
                                dict(base, world_family="b", bits_per_byte=6.0,
                                     worst_file_bits_per_byte=6.0)])
    assert summary["bits_per_byte"] == 5.0
    assert summary["worst_file_bits_per_byte"] == 6.0


def test_uniform_sanity_is_eight_bits_and_predicts_before_update(monkeypatch) -> None:
    trace = []

    class Uniform:
        fit_ops = meta_fit_ops = 0
        last_ops = update_ops = 1
        last_bytes_touched = last_update_bytes = 8
        def fit(self, training, knowledge_size, depth): trace.append("fit")
        def query(self, source, steps):
            trace.append(("query", source.slot))
            return [1.0] * 256
        def update(self, source, target):
            assert trace[-1] == ("query", source.slot)
            trace.append(("update", source.slot))
        def state_bytes(self): return 64

    monkeypatch.setattr(bench, "load_candidate", lambda name, seed: Uniform())
    rows = bench._run_trial("uniform_probe", 8, 1, 1, 1_234_567, 1_000_000)
    assert len(rows) == 5
    assert all(row["bits_per_byte"] == 8.0 for row in rows)
    assert rows[0]["workload_ops_r16"] > rows[0]["workload_ops_r1"]
