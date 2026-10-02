"""Role-only particle-proposal successor to the frozen WT v4 evaluator."""

from typing import Any

from . import heldout_wt_changepoints_prequential_v4 as _v4
from .heldout_wt_changepoints_prequential_v4 import *  # noqa: F403


BENCHMARK_VERSION = "heldout_wt_changepoints_prequential_v5"
ROLE_IMPLEMENTATION = "wt_particle_proposal_predictive_state_core_v1"
ROLE_INTERVENTIONS = {
    "wt_learned_particle_proposal_predictive_state_v1": "learned_proposal",
    "wt_source_identical_bootstrap_particle_proposal_v1": "bootstrap_proposal",
    "wt_source_identical_deterministic_posterior_mean_v1": "deterministic_posterior_mean",
}
SOURCE_IDENTICAL_CONTRACT = (
    "state_features_initialization_fit_order_prediction_update_constants_particle_"
    "budget_output_and_accounting_identical_except_preregistered_learned_bootstrap_"
    "or_deterministic_proposal_aggregation_v1"
)


def verify_role_contract(protocol: dict[str, Any]) -> None:
    roles = list(protocol.get("causal_roles", ()))
    if roles != list(ROLE_INTERVENTIONS):
        raise RuntimeError("WT v5 role/intervention contract mismatch")
    if protocol.get("shared_candidate") != roles[0]:
        raise RuntimeError("WT v5 shared role mismatch")
    if protocol.get("role_implementation") != ROLE_IMPLEMENTATION:
        raise RuntimeError("WT v5 roles must resolve to one implementation")
    if protocol.get("source_identical_contract") != SOURCE_IDENTICAL_CONTRACT:
        raise RuntimeError("WT v5 source-identical contract mismatch")


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    verify_role_contract(plan["wt_prequential_protocol"])
    return _v4._v3.run_suite(candidate_name, plan)
