"""Prospective dense-training intervention; unchanged task and measurements."""
from . import paired_view_mutable_memory_v6 as selected

BENCHMARK_VERSION = "paired_view_mutable_memory_v8"


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    if plan.get("benchmark") != BENCHMARK_VERSION:
        raise ValueError("Dense-noise cohort binding mismatch")
    return selected.run_suite(candidate_name, plan, trial_sink, phase_sink, fit_sink, data_sink)
