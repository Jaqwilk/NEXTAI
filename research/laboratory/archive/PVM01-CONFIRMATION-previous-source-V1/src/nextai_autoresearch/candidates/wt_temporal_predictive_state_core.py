from __future__ import annotations

from collections import Counter

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase
from nextai_autoresearch.wt_prequential_contract import WTQuery, WTReveal, WTTraining


WINDOW = 32
WIDTH = 10
RANK = 4
FEATURES = 2 * RANK + 2
RIDGE = 1e-3
UPDATE_ETA = 0.25
CLIP = 8.0


def _array(value, *, pad: bool = False) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != WIDTH or not np.isfinite(result).all():
        raise ValueError("WT predictive-state tensors must be finite ten-channel matrices")
    if pad:
        result = result[:WINDOW]
        if len(result) < WINDOW:
            result = np.concatenate((result, np.repeat(result[-1:], WINDOW - len(result), axis=0)))
    if len(result) != WINDOW:
        raise ValueError("WT predictive-state windows must have length 32")
    return result


def _dct_basis(columns: int = RANK) -> np.ndarray:
    time = np.arange(WINDOW, dtype=np.float64)[:, None]
    order = np.arange(columns, dtype=np.float64)[None, :]
    basis = np.cos(np.pi * (time + 0.5) * order / WINDOW)
    basis[:, 0] *= 2.0 ** -0.5
    basis *= (2.0 / WINDOW) ** 0.5
    return basis


def _coverage_weights(controls: np.ndarray) -> np.ndarray:
    counts = Counter(map(float, controls))
    weights = np.asarray([1.0 / counts[float(value)] for value in controls], dtype=np.float64)
    return weights / weights.sum()


class TemporalPredictiveState(CandidateBase):
    mode = "predictive"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.fit_ops = self.meta_fit_ops = self.last_ops = self.update_ops = 0.0
        self.last_bytes_touched = self.last_update_bytes = 0.0
        self._slots: dict[int, np.ndarray] = {}

    def fit(self, training: WTTraining, knowledge_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(knowledge_size):
            raise ValueError("temporal predictive state requires exactly K train-only WT episodes")
        histories = np.stack([_array(ep.history).T for ep in training.episodes])
        futures = np.stack([(_array(ep.target, pad=True) - _array(ep.history)[-1]).T
                            for ep in training.episodes])
        controls = np.asarray([ep.control for ep in training.episodes], dtype=np.float64)
        episode_weights = _coverage_weights(controls)
        sample_weights = np.repeat(episode_weights / WIDTH, WIDTH)
        past = histories.reshape(-1, WINDOW)
        future = futures.reshape(-1, WINDOW)
        self.past_mean = sample_weights @ past
        centered_past = past - self.past_mean
        if self.mode == "predictive":
            future_mean = sample_weights @ future
            centered_future = future - future_mean
            moment = centered_past.T @ (sample_weights[:, None] * centered_future)
            left, singular, _ = np.linalg.svd(moment, full_matrices=False)
            rank = min(RANK, max(1, int(np.sum(singular > 1e-12))))
            projection = left[:, :rank]
            if rank < RANK:
                projection = np.column_stack((projection, _dct_basis(RANK)[:, rank:]))
            self.projection = projection
        elif self.mode == "history":
            covariance = centered_past.T @ (sample_weights[:, None] * centered_past)
            left, _, _ = np.linalg.svd(covariance, full_matrices=False)
            self.projection = left[:, :RANK]
        elif self.mode == "frozen":
            self.projection = _dct_basis()
        else:
            raise ValueError(f"unknown predictive-state intervention: {self.mode}")

        states = np.einsum("eci,ir->ecr", histories - self.past_mean, self.projection)
        self.future_mean = np.einsum("e,ecf->cf", episode_weights, futures)
        self.readout = np.empty((WIDTH, FEATURES, WINDOW), dtype=np.float64)
        identity = np.eye(FEATURES)
        for channel in range(WIDTH):
            state = states[:, channel]
            design = np.column_stack((np.ones(len(state)), state, controls,
                                      state * controls[:, None]))
            target = futures[:, channel] - self.future_mean[channel]
            gram = design.T @ (episode_weights[:, None] * design)
            self.readout[channel] = np.linalg.solve(
                gram + RIDGE * identity,
                design.T @ (episode_weights[:, None] * target),
            )
        samples = len(past)
        self.fit_ops = self.meta_fit_ops = float(
            2 * samples * WINDOW * WINDOW
            + 2 * len(training.episodes) * WIDTH * (FEATURES * FEATURES + FEATURES * WINDOW)
            + WIDTH * FEATURES ** 3
        )
        self._slots.clear()

    def _features(self, history, control: float) -> np.ndarray:
        state = (_array(history).T - self.past_mean) @ self.projection
        return np.column_stack((np.ones(WIDTH), state, np.full(WIDTH, float(control)),
                                state * float(control)))

    def _weights(self, slot: int) -> np.ndarray:
        return self._slots.get(slot, self.readout)

    def query(self, source: WTQuery, steps: int):
        if not isinstance(source, WTQuery) or int(steps) != source.horizon or source.horizon not in (16, 32, 96):
            raise ValueError("invalid anonymous WT predictive-state query")
        current = _array(source.history)
        weights = self._weights(source.slot)
        blocks = []
        for _ in range((source.horizon + WINDOW - 1) // WINDOW):
            features = self._features(current, source.control)
            residual = self.future_mean + np.einsum("cf,cft->ct", features, weights)
            block = np.clip(current[-1] + residual.T, -CLIP, CLIP)
            blocks.append(block)
            current = block
        prediction = np.concatenate(blocks)[:source.horizon]
        per_block = 2 * WIDTH * WINDOW * RANK + 2 * WIDTH * FEATURES * WINDOW
        self.last_ops = float(len(blocks) * per_block)
        self.last_bytes_touched = float(len(blocks) * (
            2 * WINDOW * WIDTH * 8 + self.projection.nbytes + weights.nbytes
            + self.future_mean.nbytes
        ))
        return prediction.tolist()

    def update(self, source: WTReveal) -> None:
        if not isinstance(source, WTReveal):
            raise ValueError("predictive-state update requires a post-artifact reveal")
        features = self._features(source.history, source.control)
        weights = self._slots.setdefault(source.slot, self.readout.copy())
        target = (_array(source.target, pad=True) - _array(source.history)[-1]).T - self.future_mean
        prediction = np.einsum("cf,cft->ct", features, weights)
        for channel in range(WIDTH):
            step = UPDATE_ETA / (1.0 + float(features[channel] @ features[channel]))
            weights[channel] += step * np.outer(features[channel], target[channel] - prediction[channel])
        self.update_ops = float(3 * WIDTH * FEATURES * WINDOW)
        self.last_update_bytes = float(weights.nbytes + features.nbytes + target.nbytes)

    def state_bytes(self) -> int:
        fixed = sum(value.nbytes for value in (
            self.past_mean, self.projection, self.future_mean, self.readout,
        ))
        return int(fixed + sum(value.nbytes for value in self._slots.values()) + 128)


class Candidate(TemporalPredictiveState):
    """Auditable standalone entry for the source-identical implementation."""
