from copy import deepcopy

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


def test_v6_roles_remain_prospective() -> None:
    root = project_root()
    config = load_config(root).raw["continuous_local_cellular"]
    for key in ("shared_candidate_v6", "dense_ablation_v6", "frozen_ablation_v6"):
        assert not (root / "src/nextai_autoresearch/candidates" / f"{config[key]}.py").exists()
