import math
from dataclasses import replace
from copy import deepcopy

import pytest
from jsonschema import ValidationError

from nextai_autoresearch.benchmarks import continuous_local_cellular_v1 as bench
from nextai_autoresearch.benchmarks import continuous_local_cellular_v2 as bench_v2
from nextai_autoresearch.baseline_semantics import required_baseline_names
from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata
from nextai_autoresearch.config import load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


class _PrivilegedFixture(CandidateBase):
    metadata = CandidateMetadata("fixture", "test", "Evaluator-only exact smoke fixture")

    def fit(self, facts, universe_size, max_depth):
        self.world = facts.world
        self.fit_ops = len(self.world.training)

    def query(self, task, steps):
        self.last_ops = steps * (2 * steps + 1)
        self.last_bytes_touched = self.last_ops * 8
        return bench.oracle_target(self.world, task, steps)

    def update(self, source, target):
        self.update_ops = 1

    def state_bytes(self):
        return 64


def test_train_and_scoring_supports_are_disjoint_and_continuous() -> None:
    world = bench.make_world(1103)
    training_amplitude = max(abs(value) for row in world.training for vector in (row.left, row.center, row.right) for value in bench.decode(world, vector))
    task = bench.make_task(world, 64, 16, 2207, 0)
    scoring_amplitude = abs(bench.decode(world, task.initial[0][1])[0])
    assert training_amplitude <= 0.65
    assert scoring_amplitude >= 0.85
    assert len({row.center for row in world.training}) == bench.TRAINING_TRANSITIONS


def test_inactive_area_scale_does_not_change_the_local_causal_cone() -> None:
    world = bench.make_world(1103)
    for size in (64, 256, 1024):
        task = bench.make_task(world, size, 16, 3301, 0)
        assert len(task.initial) == 1
        assert 0 <= task.source < size and 0 <= task.target < size
        assert all(math.isfinite(value) for value in bench.oracle_target(world, task, 16))


def test_one_channel_corruption_changes_public_input_not_clean_target() -> None:
    world = bench.make_world(1103)
    clean = bench.make_task(world, 64, 8, 4409, 2)
    damaged = bench.make_task(world, 64, 8, 4409, 2, damaged=True)
    assert clean.initial != damaged.initial
    assert (clean.size, clean.source, clean.target) == (damaged.size, damaged.source, damaged.target)
    changed = sum(a != b for a, b in zip(clean.initial[0][1], damaged.initial[0][1]))
    assert changed == 1
    clean_target = bench.oracle_target(world, clean, 8)
    assert all(math.isfinite(value) for value in clean_target)


def test_meaningful_gain_exceeds_development_perturbation_floor() -> None:
    world = bench.make_world(1103)
    errors = []
    for index in range(32):
        task = bench.make_task(world, 64, 8, 2207, index)
        position, vector = task.initial[0]
        jittered = tuple(value + (0.002 if channel == index % bench.CHANNELS else 0.0)
                         for channel, value in enumerate(vector))
        changed = replace(task, initial=((position, jittered),))
        errors.append(bench._error(bench.oracle_target(world, changed, 8), bench.oracle_target(world, task, 8)))
    assert bench.MINIMUM_NRMSE_GAIN >= 5 * max(errors)


def test_exact_privileged_fixture_smokes_final_trial_schema(monkeypatch) -> None:
    monkeypatch.setattr(bench, "load_candidate", lambda name, seed: _PrivilegedFixture(seed))
    row = bench.run_trial("privileged_continuous_local_support", 64, 4, 2, 1103, 16)
    assert row["status"] == "complete"
    assert row["accuracy"] == row["warm_accuracy"] == 1.0
    assert row["stable_rollout_rate"] == 1.0
    assert row["workload_ops_r1"] < row["workload_ops_r4"] < row["workload_ops_r16"]


def test_plan_schema_freezes_matrix_and_all_mandatory_roles() -> None:
    root = project_root()
    config = load_config(root).raw["continuous_local_cellular"]
    old_roles = {
        "shared_candidate": "learned_sparse_continuous_local_rule",
        "dense_ablation": "source_identical_dense_continuous_local_rule",
        "frozen_ablation": "source_identical_frozen_continuous_local_rule",
    }
    plan = deepcopy(load_json(root / "research" / "plans" / "EXP-20260901-0021.json"))
    plan.pop("mechanism_recombination_protocol", None)
    plan["benchmark"] = bench.BENCHMARK_VERSION
    plan["matrix"]["knowledge_sizes"] = [64, 256, 1024]
    plan["matrix"]["reasoning_depths"] = [4, 8, 16]
    plan["matrix"]["queries_per_cell"] = 8
    plan["candidates"] = [
        *old_roles.values(),
        *config["classical_baselines"],
    ]
    plan["primary_metrics"] = list(config["pareto_capability_metrics"])
    plan["continuous_local_protocol"] = {
        **old_roles,
        "classical_baselines": list(config["classical_baselines"]),
        "source_identical_contract": "anonymous_channels_constants_fit_update_output_identical_except_sparse_dense_or_frozen_learning_v1",
        "state_budget_bytes": config["state_budget_bytes"],
        "minimum_nrmse_gain": config["minimum_nrmse_gain"],
        "pareto_capability_metrics": list(config["pareto_capability_metrics"]),
        "invalidation_rules": list(config["invalidation_rules"]),
    }
    directions = load_config(root).raw["metrics"]
    plan["metric_directions"] = {
        metric: "maximize" if metric in directions["maximize"] else "minimize"
        for metric in plan["primary_metrics"]
    }
    validate_document("experiment_plan", plan, root)
    assert required_baseline_names(plan) == list(config["classical_baselines"])
    wrong_matrix = deepcopy(plan)
    wrong_matrix["matrix"]["knowledge_sizes"] = [64, 256, 512]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", wrong_matrix, root)
    missing_control = deepcopy(plan)
    missing_control["candidates"].remove("continuous_local_ridge")
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", missing_control, root)

    substituted = deepcopy(plan)
    substituted["continuous_local_protocol"]["shared_candidate"] = config["shared_candidate"]
    substituted["candidates"][0] = config["shared_candidate"]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", substituted, root)


def test_v2_is_role_only_and_freezes_new_roles_without_reinterpreting_v1() -> None:
    root = project_root()
    config = load_config(root).raw["continuous_local_cellular"]
    plan = deepcopy(load_json(root / "research" / "plans" / "EXP-20260901-0022.json"))
    plan["experiment_id"] = "EXP-20990101-0001"
    plan["benchmark"] = bench_v2.BENCHMARK_VERSION
    plan["candidates"] = [
        config["shared_candidate"], config["dense_ablation"], config["frozen_ablation"],
        *config["classical_baselines"],
    ]
    plan["continuous_local_protocol"].update({
        "shared_candidate": config["shared_candidate"],
        "dense_ablation": config["dense_ablation"],
        "frozen_ablation": config["frozen_ablation"],
        "source_identical_contract": "anonymous_inputs_constants_rows_initialization_update_order_output_bounds_identical_except_factorized_monolithic_or_frozen_learning_v2",
        "invalidation_rules": list(config["invalidation_rules"]),
    })
    validate_document("experiment_plan", plan, root)
    assert bench_v2.run_suite is bench.run_suite
    assert bench_v2.run_trial is bench.run_trial
    assert bench_v2.make_world is bench.make_world
    assert required_baseline_names(plan) == list(config["classical_baselines"])

    historical_role = deepcopy(plan)
    historical_role["continuous_local_protocol"]["shared_candidate"] = "learned_sparse_continuous_local_rule"
    historical_role["candidates"][0] = "learned_sparse_continuous_local_rule"
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", historical_role, root)
