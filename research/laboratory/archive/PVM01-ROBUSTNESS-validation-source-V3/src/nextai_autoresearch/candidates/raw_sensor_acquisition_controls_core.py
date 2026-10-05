from __future__ import annotations

import numpy as np

from .base import CandidateBase
from ..raw_sensor_acquisition_contract import (
    PrivilegedRawProbeSession,
    RawProbeSession,
    RawSensorTraining,
)


class RawSensorControl(CandidateBase):
    mode = "prior"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.means = np.empty((0, 0))
        self.variances = np.empty(0)
        self.samples = np.empty((0, 0, 0))
        self.order = np.empty(0, dtype=int)
        self.last_probe_count = self.last_input_ops = self.last_bytes_touched = 0
        self._query_index = 0

    def fit(self, training: RawSensorTraining, universe_size: int, max_depth: int) -> None:
        self.samples = np.asarray(training.support.samples, dtype=np.float64)
        if self.samples.ndim != 3 or self.samples.shape[0] != universe_size:
            raise ValueError("raw sensor support must be class by repetition by sensor")
        self.means = self.samples.mean(axis=1)
        self.variances = self.samples.var(axis=1).mean(axis=0) + 0.04
        between = self.means.var(axis=0)
        self.order = np.argsort(-(between / self.variances))
        meta_values = sum(np.asarray(world.samples).size for world in training.meta_worlds)
        self.fit_ops = int(self.samples.size * 3 + meta_values)

    def _finish(self, probes: int, search_ops: int) -> None:
        self.last_probe_count = probes
        self.last_input_ops = 2 * probes
        self.last_ops = self.last_input_ops + search_ops
        self.last_bytes_touched = 8 * (probes + search_ops) + self.state_bytes()
        self._query_index += 1

    def _predict(self, observed: dict[int, float]) -> tuple[int, np.ndarray, int]:
        if not observed:
            return 0, np.ones(len(self.means)) / max(1, len(self.means)), 0
        indices = np.fromiter(observed, dtype=int)
        values = np.asarray([observed[int(index)] for index in indices])
        distances = (((self.means[:, indices] - values) ** 2) / self.variances[indices]).sum(axis=1)
        logits = -0.5 * (distances - distances.min())
        weights = np.exp(np.clip(logits, -60.0, 0.0))
        weights /= weights.sum()
        return int(np.argmax(weights)), weights, int(len(self.means) * len(indices) * 4)

    def _next_gaussian(self, weights: np.ndarray, unused: list[int]) -> tuple[int, int]:
        scores = []
        for sensor in unused:
            values = self.means[:, sensor]
            center = float(weights @ values)
            score = float(weights @ np.square(values - center)) / float(self.variances[sensor])
            scores.append((score, -sensor))
        best = max(scores)
        return -best[1], len(unused) * len(self.means) * 3

    def query(self, session: RawProbeSession, steps: int) -> int:
        if self.mode == "privileged":
            if not isinstance(session, PrivilegedRawProbeSession):
                raise TypeError("privileged raw sensor control requires evaluator target")
            self._finish(0, 1)
            return int(session.target)
        if self.mode == "prior":
            self._finish(0, 1)
            return 0
        width = self.means.shape[1]
        budget = width if self.mode == "all" else min(int(steps), width)
        if self.mode == "random":
            order = np.random.default_rng(self.seed ^ self._query_index * 65537).permutation(width)
        else:
            order = self.order
        observed: dict[int, float] = {}
        search_ops = 0
        weights = np.ones(len(self.means)) / len(self.means)
        unused = list(range(width))
        for index in range(budget):
            if self.mode == "gaussian":
                sensor, cost = self._next_gaussian(weights, unused)
                search_ops += cost
            elif self.mode == "kernel":
                flat = self.samples.reshape(-1, width)
                class_weights = np.repeat(weights / self.samples.shape[1], self.samples.shape[1])
                scores = []
                for sensor in unused:
                    center = float(class_weights @ flat[:, sensor])
                    scores.append((float(class_weights @ np.square(flat[:, sensor] - center)), -sensor))
                sensor = -max(scores)[1]
                search_ops += len(unused) * len(flat) * 3
            else:
                sensor = int(order[index])
            observed[sensor] = session.probe(sensor)
            unused.remove(sensor)
            _, weights, cost = self._predict(observed)
            search_ops += cost
        answer, _, cost = self._predict(observed)
        self._finish(len(observed), search_ops + cost)
        return answer

    def update(self, source: object, target: object = None) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return int(128 + self.means.nbytes + self.variances.nbytes + self.samples.nbytes + self.order.nbytes)


class Candidate(RawSensorControl):
    """Auditable default entry for this shared control module."""
