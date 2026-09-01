from collections import Counter
from argparse import Namespace
from copy import deepcopy

import pytest

from nextai_autoresearch import cli
from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v8 as v8
from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v9 as v9
from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v10 as v10
from nextai_autoresearch.config import ResearchConfig, load_config
from nextai_autoresearch.masked_refinement_contract import MASK
from nextai_autoresearch.utils import project_root


def test_delimiter_groups_use_tokens_not_strings_or_comments() -> None:
    groups = v8.delimiter_groups(b'x = "([)]"  # {]}\ny = ([{}])\n')
    assert groups == ((b"([{}])", 3),)


def test_immutable_corpus_has_three_ood_depth_scales() -> None:
    training, tests, _ = v8.make_stack_training(8, 123)
    selected = sum(len(file.data) for file in training.train_files)
    assert 8000 <= selected <= 8192
    assert Counter(depth for _, depth in tests) == {3: 54, 4: 21, 5: 6}
    assert v8.TRAIN_MAX_DEPTH < min(v8.TEST_DEPTHS)


def test_stack_cases_hide_one_permuted_closer() -> None:
    _, tests, permutation = v8.make_stack_training(8, 123)
    for depth in v8.TEST_DEPTHS:
        cases = v8._stack_cases(tests, depth, 8, 123, permutation)
        assert len(cases) == 8
        for _, snapshot, positions, target in cases:
            assert len(positions) == len(target) == 1
            assert snapshot[positions[0]] == MASK
            assert target[0] != MASK


@pytest.mark.parametrize(("benchmark", "task_unit"), [
    ("heldout_parallel_masked_infilling_v8", "balanced_real_python_delimiter_trace"),
    ("heldout_parallel_masked_infilling_v9", "balanced_real_python_closure_chain"),
    ("heldout_parallel_masked_infilling_v10", "balanced_real_python_closure_chain"),
])
def test_plan_new_freezes_stack_depth_contract(monkeypatch, benchmark, task_unit) -> None:
    captured = {}
    configured = load_config(project_root())
    raw = deepcopy(configured.raw)
    raw["project"]["benchmark_version"] = benchmark
    monkeypatch.setattr(cli, "load_config", lambda root: ResearchConfig(raw, configured.path))
    monkeypatch.setattr(cli, "ensure_layout", lambda root: None)
    monkeypatch.setattr(cli, "ensure_can_create_plan", lambda root: None)
    monkeypatch.setattr(cli, "latest_hypotheses", lambda root: {"HYP-9999": {}})
    monkeypatch.setattr(cli, "next_experiment_id", lambda root: "EXP-20990101-9999")
    monkeypatch.setattr(cli, "_git_value", lambda *args: None)
    monkeypatch.setattr(cli, "atomic_write_json", lambda path, value: captured.update(plan=value))
    monkeypatch.setattr(cli, "register_plan", lambda plan, path, root: "test-digest")
    candidates = [
        raw["stack_depth"][key] for key in
        ("shared_candidate", "causal_ablation_1", "causal_ablation_2")
    ] + list(raw["masked_refinement"]["classical_baselines"])
    cli.command_plan_new(Namespace(
        hypothesis="HYP-9999", parent=None, title="stack-depth schema regression",
        question="Does learned pushdown state extrapolate beyond training depth?",
        family="learned_pushdown", candidates=candidates, budget="quick",
        primary_metric=["accuracy", "bits_per_byte", "mean_query_ops", "state_bytes"],
        prediction="No result is observed in this schema-only test.",
        kill_criterion=["Reject if any depth is unavailable."],
        promotion_criterion=["A quick cannot promote."],
        alternative=["Finite context may explain the result."],
        confound=["Delimiter frequency may differ by depth."],
        positive_conclusion="Permit unchanged replication only.",
        null_conclusion="Treat the direction as unresolved.",
        negative_conclusion="Discard this exact pushdown rule.",
    ))
    plan = captured["plan"]
    assert plan["matrix"]["reasoning_depths"] == [3, 4, 5]
    assert plan["masked_refinement_protocol"]["training_max_depth"] == 2
    assert plan["masked_refinement_protocol"]["test_depths"] == [3, 4, 5]
    assert plan["masked_refinement_protocol"]["task_unit"] == task_unit


def test_v8_target_is_first_order_alias_but_v9_requires_full_stack() -> None:
    identity = tuple(range(256))
    raw = b"([{}])"
    v8_case = v8._stack_cases([(raw, 3)], 3, 1, 7, identity)[0]
    assert v8_case[2:] == ((3,), (ord("}"),))
    assert v8_case[1][2] == ord("{")

    _, snapshot, positions, target = v9.closure_chain_case(raw, 3, 101, identity)
    assert positions == (3, 4, 5)
    assert target == tuple(map(ord, "}])"))
    assert all(snapshot[position] == MASK for position in positions)

    close = {ord("("): ord(")"), ord("["): ord("]"), ord("{"): ord("}")}
    bounded = []
    stack = []
    for value in snapshot:
        if value in close:
            stack.append(value)
            stack = stack[-2:]
        elif value == MASK and stack:
            bounded.append(close[stack.pop()])
    assert tuple(bounded) != target


def test_v9_masks_one_matching_close_at_every_depth() -> None:
    _, tests, permutation = v8.make_stack_training(8, 123)
    for depth in v9.TEST_DEPTHS:
        for _, snapshot, positions, target in v9._stack_cases(
            tests, depth, 8, 123, permutation
        ):
            assert len(positions) == len(target) == depth
            assert all(snapshot[position] == MASK for position in positions)


def test_v10_changes_only_the_privileged_adapter_cohort() -> None:
    assert v10.run_suite is v9.run_suite
    assert v10.BENCHMARK_VERSION == "heldout_parallel_masked_infilling_v10"
