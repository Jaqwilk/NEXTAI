"""Maintenance-only identity for prospective WT-01 contract preparation."""

BENCHMARK_VERSION = "wt01_causal_revalidation_preparation_v1"


def run_suite(candidate, plan):
    raise RuntimeError(
        "WT-01 preparation has no scoring authority; freeze a claim-specific contract first"
    )
