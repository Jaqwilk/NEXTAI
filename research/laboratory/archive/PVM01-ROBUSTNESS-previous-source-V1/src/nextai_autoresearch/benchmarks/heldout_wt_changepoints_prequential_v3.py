from __future__ import annotations

from . import heldout_wt_changepoints_prequential_v2 as v2


BENCHMARK_VERSION = "heldout_wt_changepoints_prequential_v3"
TRAIN_SEEDS = v2.TRAIN_SEEDS
DEVELOPMENT_SEEDS = v2.DEVELOPMENT_SEEDS
TEST_SEEDS = v2.TEST_SEEDS
KNOWLEDGE_SIZES = v2.KNOWLEDGE_SIZES
HORIZONS = v2.HORIZONS
FIT_DEPTH = v2.FIT_DEPTH
FIT_HORIZON = v2.FIT_HORIZON
BASELINES = (*v2.BASELINES, "wt_coverage_aware_spectral_psr_v1", "wt_train_only_discretized_cssr_v1")
verify_static_contract = v2.verify_static_contract
run_suite = v2.run_suite
development_smoke = v2.development_smoke
