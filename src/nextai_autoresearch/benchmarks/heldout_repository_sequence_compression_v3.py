from __future__ import annotations

from . import heldout_repository_sequence_compression_v2 as v2


BENCHMARK_VERSION = "heldout_repository_sequence_compression_v3"
CORPUS = v2.CORPUS
SEGMENT_MULTIPLIER = v2.SEGMENT_MULTIPLIER
make_training = v2.make_training
run_suite = v2.run_suite
verify_static_contract = v2.verify_static_contract
