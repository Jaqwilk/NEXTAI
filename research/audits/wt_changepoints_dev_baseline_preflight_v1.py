from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file


TRAIN_SEEDS = tuple(range(6))
DEVELOPMENT_SEEDS = (6, 7)
HORIZONS = (16, 32, 96)
FIT_DEPTH = 32
RIDGE = 1e-3
BOOTSTRAPS = 2048
BOOTSTRAP_SEED = 116031
SATURATION_NRMSE = 0.50
SATURATION_WORST_FILE_NRMSE = 0.75
PRIVATE = {"timestamp", "config", "counter", "flag", "intervention"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _paths(root: Path, seeds: tuple[int, ...]) -> list[Path]:
    base = root / "research/data/wt_changepoints_v1/extracted/wt_changepoints_v1"
    return [base / f"load_in_seed_{seed}.csv" for seed in seeds]


def _load(paths: list[Path]) -> list[np.ndarray]:
    arrays = [np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")
              for path in paths]
    if any(array.ndim != 1 for array in arrays):
        raise AssertionError("each source file must be one row table")
    return arrays


def _partition(train: list[np.ndarray]) -> tuple[str, tuple[str, ...]]:
    names = train[0].dtype.names
    if names is None or any(array.dtype.names != names for array in train):
        raise AssertionError("schema mismatch")
    numeric = [name for name in names if np.issubdtype(train[0].dtype[name], np.number)]
    controls = []
    for name in numeric:
        valid = True
        for array in train:
            markers = set(np.flatnonzero(array["intervention"] == 1.0)[1:].tolist())
            changes = set((np.flatnonzero(np.diff(array[name].astype(float)) != 0.0) + 1).tolist())
            valid &= changes == markers
        if valid:
            controls.append(name)
    if controls != ["load_in"]:
        raise AssertionError(f"mechanical control must be unique, got {controls}")
    marker_union = []
    for array in train:
        marker_union.append(set(np.flatnonzero(array["intervention"] == 1.0).tolist()))
    responses = []
    for name in numeric:
        if name in PRIVATE or name == controls[0]:
            continue
        varies_between_markers = any(
            any((index + 1) not in markers and delta != 0.0
                for index, delta in enumerate(np.diff(array[name].astype(float))))
            for array, markers in zip(train, marker_union)
        )
        if varies_between_markers:
            responses.append(name)
    if len(responses) != 10:
        raise AssertionError(f"mechanical response count must be 10, got {responses}")
    return controls[0], tuple(responses)


def _episodes(arrays: list[np.ndarray], control: str, responses: tuple[str, ...]):
    result = []
    for slot, array in enumerate(arrays):
        values = np.column_stack([array[name].astype(float) for name in responses])
        markers = np.flatnonzero(array["intervention"] == 1.0)
        slot_episodes = []
        for event_index, start in enumerate(markers[1:], start=1):
            pre = values[start - FIT_DEPTH:start]
            target = values[start:start + max(HORIZONS)]
            if pre.shape != (FIT_DEPTH, len(responses)) or target.shape != (96, len(responses)):
                raise AssertionError("episode boundary is incomplete")
            slot_episodes.append({
                "slot": slot, "event_index": event_index,
                "control": float(array[control][start]), "pre": pre, "target": target,
            })
        if len(slot_episodes) != 9:
            raise AssertionError("each file must provide nine history-bearing episodes")
        result.append(slot_episodes)
    return result


def _normalization(train: list[np.ndarray], responses: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    values = np.concatenate([
        np.column_stack([array[name].astype(float) for name in responses]) for array in train
    ])
    mean, scale = values.mean(axis=0), values.std(axis=0)
    if np.any(scale < 1e-9):
        raise AssertionError("response scale is degenerate")
    return mean, scale


def _feature(episode: dict, mean: np.ndarray, scale: np.ndarray,
             control_mean: float, control_scale: float) -> np.ndarray:
    pre = (episode["pre"] - mean) / scale
    return np.concatenate((
        [1.0], pre[-1], pre.mean(axis=0), pre[-1] - pre[0],
        [(episode["control"] - control_mean) / control_scale],
    ))


def _training_objects(train_episodes, mean: np.ndarray, scale: np.ndarray):
    flat = [episode for slot in train_episodes for episode in slot]
    controls = np.asarray([episode["control"] for episode in flat])
    control_mean, control_scale = float(controls.mean()), float(controls.std())
    if control_scale < 1e-9:
        raise AssertionError("control scale is degenerate")
    x = np.stack([_feature(ep, mean, scale, control_mean, control_scale) for ep in flat])
    y = np.stack([((ep["target"] - mean) / scale).reshape(-1) for ep in flat])
    precision = np.linalg.inv(x.T @ x + RIDGE * np.eye(x.shape[1]))
    weights = precision @ x.T @ y
    bank = {}
    for level in sorted(set(np.round(controls, 6))):
        selected = [ep for ep in flat if round(ep["control"], 6) == level]
        residuals = [((ep["target"] - mean) / scale) - ((ep["pre"][-1] - mean) / scale)
                     for ep in selected]
        bank[str(level)] = np.mean(residuals, axis=0)
    return flat, control_mean, control_scale, precision, weights, bank


def _errors(prediction: np.ndarray, target: np.ndarray) -> dict[int, float]:
    return {h: float(np.mean(np.square(prediction[:h] - target[:h]))) for h in HORIZONS}


def _noise_floor(flat, mean: np.ndarray, scale: np.ndarray) -> dict:
    episode_mse = {h: [] for h in HORIZONS}
    for episode in flat:
        target = (episode["target"] - mean) / scale
        persistence = np.repeat(((episode["pre"][-1] - mean) / scale)[None, :], 96, axis=0)
        for horizon, mse in _errors(persistence, target).items():
            episode_mse[horizon].append(mse)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    null_p95 = {}
    for horizon in HORIZONS:
        values = np.asarray(episode_mse[horizon])
        changes = []
        for _ in range(BOOTSTRAPS):
            left = np.sqrt(values[rng.integers(0, len(values), len(values))].mean())
            right = np.sqrt(values[rng.integers(0, len(values), len(values))].mean())
            changes.append(abs(float(left - right)))
        null_p95[str(horizon)] = float(np.quantile(changes, 0.95, method="higher"))
    return {"train_persistence_bootstrap_null_p95": null_p95,
            "minimum_meaningful_nrmse_effect": max(null_p95.values())}


def _freeze(root: Path, output: Path) -> None:
    paths = _paths(root, TRAIN_SEEDS)
    train = _load(paths)
    control, responses = _partition(train)
    mean, scale = _normalization(train, responses)
    train_episodes = _episodes(train, control, responses)
    flat, *_ = _training_objects(train_episodes, mean, scale)
    noise = _noise_floor(flat, mean, scale)
    payload = {
        "schema_version": 1,
        "artifact": "wt_changepoints_dev_baseline_gate_preregistered_v1",
        "created_at": _now(),
        "scope": "train seeds 0-5 only; development seeds 6-7 and test seeds 8-9 unread",
        "script_sha256": sha256_file(Path(__file__)),
        "manifest_sha256": sha256_file(root / "research/data/wt_changepoints_v1/manifest.json"),
        "input_sha256": {path.name: sha256_file(path) for path in paths},
        "control_discovery": "unique numeric column changing at every noninitial marker and never between markers",
        "response_discovery": "numeric nonmetadata columns varying within a non-marker segment",
        "anonymous_control_count": 1,
        "anonymous_response_count": len(responses),
        "train_normalization": "per-response mean and population standard deviation over all train rows",
        "fit_depth": FIT_DEPTH,
        "horizons": list(HORIZONS),
        "baselines": {
            "persistence": "repeat final normalized pre-event response",
            "exact_control_level_bank": "mean train residual curve grouped by rounded public control level",
            "slot_local_rls": "fixed ridge-0.001 32-feature pooled linear initialization with forgetting 1 slot-local reveal updates",
        },
        "trivial_solution_rule": {
            "reject_if_any_baseline_has_nrmse_h96_at_most": SATURATION_NRMSE,
            "and_worst_file_nrmse_h96_at_most": SATURATION_WORST_FILE_NRMSE,
            "and_finite_rollout_rate": 1.0,
        },
        "decision_rule": "reject_before_benchmark on trivial solution; otherwise permit only a later protected benchmark service",
        "forbidden_inputs": ["development outcomes before this artifact", "seed 8", "seed 9", "scored results"],
        **noise,
    }
    atomic_write_json(output, payload)


def _summarize(records: dict[str, list[dict]]) -> dict:
    summary = {}
    for name, rows in records.items():
        item = {f"nrmse_h{h}": float(np.sqrt(np.mean([row["mse"][h] for row in rows])))
                for h in HORIZONS}
        item["worst_file_nrmse_h96"] = max(
            np.sqrt(np.mean([row["mse"][96] for row in rows if row["slot"] == slot]))
            for slot in sorted(set(row["slot"] for row in rows))
        )
        item["finite_rollout_rate"] = float(np.mean([row["finite"] for row in rows]))
        summary[name] = item
    return summary


def _evaluate(root: Path, preregistration: Path, output: Path) -> None:
    prereg = load_json(preregistration)
    if prereg["script_sha256"] != sha256_file(Path(__file__)):
        raise AssertionError("script changed after preregistration")
    train_paths, dev_paths = _paths(root, TRAIN_SEEDS), _paths(root, DEVELOPMENT_SEEDS)
    train, development = _load(train_paths), _load(dev_paths)
    control, responses = _partition(train)
    mean, scale = _normalization(train, responses)
    train_episodes = _episodes(train, control, responses)
    flat, cmean, cscale, precision, weights, bank = _training_objects(
        train_episodes, mean, scale
    )
    if _noise_floor(flat, mean, scale)["minimum_meaningful_nrmse_effect"] != prereg[
        "minimum_meaningful_nrmse_effect"
    ]:
        raise AssertionError("train-only threshold did not reproduce")
    records = {name: [] for name in ("persistence", "exact_control_level_bank", "slot_local_rls")}
    for slot, episodes in enumerate(_episodes(development, control, responses)):
        slot_precision, slot_weights = precision.copy(), weights.copy()
        for episode in episodes:
            target = (episode["target"] - mean) / scale
            last = (episode["pre"][-1] - mean) / scale
            predictions = {
                "persistence": np.repeat(last[None, :], 96, axis=0),
                "exact_control_level_bank": last + bank[str(round(episode["control"], 6))],
                "slot_local_rls": (_feature(episode, mean, scale, cmean, cscale) @ slot_weights).reshape(96, -1),
            }
            for name, prediction in predictions.items():
                records[name].append({"slot": slot, "mse": _errors(prediction, target),
                                      "finite": bool(np.isfinite(prediction).all())})
            x = _feature(episode, mean, scale, cmean, cscale)
            gain = slot_precision @ x / (1.0 + x @ slot_precision @ x)
            slot_weights += gain[:, None] * (target.reshape(-1) - x @ slot_weights)
            slot_precision -= np.outer(gain, x @ slot_precision)
    summary = _summarize(records)
    saturating = [name for name, item in summary.items()
                  if item["nrmse_h96"] <= SATURATION_NRMSE
                  and item["worst_file_nrmse_h96"] <= SATURATION_WORST_FILE_NRMSE
                  and item["finite_rollout_rate"] == 1.0]
    p, y = 32, 96 * len(responses)
    costs = {
        "persistence": {"fit_ops_estimate": 0, "query_ops_per_episode_estimate": 96 * len(responses), "state_bytes": 0},
        "exact_control_level_bank": {"fit_ops_estimate": len(flat) * y, "query_ops_per_episode_estimate": y, "state_bytes": len(bank) * y * 8},
        "slot_local_rls": {"fit_ops_estimate": len(flat) * (p * p + p * y), "query_ops_per_episode_estimate": 2 * p * y, "update_ops_per_episode_estimate": 2 * p * y + 4 * p * p, "state_bytes_per_slot": (p * y + p * p) * 8},
    }
    payload = {
        "schema_version": 1,
        "artifact": "wt_changepoints_dev_baseline_preflight_v1",
        "created_at": _now(),
        "scientific_evidence": False,
        "preregistration_path": str(preregistration.relative_to(root)).replace("\\", "/"),
        "preregistration_sha256": sha256_file(preregistration),
        "script_sha256": sha256_file(Path(__file__)),
        "accessed_data": [path.name for path in train_paths + dev_paths],
        "unread_test_files": ["load_in_seed_8.csv", "load_in_seed_9.csv"],
        "development_episode_count": 18,
        "minimum_meaningful_nrmse_effect": prereg["minimum_meaningful_nrmse_effect"],
        "results": summary,
        "cost_estimates": costs,
        "saturating_baselines": saturating,
        "decision": "reject_before_benchmark" if saturating else "pass_for_later_protected_benchmark_service",
        "note": "Development-only feasibility diagnostic; never hypothesis evidence, replication or promotion input.",
    }
    atomic_write_json(output, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "evaluate"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path)
    args = parser.parse_args()
    root = project_root()
    if args.mode == "freeze":
        _freeze(root, args.output)
    else:
        if args.preregistration is None:
            parser.error("evaluate requires --preregistration")
        _evaluate(root, args.preregistration, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
