from copy import deepcopy

from nextai_autoresearch.baseline_semantics import required_baseline_names
from nextai_autoresearch.benchmarks import continuous_local_cellular_v1 as v1
from nextai_autoresearch.benchmarks import continuous_local_cellular_v4 as v4
from nextai_autoresearch.benchmarks import continuous_local_cellular_v5 as v5
from nextai_autoresearch.config import load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


def test_v5_is_role_only_and_freezes_error_novelty_tree_roles() -> None:
    root = project_root()
    config = load_config(root).raw["continuous_local_cellular"]
    plan = deepcopy(load_json(root / "research/plans/EXP-20260901-0037.json"))
    plan["experiment_id"] = "EXP-20990101-0004"
    plan["benchmark"] = v5.BENCHMARK_VERSION
    plan["candidates"] = [
        config["shared_candidate_v5"], config["dense_ablation_v5"], config["frozen_ablation_v5"],
        *config["classical_baselines"],
    ]
    plan["continuous_local_protocol"].update({
        "shared_candidate": config["shared_candidate_v5"],
        "dense_ablation": config["dense_ablation_v5"],
        "frozen_ablation": config["frozen_ablation_v5"],
        "source_identical_contract": "anonymous_inputs_features_constants_initialization_fit_prediction_update_accounting_identical_except_error_novelty_split_shuffled_split_or_frozen_partition_v5",
        "invalidation_rules": list(config["invalidation_rules"]),
    })
    validate_document("experiment_plan", plan, root)
    assert v5.run_suite is v4.run_suite is v1.run_suite
    assert v5.run_trial is v4.run_trial is v1.run_trial
    assert v5.make_world is v4.make_world is v1.make_world
    assert required_baseline_names(plan) == list(config["classical_baselines"])
