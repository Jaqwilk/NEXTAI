from __future__ import annotations

import copy
import hashlib

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v1 as bench
from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v2 as bench_v2
from nextai_autoresearch.benchmarks import heldout_repository_sequence_compression_v3 as bench_v3
from nextai_autoresearch.cli import _compression_protocol
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.candidates.masked_baselines import CTWByteModel, PPMDModel
from nextai_autoresearch.repository_sequence_contract import ByteContext
from nextai_autoresearch.metrics import aggregate_trials
from nextai_autoresearch.runner import _frontier
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


def _config_for(version: str) -> ResearchConfig:
    active = load_config(project_root())
    raw = copy.deepcopy(active.raw)
    raw["project"]["benchmark_version"] = version
    if version.endswith("_v2"):
        raw["compression"].update({
            "shared_candidate": "layer_local_goodness_byte",
            "global_credit_ablation": "source_identical_end_to_end_gradient_byte",
            "frozen_hidden_ablation": "source_identical_frozen_hidden_byte",
        })
    return ResearchConfig(raw, active.path)


def _compression_plan(version: str) -> dict:
    plan = _plan()
    config = _config_for(version)
    plan["benchmark"] = version
    plan["matrix"].update({"knowledge_sizes": [8, 20, 32],
                           "reasoning_depths": [4, 16, 64], "queries_per_cell": 8})
    plan["candidates"] = [
        *_compression_protocol(config).get(
            "credit_assignment_roles", _compression_protocol(config).get("causal_roles", ())
        ),
        *config.raw["compression"]["classical_baselines"],
    ]
    plan["compression_protocol"] = _compression_protocol(config)
    plan["primary_metrics"] = list(plan["compression_protocol"]["pareto_capability_metrics"])
    maximize = set(config.raw["metrics"]["maximize"])
    plan["metric_directions"] = {
        metric: "maximize" if metric in maximize else "minimize"
        for metric in plan["primary_metrics"]
    }
    return plan


def _v2_plan() -> dict:
    return _compression_plan(bench_v2.BENCHMARK_VERSION)


def _v3_plan() -> dict:
    return _compression_plan(bench_v3.BENCHMARK_VERSION)


def test_corpus_is_whole_file_disjoint_and_matches_hashes() -> None:
    training, test = bench.make_training(8, 1103)
    assert sum(size for _, _, size, _ in bench.CORPUS) == 367_255
    assert {role for role, *_ in bench.CORPUS} == {"train", "validation", "test"}
    assert len(training.train_files) == 33
    assert len(training.validation_files) == 5
    assert len(test) == 5
    assert training.acquisition_ops == 367_255


def test_frozen_corpus_recovers_original_bytes_after_rule_files_change() -> None:
    root = project_root()
    role, relative, size, digest = bench.CORPUS[0]
    assert role == "train" and relative == "AGENTS.md"
    recovered = bench._frozen_corpus_bytes(root, relative, size, digest)
    assert (root / relative).read_bytes() != recovered
    assert len(recovered) == size
    assert hashlib.sha256(recovered).hexdigest() == digest


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


def test_v2_preserves_v1_corpus_and_freezes_credit_assignment_contract() -> None:
    assert bench_v2.CORPUS == bench.CORPUS
    assert bench_v2.SEGMENT_MULTIPLIER == bench.SEGMENT_MULTIPLIER == 128
    assert bench_v2.verify_static_contract()["acquisition_bytes"] == 367_255
    plan = _v2_plan()
    validate_document("experiment_plan", plan, project_root())
    assert plan["compression_protocol"]["credit_assignment_roles"] == plan["candidates"][:3]
    invalid = copy.deepcopy(plan)
    invalid["matrix"]["reasoning_depths"] = [4, 16, 63]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", invalid, project_root())


def test_v3_changes_only_prospective_causal_roles() -> None:
    assert bench_v3.CORPUS == bench_v2.CORPUS == bench.CORPUS
    assert bench_v3.SEGMENT_MULTIPLIER == bench_v2.SEGMENT_MULTIPLIER == 128
    assert bench_v3.verify_static_contract() == bench_v2.verify_static_contract()
    plan = _v3_plan()
    validate_document("experiment_plan", plan, project_root())
    protocol = plan["compression_protocol"]
    assert protocol["causal_roles"] == plan["candidates"][:3]
    assert "credit_assignment_roles" not in protocol
    assert protocol["classical_baselines"] == _v2_plan()["compression_protocol"]["classical_baselines"]


@pytest.mark.parametrize("name,model_type", [
    ("ppm_d_order5_byte", PPMDModel),
    ("ctw_depth2_byte", CTWByteModel),
])
def test_registered_repository_coders_use_reference_models_and_real_bytes(name, model_type) -> None:
    module = __import__(f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"])
    candidate = module.Candidate(7)
    training, testing = bench_v2.make_training(8, 1_500_003)
    candidate.fit(training, 8, 64)
    assert isinstance(candidate.model, model_type)
    history = tuple(testing[0][1][:64])
    row = candidate.query(ByteContext(91, history), 1)
    assert len(row) == 256
    assert sum(row) == pytest.approx(1.0, abs=1e-12)
    before = candidate.state_bytes()
    candidate.update(ByteContext(91, history), testing[0][1][64])
    assert candidate.state_bytes() == before
    assert candidate.update_ops == 0


def test_repository_uniform_unigram_lz_and_dense_controls_have_distinct_semantics() -> None:
    training, testing = bench_v2.make_training(8, 1_500_003)
    data = testing[0][1]
    rows = {}
    instances = {}
    for name in ("uniform_byte", "empirical_unigram_byte", "lz_dictionary_byte",
                 "dense_autoregressive_byte"):
        module = __import__(f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"])
        instances[name] = module.Candidate(11)
        instances[name].fit(training, 8, 4)
        rows[name] = instances[name].query(ByteContext(77, tuple(data[:4])), 1)
        assert sum(rows[name]) == pytest.approx(1.0, abs=1e-12)
    assert rows["uniform_byte"] == [1 / 256] * 256
    assert max(rows["empirical_unigram_byte"]) > min(rows["empirical_unigram_byte"])
    assert instances["lz_dictionary_byte"].phrases
    dense_other = instances["dense_autoregressive_byte"].query(
        ByteContext(78, tuple(reversed(data[:4]))), 1
    )
    assert rows["dense_autoregressive_byte"] != dense_other


def test_v2_real_file_final_schema_and_timeout_safe_frontier() -> None:
    plan, config = _v2_plan(), load_config(project_root())
    complete = []
    for name in config.raw["compression"]["classical_baselines"]:
        trials = bench._run_trial(name, 8, 4, 1, 1103, 4_194_304)
        complete.append({"candidate": name, "status": "complete",
                         "summary": aggregate_trials(trials)})
    frontier, axes = _frontier(complete, plan, config)
    assert frontier
    assert axes["maximize"] == ["accuracy"]
    assert "bits_per_byte" in axes["minimize"]
    with_timeout = [*complete, {"candidate": "timed_out_probe", "status": "timeout",
                                "summary": {"status": "timeout"}}]
    assert _frontier(with_timeout, plan, config)[0] == frontier
