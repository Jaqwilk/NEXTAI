"""Maintenance-only identity for the frozen WT-01 mechanism contract."""

BENCHMARK_VERSION = "wt01_causal_contract_v1"


def run_suite(candidate, plan):
    raise RuntimeError(
        "WT-01 causal contract is not executable: data, effect threshold and scoring authority remain blocked"
    )
