"""Role-only verified-incumbent successor to the frozen whole-I/O v3 evaluator."""

from typing import Any

from . import program_induction_from_whole_io_v3 as _v3
from .program_induction_from_whole_io_v3 import *  # noqa: F403

BENCHMARK_VERSION = "program_induction_from_whole_io_v4"
ROLE_IMPLEMENTATION = "verified_incumbent_program_vm_core_v1"
ROLE_SOURCES = {
    "learned_verified_incumbent_program_vm": "meta",
    "source_identical_support_only_verified_incumbent_program_vm": "support",
    "source_identical_frozen_verified_incumbent_program_vm": "frozen",
}
SOURCE_IDENTICAL_CONTRACT = (
    "complete_solver_objective_bounds_ties_support_execution_output_verifier_"
    "fallback_and_fixed_branch_order_identical_except_meta_support_or_frozen_"
    "initial_incumbent_v1"
)


def verify_role_contract(protocol: dict[str, Any]) -> None:
    roles = {
        str(protocol["shared_candidate"]): "meta",
        str(protocol["support_only_ablation"]): "support",
        str(protocol["frozen_ablation"]): "frozen",
    }
    if roles != ROLE_SOURCES:
        raise RuntimeError("whole-I/O v4 role/source contract mismatch")
    if protocol.get("role_implementation") != ROLE_IMPLEMENTATION:
        raise RuntimeError("whole-I/O v4 roles must resolve to one implementation")
    if protocol.get("source_identical_contract") != SOURCE_IDENTICAL_CONTRACT:
        raise RuntimeError("whole-I/O v4 source-identical contract mismatch")


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    return _v3.run_trial(candidate_name, knowledge_size, reasoning_depth,
                         queries_per_cell, seed, max_depth)


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    verify_role_contract(plan["whole_io_search_protocol"])
    return _v3.run_suite(candidate_name, plan)
