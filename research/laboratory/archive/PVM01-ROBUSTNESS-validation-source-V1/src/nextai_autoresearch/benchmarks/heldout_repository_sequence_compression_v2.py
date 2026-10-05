from __future__ import annotations

from pathlib import Path

from . import heldout_repository_sequence_compression_v1 as v1


BENCHMARK_VERSION = "heldout_repository_sequence_compression_v2"
CORPUS = v1.CORPUS
SEGMENT_MULTIPLIER = v1.SEGMENT_MULTIPLIER
make_training = v1.make_training
run_suite = v1.run_suite


def verify_static_contract(root: Path | None = None) -> dict[str, int]:
    roles, acquisition = v1._load_corpus(root)
    return {
        "files": sum(map(len, roles.values())),
        "train_files": len(roles["train"]),
        "validation_files": len(roles["validation"]),
        "test_files": len(roles["test"]),
        "acquisition_bytes": acquisition,
    }
