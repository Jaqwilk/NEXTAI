from __future__ import annotations

from . import heldout_repository_sequence_compression_v3 as v3


BENCHMARK_VERSION = "heldout_repository_sequence_compression_v4"
CORPUS = v3.CORPUS
SEGMENT_MULTIPLIER = v3.SEGMENT_MULTIPLIER
make_training = v3.make_training
run_suite = v3.run_suite
verify_static_contract = v3.verify_static_contract
