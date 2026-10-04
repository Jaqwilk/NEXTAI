from pathlib import Path
from typing import Any

from .heldout_dronepropa_factor_recombination_v5 import (
    ROLE_COUNTS,
    SPLIT_MANIFEST,
    SPLIT_MANIFEST_SHA256,
    run_suite as _run_suite,
    verify_corpus_hashes as _verify_corpus_hashes,
    verify_static_contract as _verify_static_contract,
)

BENCHMARK_VERSION = "heldout_dronepropa_factor_recombination_v6"


def verify_static_contract(root: Path | None = None) -> dict[str, Any]:
    return _verify_static_contract(root)


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    return _run_suite(candidate_name, plan)


def verify_corpus_hashes(root: Path | None = None) -> dict[str, int]:
    return _verify_corpus_hashes(root)
