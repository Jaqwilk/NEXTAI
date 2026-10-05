from __future__ import annotations

from . import heldout_repository_sequence_compression_v4 as v4


BENCHMARK_VERSION = "heldout_repository_sequence_compression_v5"
CORPUS = v4.CORPUS
SEGMENT_MULTIPLIER = v4.SEGMENT_MULTIPLIER
make_training = v4.make_training
run_suite = v4.run_suite
verify_static_contract = v4.verify_static_contract
