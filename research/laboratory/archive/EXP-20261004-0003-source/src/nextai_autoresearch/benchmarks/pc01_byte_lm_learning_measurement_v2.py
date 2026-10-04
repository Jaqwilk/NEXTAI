"""New diagnostic cohort for validated Windows telemetry; no legacy scoring."""
BENCHMARK_VERSION = "pc01_byte_lm_learning_measurement_v2"


def run_suite(candidate, plan):
    raise RuntimeError("PC-01 requires the registered diagnostic runner, not legacy run_suite")
