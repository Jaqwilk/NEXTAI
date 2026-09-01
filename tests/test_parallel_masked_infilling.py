from __future__ import annotations

import copy
from argparse import Namespace

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v1 as bench
from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v3 as bench_v3
from nextai_autoresearch import cli
from nextai_autoresearch.benchmarks.heldout_repository_sequence_compression_v1 import CORPUS as OLD
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.masked_refinement_contract import (
    MASK,
    ByteFile,
    MaskedQuery,
    MaskedTraining,
)
from nextai_autoresearch.candidates.local_sparse_predictive_code_core import (
    ACTIVE, LATENT, LEARNING_RATE, PATCH, SEED_SALT, Candidate as SparseCodeCore,
)
from nextai_autoresearch.metrics import aggregate_trials
from nextai_autoresearch.runner import _frontier
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


class Uniform:
    def __init__(self) -> None:
        self.snapshots = []
        self.last_ops = self.last_bytes_touched = 0
        self.last_critical_path_steps = 1

    def query(self, query: MaskedQuery, rounds: int):
        assert rounds == query.maximum_rounds
        self.snapshots.append(query.snapshot)
        self.last_ops = len(query.masked_positions) * 256
        return tuple((1 / 256,) * 256 for _ in query.masked_positions)


def test_corpus_is_whole_file_hashed_and_disjoint_from_exp0044() -> None:
    roles, acquisition = bench._load_corpus()
    assert {role: len(files) for role, files in roles.items()} == {
        "train": 35, "validation": 4, "test": 9,
    }
    assert acquisition == 305_214
    assert len({digest for *_, digest in bench.CORPUS}) == len(bench.CORPUS)
    assert {row[1] for row in bench.CORPUS}.isdisjoint({row[1] for row in OLD})


def test_runner_seed_relabels_all_public_training_bytes() -> None:
    first, tests_a = bench.make_training(8, 1_500_001)
    second, tests_b = bench.make_training(8, 1_500_002)
    assert sum(len(file.data) for file in first.train_files) == 8 * 1024
    assert first.train_files[0].data != second.train_files[0].data
    assert tests_a[0][1] != tests_b[0][1]
    assert all(0 <= value < 256 for file in first.train_files for value in file.data)


def test_rounds_use_immutable_snapshot_batches_without_truth_reveal() -> None:
    candidate = Uniform()
    initial = (7, 8, MASK, MASK, MASK, MASK, 9, 10)
    row = bench._run_case(candidate, "uniform_masked_byte",
                          (17, initial, (2, 3, 4, 5), (1, 2, 3, 4)), 2)
    assert len(candidate.snapshots) == 2
    assert candidate.snapshots[0] == initial
    assert candidate.snapshots[1].count(MASK) == 2
    assert row["probabilities"] == (4 + 2) * 256
    assert row["critical"] >= 2
    assert not hasattr(MaskedQuery(1, initial, (2,), 0, 1), "target")


def _masked_plan() -> dict:
    plan = copy.deepcopy(load_json(
        project_root() / "research" / "plans" / "EXP-20260830-0046.json"
    ))
    plan["benchmark"] = bench.BENCHMARK_VERSION
    plan["candidates"] = ["iterative_masked_learner", "one_pass_masked_learner"]
    plan.pop("transfer_protocol")
    plan["masked_refinement_protocol"] = {
        "corpus_id": "nextai_disjoint_masked_corpus_sha256_v1",
        "split_unit": "whole_files_sha256",
        "test_file_access": "evaluator_only",
        "simultaneous_snapshot_rounds": True,
        "span_lengths": [8, 32, 128],
        "context_bytes": 64,
        "runner_random_masks_and_permutation": True,
        "shared_candidate": "iterative_masked_learner",
        "one_pass_ablation": "one_pass_masked_learner",
        "classical_baselines": list(load_config().raw["masked_refinement"]["classical_baselines"]),
        "declared_horizons": [1, 4, 16],
        "state_budget_bytes": 4_194_304,
        "invalidation_rules": ["Invalidate this masked cohort on leakage."] * 4,
    }
    return plan


def test_masked_plan_requires_snapshot_and_classical_controls() -> None:
    plan = _masked_plan()
    validate_document("experiment_plan", plan, project_root())
    del plan["masked_refinement_protocol"]["simultaneous_snapshot_rounds"]
    with pytest.raises(ValidationError, match="simultaneous_snapshot_rounds"):
        validate_document("experiment_plan", plan, project_root())


def test_masked_metrics_and_loss_frontier_do_not_use_top1_gate() -> None:
    trial = {
        "status": "complete", "knowledge_size": 8, "reasoning_depth": 1,
        "mean_query_ops": 10, "mean_warm_query_ops": 10, "accuracy": 0.2,
        "warm_accuracy": 0.2, "continual_retention": 0, "p50_latency_us": 1,
        "p95_latency_us": 1, "fit_seconds": 1, "state_bytes": 16,
        "update_ops": 0, "update_latency_us": 0, "seed": 7,
        "bits_per_byte": 4, "exact_span_accuracy": 0.1,
        "critical_path_steps": 3, "total_position_probabilities": 1024,
        "workload_ops_r16": 100,
    }
    summary = aggregate_trials([trial])
    assert summary["exact_span_accuracy"] == 0.1
    assert summary["critical_path_steps"] == 3
    plan = _masked_plan()
    plan["primary_metrics"] = ["bits_per_byte", "exact_span_accuracy"]
    plan["metric_directions"] = {
        "bits_per_byte": "minimize", "exact_span_accuracy": "maximize",
    }
    front, axes = _frontier([
            {"candidate": "low_accuracy", "status": "complete", "summary": summary}
    ], plan, load_config())
    assert front == ["low_accuracy"]
    assert axes == {"maximize": ["exact_span_accuracy"], "minimize": ["bits_per_byte"]}


@pytest.mark.parametrize("name", [
    "left_to_right_ppm_masked_byte",
    "context_tree_weighting_masked_byte",
])
def test_named_context_controls_use_higher_order_evidence(name: str) -> None:
    module = __import__(
        f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"]
    )
    candidate = module.Candidate(seed=7)
    data = tuple([7, 1, 2, 8, 1, 3] * 200)
    candidate.fit(MaskedTraining((ByteFile(1, data),), (), len(data)), 8, 4)

    def prediction(prefix: tuple[int, ...]) -> list[float]:
        query = MaskedQuery(2, (*prefix, MASK, 9), (len(prefix),), 0, 1)
        return candidate.query(query, 1)[0]

    after_71 = prediction((7, 1))
    after_81 = prediction((8, 1))
    assert after_71[2] > after_71[3]
    assert after_81[3] > after_81[2]


def test_v3_preserves_evaluator_and_versions_only_future_causal_roles() -> None:
    config = load_config()
    masked = config.raw["masked_refinement"]
    assert config.benchmark_version == "heldout_parallel_masked_infilling_v3"
    assert bench_v3.run_suite is bench.run_suite
    assert masked["shared_candidate"] == "local_sparse_predictive_code_masked_byte"
    assert masked["one_pass_ablation"] == (
        "source_identical_one_pass_predictive_code_masked_byte"
    )
    assert masked["causal_ablation_2"] == (
        "source_identical_frozen_code_predictive_byte"
    )
    assert bench._effective_rounds("one_pass_masked_learner", {
        "one_pass_ablation": "one_pass_masked_learner"
    }, 6) == 1
    assert bench._effective_rounds(masked["one_pass_ablation"], masked, 6) == 1
    assert bench._effective_rounds(masked["shared_candidate"], masked, 6) == 6


def test_v3_plan_schema_locks_all_three_source_identical_roles() -> None:
    plan = _masked_plan()
    plan["benchmark"] = "heldout_parallel_masked_infilling_v3"
    plan["candidates"] = [
        "local_sparse_predictive_code_masked_byte",
        "source_identical_one_pass_predictive_code_masked_byte",
        "source_identical_frozen_code_predictive_byte",
        *plan["masked_refinement_protocol"]["classical_baselines"],
    ]
    protocol = plan["masked_refinement_protocol"]
    protocol["shared_candidate"] = plan["candidates"][0]
    protocol["one_pass_ablation"] = plan["candidates"][1]
    protocol["causal_ablation_2"] = plan["candidates"][2]
    validate_document("experiment_plan", plan, project_root())
    protocol["shared_candidate"] = "iterative_masked_learner"
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", plan, project_root())


def test_v3_plan_generator_freezes_discriminating_matrix(monkeypatch) -> None:
    captured = {}
    configured = load_config()
    monkeypatch.setattr(
        cli, "load_config", lambda root: ResearchConfig(
            copy.deepcopy(configured.raw), configured.path
        )
    )
    monkeypatch.setattr(cli, "ensure_layout", lambda root: None)
    monkeypatch.setattr(cli, "ensure_can_create_plan", lambda root: None)
    monkeypatch.setattr(cli, "latest_hypotheses", lambda root: {"HYP-9999": {}})
    monkeypatch.setattr(cli, "next_experiment_id", lambda root: "EXP-20990101-9999")
    monkeypatch.setattr(cli, "_git_value", lambda *args: None)
    monkeypatch.setattr(cli, "atomic_write_json", lambda path, value: captured.update(plan=value))
    monkeypatch.setattr(cli, "register_plan", lambda plan, path, root: "test-digest")
    masked = configured.raw["masked_refinement"]
    candidates = [
        masked["shared_candidate"], masked["one_pass_ablation"],
        masked["causal_ablation_2"], *masked["classical_baselines"],
    ]
    cli.command_plan_new(Namespace(
        hypothesis="HYP-9999", parent=None, title="masked v3 matrix regression",
        question="Does v3 preserve a discriminating refinement matrix?",
        family="test", candidates=candidates, budget="quick",
        primary_metric=["bits_per_byte", "exact_span_accuracy"],
        prediction="No score; schema synthesis regression only.",
        kill_criterion=["Reject malformed protocol."],
        promotion_criterion=["This test cannot promote."],
        alternative=["Global quick defaults could erase iterative contrast."],
        confound=["No runner seed is realized."],
        positive_conclusion="The generated contract validates.",
        null_conclusion="Treat as infrastructure failure.",
        negative_conclusion="Repair before preregistration.",
    ))
    plan = captured["plan"]
    assert plan["matrix"] == {
        "knowledge_sizes": [8, 32],
        "reasoning_depths": [1, 4, 6],
        "queries_per_cell": 8,
        "seed_policy": {
            "method": "runner_random_v1", "count": 1,
            "minimum": 1_000_000, "maximum": 2_147_483_647,
        },
    }
    validate_document("experiment_plan", plan, project_root())


def test_v3_sparse_code_roles_share_source_constants_and_only_frozen_skips_learning() -> None:
    modules = [__import__(
        f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"]
    ) for name in (
        "local_sparse_predictive_code_masked_byte",
        "source_identical_one_pass_predictive_code_masked_byte",
        "source_identical_frozen_code_predictive_byte",
    )]
    assert all(module.Candidate.__mro__[1] is SparseCodeCore for module in modules)
    assert (PATCH, LATENT, ACTIVE, LEARNING_RATE, SEED_SALT) == (
        16, 32, 4, 0.025, 0x4C504331,
    )
    training = MaskedTraining((ByteFile(1, tuple(range(32))),), (), 32)
    candidates = [module.Candidate(seed=17) for module in modules]
    initial = candidates[0].code.copy()
    for candidate in candidates:
        candidate.fit(training, 8, 6)
    assert not (candidates[0].code == initial).all()
    assert (candidates[0].code == candidates[1].code).all()
    assert (candidates[2].code == initial).all()
    assert len({candidate.fit_ops for candidate in candidates}) == 1


def test_v3_sparse_code_query_is_simultaneous_and_finite() -> None:
    candidate = __import__(
        "nextai_autoresearch.candidates.local_sparse_predictive_code_masked_byte",
        fromlist=["Candidate"],
    ).Candidate(seed=19)
    snapshot = tuple(range(64)) + (MASK,) * 8 + tuple(range(72, 144))
    forward = MaskedQuery(2, snapshot, (64, 67, 71), 0, 6)
    reverse = MaskedQuery(2, snapshot, (71, 67, 64), 0, 6)
    first = candidate.query(forward, 6)
    second = candidate.query(reverse, 6)
    assert first == list(reversed(second))
    assert all(len(row) == 256 and abs(sum(row) - 1.0) < 1e-6 for row in first)
    assert candidate.last_critical_path_steps == 4
    assert candidate.state_bytes() < 4_194_304
