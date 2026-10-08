from copy import deepcopy

import numpy as np
import pytest

from nextai_autoresearch.baseline_semantics import required_baseline_names
from nextai_autoresearch.benchmarks import continuous_local_cellular_v1 as v1
from nextai_autoresearch.benchmarks import continuous_local_cellular_v5 as v5
from nextai_autoresearch.benchmarks import continuous_local_cellular_v6 as v6
from nextai_autoresearch.config import load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


def test_v6_is_role_only_and_freezes_predictive_coordinate_chart_roles() -> None:
    root = project_root()
    config = load_config(root).raw["continuous_local_cellular"]
    plan = deepcopy(load_json(root / "research/plans/EXP-20260901-0049.json"))
    plan["experiment_id"] = "EXP-20990101-0006"
    plan["benchmark"] = v6.BENCHMARK_VERSION
    plan["candidates"] = [
        config["shared_candidate_v6"], config["dense_ablation_v6"],
        config["frozen_ablation_v6"], *config["classical_baselines"],
    ]
    plan["continuous_local_protocol"].update({
        "shared_candidate": config["shared_candidate_v6"],
        "dense_ablation": config["dense_ablation_v6"],
        "frozen_ablation": config["frozen_ablation_v6"],
        "source_identical_contract": "anonymous_inputs_chart_capacity_feature_library_fit_prediction_update_accounting_identical_except_aligned_shuffled_or_frozen_predictive_coordinate_chart_v6",
        "invalidation_rules": list(config["invalidation_rules"]),
    })
    validate_document("experiment_plan", plan, root)
    assert v6.run_suite is v5.run_suite is v1.run_suite
    assert v6.run_trial is v5.run_trial is v1.run_trial
    assert v6.make_world is v5.make_world is v1.make_world
    assert required_baseline_names(plan) == list(config["classical_baselines"])


def _chart_rows(reverse: bool = False):
    rows = []
    for index in range(384):
        x = ((index * 37) % 383) / 191.0 - 1.0
        y = ((index * 101) % 379) / 189.0 - 1.0

        def observed(a, b):
            return (a ** 3, a, b ** 3, b)

        left = observed(0.7 * x - 0.1, 0.4 * y + 0.2)
        center = observed(x, y)
        right = observed(-0.3 * x + 0.1, 0.6 * y - 0.1)
        next_x = 0.2 * left[1] + 0.5 * center[1] + 0.3 * right[1]
        next_y = 0.3 * left[3] + 0.4 * center[3] + 0.2 * right[3]
        rows.append(v1.Transition(left, center, right, observed(next_x, next_y)))
    return tuple(reversed(rows)) if reverse else tuple(rows)


def test_v6_predictive_chart_semantics_are_frozen_before_implementation() -> None:
    core = pytest.importorskip("nextai_autoresearch.candidates.predictive_coordinate_chart_core")
    aligned_module = pytest.importorskip("nextai_autoresearch.candidates.learned_predictive_coordinate_chart_v1")
    shuffled_module = pytest.importorskip(
        "nextai_autoresearch.candidates.source_identical_shuffled_predictive_coordinate_chart_v1"
    )
    frozen_module = pytest.importorskip(
        "nextai_autoresearch.candidates.source_identical_frozen_predictive_coordinate_chart_v1"
    )
    roles = (aligned_module.Candidate, shuffled_module.Candidate, frozen_module.Candidate)
    assert all(issubclass(role, core.PredictiveCoordinateChart) for role in roles)
    assert (core.CHART_DIM, core.TRANSITION_WIDTH, core.DECODER_WIDTH, core.RIDGE,
            core.UPDATE_ETA, core.OUTPUT_BOUND, core.SCORE_PERMUTATION) == (
        2, 28, 6, 0.001, 0.05, 1.5, (2, 5, 1, 4, 0, 3),
    )
    rows = _chart_rows()
    aligned, shuffled, frozen = (role(17) for role in roles)
    for candidate in (aligned, shuffled, frozen):
        candidate.fit(rows, 64, 16)
    assert aligned.selected_pair == (1, 3)
    assert shuffled.pair_scores == aligned.pair_scores
    assert shuffled.selected_pair != aligned.selected_pair
    assert frozen.selected_pair == (0, 1)
    reordered = roles[0](17)
    reordered.fit(_chart_rows(True), 64, 16)
    assert reordered.selected_pair == aligned.selected_pair
    assert np.allclose(reordered.transition_weights, aligned.transition_weights)
    assert np.allclose(reordered.decoder_weights, aligned.decoder_weights)
    before = aligned.transition_weights.copy(), aligned.decoder_weights.copy()
    aligned.update(rows[-1], None)
    assert not np.array_equal(before[0], aligned.transition_weights)
    assert not np.array_equal(before[1], aligned.decoder_weights)
    task = v1.Task(64, 0, 1, ((0, rows[0].center),))
    answer = aligned.query(task, 4)
    assert len(answer) == 4 and np.isfinite(answer).all()
    assert aligned.fit_ops > 0 and aligned.update_ops > 0 and aligned.last_ops > 0
    assert aligned.state_bytes() > 0 and aligned.last_bytes_touched > 0
