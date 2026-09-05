from __future__ import annotations

from typing import Any

from .heldout_mechanism_recombination_v4 import (
    BASELINES, _run_cell, static_control_gate as _v4_gate,
)


BENCHMARK_VERSION = "heldout_mechanism_recombination_v6"
TEST_SEQUENCES = {
    4: tuple("CBAC"),
    8: tuple("CBACABAC"),
    16: tuple("CBACABACBCABCBAC"),
}
EXPOSURE_COUNT = 16


def static_control_gate(seed: int = 1_501_103, source_seed: int = 1103) -> dict[str, Any]:
    gate = _v4_gate(seed, source_seed)
    gate.update({
        "test_composition_lengths": list(TEST_SEQUENCES),
        "all_tests_exceed_training_depth": min(TEST_SEQUENCES) > gate["train_max_composition_length"],
    })
    return gate


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix, protocol = plan["matrix"], plan["mechanism_recombination_protocol"]
    if list(matrix["reasoning_depths"]) != list(TEST_SEQUENCES):
        raise ValueError("v6 requires frozen composition lengths 4, 8 and 16")
    rows = []
    for seed in matrix["seeds"]:
        for size in matrix["knowledge_sizes"]:
            for depth in matrix["reasoning_depths"]:
                row = _run_cell(
                    candidate_name, int(size), EXPOSURE_COUNT,
                    int(matrix["queries_per_cell"]), int(seed),
                    int(protocol["mechanism_source_seed"]),
                    int(protocol["state_budget_bytes"]), TEST_SEQUENCES[int(depth)],
                )
                row["reasoning_depth"] = int(depth)
                row["exposure_count"] = EXPOSURE_COUNT
                rows.append(row)
    return rows


__all__ = ["BASELINES", "BENCHMARK_VERSION", "EXPOSURE_COUNT", "TEST_SEQUENCES", "run_suite", "static_control_gate"]
