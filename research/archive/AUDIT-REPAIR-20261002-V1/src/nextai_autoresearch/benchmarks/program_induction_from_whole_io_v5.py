"""Role-only certified-pattern-bound successor to the frozen whole-I/O v4 evaluator."""

from typing import Any

from . import program_induction_from_whole_io_v3 as _v3
from . import program_induction_from_whole_io_v4 as _v4
from .program_induction_from_whole_io_v4 import *  # noqa: F403

BENCHMARK_VERSION = "program_induction_from_whole_io_v5"
ROLE_IMPLEMENTATION = "certified_pattern_bound_program_vm_core_v1"
ROLE_SOURCES = {
    "learned_certified_pattern_bound_program_vm": "meta",
    "source_identical_support_only_certified_pattern_bound_program_vm": "support",
    "source_identical_frozen_certified_pattern_bound_program_vm": "frozen",
}
SOURCE_IDENTICAL_CONTRACT = (
    "complete_solver_objective_initial_incumbent_branch_order_ties_support_"
    "execution_output_identical_except_meta_support_or_frozen_admissible_"
    "pattern_bound_v1"
)


def verify_role_contract(protocol: dict[str, Any]) -> None:
    roles = {
        str(protocol["shared_candidate"]): "meta",
        str(protocol["support_only_ablation"]): "support",
        str(protocol["frozen_ablation"]): "frozen",
    }
    if roles != ROLE_SOURCES:
        raise RuntimeError("whole-I/O v5 role/source contract mismatch")
    if protocol.get("role_implementation") != ROLE_IMPLEMENTATION:
        raise RuntimeError("whole-I/O v5 roles must resolve to one implementation")
    if protocol.get("source_identical_contract") != SOURCE_IDENTICAL_CONTRACT:
        raise RuntimeError("whole-I/O v5 source-identical contract mismatch")


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    return _v4.run_trial(candidate_name, knowledge_size, reasoning_depth,
                         queries_per_cell, seed, max_depth)


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    verify_role_contract(plan["whole_io_search_protocol"])
    return _v3.run_suite(candidate_name, plan)
