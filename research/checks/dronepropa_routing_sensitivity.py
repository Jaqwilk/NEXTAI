"""Preregistered no-score routing sensitivity audit for DronePropA."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dronepropa_protocol_gate import NAME_RE, SELECTED_ROWS, load_matrices  # noqa: E402

VISIBLE_CEILING = 0.25
PERMUTATIONS = 5000
PERMUTATION_SEED = 7601
BINS = np.array([-np.inf, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, np.inf])


def adaptation_view(qdrone: np.ndarray) -> tuple[list[np.ndarray], list[int]]:
    sample_count = qdrone.shape[1]
    usable_start = math.ceil(0.10 * sample_count) + 31
    usable_stop = math.floor(0.90 * sample_count) - 1
    adaptation_stop = usable_start + math.floor(0.20 * (usable_stop - usable_start))
    edges = np.linspace(usable_start, adaptation_stop + 1, 33)
    anchors = [int(math.floor((edges[index] + edges[index + 1] - 1) / 2)) for index in range(32)]
    if len(set(anchors)) != 32 or anchors[0] - 31 < math.ceil(0.10 * sample_count) or anchors[-1] + 1 > usable_stop:
        raise ValueError("adaptation anchor guard failed")
    selected = qdrone[SELECTED_ROWS]
    visible = [np.concatenate([selected[channel, anchor - 31 : anchor + 1] for anchor in anchors]) for channel in range(10)]
    for channel in range(4, 10):
        visible[channel] = np.concatenate([visible[channel], selected[channel, np.array(anchors) + 1]])
    return visible, anchors


def features(visible: list[np.ndarray], qdrone: np.ndarray, anchors: list[int]) -> dict[str, np.ndarray]:
    amplitude = []
    histogram = []
    lag = []
    selected = qdrone[SELECTED_ROWS]
    for channel, values in enumerate(visible):
        mean = float(values.mean())
        scale = float(values.std())
        amplitude.extend([mean, scale, *np.quantile(values, [0.10, 0.50, 0.90]), float(np.ptp(values))])
        normalized = (values - mean) / max(scale, 1e-12)
        histogram.extend(np.histogram(normalized, bins=BINS)[0] / values.size)
        correlations = []
        for anchor in anchors:
            history = selected[channel, anchor - 31 : anchor + 1]
            if history[:-1].std() < 1e-12 or history[1:].std() < 1e-12:
                correlations.append(0.0)
            else:
                correlations.append(float(np.corrcoef(history[:-1], history[1:])[0, 1]))
        lag.append(float(np.mean(correlations)))
    groups = {
        "amplitude": np.asarray(amplitude),
        "histogram": np.asarray(histogram),
        "lag": np.asarray(lag),
    }
    groups["combined"] = np.concatenate(list(groups.values()))
    return groups


def nested_accuracy(x: np.ndarray, labels: np.ndarray, trajectories: np.ndarray, speeds: np.ndarray) -> float:
    correct = total = 0
    for trajectory in sorted(set(trajectories.tolist())):
        for speed in sorted(set(speeds.tolist())):
            test = (trajectories == trajectory) & (speeds == speed)
            train = (trajectories != trajectory) & (speeds != speed)
            if int(test.sum()) != 9 or int(train.sum()) != 27 or len(set(labels[train].tolist())) != 9:
                raise ValueError("nested fold contract failed")
            mean = x[train].mean(axis=0)
            scale = x[train].std(axis=0)
            scale[scale < 1e-12] = 1.0
            train_x = (x[train] - mean) / scale
            test_x = (x[test] - mean) / scale
            train_y = labels[train]
            centroids = {label: train_x[train_y == label].mean(axis=0) for label in sorted(set(train_y.tolist()))}
            predictions = np.array([
                min(centroids, key=lambda label: (float(np.square(row - centroids[label]).sum()), label))
                for row in test_x
            ])
            correct += int((predictions == labels[test]).sum())
            total += int(test.sum())
    return correct / total


def wilson(successes: int, total: int) -> list[float]:
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [center - margin, center + margin]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    visible_counts = []
    for path in sorted(args.root.glob("*.mat"), key=lambda item: item.name):
        match = NAME_RE.match(path.name)
        if not match or match.group("f") == "0" or match.group("t") == "4":
            continue
        matrices, _, session = load_matrices(path)
        qdrone = matrices["QDrone_data"]
        visible, anchors = adaptation_view(qdrone)
        if not all(np.isfinite(values).all() for values in visible):
            raise ValueError(f"nonfinite candidate-visible adaptation view: {path.name}")
        rows.append({
            "label": int(match.group("f")) * 10 + int(match.group("sv")),
            "trajectory": int(match.group("t")),
            "speed": int(match.group("sp")),
            "session": np.array([session]),
            "features": features(visible, qdrone, anchors),
        })
        visible_counts.append(sum(values.size for values in visible))
    if len(rows) != 72:
        raise ValueError(f"expected 72 rows, got {len(rows)}")
    labels = np.array([row["label"] for row in rows])
    trajectories = np.array([row["trajectory"] for row in rows])
    speeds = np.array([row["speed"] for row in rows])
    matrices = {name: np.stack([row["features"][name] for row in rows]) for name in rows[0]["features"]}
    observed = {name: nested_accuracy(matrix, labels, trajectories, speeds) for name, matrix in matrices.items()}
    privileged_session = nested_accuracy(np.stack([row["session"] for row in rows]), labels, trajectories, speeds)
    rng = np.random.default_rng(PERMUTATION_SEED)
    null = np.empty(PERMUTATIONS)
    combined = matrices["combined"]
    cells = [np.flatnonzero((trajectories == trajectory) & (speeds == speed)) for trajectory in sorted(set(trajectories)) for speed in sorted(set(speeds))]
    for index in range(PERMUTATIONS):
        permuted = labels.copy()
        for cell in cells:
            permuted[cell] = rng.permutation(permuted[cell])
        null[index] = nested_accuracy(combined, permuted, trajectories, speeds)
    null_q95 = float(np.quantile(null, 0.95, method="higher"))
    p_value = float((1 + np.count_nonzero(null >= observed["combined"])) / (PERMUTATIONS + 1))
    ceiling = max(VISIBLE_CEILING, null_q95)
    passed = max(observed.values()) <= VISIBLE_CEILING and observed["combined"] <= ceiling and p_value >= 0.05
    successes = round(observed["combined"] * 72)
    result = {
        "schema_version": 1,
        "decision": "pass_for_protected_evaluator_migration" if passed else "reject_before_implementation",
        "preregistration_sha256": "68fada2f74671792b2ddee12d312f443da724f9d8351b429dcfcadfa529accac",
        "candidate_visible_nested_accuracy": observed,
        "combined_correct": successes,
        "combined_total": 72,
        "combined_wilson_95": wilson(successes, 72),
        "chance_accuracy": 1 / 9,
        "visible_ceiling": VISIBLE_CEILING,
        "permutation_count": PERMUTATIONS,
        "permutation_seed": PERMUTATION_SEED,
        "permutation_null_q95": null_q95,
        "combined_decision_ceiling": ceiling,
        "combined_permutation_p": p_value,
        "privileged_session_accuracy_diagnostic_only": privileged_session,
        "forbidden_access_count": 0,
        "feature_dimensions": {name: matrix.shape[1] for name, matrix in matrices.items()},
        "visible_scalar_count_per_file_min": min(visible_counts),
        "visible_scalar_count_per_file_max": max(visible_counts),
        "files": len(rows),
        "folds": 8,
        "predictive_scoring_performed": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
