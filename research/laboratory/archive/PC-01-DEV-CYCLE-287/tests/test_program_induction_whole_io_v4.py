import copy

import pytest

from nextai_autoresearch.benchmarks import program_induction_from_whole_io_v3 as v3
from nextai_autoresearch.benchmarks import program_induction_from_whole_io_v4 as v4
from nextai_autoresearch.config import load_config
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import load_json, project_root


def _protocol() -> dict:
    config = load_config(project_root()).raw["whole_io_search"]
    return {
        "shared_candidate": config["shared_candidate_v4"],
        "support_only_ablation": config["support_only_ablation_v4"],
        "frozen_ablation": config["frozen_ablation_v4"],
        "classical_baselines": list(config["classical_baselines"]),
        "source_identical_contract": v4.SOURCE_IDENTICAL_CONTRACT,
        "role_implementation": v4.ROLE_IMPLEMENTATION,
        "state_budget_bytes": config["state_budget_bytes"],
        "pareto_capability_metrics": list(config["pareto_capability_metrics"]),
        "invalidation_rules": list(config["invalidation_rules"]),
    }


def test_v4_is_additive_for_existing_v3_control_semantics() -> None:
    old = v3.run_trial("enumerative_mdl_vm", 8, 4, 2, 1103, 6)
    new = v4.run_trial("enumerative_mdl_vm", 8, 4, 2, 1103, 6)
    stable = lambda row: {
        key: value for key, value in row.items()
        if "latency" not in key and not key.endswith("_seconds")
    }
    assert stable(new) == stable(old)


def test_v4_roles_share_one_implementation_and_only_source_varies() -> None:
    protocol = _protocol()
    v4.verify_role_contract(protocol)
    assert set(v4.ROLE_SOURCES.values()) == {"meta", "support", "frozen"}
    wrong = copy.deepcopy(protocol)
    wrong["shared_candidate"] = "learned_amortized_constraint_order_vm"
    with pytest.raises(RuntimeError, match="role/source"):
        v4.verify_role_contract(wrong)
    wrong = copy.deepcopy(protocol)
    wrong["role_implementation"] = "approximate_vm"
    with pytest.raises(RuntimeError, match="one implementation"):
        v4.verify_role_contract(wrong)


def test_v4_prospective_plan_contract_is_cohort_separated() -> None:
    root = project_root()
    config = load_config(root).raw["whole_io_search"]
    plan = load_json(root / "research" / "plans" / "EXP-20260901-0036.json")
    plan["experiment_id"] = "EXP-20990101-0004"
    plan["benchmark"] = v4.BENCHMARK_VERSION
    roles = [config["shared_candidate_v4"], config["support_only_ablation_v4"], config["frozen_ablation_v4"]]
    plan["candidates"] = [*roles, *config["classical_baselines"]]
    plan["whole_io_search_protocol"] = _protocol()
    validate_document("experiment_plan", plan, root)
    historical = load_json(root / "research" / "plans" / "EXP-20260901-0036.json")
    assert historical["benchmark"] == v3.BENCHMARK_VERSION
