from pathlib import Path
from typing import Any

from .heldout_dronepropa_factor_recombination_v1 import (
    _run_suite_for_split,
    verify_corpus_hashes as _verify_corpus_hashes,
    verify_static_contract as _verify_static_contract,
)


BENCHMARK_VERSION = "heldout_dronepropa_factor_recombination_v2"
SPLIT_MANIFEST = Path("research/checks/dronepropa_anonymous_split_v2.jsonl")
SPLIT_MANIFEST_SHA256 = "fddd1c98aae13460ec58af25dbbea94f6f25177486da59a1e94f6a25f844a0e4"
ROLE_COUNTS = {
    "train": 64,
    "validation": 8,
    "test": 24,
    "ood_healthy_diagnostic": 8,
    "privileged_oracle_support": 26,
}


def verify_static_contract(root: Path | None = None) -> dict[str, Any]:
    return _verify_static_contract(
        root,
        split_manifest=SPLIT_MANIFEST,
        split_sha256=SPLIT_MANIFEST_SHA256,
        role_counts=ROLE_COUNTS,
    )


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    return _run_suite_for_split(
        candidate_name, plan, SPLIT_MANIFEST, SPLIT_MANIFEST_SHA256, ROLE_COUNTS
    )


def verify_corpus_hashes(root: Path | None = None) -> dict[str, int]:
    return _verify_corpus_hashes(root, SPLIT_MANIFEST)
