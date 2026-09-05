"""Identity marker for the diagnostic dispatcher; not a legacy K/D benchmark."""
BENCHMARK_VERSION = "pc01_byte_lm_learning_measurement_v1"


def run_suite(candidate, plan):
    raise RuntimeError("PC-01 requires the registered diagnostic runner, not legacy run_suite")
