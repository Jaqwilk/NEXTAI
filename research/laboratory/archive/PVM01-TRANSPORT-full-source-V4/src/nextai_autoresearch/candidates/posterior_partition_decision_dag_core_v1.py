from __future__ import annotations

import math

import numpy as np

from .base import CandidateBase
from ..raw_sensor_acquisition_contract import RawProbeSession, RawSensorTraining, RawSensorWorld


VARIANCE_FLOOR = 0.04
RIDGE = 0.01
MAX_WEIGHT = 4.0
MAX_DEPTH = 16
FROZEN_WEIGHTS = np.asarray((0.5, 0.5), dtype=np.float64)


class PosteriorPartitionDecisionDAG(CandidateBase):
    mode = "shared"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.means = np.empty((0, 0))
        self.variances = np.empty(0)
        self.weights = FROZEN_WEIGHTS.copy()
        self.nodes: list[tuple[int, float, int, int, tuple[int, ...]]] = []
        self.last_probe_count = self.last_input_ops = self.last_bytes_touched = 0

    @staticmethod
    def _feature(means: np.ndarray, variances: np.ndarray,
                 classes: tuple[int, ...], sensor: int):
        order = sorted(classes, key=lambda item: (float(means[item, sensor]), item))
        middle = len(order) // 2
        if middle == 0:
            return None
        lower, upper = means[order[middle - 1], sensor], means[order[middle], sensor]
        if not upper > lower:
            return None
        threshold = float((lower + upper) / 2.0)
        left = tuple(item for item in classes if means[item, sensor] <= threshold)
        right = tuple(item for item in classes if means[item, sensor] > threshold)
        balance = 4.0 * len(left) * len(right) / (len(classes) ** 2)
        margin = min(MAX_WEIGHT, float(upper - lower) / math.sqrt(float(variances[sensor])))
        return np.asarray((balance, margin)), threshold, left, right

    @classmethod
    def _utility_examples(cls, world: RawSensorWorld) -> tuple[np.ndarray, np.ndarray, int]:
        samples = np.asarray(world.samples, dtype=np.float64)
        classes, repetitions, sensors = samples.shape
        rows, targets = [], []
        operations = 0
        all_classes = tuple(range(classes))
        for heldout in range(repetitions):
            retained = np.delete(samples, heldout, axis=1)
            means = retained.mean(axis=1)
            variances = retained.var(axis=1).mean(axis=0) + VARIANCE_FLOOR
            for sensor in range(sensors):
                split = cls._feature(means, variances, all_classes, sensor)
                operations += int(classes * math.ceil(math.log2(max(2, classes))) + classes * 4)
                if split is None:
                    continue
                feature, threshold, left, _ = split
                expected_left = np.zeros(classes, dtype=bool)
                expected_left[list(left)] = True
                observed_left = samples[:, heldout, sensor] <= threshold
                rows.append(feature)
                targets.append(float(np.mean(expected_left == observed_left)))
        return np.asarray(rows), np.asarray(targets), operations

    def _learn_weights(self, worlds: tuple[RawSensorWorld, ...]) -> None:
        features, targets = [], []
        for world in worlds:
            rows, values, operations = self._utility_examples(world)
            self.fit_ops += operations
            if len(rows):
                features.append(rows)
                targets.append(values)
        if not features:
            self.weights = FROZEN_WEIGHTS.copy()
            return
        design, response = np.vstack(features), np.concatenate(targets)
        system = design.T @ design + RIDGE * np.eye(2)
        solution = np.clip(np.linalg.solve(system, design.T @ response), 0.0, MAX_WEIGHT)
        total = float(solution.sum())
        self.weights = solution / total if total > 0.0 else FROZEN_WEIGHTS.copy()
        self.fit_ops += int(len(design) * 8 + 8)

    def _build(self, classes: tuple[int, ...], used: tuple[int, ...], depth: int) -> int:
        index = len(self.nodes)
        self.nodes.append((-1, 0.0, -1, -1, classes))
        if len(classes) <= 1 or depth >= MAX_DEPTH:
            return index
        best = None
        for sensor in range(self.means.shape[1]):
            if sensor in used:
                continue
            split = self._feature(self.means, self.variances, classes, sensor)
            self.fit_ops += int(len(classes) * math.ceil(math.log2(max(2, len(classes)))) + 6)
            if split is None:
                continue
            feature, threshold, left, right = split
            proposal = (float(self.weights @ feature), -sensor, threshold, left, right)
            if best is None or proposal[:2] > best[:2]:
                best = proposal
        if best is None:
            return index
        _, negative_sensor, threshold, left, right = best
        sensor = -negative_sensor
        next_used = (*used, sensor)
        left_node = self._build(left, next_used, depth + 1)
        right_node = self._build(right, next_used, depth + 1)
        self.nodes[index] = (sensor, float(threshold), left_node, right_node, classes)
        return index

    def fit(self, training: RawSensorTraining, universe_size: int, max_depth: int) -> None:
        if int(max_depth) != MAX_DEPTH:
            raise ValueError("decision DAG requires the preregistered maximum depth 16")
        support = np.asarray(training.support.samples, dtype=np.float64)
        if support.ndim != 3 or support.shape[0] != universe_size or support.shape[2] != 48:
            raise ValueError("raw sensor support must be K by three by 48")
        self.means = support.mean(axis=1)
        self.variances = support.var(axis=1).mean(axis=0) + VARIANCE_FLOOR
        self.fit_ops = int(3 * support.size)
        if self.mode == "shared":
            if len(training.meta_worlds) != 3:
                raise ValueError("shared decision DAG requires exactly three meta worlds")
            self._learn_weights(training.meta_worlds)
        elif self.mode == "support_only":
            self._learn_weights((training.support,))
        elif self.mode != "frozen":
            raise ValueError(f"unknown decision DAG mode: {self.mode}")
        self.nodes = []
        self._build(tuple(range(universe_size)), (), 0)

    def query(self, session: RawProbeSession, steps: int) -> int:
        node_index, observed, traversal_ops = 0, {}, 0
        for _ in range(min(int(steps), MAX_DEPTH)):
            sensor, threshold, left, right, _ = self.nodes[node_index]
            if sensor < 0:
                break
            value = session.probe(sensor)
            observed[sensor] = value
            node_index = left if value <= threshold else right
            traversal_ops += 3
        classes = self.nodes[node_index][4]
        sensors = tuple(observed)
        if sensors:
            values = np.asarray([observed[sensor] for sensor in sensors])
            distances = (((self.means[np.ix_(classes, sensors)] - values) ** 2)
                         / self.variances[list(sensors)]).sum(axis=1)
            answer = classes[int(np.argmin(distances))]
            leaf_ops = len(classes) * len(sensors) * 4
        else:
            answer, leaf_ops = min(classes), 1
        probes = len(observed)
        self.last_probe_count = probes
        self.last_input_ops = 2 * probes
        self.last_ops = self.last_input_ops + traversal_ops + leaf_ops
        self.last_bytes_touched = 8 * (probes + traversal_ops + leaf_ops) + self.state_bytes()
        return int(answer)

    def update(self, source: object, target: object = None) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        graph = sum(40 + 8 * len(node[4]) for node in self.nodes)
        return int(128 + self.means.nbytes + self.variances.nbytes + self.weights.nbytes + graph)


class Candidate(PosteriorPartitionDecisionDAG):
    """Auditable default entry for the source-identical decision-DAG core."""
