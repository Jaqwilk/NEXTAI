from __future__ import annotations

import numpy as np

from .base import CandidateBase
from ..raw_sensor_acquisition_contract import RawProbeSession, RawSensorTraining, RawSensorWorld


BIN_UPPER = np.asarray((0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, np.inf))
SMOOTHING = 1.0
VARIANCE_FLOOR = 0.04


class RawSensorProbeLearner(CandidateBase):
    mode = "shared"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.means = np.empty((0, 0))
        self.variances = np.empty(0)
        self.log_ratio = np.zeros(len(BIN_UPPER))
        self.last_probe_count = self.last_input_ops = self.last_bytes_touched = 0

    @staticmethod
    def _calibration_counts(world: RawSensorWorld) -> tuple[np.ndarray, np.ndarray, int]:
        samples = np.asarray(world.samples, dtype=np.float64)
        means = samples.mean(axis=1)
        variances = samples.var(axis=1).mean(axis=0) + VARIANCE_FLOOR
        scale = np.sqrt(variances)
        same = np.abs(samples - means[:, None, :]) / scale
        all_residuals = np.abs(samples[:, :, None, :] - means[None, None, :, :]) / scale
        mask = ~np.eye(len(means), dtype=bool)
        different = all_residuals[mask[:, None, :, None].repeat(samples.shape[1], 1)
                                  .repeat(samples.shape[2], 3)]
        same_counts = np.histogram(same, bins=np.r_[0.0, BIN_UPPER])[0].astype(float)
        different_counts = np.histogram(different, bins=np.r_[0.0, BIN_UPPER])[0].astype(float)
        comparisons = int(samples.size * len(means))
        return same_counts, different_counts, comparisons

    def fit(self, training: RawSensorTraining, universe_size: int, max_depth: int) -> None:
        support = np.asarray(training.support.samples, dtype=np.float64)
        if support.ndim != 3 or support.shape[0] != universe_size:
            raise ValueError("raw sensor support must be class by repetition by sensor")
        self.means = support.mean(axis=1)
        self.variances = support.var(axis=1).mean(axis=0) + VARIANCE_FLOOR
        self.fit_ops = int(3 * support.size)
        if self.mode == "frozen":
            return
        worlds = training.meta_worlds if self.mode == "shared" else (training.support,)
        if self.mode == "shared" and len(worlds) != 3:
            raise ValueError("shared raw sensor learner requires exactly three meta worlds")
        same = np.zeros(len(BIN_UPPER))
        different = np.zeros(len(BIN_UPPER))
        for world in worlds:
            positive, negative, comparisons = self._calibration_counts(world)
            same += positive
            different += negative
            self.fit_ops += comparisons * 4
        same_probability = (same + SMOOTHING) / (same.sum() + SMOOTHING * len(same))
        different_probability = (different + SMOOTHING) / (
            different.sum() + SMOOTHING * len(different)
        )
        self.log_ratio = np.log(same_probability) - np.log(different_probability)

    def _posterior(self, observed: dict[int, float]) -> tuple[np.ndarray, int]:
        logits = np.zeros(len(self.means))
        for sensor, value in observed.items():
            residual = np.abs(self.means[:, sensor] - value) / np.sqrt(self.variances[sensor])
            if self.mode == "frozen":
                logits -= 0.5 * residual * residual
            else:
                logits += self.log_ratio[np.searchsorted(BIN_UPPER, residual, side="left")]
        logits -= logits.max(initial=0.0)
        weights = np.exp(np.clip(logits, -60.0, 0.0))
        weights /= weights.sum()
        return weights, int(len(self.means) * max(1, len(observed)) * 5)

    def _next_sensor(self, weights: np.ndarray, unused: list[int]) -> tuple[int, int]:
        scores = []
        for sensor in unused:
            values = self.means[:, sensor]
            center = float(weights @ values)
            score = float(weights @ np.square(values - center)) / float(self.variances[sensor])
            scores.append((score, -sensor))
        best = max(scores)
        return -best[1], len(unused) * len(self.means) * 3

    def query(self, session: RawProbeSession, steps: int) -> int:
        unused = list(range(self.means.shape[1]))
        observed: dict[int, float] = {}
        weights = np.ones(len(self.means)) / len(self.means)
        operations = 0
        for _ in range(min(int(steps), len(unused))):
            sensor, cost = self._next_sensor(weights, unused)
            operations += cost
            observed[sensor] = session.probe(sensor)
            unused.remove(sensor)
            weights, cost = self._posterior(observed)
            operations += cost
        probes = len(observed)
        self.last_probe_count = probes
        self.last_input_ops = 2 * probes
        self.last_ops = self.last_input_ops + operations
        self.last_bytes_touched = 8 * (probes + operations) + self.state_bytes()
        return int(np.argmax(weights))

    def update(self, source: object, target: object = None) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return int(128 + self.means.nbytes + self.variances.nbytes + self.log_ratio.nbytes)


class Candidate(RawSensorProbeLearner):
    """Auditable default entry for the shared source-identical core."""
