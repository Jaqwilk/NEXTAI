from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v1 as bench
from nextai_autoresearch.benchmarks.heldout_repository_sequence_compression_v1 import CORPUS as OLD
from nextai_autoresearch.config import load_config
from nextai_autoresearch.masked_refinement_contract import (
    MASK,
    ByteFile,
    MaskedQuery,
    MaskedTraining,
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
