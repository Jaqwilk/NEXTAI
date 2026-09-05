from __future__ import annotations

from . import heldout_repository_sequence_compression_v5 as v5


BENCHMARK_VERSION = "heldout_repository_sequence_compression_v6"
CORPUS = v5.CORPUS
SEGMENT_MULTIPLIER = v5.SEGMENT_MULTIPLIER
make_training = v5.make_training
run_suite = v5.run_suite
verify_static_contract = v5.verify_static_contract
