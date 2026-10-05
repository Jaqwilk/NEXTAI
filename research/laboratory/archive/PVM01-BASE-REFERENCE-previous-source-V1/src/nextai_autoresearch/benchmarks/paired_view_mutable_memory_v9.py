"""Independent new units; frozen models/task and service measurement law."""
from . import paired_view_mutable_memory_v8 as selected

BENCHMARK_VERSION = "paired_view_mutable_memory_v9"


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    if plan.get("benchmark") != BENCHMARK_VERSION:
        raise ValueError("Independent confirmation cohort binding mismatch")
    adapted = dict(plan, benchmark=selected.BENCHMARK_VERSION)
    return selected.run_suite(candidate_name, adapted, trial_sink, phase_sink, fit_sink, data_sink)
