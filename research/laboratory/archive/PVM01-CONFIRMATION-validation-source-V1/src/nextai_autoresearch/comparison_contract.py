"""Shared qualification rules; new plans freeze their useful-quality contract."""
from __future__ import annotations


def is_legacy_loss_cohort(benchmark: str) -> bool:
    return benchmark.startswith(("heldout_parallel_masked_", "heldout_wt_changepoints_", "heldout_repository_sequence_"))


def quality_contract(plan: dict, default_minimum: float = 0.95) -> dict:
    declared = plan.get("eligibility_contract")
    if declared is not None:
        return declared
    # One compatibility rule for frozen cohorts predating the explicit field.
    # Do not let today's global threshold change historical qualification.
    return {"metric": "accuracy", "minimum": None if is_legacy_loss_cohort(str(plan.get("benchmark", ""))) else 0.95}


def passes_quality(summary: dict, contract: dict) -> bool:
    value = summary.get(contract["metric"])
    if value is None:
        return False
    minimum = contract.get("minimum")
    return minimum is None or float(value) >= float(minimum)
