from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase
from nextai_autoresearch.wt_prequential_contract import WTQuery, WTReveal, WTTraining


WINDOW, WIDTH, FEATURES, MAX_HORIZON = 32, 10, 5, 96
TRACE_DECAY, ERROR_GATE, UPDATE_ETA = 0.75, 0.90, 0.05
FEATURE_CLIP, WEIGHT_CLIP, OUTPUT_CLIP = 4.0, 2.0, 8.0
MODES = {
    "aligned_error_gated", "frozen_zero_trace",
    "shuffled_temporal_credit", "aligned_dense_credit",
}


def _matrix(value, rows: int | None = None) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != WIDTH or not np.isfinite(array).all():
        raise ValueError("WT local-credit tensors must be finite ten-channel matrices")
    if rows is not None and len(array) != rows:
        raise ValueError(f"WT local-credit tensor must have {rows} rows")
    return array


class LocalCreditTrace(CandidateBase):
    """One shared implementation; wrappers select only a frozen causal intervention."""

    mode = "aligned_error_gated"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        if self.mode not in MODES:
            raise ValueError(f"unknown local-credit intervention: {self.mode}")
        newest_first = TRACE_DECAY ** np.arange(WINDOW - 1, -1, -1, dtype=np.float64)
        self._aligned_weights = newest_first / newest_first.sum()
        permutation = np.random.default_rng(int(seed) ^ 0x454C4947).permutation(WINDOW)
        self._shuffled_weights = self._aligned_weights[permutation]
        self._slots: dict[int, np.ndarray] = {}
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0.0

    def fit(self, training: WTTraining, knowledge_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(knowledge_size):
            raise ValueError("local credit requires exactly K train-only WT episodes")
        sums: dict[float, np.ndarray] = {}
        counts: dict[float, int] = {}
        global_sum = np.zeros((WINDOW, WIDTH), dtype=np.float64)
        for episode in training.episodes:
            history = _matrix(episode.history, WINDOW)
            target = _matrix(episode.target, WINDOW)
            residual = target - history[-1]
            key = float(episode.control)
            sums[key] = sums.get(key, np.zeros_like(residual)) + residual
            counts[key] = counts.get(key, 0) + 1
            global_sum += residual
        self._banks = {key: value / counts[key] for key, value in sums.items()}
        self._global = global_sum / len(training.episodes)
        self._slots.clear()
        self.fit_ops = self.meta_fit_ops = float(len(training.episodes) * WINDOW * WIDTH * 2)

    def _base_residual(self, control: float, horizon: int) -> np.ndarray:
        bank = self._banks.get(float(control), self._global)
        if horizon <= WINDOW:
            return bank[:horizon]
        return np.concatenate((bank, np.repeat(bank[-1:], horizon - WINDOW, axis=0)))

    def _trace(self, history, control: float) -> np.ndarray:
        values = _matrix(history, WINDOW)
        differences = np.vstack((np.zeros((1, WIDTH)), np.diff(values, axis=0)))
        features = np.stack((
            np.ones_like(values), np.full_like(values, float(control)), values,
            differences, values * float(control),
        ), axis=2)
        features = np.clip(features, -FEATURE_CLIP, FEATURE_CLIP)
        weights = self._shuffled_weights if self.mode == "shuffled_temporal_credit" else self._aligned_weights
        return np.clip(np.einsum("t,tcf->cf", weights, features), -FEATURE_CLIP, FEATURE_CLIP)

    def _predict(self, slot: int, history, control: float, horizon: int) -> tuple[np.ndarray, np.ndarray]:
        current = _matrix(history, WINDOW)
        trace = self._trace(current, control)
        weights = self._slots.get(int(slot))
        correction = (np.zeros((horizon, WIDTH)) if weights is None
                      else np.einsum("cf,cfh->hc", trace, weights[:, :, :horizon]))
        prediction = current[-1] + self._base_residual(control, horizon) + correction
        return np.clip(prediction, -OUTPUT_CLIP, OUTPUT_CLIP), trace

    def query(self, source: WTQuery, steps: int):
        if (not isinstance(source, WTQuery) or int(steps) != source.horizon
                or source.horizon not in (16, 32, 96)):
            raise ValueError("invalid anonymous WT local-credit query")
        prediction, trace = self._predict(
            source.slot, source.history, source.control, source.horizon,
        )
        weights = self._slots.get(int(source.slot))
        self.last_ops = float(WINDOW * WIDTH * FEATURES * 3 + source.horizon * WIDTH * FEATURES * 2)
        self.last_bytes_touched = float(
            WINDOW * WIDTH * 8 + trace.nbytes + prediction.nbytes
            + (0 if weights is None else weights.nbytes)
        )
        return prediction.tolist()

    def update(self, source: WTReveal) -> None:
        if not isinstance(source, WTReveal):
            raise ValueError("local-credit update requires a post-artifact reveal")
        target = _matrix(source.target)
        if len(target) not in (16, 32, 96):
            raise ValueError("local-credit reveal has an undeclared horizon")
        prediction, trace = self._predict(source.slot, source.history, source.control, len(target))
        error = target - prediction
        rms = float(np.sqrt(np.mean(error * error)))
        common_ops = WINDOW * WIDTH * FEATURES * 3 + len(target) * WIDTH * (FEATURES * 2 + 3)
        should_update = self.mode == "aligned_dense_credit" or (
            self.mode in {"aligned_error_gated", "shuffled_temporal_credit"} and rms > ERROR_GATE
        )
        if self.mode == "frozen_zero_trace" or not should_update:
            self.update_ops = float(common_ops)
            self.last_update_bytes = float(trace.nbytes + target.nbytes + prediction.nbytes)
            return
        weights = self._slots.setdefault(
            int(source.slot), np.zeros((WIDTH, FEATURES, MAX_HORIZON), dtype=np.float64),
        )
        for channel in range(WIDTH):
            step = UPDATE_ETA / (1.0 + float(trace[channel] @ trace[channel]))
            weights[channel, :, :len(target)] += step * np.outer(trace[channel], error[:, channel])
        np.clip(weights, -WEIGHT_CLIP, WEIGHT_CLIP, out=weights)
        self.update_ops = float(common_ops + WIDTH * len(target) * FEATURES * 3)
        self.last_update_bytes = float(trace.nbytes + target.nbytes + prediction.nbytes + weights.nbytes)

    def state_bytes(self) -> int:
        fixed = self._global.nbytes + self._aligned_weights.nbytes + self._shuffled_weights.nbytes
        fixed += sum(bank.nbytes + 8 for bank in self._banks.values())
        return int(fixed + sum(weights.nbytes for weights in self._slots.values()) + 128)


class Candidate(LocalCreditTrace):
    """Auditable standalone entry for the shared implementation."""
