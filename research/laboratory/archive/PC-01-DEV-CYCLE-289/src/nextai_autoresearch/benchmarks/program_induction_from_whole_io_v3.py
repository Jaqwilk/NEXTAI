"""Full-cost, role-only successor to the frozen whole-I/O v2 evaluator."""

from typing import Any

from . import program_induction_from_whole_io_v2 as _v2
from .program_induction_from_whole_io_v2 import *  # noqa: F403

BENCHMARK_VERSION = "program_induction_from_whole_io_v3"


def run_trial(candidate_name: str, knowledge_size: int, reasoning_depth: int,
              queries_per_cell: int, seed: int, max_depth: int) -> dict[str, Any]:
    row = _v2.run_trial(candidate_name, knowledge_size, reasoning_depth,
                        queries_per_cell, seed, max_depth)
    support_width = len(_v2.SUPPORT_INPUTS) + 1
    acquisition = float(4 * knowledge_size * support_width * knowledge_size
                        + (queries_per_cell + 1) * len(_v2.SUPPORT_INPUTS) * knowledge_size)
    charged_queries = float(
        queries_per_cell * (row["mean_query_ops"] + row["mean_warm_query_ops"])
        + 2 * row["mean_query_ops"]
    )
    row.update({
        "data_acquisition_ops": acquisition,
        "mean_bytes_touched": row["mean_bytes_loaded"],
        "peak_state_bytes": max(row["state_bytes"], row["fit_peak_bytes"]),
        "workload_ops_r1": acquisition + row["fit_ops"] + charged_queries + row["update_ops"],
        "workload_ops_r4": acquisition + row["fit_ops"] + 4 * charged_queries + row["update_ops"],
        "workload_ops_r16": acquisition + row["fit_ops"] + 16 * charged_queries + row["update_ops"],
    })
    return row


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = plan["matrix"]
    max_depth = max(map(int, matrix["reasoning_depths"]))
    return [
        run_trial(candidate_name, int(size), int(depth), int(matrix["queries_per_cell"]),
                  int(seed), max_depth)
        for seed in matrix["seeds"]
        for size in matrix["knowledge_sizes"]
        for depth in matrix["reasoning_depths"]
    ]
