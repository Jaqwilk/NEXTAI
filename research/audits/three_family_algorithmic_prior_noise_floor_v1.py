from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from nextai_autoresearch.benchmarks import continuous_event_predictive_state_v1 as event
from nextai_autoresearch.benchmarks.heldout_dronepropa_factor_recombination_v1 import (
    _corpus_rows,
    _load_flights,
)
from nextai_autoresearch.benchmarks.heldout_three_family_continuous_transfer_v1 import (
    DS_SEGMENTS,
    TRAIN_UNITS,
)
from nextai_autoresearch.utils import (
    atomic_write_json,
    load_json,
    project_root,
    sha256_file,
    utc_now,
)


DEVELOPMENT_SEEDS = (1103, 2207, 3301)
BOOTSTRAPS_PER_SEED = 512
QUANTILE = 0.95


def _development_series(root: Path) -> dict[str, list[np.ndarray]]:
    base = root / "research/data/ncmapss_ds08a_portable_v1"
    manifest = load_json(base / "manifest.json")
    arrays = {
        role: np.load(base / f"X_s_{role}.npy", mmap_mode="r")
        for role in ("dev", "test")
    }
    ds = []
    for unit in TRAIN_UNITS:
        role, start, _ = DS_SEGMENTS[unit]
        ds.append(np.asarray(arrays[role][start + 1 : start + 109], dtype=np.float64))

    rows = [row for row in _corpus_rows(root) if row["role"] == "train"][:9]
    drone = [np.asarray(flight.states[33:141], dtype=np.float64)
             for flight in _load_flights(rows)]

    continuous = []
    for index in range(9):
        seed = 1103 + index * 104729
        world = event.make_world(32, seed)
        continuous.append(
            np.asarray(event.make_episode(world, seed).targets, dtype=np.float64)[:, None]
        )
    if not all(len(values) == 9 for values in (ds, drone, continuous)):
        raise AssertionError("development fixture must contain nine training worlds per family")
    return {
        "ncmapss_ds08a": ds,
        "dronepropa": drone,
        "continuous_event": continuous,
        "_input_identity": [{
            "path": "research/data/ncmapss_ds08a_portable_v1/manifest.json",
            "sha256": sha256_file(base / "manifest.json"),
            "declared_files": manifest["files"],
        }],
    }


def _world_scores(series: list[np.ndarray], knowledge: int) -> np.ndarray:
    selected = series[:knowledge]
    stacked = np.concatenate(selected)
    scale = stacked.std(axis=0)
    scale[scale < 1e-9] = 1.0
    return np.asarray([
        float(np.sqrt(np.mean(np.square(np.diff(values / scale, axis=0)))))
        for values in selected
    ])


def _estimate(series: dict[str, list[np.ndarray]]) -> dict:
    families = ("ncmapss_ds08a", "dronepropa", "continuous_event")
    scores = {
        f"{family}/K{knowledge}": _world_scores(series[family], knowledge)
        for family in families for knowledge in (4, 9)
    }
    shared_cells: dict[str, float] = {}
    cross_cells: dict[str, float] = {}
    worst_changes = []
    for seed in DEVELOPMENT_SEEDS:
        for knowledge in (4, 9):
            shared_by_family: dict[str, list[float]] = {family: [] for family in families}
            cross_by_family: dict[str, list[float]] = {family: [] for family in families}
            for family_index, family in enumerate(families):
                values = scores[f"{family}/K{knowledge}"]
                rng = np.random.default_rng(seed ^ knowledge * 65537 ^ family_index * 104729)
                for _ in range(BOOTSTRAPS_PER_SEED):
                    means = [float(values[rng.integers(0, len(values), len(values))].mean())
                             for _ in range(4)]
                    shared_by_family[family].append(abs(means[0] - means[1]))
                    cross_by_family[family].append(abs(means[2] - means[3]))
            for family in families:
                key = f"{family}/K{knowledge}/seed{seed}"
                shared_cells[key] = float(np.quantile(shared_by_family[family], QUANTILE, method="higher"))
                cross_cells[key] = float(np.quantile(cross_by_family[family], QUANTILE, method="higher"))
            for repeat in range(BOOTSTRAPS_PER_SEED):
                left, right = [], []
                for family in families:
                    values = scores[f"{family}/K{knowledge}"]
                    rng = np.random.default_rng(
                        seed ^ knowledge * 8191 ^ repeat * 131071 ^ families.index(family) * 524287
                    )
                    left.append(1.0 / (1.0 + float(values[rng.integers(0, len(values), len(values))].mean())))
                    right.append(1.0 / (1.0 + float(values[rng.integers(0, len(values), len(values))].mean())))
                worst_changes.append(abs(min(left) - min(right)))
    return {
        "development_seeds": list(DEVELOPMENT_SEEDS),
        "bootstraps_per_seed_and_cell": BOOTSTRAPS_PER_SEED,
        "null_quantile": QUANTILE,
        "world_score": "persistence NRMSE of training-role support targets after training-role scale normalization",
        "shared_vs_independent_gain_minimum_effect": max(shared_cells.values()),
        "cross_family_transfer_gain_minimum_effect": max(cross_cells.values()),
        "worst_family_accuracy_tolerance": float(
            np.quantile(worst_changes, QUANTILE, method="higher")
        ),
        "per_cell_shared_null_p95": shared_cells,
        "per_cell_cross_null_p95": cross_cells,
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
    payload = {
        "schema_version": 1,
        "created_at": utc_now(),
        "artifact": "three_family_algorithmic_prior_noise_floor_v1",
        "benchmark": "heldout_three_family_continuous_transfer_v2",
        "scope": "development training-role worlds only; no scoring result or scoring seed access",
        "method": "paired independent world-level bootstrap null on fixed persistence-resolution scores",
        "script_sha256": sha256_file(Path(__file__)),
        "input_identity": series["_input_identity"],
        "deterministic_repeat_match": True,
        "forbidden_inputs": ["EXP-20260831-0001", "EXP-20260831-0002", "runner scoring seeds"],
        **first,
    }
    atomic_write_json(args.output, payload)
    print(args.output)


if __name__ == "__main__":
    main()
