from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from three_family_algorithmic_prior_noise_floor_v1 import (
    _development_series, _world_scores,
)
from nextai_autoresearch.utils import atomic_write_json, project_root, sha256_file, utc_now


KNOWLEDGE_SIZES = (4, 6, 9)
DEVELOPMENT_SEEDS = (1103, 2207, 3301)
BOOTSTRAPS = 512
QUANTILE = 0.95


def _estimate(series: dict[str, list[np.ndarray]]) -> dict:
    families = ("ncmapss_ds08a", "dronepropa", "continuous_event")
    scores = {
        f"{family}/K{knowledge}": _world_scores(series[family], knowledge)
        for family in families for knowledge in KNOWLEDGE_SIZES
    }
    cells, worst_changes = {}, []
    for seed in DEVELOPMENT_SEEDS:
        for knowledge in KNOWLEDGE_SIZES:
            for family_index, family in enumerate(families):
                values = scores[f"{family}/K{knowledge}"]
                rng = np.random.default_rng(seed ^ knowledge * 65537 ^ family_index * 104729)
                differences = []
                for _ in range(BOOTSTRAPS):
                    left = values[rng.integers(0, len(values), len(values))].mean()
                    right = values[rng.integers(0, len(values), len(values))].mean()
                    differences.append(abs(float(left - right)))
                cells[f"{family}/K{knowledge}/seed{seed}"] = float(
                    np.quantile(differences, QUANTILE, method="higher")
                )
            for repeat in range(BOOTSTRAPS):
                left, right = [], []
                for family_index, family in enumerate(families):
                    values = scores[f"{family}/K{knowledge}"]
                    rng = np.random.default_rng(
                        seed ^ knowledge * 8191 ^ repeat * 131071 ^ family_index * 524287
                    )
                    left.append(1 / (1 + float(values[rng.integers(0, len(values), len(values))].mean())))
                    right.append(1 / (1 + float(values[rng.integers(0, len(values), len(values))].mean())))
                worst_changes.append(abs(min(left) - min(right)))
    minimum_effect = max(cells.values())
    return {
        "development_seeds": list(DEVELOPMENT_SEEDS),
        "knowledge_sizes": list(KNOWLEDGE_SIZES),
        "bootstraps_per_seed_and_cell": BOOTSTRAPS,
        "null_quantile": QUANTILE,
        "world_score": "persistence NRMSE of training-role support targets after training-role scale normalization",
        "minimum_nrmse_advantage": minimum_effect,
        "minimum_nrmse_advantage_applies_individually_to": [
            "tensor_raw_window_local_linear_v1",
            "tensor_random_projection_hash_v1",
            "tensor_persistence_v1"
        ],
        "shared_vs_independent_gain_minimum_effect": minimum_effect,
        "cross_family_transfer_gain_minimum_effect": minimum_effect,
        "worst_family_accuracy_tolerance": float(
            np.quantile(worst_changes, QUANTILE, method="higher")
        ),
        "per_cell_null_p95": cells,
        "development_world_scores": {
            key: [float(value) for value in values] for key, values in scores.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = project_root()
    series = _development_series(root)
    first, repeated = _estimate(series), _estimate(series)
    if first != repeated:
        raise AssertionError("deterministic repeat mismatch")
    atomic_write_json(args.output, {
        "schema_version": 1,
        "artifact": "three_family_predictive_index_noise_floor_v1",
        "benchmark": "heldout_three_family_continuous_transfer_v3",
        "created_at": utc_now(),
        "scope": "development training-role worlds only; no v3 test world, scored result or scoring seed access",
        "method": "independent world-level bootstrap null on fixed persistence-resolution scores",
        "script_sha256": sha256_file(Path(__file__)),
        "parent_development_extractor_sha256": sha256_file(
            root / "research/audits/three_family_algorithmic_prior_noise_floor_v1.py"
        ),
        "input_identity": series["_input_identity"],
        "deterministic_repeat_match": True,
        "forbidden_inputs": [
            "EXP-20260831-0001", "EXP-20260831-0002", "EXP-20260831-0003",
            "runner scoring seeds", "v3 test worlds"
        ],
        **first,
    })
    print(args.output)


if __name__ == "__main__":
    main()
