from __future__ import annotations

import numpy as np

from ..three_family_tensor_contract import Tensor, Training


RIDGE = 1e-3
EPSILON = 1e-6
RADIUS = 0.25
MODULE_CAP = 64
MIN_ENVIRONMENTS = 3
MAX_RELATIONS = 4
OUTPUT_CLIP = 8.0
WIDTH = 32
SESSION_BYTES = WIDTH * (MAX_RELATIONS + MAX_RELATIONS + 1) * 8


def _relation(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float, float]:
    count = len(x)
    xmean, ymean = float(x.mean()), float(y.mean())
    centered = x - xmean
    slope = float(centered @ (y - ymean) / (centered @ centered + RIDGE))
    intercept = ymean - slope * xmean
    residual = y - (intercept + slope * x)
    mse = float(residual @ residual / max(1, count))
    signature = np.array(
        [np.tanh(slope), np.tanh(intercept), 0.25 * np.log(mse + EPSILON)],
        dtype=np.float64,
    )
    return signature, mse, float(12 * count + 20)


def _extract_world(
    source: Tensor, target: Tensor, environment: int,
) -> tuple[list[tuple[np.ndarray, int, int, int, float]], float]:
    inputs = np.flatnonzero(source.mask.any(axis=0))
    outputs = np.flatnonzero(target.mask.any(axis=0))
    records: list[tuple[np.ndarray, int, int, int, float]] = []
    operations = 0.0
    for output in outputs:
        for input_index in inputs:
            visible = source.mask[:, input_index] & target.mask[:, output]
            signature, mse, local_ops = _relation(
                source.values[visible, input_index].astype(np.float64),
                target.values[visible, output].astype(np.float64),
            )
            records.append((signature, environment, int(input_index), int(output), mse))
            operations += local_ops
    return records, operations


def _learn_prototypes(
    records: list[tuple[np.ndarray, int, int, int, float]],
    environments: int,
    mode: str,
) -> tuple[np.ndarray, float]:
    if mode == "frozen":
        prototypes = [
            (np.tanh(slope), 0.0, residual)
            for slope in (-1.0, 0.0, 1.0)
            for residual in (-1.0, 0.0, 1.0)
        ]
        return np.asarray(prototypes, dtype=np.float64), 0.0
    clusters: list[dict[str, object]] = []
    operations = 0.0
    ordered = sorted(records, key=lambda row: (*row[0].tolist(), row[1], row[3], row[2]))
    for signature, environment, _, _, _ in ordered:
        distances = [float(np.linalg.norm(signature - item["sum"] / item["count"]))
                     for item in clusters]
        operations += float(8 * len(distances))
        nearest = min(range(len(distances)), key=lambda index: (distances[index], index)) if distances else -1
        if nearest < 0 or (distances[nearest] > RADIUS and len(clusters) < MODULE_CAP):
            clusters.append({"sum": signature.copy(), "count": 1,
                             "environments": {environment: [signature.copy(), 1]}})
            continue
        cluster = clusters[nearest]
        cluster["sum"] += signature
        cluster["count"] += 1
        environment_rows = cluster["environments"]
        if environment not in environment_rows:
            environment_rows[environment] = [signature.copy(), 1]
        else:
            environment_rows[environment][0] += signature
            environment_rows[environment][1] += 1
    retained = []
    required = min(MIN_ENVIRONMENTS, environments)
    for cluster in clusters:
        center = cluster["sum"] / cluster["count"]
        environment_rows = cluster["environments"]
        deviations = [float(np.linalg.norm(total / count - center))
                      for total, count in environment_rows.values()]
        operations += float(8 * len(deviations))
        if mode == "pooled" or (len(environment_rows) >= required and max(deviations, default=0.0) <= RADIUS):
            retained.append(center)
    return (np.asarray(retained, dtype=np.float64).reshape(-1, 3)
            if retained else np.empty((0, 3), dtype=np.float64)), operations


class Candidate:
    """Environment-stable anonymous scalar relations with local support readout."""

    CONSTANTS = (RIDGE, EPSILON, RADIUS, MODULE_CAP, MIN_ENVIRONMENTS,
                 MAX_RELATIONS, OUTPUT_CLIP)

    def __init__(self, seed: int, mode: str = "invariant") -> None:
        if mode not in {"invariant", "pooled", "frozen"}:
            raise ValueError(f"unknown invariant-module mode: {mode}")
        self.seed, self.mode = seed, mode
        self.prototypes = np.empty((0, 3), dtype=np.float64)
        self.fit_ops = self.adaptation_ops = self.last_ops = 0.0
        self.last_bytes_touched = 0.0
        self.last_stable = True

    def fit(self, training: Training) -> None:
        if not isinstance(training, Training):
            raise ValueError("invariant-module fit requires anonymous tensor training")
        records: list[tuple[np.ndarray, int, int, int, float]] = []
        self.fit_ops = 0.0
        for environment, world in enumerate(training.worlds):
            extracted, operations = _extract_world(
                world.support_input, world.support_target, environment
            )
            records.extend(extracted)
            self.fit_ops += operations
        self.prototypes, operations = _learn_prototypes(
            records, len(training.worlds), self.mode
        )
        self.fit_ops += operations

    def adapt(self, support_input: Tensor, support_target: Tensor) -> dict[str, np.ndarray]:
        records, operations = _extract_world(support_input, support_target, 0)
        selected = np.full((WIDTH, MAX_RELATIONS), -1, dtype=np.int64)
        counts = np.zeros(WIDTH, dtype=np.int64)
        weights = np.zeros((WIDTH, MAX_RELATIONS + 1), dtype=np.float64)
        input_mask = support_input.mask.any(axis=0)
        output_mask = support_target.mask.any(axis=0)
        for output in np.flatnonzero(output_mask):
            local = [row for row in records if row[3] == output]
            ranked = []
            for signature, _, input_index, _, mse in local:
                if len(self.prototypes):
                    distances = np.linalg.norm(self.prototypes - signature, axis=1)
                    distance = float(distances.min())
                    operations += float(8 * len(distances))
                    if distance <= RADIUS:
                        ranked.append((distance, mse, input_index))
                else:
                    ranked.append((0.0, mse, input_index))
            if not ranked:
                ranked = [(0.0, row[4], row[2]) for row in local]
            chosen = sorted(ranked)[:MAX_RELATIONS]
            indices = [item[2] for item in chosen]
            counts[output] = len(indices)
            selected[output, :len(indices)] = indices
            visible = support_target.mask[:, output].copy()
            for input_index in indices:
                visible &= support_input.mask[:, input_index]
            design = np.column_stack((
                np.ones(int(visible.sum())),
                support_input.values[visible][:, indices].astype(np.float64),
            ))
            target = support_target.values[visible, output].astype(np.float64)
            gram = design.T @ design + RIDGE * np.eye(design.shape[1])
            local_weights = np.linalg.solve(gram, design.T @ target)
            weights[output, :len(local_weights)] = local_weights
            operations += float(len(design) * design.shape[1] * (design.shape[1] + 1)
                                + design.shape[1] ** 3)
        self.adaptation_ops = operations
        return {"selected": selected, "counts": counts, "weights": weights,
                "input_mask": input_mask, "output_mask": output_mask}

    def predict(self, session: dict[str, np.ndarray], history: Tensor,
                future_public: Tensor) -> np.ndarray:
        input_mask = session["input_mask"]
        outputs = np.flatnonzero(session["output_mask"])
        public = future_public.mask.any(axis=0) & input_mask
        state = np.flatnonzero(input_mask & ~public)
        current = np.where(history.mask[-1] & input_mask, history.values[-1], 0.0).astype(np.float64)
        result = np.zeros((50, WIDTH), dtype=np.float64)
        operations = 0.0
        for step in range(50):
            following = np.zeros(len(outputs), dtype=np.float64)
            for position, output in enumerate(outputs):
                count = int(session["counts"][output])
                indices = session["selected"][output, :count]
                features = np.r_[1.0, current[indices]]
                following[position] = float(features @ session["weights"][output, :count + 1])
                operations += float(2 * len(features) + 2)
            following = np.clip(following, -OUTPUT_CLIP, OUTPUT_CLIP)
            result[step, outputs] = following
            current[:] = 0.0
            current[public] = future_public.values[step, public]
            count = min(len(state), len(following))
            current[state[:count]] = following[:count]
            operations += float(4 * len(following) + len(public))
        self.last_stable = bool(np.isfinite(result).all())
        if not self.last_stable:
            raise ValueError("invariant-module prediction is non-finite")
        self.last_ops = operations
        self.last_bytes_touched = float(
            self.prototypes.nbytes + history.values.nbytes + future_public.values.nbytes
            + session["selected"].nbytes + session["weights"].nbytes + result.nbytes
        )
        return result.astype(np.float32)

    def state_bytes(self) -> int:
        return int(self.prototypes.nbytes + SESSION_BYTES + 64)
