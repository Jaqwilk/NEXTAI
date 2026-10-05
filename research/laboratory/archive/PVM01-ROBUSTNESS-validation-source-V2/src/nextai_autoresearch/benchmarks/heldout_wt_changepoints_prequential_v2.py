from __future__ import annotations

from . import heldout_wt_changepoints_prequential_v1 as v1


BENCHMARK_VERSION = "heldout_wt_changepoints_prequential_v2"
TRAIN_SEEDS = v1.TRAIN_SEEDS
DEVELOPMENT_SEEDS = v1.DEVELOPMENT_SEEDS
TEST_SEEDS = v1.TEST_SEEDS
KNOWLEDGE_SIZES = v1.KNOWLEDGE_SIZES
HORIZONS = v1.HORIZONS
FIT_DEPTH = v1.FIT_DEPTH
FIT_HORIZON = v1.FIT_HORIZON
BASELINES = v1.BASELINES
verify_static_contract = v1.verify_static_contract
run_suite = v1.run_suite
development_smoke = v1.development_smoke
