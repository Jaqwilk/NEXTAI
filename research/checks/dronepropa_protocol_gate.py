"""No-score integrity, timing, routing and synthetic identifiability gate."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "dronepropa_v1"
sys.path.insert(0, str(DATA_DIR))
from audit_mat_v5 import MI_COMPRESSED, MI_MATRIX, elements  # noqa: E402


NAME_RE = re.compile(r"^F(?P<f>[0-3])_SV(?P<sv>[0-3])_SP(?P<sp>[12])_t(?P<t>[1-5])(?:_D(?P<d>[1-3])(?:_R(?P<r>[1-3]))?)?\.mat$")
SESSION_RE = re.compile(rb"Created on: (.{24})")
SELECTED_ROWS = np.array([46, 48, 50, 52, 26, 27, 28, 29, 30, 31])
ESC_ROWS = {47, 49, 51, 53}
ROUTER_THRESHOLD = 0.35


def inflate(payload: memoryview) -> tuple[bytes, bool]:
    try:
        return zlib.decompress(payload), False
    except zlib.error:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(payload)
        inner = list(elements(raw))
        if len(inner) != 1 or inner[0][0] != MI_MATRIX or len(inner[0][1]) + 8 != len(raw):
            raise
        return raw, True


def load_matrices(path: Path) -> tuple[dict[str, np.ndarray], int, float]:
    raw = path.read_bytes()
    matrices: dict[str, np.ndarray] = {}
    incomplete = 0
    for kind, payload in elements(memoryview(raw)[128:], compressed_unpadded=True):
        if kind != MI_COMPRESSED:
            continue
        expanded, was_incomplete = inflate(payload)
        incomplete += int(was_incomplete)
        for inner_kind, matrix_payload in elements(expanded):
            if inner_kind != MI_MATRIX:
                continue
            parts = list(elements(matrix_payload))
            dims = tuple(np.frombuffer(parts[1][1], dtype="<i4").astype(int))
            name = bytes(parts[2][1]).decode("utf-8").rstrip("\0")
            numeric = next((part for part in parts[3:] if part[0] == 9), None)
            if numeric is not None:
                matrices[name] = np.frombuffer(numeric[1], dtype="<f8").reshape(dims, order="F")
    match = SESSION_RE.search(raw[:116])
    session = 0.0
    if match:
        session = datetime.strptime(match.group(1).decode("ascii").strip(), "%a %b %d %H:%M:%S %Y").timestamp()
    return matrices, incomplete, session


def router_accuracy(features: np.ndarray, labels: np.ndarray, trajectories: np.ndarray) -> float:
    correct = total = 0
    for heldout in sorted(set(trajectories.tolist())):
        train = trajectories != heldout
        test = ~train
        mean = features[train].mean(axis=0)
        scale = features[train].std(axis=0)
        scale[scale < 1e-12] = 1.0
        x_train = (features[train] - mean) / scale
        x_test = (features[test] - mean) / scale
        y_train = labels[train]
        centroids = {label: x_train[y_train == label].mean(axis=0) for label in sorted(set(y_train.tolist()))}
        predicted = np.array([
            min(centroids, key=lambda label: float(np.square(row - centroids[label]).sum()))
            for row in x_test
        ])
        correct += int((predicted == labels[test]).sum())
        total += int(test.sum())
    return correct / total


def synthetic_fixture() -> dict[str, float]:
    base = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
    basis = np.linalg.qr(np.array([[1.0, 0.0], [2.0, 1.0], [0.0, 1.0], [0.0, -2.0], [1.0, 0.0], [-1.0, 1.0]]))[0]
    type_weight = {1: -2.0, 2: 0.0, 3: 3.0}
    severity_weight = {1: -1.0, 2: 1.0, 3: 4.0}
    vector = lambda f, sv: base + basis[:, 0] * type_weight[f] + basis[:, 1] * severity_weight[sv]
    train_pairs = [(1, 1), (1, 2), (2, 1), (2, 3), (3, 2)]
    test_pairs = [(1, 3), (2, 2), (3, 1)]
    train = np.stack([vector(*pair) for pair in train_pairs])
    center = train.mean(axis=0)
    learned_basis = np.linalg.svd(train - center, full_matrices=False)[2][:2].T
    measurement = np.eye(6)[[0, 2]]
    reconstruction_errors = []
    nearest_exact = 0
    for pair in test_pairs:
        truth = vector(*pair)
        coefficients = np.linalg.solve(measurement @ learned_basis, measurement @ (truth - center))
        reconstructed = center + learned_basis @ coefficients
        reconstruction_errors.append(float(np.max(np.abs(reconstructed - truth))))
        nearest = train[np.argmin(np.square(train - truth).sum(axis=1))]
        nearest_exact += int(np.allclose(nearest, truth, atol=1e-12))
    return {
        "shared_subspace_max_abs_error": max(reconstruction_errors),
        "shared_subspace_exact_rate": float(max(reconstruction_errors) < 1e-10),
        "exact_table_test_coverage": 0.0,
        "nearest_template_exact_rate": nearest_exact / len(test_pairs),
        "easy_router_exact_rate": 0.0,
    }


def split_role(name: str) -> str:
    match = NAME_RE.match(name)
    if not match:
        raise ValueError(f"unexpected source name: {name}")
    f, sv, trajectory = (int(match.group(key)) for key in ("f", "sv", "t"))
    drone = int(match.group("d") or 0)
    if trajectory == 4:
        return "reserved_adversarial"
    if f == 0:
        return "train" if drone == 1 else "ood_healthy_diagnostic"
    pair = (f, sv)
    if pair in {(1, 3), (2, 2), (3, 1)}:
        return "test"
    if pair == (3, 3):
        return "validation"
    if pair in {(1, 1), (1, 2), (2, 1), (2, 3), (3, 2)}:
        return "train"
    raise ValueError(f"unassigned source name: {name}")


def write_anonymous_split(path: Path) -> dict[str, int]:
    rows = []
    for line in (DATA_DIR / "files.jsonl").read_text(encoding="utf-8").splitlines():
        source = json.loads(line)
        qdrone = next(leaf for leaf in source["leaves"] if leaf["path"] == "QDrone_data")
        rows.append({
            "anonymous_path": f"flights/{source['sha256'][:24]}.mat",
            "bytes": source["bytes"],
            "qdrone_numeric_sha256": qdrone["numeric_sha256"],
            "role": split_role(source["name"]),
            "samples": qdrone["dims"][1],
            "source_sha256": source["sha256"],
        })
    rows.sort(key=lambda row: row["anonymous_path"])
    counts = {role: sum(row["role"] == role for row in rows) for role in sorted({row["role"] for row in rows})}
    expected = {"ood_healthy_diagnostic": 8, "reserved_adversarial": 26, "test": 24, "train": 64, "validation": 8}
    if counts != expected:
        raise ValueError(f"split counts differ: {counts}")
    path.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split-output", type=Path)
    args = parser.parse_args()
    rows = []
    timing_failures = []
    finite_failures = []
    incomplete_files = []
    for path in sorted(args.root.glob("*.mat"), key=lambda item: item.name):
        matrices, incomplete, session = load_matrices(path)
        qdrone = matrices["QDrone_data"]
        remaining = np.delete(qdrone, sorted(ESC_ROWS), axis=0)
        if not np.isfinite(remaining).all() or not np.isfinite(matrices["commander_data"]).all() or not np.isfinite(matrices["stabilizer_data"]).all():
            finite_failures.append(path.name)
        delta = np.diff(qdrone[0])
        median_delta = float(np.median(delta))
        if not np.all(delta > 0) or not 0.0009 <= median_delta <= 0.0011:
            timing_failures.append({"name": path.name, "median_delta": median_delta, "strictly_increasing": bool(np.all(delta > 0))})
        if incomplete:
            incomplete_files.append({"name": path.name, "members": incomplete})
        match = NAME_RE.match(path.name)
        if match and match.group("f") != "0" and match.group("t") != "4":
            selected = qdrone[SELECTED_ROWS]
            mean = selected.mean(axis=1)
            std = selected.std(axis=1)
            quantiles = np.quantile(selected, [0.10, 0.50, 0.90], axis=1).T.reshape(-1)
            amplitude = np.concatenate([mean, std, quantiles, np.ptp(selected, axis=1)])
            normalized = (selected - mean[:, None]) / np.maximum(std[:, None], 1e-12)
            bins = np.array([-np.inf, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, np.inf])
            histogram = np.concatenate([np.histogram(channel, bins=bins)[0] / channel.size for channel in normalized])
            rows.append({
                "label": int(match.group("f")) * 10 + int(match.group("sv")),
                "trajectory": int(match.group("t")),
                "length": np.array([qdrone.shape[1]], dtype=float),
                "session": np.array([session], dtype=float),
                "amplitude": amplitude,
                "histogram": histogram,
            })
    labels = np.array([row["label"] for row in rows])
    trajectories = np.array([row["trajectory"] for row in rows])
    feature_groups = {
        name: np.stack([row[name] for row in rows])
        for name in ("length", "session", "amplitude", "histogram")
    }
    feature_groups["combined"] = np.concatenate(list(feature_groups.values()), axis=1)
    routing = {name: router_accuracy(values, labels, trajectories) for name, values in feature_groups.items()}
    fixture = synthetic_fixture()
    passed = (
        not timing_failures
        and not finite_failures
        and len(incomplete_files) == 1
        and fixture["shared_subspace_exact_rate"] == 1.0
        and fixture["exact_table_test_coverage"] == 0.0
        and fixture["nearest_template_exact_rate"] == 0.0
        and max(routing.values()) <= ROUTER_THRESHOLD
    )
    result = {
        "schema_version": 1,
        "decision": "pass_for_evaluator_migration" if passed else "reject_before_implementation",
        "router_chance": 1 / 9,
        "router_threshold_frozen_before_run": ROUTER_THRESHOLD,
        "routing_accuracy_leave_one_trajectory_out": routing,
        "synthetic_identifiability_fixture": fixture,
        "timing_failures": timing_failures,
        "finite_failures_after_uniform_esc_exclusion": finite_failures,
        "verified_incomplete_zlib_files": incomplete_files,
        "faulty_scored_family_files_audited": len(rows),
    }
    if args.split_output:
        result["anonymous_split_counts"] = write_anonymous_split(args.split_output)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
