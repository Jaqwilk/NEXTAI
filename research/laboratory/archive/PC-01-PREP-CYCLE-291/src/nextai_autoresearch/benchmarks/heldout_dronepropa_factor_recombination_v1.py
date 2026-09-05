from __future__ import annotations

import hashlib
import importlib
import json
import math
import random
import re
import struct
import time
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from ..candidates.dronepropa_baselines import (
    ConditionOracle,
    ConditionSpecialist,
    ContextualGaussianChowLiu,
    EmpiricalGaussianJoint,
    NearestOperatorTemplate,
    PooledARX,
    RLSARX,
    RidgeARX,
    affine_predict,
    affine_ridge,
)
from ..dronepropa_contract import DynamicsPrediction, DynamicsTraining, FlightExamples
from ..utils import project_root, sha256_file


BENCHMARK_VERSION = "heldout_dronepropa_factor_recombination_v1"
FILES_MANIFEST = Path("research/data/dronepropa_v1/files.jsonl")
SPLIT_MANIFEST = Path("research/checks/dronepropa_anonymous_split_v1.jsonl")
FILES_MANIFEST_SHA256 = "76a27c66b38b634cbee362a8a2af250b02b2a1dea44eb9328d1d731472b24f53"
SPLIT_MANIFEST_SHA256 = "8381cc9d8e245059cf6ce49a5ba988bb50a588a14de445e73cb72709fdaffed0"
ARCHIVE_SHA256 = "a7255dc4393a2314ba2a684beb3684106dbb6de23ba141eaa0529bd21ba3d825"
ARCHIVE_BYTES = 4_438_911_840
ARCHIVE_PATH = Path("research/data/dronepropa_v1/archive/ftdyxrr3c5-1.zip")
EXTRACTED_BYTES = 4_537_694_153
GENERATED_LIST_BYTES = 2_550
GENERATED_LIST_SHA256 = "880b3d1b25a3a515befd3190696748e5bded975fdeb6e7e4f5db566ab0d88756"
SELECTED_ROWS = np.array([46, 48, 50, 52, 26, 27, 28, 29, 30, 31])
BAD_ESC_ROWS_1BASED = (48, 50, 52, 54)
HISTORY = 32
HORIZONS = (1, 10, 50)
ROLE_COUNTS = {"train": 64, "validation": 8, "test": 24, "ood_healthy_diagnostic": 8, "reserved_adversarial": 26}
MI_MATRIX, MI_COMPRESSED = 14, 15
STABLE_Z_BOUND = 20.0
_FACTOR_NAME = re.compile(r"F(\d+)_SV(\d+)_SP(\d+)_t(\d+)(?:_D(\d+)(?:_R(\d+))?)?\.mat$")


def _elements(data: bytes | memoryview, *, compressed_unpadded: bool = False) -> Iterator[tuple[int, memoryview]]:
    view, position = memoryview(data), 0
    while position + 8 <= len(view):
        first = struct.unpack_from("<I", view, position)[0]
        if first >> 16:
            kind, size = first & 0xFFFF, first >> 16
            yield kind, view[position + 4 : position + 4 + size]
            position += 8
        else:
            kind, size = first, struct.unpack_from("<I", view, position + 4)[0]
            start = position + 8
            yield kind, view[start : start + size]
            position = start + (size if compressed_unpadded and kind == MI_COMPRESSED else ((size + 7) // 8) * 8)


def _inflate(payload: memoryview) -> bytes:
    try:
        return zlib.decompress(payload)
    except zlib.error as error:
        decoder = zlib.decompressobj()
        expanded = decoder.decompress(payload)
        if len(expanded) < 8 or struct.unpack_from("<II", expanded, 0) != (MI_MATRIX, len(expanded) - 8):
            raise ValueError("invalid incomplete zlib member") from error
        return expanded


def _qdrone_matrix(matrix_payload: memoryview) -> np.ndarray | None:
    parts = list(_elements(matrix_payload))
    if len(parts) < 4:
        return None
    dimensions = tuple(int(value) for value in np.frombuffer(parts[1][1], dtype="<i4"))
    name = bytes(parts[2][1]).decode("utf-8", "replace").rstrip("\0")
    if name != "QDrone_data" or len(dimensions) != 2 or dimensions[0] != 56:
        return None
    numeric = next((payload for kind, payload in parts[3:] if kind == 9), None)
    if numeric is None:
        raise ValueError("QDrone_data has no double payload")
    values = np.frombuffer(numeric, dtype="<f8")
    if values.size != dimensions[0] * dimensions[1]:
        raise ValueError("QDrone_data size mismatch")
    return values.reshape(dimensions, order="F")


def load_selected_flight(path: Path, expected_sha256: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    raw = path.read_bytes()
    if expected_sha256 and hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("immutable source hash mismatch")
    if not raw.startswith(b"MATLAB 5.0 MAT-file") or raw[126:128] != b"IM":
        raise ValueError("unsupported MATLAB v5 file")
    qdrone = None
    for kind, payload in _elements(memoryview(raw)[128:], compressed_unpadded=True):
        containers = _elements(_inflate(payload)) if kind == MI_COMPRESSED else ((kind, payload),)
        for inner_kind, inner in containers:
            if inner_kind == MI_MATRIX:
                candidate = _qdrone_matrix(inner)
                if candidate is not None:
                    qdrone = candidate
    if qdrone is None:
        raise ValueError("QDrone_data is missing")
    delta = np.diff(qdrone[0])
    if not np.all(delta > 0) or not 0.0009 <= float(np.median(delta)) <= 0.0011:
        raise ValueError("invalid QDrone time axis")
    selected = qdrone[SELECTED_ROWS].T.copy()
    if not np.isfinite(selected).all():
        raise ValueError("selected channels must be finite")
    return selected[:, :4], selected[:, 4:]


def usable_bounds(sample_count: int) -> tuple[int, int]:
    start = math.ceil(0.10 * sample_count) + HISTORY - 1
    stop = math.floor(0.90 * sample_count) - max(HORIZONS)
    if stop <= start:
        raise ValueError("flight is too short")
    return start, stop


def adaptation_anchors(sample_count: int) -> tuple[int, ...]:
    start, stop = usable_bounds(sample_count)
    adaptation_stop = start + math.floor(0.20 * (stop - start + 1)) - 1
    edges = np.linspace(start, adaptation_stop + 1, 33)
    anchors = tuple(int(math.floor((edges[index] + edges[index + 1] - 1) / 2)) for index in range(32))
    if len(set(anchors)) != 32 or anchors[0] - HISTORY + 1 < 0 or anchors[-1] + 1 > stop:
        raise ValueError("adaptation boundary failed")
    return anchors


def training_anchors(sample_count: int, count: int = 128) -> tuple[int, ...]:
    start, stop = usable_bounds(sample_count)
    edges = np.linspace(start, stop + 1, count + 1)
    anchors = tuple(
        int(math.floor((edges[index] + edges[index + 1] - 1) / 2))
        for index in range(count)
    )
    if len(set(anchors)) != count:
        raise ValueError("training anchors are not unique")
    return anchors


def evaluation_anchors(sample_count: int, seed: int, count: int = 128) -> tuple[int, ...]:
    start, stop = usable_bounds(sample_count)
    evaluation_start = start + math.floor(0.20 * (stop - start + 1))
    edges = np.linspace(evaluation_start, stop + 1, count + 1)
    rng = random.Random(seed)
    anchors = []
    margin = (HISTORY + max(HORIZONS)) // 2
    for index in range(count):
        low = math.ceil(edges[index]) + margin
        high = math.floor(edges[index + 1]) - margin - 1
        if high < low:
            raise ValueError("evaluation bin is empty")
        anchors.append(rng.randint(low, high))
    if any(right - left < HISTORY + max(HORIZONS) for left, right in zip(anchors, anchors[1:])):
        raise ValueError("evaluation windows overlap")
    return tuple(anchors)


def arx_examples(controls: np.ndarray, states: np.ndarray, anchors: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    if controls.shape[0] != states.shape[0] or controls.shape[1] != 4 or states.shape[1] != 6:
        raise ValueError("expected aligned four-control and six-state arrays")
    features = np.stack([np.column_stack((controls[t - HISTORY + 1 : t + 1], states[t - HISTORY + 1 : t + 1])).reshape(-1) for t in anchors])
    targets = states[np.asarray(anchors) + 1]
    if not np.isfinite(features).all() or not np.isfinite(targets).all():
        raise ValueError("ARX examples must be finite")
    return features, targets


def verify_static_contract(
    root: Path | None = None,
    *,
    split_manifest: Path = SPLIT_MANIFEST,
    split_sha256: str = SPLIT_MANIFEST_SHA256,
    role_counts: dict[str, int] = ROLE_COUNTS,
) -> dict[str, Any]:
    base = (root or project_root()).resolve()
    if sha256_file(base / FILES_MANIFEST) != FILES_MANIFEST_SHA256:
        raise ValueError("DronePropA file manifest mismatch")
    if sha256_file(base / split_manifest) != split_sha256:
        raise ValueError("DronePropA split manifest mismatch")
    split = [json.loads(line) for line in (base / split_manifest).read_text(encoding="utf-8").splitlines()]
    counts = dict(Counter(str(row["role"]) for row in split))
    if counts != role_counts or len({row["source_sha256"] for row in split}) != 130:
        raise ValueError("DronePropA split role/count/hash contract failed")
    if any(set(row) != {"anonymous_path", "bytes", "qdrone_numeric_sha256", "role", "samples", "source_sha256"} for row in split):
        raise ValueError("DronePropA split exposes an unexpected field")
    return {"files": len(split), "roles": counts, "split_sha256": split_sha256}


def full_cost(offline: float, adaptation: float, queries: float, updates: float, reuse: int) -> float:
    return float(ARCHIVE_BYTES + EXTRACTED_BYTES + offline + reuse * (adaptation + queries + updates))


@dataclass(frozen=True)
class _Flight:
    slot: int
    controls: np.ndarray
    states: np.ndarray
    condition: str
    trajectory: str
    source_bytes: int


def _corpus_rows(root: Path, split_manifest: Path = SPLIT_MANIFEST) -> list[dict[str, Any]]:
    split = [json.loads(line) for line in (root / split_manifest).read_text(encoding="utf-8").splitlines()]
    files = [json.loads(line) for line in (root / FILES_MANIFEST).read_text(encoding="utf-8").splitlines()]
    names = {str(row["sha256"]): str(row["name"]) for row in files}
    paths = {path.name: path for path in (root / "research/data/dronepropa_v1/extracted").rglob("*.mat")}
    if len(names) != 130 or len(paths) != 130:
        raise ValueError("DronePropA source inventory is incomplete")
    rows: list[dict[str, Any]] = []
    for slot, row in enumerate(split):
        name = names.get(str(row["source_sha256"]))
        match = _FACTOR_NAME.fullmatch(name or "")
        if name not in paths or match is None:
            raise ValueError("DronePropA private factor/path join failed")
        enriched = dict(row)
        enriched.update(
            slot=slot,
            path=paths[name],
            condition=f"F{match.group(1)}_SV{match.group(2)}",
            trajectory=f"t{match.group(4)}",
        )
        rows.append(enriched)
    return rows


def _load_flights(rows: list[dict[str, Any]]) -> list[_Flight]:
    flights = []
    for row in rows:
        controls, states = load_selected_flight(Path(row["path"]), str(row["source_sha256"]))
        flights.append(
            _Flight(
                int(row["slot"]), controls, states, str(row["condition"]),
                str(row["trajectory"]), int(row["bytes"]),
            )
        )
    return flights


def verify_corpus_hashes(
    root: Path | None = None, split_manifest: Path = SPLIT_MANIFEST
) -> dict[str, int]:
    base = (root or project_root()).resolve()
    archive = base / ARCHIVE_PATH
    if archive.stat().st_size != ARCHIVE_BYTES or sha256_file(archive) != ARCHIVE_SHA256:
        raise ValueError("DronePropA archive hash/size mismatch")
    rows = _corpus_rows(base, split_manifest)
    checked_bytes = ARCHIVE_BYTES
    for row in rows:
        path = Path(row["path"])
        if path.stat().st_size != int(row["bytes"]):
            raise ValueError("DronePropA extracted file size mismatch")
        if sha256_file(path) != str(row["source_sha256"]):
            raise ValueError("DronePropA extracted file hash mismatch")
        checked_bytes += int(row["bytes"])
    generated = list(
        (base / "research/data/dronepropa_v1/extracted").rglob("generated_file_list.txt")
    )
    if (
        len(generated) != 1
        or generated[0].stat().st_size != GENERATED_LIST_BYTES
        or sha256_file(generated[0]) != GENERATED_LIST_SHA256
    ):
        raise ValueError("DronePropA generated file list hash/size mismatch")
    checked_bytes += GENERATED_LIST_BYTES
    if checked_bytes != ARCHIVE_BYTES + EXTRACTED_BYTES:
        raise ValueError("DronePropA full corpus byte boundary mismatch")
    return {"files": len(rows), "bytes": checked_bytes}


def _examples(flight: _Flight, anchors: tuple[int, ...]) -> FlightExamples:
    features, targets = arx_examples(flight.controls, flight.states, anchors)
    return FlightExamples(flight.slot, features, targets)


@dataclass(frozen=True)
class _Normalization:
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    target_mean: np.ndarray
    target_scale: np.ndarray

    def examples(self, source: FlightExamples) -> FlightExamples:
        return FlightExamples(
            source.slot,
            (source.features - self.feature_mean) / self.feature_scale,
            (source.targets - self.target_mean) / self.target_scale,
        )


def _normalization(training: tuple[FlightExamples, ...]) -> _Normalization:
    features = np.concatenate([row.features for row in training])
    targets = np.concatenate([row.targets for row in training])
    feature_scale = features.std(axis=0)
    target_scale = targets.std(axis=0)
    feature_scale[feature_scale < 1e-9] = 1.0
    target_scale[target_scale < 1e-9] = 1.0
    return _Normalization(features.mean(axis=0), feature_scale, targets.mean(axis=0), target_scale)


def _array_bytes(value: Any, seen: set[int] | None = None) -> int:
    seen = seen or set()
    if id(value) in seen:
        return 0
    seen.add(id(value))
    if isinstance(value, np.ndarray):
        return int(value.nbytes)
    if isinstance(value, dict):
        return 64 + sum(_array_bytes(key, seen) + _array_bytes(item, seen) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return 64 + sum(_array_bytes(item, seen) for item in value)
    if hasattr(value, "__dict__"):
        return 64 + _array_bytes(vars(value), seen)
    return 16


class _Runtime:
    def __init__(
        self,
        candidate_name: str,
        seed: int,
        training: tuple[FlightExamples, ...],
        labels: tuple[str, ...],
        normalization: _Normalization,
        privileged_training: tuple[FlightExamples, ...] = (),
        privileged_labels: tuple[str, ...] = (),
    ) -> None:
        self.name, self.normalization = candidate_name, normalization
        self.fit_ops = self.adaptation_ops = self.query_ops = self.update_ops = 0.0
        self.model: Any = None
        self.sessions: list[Any] = []
        features = np.concatenate([row.features for row in training])
        targets = np.concatenate([row.targets for row in training])
        dimension, outputs = features.shape[1], targets.shape[1]
        ridge_ops = float(len(features) * (2 * (dimension + 1) ** 2 + 2 * (dimension + 1) * outputs))
        self.query_ops = float(2 * (dimension + 1) * outputs + 2 * dimension + 2 * outputs)
        if candidate_name == "persistence_state_v1":
            self.model = None
            self.query_ops = 6.0
        elif candidate_name in {"ridge_arx_v1", "no_sharing_pooled_arx_v1"}:
            self.model = PooledARX()
            self.model.fit(features, targets)
            self.fit_ops = ridge_ops
        elif candidate_name == "rls_arx_v1":
            self.model = RLSARX(dimension)
            self.model.fit(features, targets)
            self.fit_ops = float(len(features) * (4 * (dimension + 1) ** 2 + 4 * (dimension + 1) * outputs))
        elif candidate_name == "nearest_operator_template_v1":
            self.model = NearestOperatorTemplate()
            self.model.fit([(row.features, row.targets) for row in training])
            self.fit_ops = ridge_ops
        elif candidate_name == "source_identical_independent_arx_v1":
            self.model = None
        elif candidate_name == "empirical_gaussian_joint_v1":
            self.model = EmpiricalGaussianJoint()
            self.model.fit(features, targets)
            self.fit_ops = float(len(features) * (dimension + outputs) ** 2)
            self.query_ops += float(2 * dimension * outputs)
        elif candidate_name == "contextual_gaussian_chow_liu_v1":
            self.model = ContextualGaussianChowLiu()
            self.model.fit(features, targets)
            self.fit_ops = ridge_ops + float(len(features) * outputs ** 2)
        elif candidate_name in {
            "oracle_charged_condition_specialist_arx_v1",
            "privileged_condition_oracle_arx_v1",
        }:
            cls = ConditionSpecialist if candidate_name.startswith("oracle_charged") else ConditionOracle
            self.model = cls()
            self.model.fit([(label, row.features, row.targets) for label, row in zip(labels, training)])
            self.fit_ops = ridge_ops
        elif candidate_name in {
            "oracle_charged_condition_specialist_arx_v2",
            "privileged_same_condition_oracle_arx_v2",
            "privileged_all_condition_support_arx_v3",
            "privileged_same_condition_support_arx_v3",
        }:
            if not privileged_training or len(privileged_training) != len(privileged_labels):
                raise RuntimeError("v2 privileged control requires frozen t4 oracle support")
            cls = ConditionSpecialist if candidate_name in {
                "oracle_charged_condition_specialist_arx_v2",
                "privileged_all_condition_support_arx_v3",
            } else ConditionOracle
            self.model = cls()
            self.model.fit([
                (label, row.features, row.targets)
                for label, row in zip(privileged_labels, privileged_training)
            ])
            support_size = sum(row.features.shape[0] for row in privileged_training)
            self.fit_ops = float(
                support_size * (2 * (dimension + 1) ** 2 + 2 * (dimension + 1) * outputs)
            )
        else:
            module = importlib.import_module(f"nextai_autoresearch.candidates.{candidate_name}")
            self.model = module.Candidate(seed)
            self.model.fit(DynamicsTraining(training, ARCHIVE_BYTES + EXTRACTED_BYTES, int(features.size + targets.size)))
            self.fit_ops = float(getattr(self.model, "fit_ops", features.size + targets.size))

    def adapt(self, examples: FlightExamples, condition: str) -> Any:
        dimension, outputs = examples.features.shape[1], examples.targets.shape[1]
        ridge_ops = float(len(examples.features) * (2 * (dimension + 1) ** 2 + 2 * (dimension + 1) * outputs))
        if self.name == "persistence_state_v1":
            session: Any = None
        elif self.name == "ridge_arx_v1":
            session = self.model
        elif self.name == "no_sharing_pooled_arx_v1":
            pooled_x = np.concatenate((self._pooled_features(), examples.features))
            pooled_y = np.concatenate((self._pooled_targets(), examples.targets))
            session = RidgeARX()
            session.fit(pooled_x, pooled_y)
            self.adaptation_ops += ridge_ops
        elif self.name == "rls_arx_v1":
            session = RLSARX(dimension)
            session.weights = self.model.weights.copy()
            session.covariance = self.model.covariance.copy()
            session.fit(examples.features, examples.targets)
            self.adaptation_ops += float(len(examples.features) * (4 * (dimension + 1) ** 2 + 4 * (dimension + 1) * outputs))
        elif self.name == "nearest_operator_template_v1":
            session = self.model.templates[self.model.select(examples.features, examples.targets)]
            self.adaptation_ops += ridge_ops + float(len(self.model.templates) * (dimension + 1) * outputs)
        elif self.name == "source_identical_independent_arx_v1":
            session = RidgeARX()
            session.fit(examples.features, examples.targets)
            self.adaptation_ops += ridge_ops
        elif self.name in {
            "empirical_gaussian_joint_v1", "contextual_gaussian_chow_liu_v1",
        }:
            session = self.model
        elif self.name in {
            "oracle_charged_condition_specialist_arx_v1",
            "privileged_condition_oracle_arx_v1",
            "oracle_charged_condition_specialist_arx_v2",
            "privileged_same_condition_oracle_arx_v2",
            "privileged_all_condition_support_arx_v3",
            "privileged_same_condition_support_arx_v3",
        }:
            if condition not in self.model.models:
                raise RuntimeError(
                    "exact-condition privileged control is undefined because the "
                    "held-out condition is absent from training"
                )
            session = self.model.models[condition]
        else:
            session = self.model.adapt(examples)
            self.adaptation_ops += float(getattr(session, "adaptation_ops", examples.features.size + examples.targets.size))
        self.sessions.append(session)
        return session

    def _pooled_features(self) -> np.ndarray:
        return np.asarray(self.model._runtime_training_features)

    def _pooled_targets(self) -> np.ndarray:
        return np.asarray(self.model._runtime_training_targets)

    def retain_training(self, training: tuple[FlightExamples, ...]) -> None:
        if self.name == "no_sharing_pooled_arx_v1":
            self.model._runtime_training_features = np.concatenate([row.features for row in training])
            self.model._runtime_training_targets = np.concatenate([row.targets for row in training])

    def predict(self, session: Any, normalized_feature: np.ndarray) -> DynamicsPrediction:
        row = normalized_feature.reshape(1, -1)
        if self.name == "persistence_state_v1":
            raw_last = row[0, -6:] * self.normalization.feature_scale[-6:] + self.normalization.feature_mean[-6:]
            mean = ((raw_last - self.normalization.target_mean) / self.normalization.target_scale).reshape(1, -1)
            return DynamicsPrediction(mean, np.full((1, 6), np.nan))
        if self.name == "empirical_gaussian_joint_v1":
            mean, covariance = session.conditional(row)
            return DynamicsPrediction(mean, np.broadcast_to(np.diag(covariance), mean.shape))
        if self.name == "contextual_gaussian_chow_liu_v1":
            mean = session.predict(row)
            return DynamicsPrediction(mean, np.broadcast_to(session.variance, mean.shape))
        if isinstance(session, np.ndarray):
            mean = affine_predict(session, row)
            return DynamicsPrediction(mean, np.full(mean.shape, np.nan))
        prediction = session.predict(row)
        if isinstance(prediction, DynamicsPrediction):
            return prediction
        mean = np.asarray(prediction, dtype=float).reshape(1, -1)
        return DynamicsPrediction(mean, np.full(mean.shape, np.nan))

    def state_bytes(self) -> int:
        return _array_bytes(self.model) + max((_array_bytes(item) for item in self.sessions), default=0)


def _feature(controls: np.ndarray, states: np.ndarray) -> np.ndarray:
    return np.column_stack((controls, states)).reshape(-1)


def _run_cell(
    candidate_name: str,
    seed: int,
    knowledge_size: int,
    reasoning_depth: int,
    train_flights: list[_Flight],
    test_flights: list[_Flight],
    privileged_flights: list[_Flight] | None = None,
    evaluation_count: int = 128,
) -> dict[str, Any]:
    selected = train_flights[:knowledge_size]
    raw_training = tuple(_examples(flight, training_anchors(len(flight.states))) for flight in selected)
    normalizer = _normalization(raw_training)
    training = tuple(normalizer.examples(row) for row in raw_training)
    support = privileged_flights or []
    if candidate_name in {
        "privileged_same_condition_oracle_arx_v2",
        "privileged_same_condition_support_arx_v3",
    }:
        test_conditions = {flight.condition for flight in test_flights}
        support = [flight for flight in support if flight.condition in test_conditions]
    raw_support = tuple(
        _examples(flight, training_anchors(len(flight.states))) for flight in support
    )
    normalized_support = tuple(normalizer.examples(row) for row in raw_support)
    started = time.perf_counter()
    runtime = _Runtime(
        candidate_name,
        seed,
        training,
        tuple(row.condition for row in selected),
        normalizer,
        normalized_support,
        tuple(row.condition for row in support),
    )
    runtime.retain_training(training)
    fit_seconds = time.perf_counter() - started
    errors: dict[int, list[float]] = {1: [], 10: [], 50: []}
    flight_scores: list[float] = []
    condition_errors: dict[str, list[float]] = {}
    trajectory_errors: dict[str, list[float]] = {}
    log_losses: list[float] = []
    latencies: list[float] = []
    stable = total_rollouts = queries = 0
    for flight in test_flights:
        adaptation = normalizer.examples(_examples(flight, adaptation_anchors(len(flight.states))))
        session = runtime.adapt(adaptation, flight.condition)
        anchors = evaluation_anchors(
            len(flight.states), seed ^ (flight.slot * 0x9E3779B1), evaluation_count
        )
        local: list[float] = []
        for anchor in anchors:
            controls = flight.controls[anchor - HISTORY + 1 : anchor + 1].copy()
            states = flight.states[anchor - HISTORY + 1 : anchor + 1].copy()
            for step in range(1, 51):
                normalized = (_feature(controls, states) - normalizer.feature_mean) / normalizer.feature_scale
                before = time.perf_counter_ns()
                distribution = runtime.predict(session, normalized)
                latencies.append((time.perf_counter_ns() - before) / 1000)
                predicted = distribution.mean[0] * normalizer.target_scale + normalizer.target_mean
                queries += 1
                if step == 1 and np.isfinite(distribution.variance).all():
                    residual = (
                        (flight.states[anchor + 1] - normalizer.target_mean)
                        / normalizer.target_scale
                        - distribution.mean[0]
                    )
                    variance = np.maximum(distribution.variance[0], 1e-9)
                    log_losses.append(float(0.5 * np.sum(np.log(2 * math.pi * variance) + residual ** 2 / variance)))
                if step in errors:
                    target = flight.states[anchor + step]
                    squared = np.minimum(np.square((predicted - target) / normalizer.target_scale), 1e12)
                    value = float(np.mean(squared)) if np.isfinite(squared).all() else 1e12
                    errors[step].append(value)
                    local.append(value)
                    condition_errors.setdefault(flight.condition, []).append(value)
                    trajectory_errors.setdefault(flight.trajectory, []).append(value)
                if step in (10, 50):
                    total_rollouts += 1
                    stable += int(np.isfinite(predicted).all() and np.max(np.abs((predicted - normalizer.target_mean) / normalizer.target_scale)) <= STABLE_Z_BOUND)
                controls = np.vstack((controls[1:], flight.controls[anchor + step]))
                states = np.vstack((states[1:], predicted))
        flight_scores.append(math.sqrt(float(np.mean(local))))
    state = runtime.state_bytes()
    if state > 67_108_864:
        raise ValueError(f"state budget exceeded: {state} > 67108864")
    horizon_nrmse = {horizon: math.sqrt(float(np.mean(values))) for horizon, values in errors.items()}
    normalized_rmse = math.sqrt(float(np.mean([value for values in errors.values() for value in values])))
    preprocessing = float(sum(
        row.features.size + row.targets.size for row in (*raw_training, *raw_support)
    ))
    query_work = runtime.query_ops * queries
    acquisition = float(ARCHIVE_BYTES + EXTRACTED_BYTES)
    percentiles = np.percentile(latencies, [50, 95])
    result = {
        "status": "complete", "knowledge_size": knowledge_size,
        "reasoning_depth": reasoning_depth, "seed": seed,
        "accuracy": 1.0 / (1.0 + normalized_rmse), "warm_accuracy": 1.0 / (1.0 + normalized_rmse),
        "continual_retention": 1.0, "normalized_rmse": normalized_rmse,
        "teacher_forced_nrmse": horizon_nrmse[1], "rollout_10_nrmse": horizon_nrmse[10],
        "rollout_50_nrmse": horizon_nrmse[50],
        "worst_flight_normalized_rmse": max(flight_scores),
        "worst_condition_normalized_rmse": max(math.sqrt(float(np.mean(values))) for values in condition_errors.values()),
        "stable_rollout_rate": stable / total_rollouts,
        "conditional_log_loss": float(np.mean(log_losses)) if log_losses else None,
        "condition_nrmse": {key: math.sqrt(float(np.mean(value))) for key, value in condition_errors.items()},
        "trajectory_nrmse": {key: math.sqrt(float(np.mean(value))) for key, value in trajectory_errors.items()},
        "mean_query_ops": runtime.query_ops, "mean_warm_query_ops": runtime.query_ops,
        "p50_latency_us": float(percentiles[0]), "p95_latency_us": float(percentiles[1]),
        "fit_seconds": fit_seconds, "fit_ops": runtime.fit_ops,
        "meta_fit_ops": runtime.fit_ops, "data_acquisition_ops": acquisition,
        "preprocessing_ops": preprocessing, "adaptation_ops": runtime.adaptation_ops,
        "fit_peak_bytes": state, "state_bytes": state, "peak_state_bytes": state,
        "mean_input_ops": 320.0, "mean_comparisons": 0.0,
        "mean_bytes_touched": float(8 * (320 + 6)), "update_ops": runtime.update_ops,
        "workload_ops": full_cost(runtime.fit_ops + preprocessing, runtime.adaptation_ops, query_work, runtime.update_ops, 1),
        "workload_ops_r1": full_cost(runtime.fit_ops + preprocessing, runtime.adaptation_ops, query_work, runtime.update_ops, 1),
        "workload_ops_r4": full_cost(runtime.fit_ops + preprocessing, runtime.adaptation_ops, query_work, runtime.update_ops, 4),
        "workload_ops_r16": full_cost(runtime.fit_ops + preprocessing, runtime.adaptation_ops, query_work, runtime.update_ops, 16),
        "update_latency_us": 0.0,
    }
    return result


def _run_suite_for_split(
    candidate_name: str,
    plan: dict[str, Any],
    split_manifest: Path,
    split_sha256: str,
    role_counts: dict[str, int],
) -> list[dict[str, Any]]:
    verify_static_contract(
        split_manifest=split_manifest,
        split_sha256=split_sha256,
        role_counts=role_counts,
    )
    matrix = plan["matrix"]
    max_knowledge = max(int(value) for value in matrix["knowledge_sizes"])
    rows = _corpus_rows(project_root(), split_manifest)
    train_rows = [row for row in rows if row["role"] == "train"][:max_knowledge]
    test_rows = [row for row in rows if row["role"] == "test"]
    privileged_rows = (
        [row for row in rows if row["role"] == "privileged_oracle_support"]
        if candidate_name in {
            "oracle_charged_condition_specialist_arx_v2",
            "privileged_same_condition_oracle_arx_v2",
        }
        else []
    )
    train_flights, test_flights = _load_flights(train_rows), _load_flights(test_rows)
    privileged_flights = _load_flights(privileged_rows)
    return [
        _run_cell(
            candidate_name,
            int(seed),
            int(size),
            int(depth),
            train_flights,
            test_flights,
            privileged_flights,
        )
        for seed in matrix["seeds"]
        for size in matrix["knowledge_sizes"]
        for depth in matrix["reasoning_depths"]
    ]


def run_suite(candidate_name: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    return _run_suite_for_split(
        candidate_name, plan, SPLIT_MANIFEST, SPLIT_MANIFEST_SHA256, ROLE_COUNTS
    )
