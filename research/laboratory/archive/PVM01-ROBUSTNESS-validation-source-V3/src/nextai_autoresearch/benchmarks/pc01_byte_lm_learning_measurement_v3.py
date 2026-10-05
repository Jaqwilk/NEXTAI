"""Prospective identified GPU metadata cohort. Maintenance is not scoring authority."""
BENCHMARK_VERSION = "pc01_byte_lm_learning_measurement_v3"


def run_suite(candidate, plan):
    raise RuntimeError("PC-01 requires the registered diagnostic runner, not legacy run_suite")
