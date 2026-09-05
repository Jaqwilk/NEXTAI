"""Role-only local-credit successor to the frozen WT v3 evaluator."""

from typing import Any

from . import heldout_wt_changepoints_prequential_v3 as _v3
from .heldout_wt_changepoints_prequential_v3 import *  # noqa: F403


BENCHMARK_VERSION = "heldout_wt_changepoints_prequential_v4"
ROLE_IMPLEMENTATION = "wt_local_credit_trace_core_v1"
ROLE_INTERVENTIONS = {
    "wt_error_triggered_eligibility_trace_v1": "aligned_error_gated",
    "wt_source_identical_frozen_eligibility_trace_v1": "frozen_zero_trace",
    "wt_source_identical_shuffled_eligibility_trace_v1": "shuffled_temporal_credit",
    "wt_source_identical_dense_eligibility_trace_v1": "aligned_dense_credit",
}
SOURCE_IDENTICAL_CONTRACT = (
    "features_initialization_fit_order_prediction_rollout_update_constants_and_"
    "accounting_identical_except_preregistered_error_gate_temporal_credit_"
    "alignment_or_dense_credit_v1"
)


def verify_role_contract(protocol: dict[str, Any]) -> None:
    roles = list(protocol.get("causal_roles", ()))
    if roles != list(ROLE_INTERVENTIONS):
        raise RuntimeError("WT v4 role/intervention contract mismatch")
    if protocol.get("shared_candidate") != roles[0]:
        raise RuntimeError("WT v4 shared role mismatch")
    if protocol.get("role_implementation") != ROLE_IMPLEMENTATION:
        raise RuntimeError("WT v4 roles must resolve to one implementation")
    if protocol.get("source_identical_contract") != SOURCE_IDENTICAL_CONTRACT:
        raise RuntimeError("WT v4 source-identical contract mismatch")


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    verify_role_contract(plan["wt_prequential_protocol"])
    return _v3.run_suite(candidate_name, plan)
