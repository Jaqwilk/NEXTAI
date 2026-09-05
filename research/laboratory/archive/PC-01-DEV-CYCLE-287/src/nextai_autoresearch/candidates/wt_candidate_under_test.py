from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase
from nextai_autoresearch.wt_prequential_contract import WTQuery, WTReveal, WTTraining


WIDTH = 10
POPULATION = 2 * WIDTH + 2


def _matrix(value) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != WIDTH or not np.isfinite(array).all():
        raise ValueError("WT event tensors must be finite ten-channel matrices")
    return array


def _active_rows(history: np.ndarray, control: float) -> np.ndarray:
    delta = history[-1] - history[-2]
    magnitude = np.abs(delta)
    winners = np.flatnonzero(magnitude == magnitude.max())
    response = 2 * winners + (delta[winners] < 0.0)
    control_row = 2 * WIDTH + int(float(control) < 0.0)
    return np.concatenate((response, [control_row])).astype(np.int64)


def _velocity(history: np.ndarray, target: np.ndarray) -> np.ndarray:
    return (target[-1] - history[-1]) / float(len(target))


class Candidate(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.meta_fit_ops = self.last_bytes_touched = self.last_update_bytes = 0.0
        self._slots: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    def fit(self, training: WTTraining, universe_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(universe_size):
            raise ValueError("WT event fit requires exactly K frozen episodes")
        sums = np.zeros((POPULATION, WIDTH), dtype=np.float64)
        counts = np.zeros(POPULATION, dtype=np.float64)
        operations = 0
        for episode in training.episodes:
            history, target = _matrix(episode.history), _matrix(episode.target)
            rows, velocity = _active_rows(history, episode.control), _velocity(history, target)
            sums[rows] += velocity
            counts[rows] += 1.0
            operations += 3 * WIDTH + 2 * len(rows) * WIDTH
        self._weights = np.divide(sums, counts[:, None], out=sums, where=counts[:, None] > 0.0)
        self._counts = counts
        self.fit_ops = self.meta_fit_ops = float(operations)
        self._slots.clear()

    def _state(self, slot: int) -> tuple[np.ndarray, np.ndarray]:
        if slot not in self._slots:
            self._slots[slot] = (self._weights.copy(), self._counts.copy())
        return self._slots[slot]

    def query(self, source: WTQuery, steps: int):
        if not isinstance(source, WTQuery) or int(steps) != source.horizon:
            raise ValueError("invalid WT event query")
        history = _matrix(source.history)
        weights, _ = self._state(source.slot)
        rows = _active_rows(history, source.control)
        velocity = weights[rows].mean(axis=0)
        result = history[-1] + np.arange(1, int(steps) + 1)[:, None] * velocity
        if not np.isfinite(result).all():
            raise ValueError("WT event query produced non-finite state")
        self.last_ops = float(2 * WIDTH + len(rows) * WIDTH + int(steps) * 2 * WIDTH)
        self.last_bytes_touched = float(history.nbytes + result.nbytes + weights[rows].nbytes)
        return result.tolist()

    def update(self, source: WTReveal) -> None:
        if not isinstance(source, WTReveal):
            raise ValueError("WT event update requires a post-prediction reveal")
        history, target = _matrix(source.history), _matrix(source.target)
        weights, counts = self._state(source.slot)
        rows, velocity = _active_rows(history, source.control), _velocity(history, target)
        for row in rows:
            counts[row] += 1.0
            weights[row] += (velocity - weights[row]) / counts[row]
        self.update_ops = float(3 * WIDTH + 3 * len(rows) * WIDTH)
        self.last_update_bytes = float(len(rows) * (WIDTH + 1) * 8)

    def state_bytes(self) -> int:
        total = self._weights.nbytes + self._counts.nbytes
        total += sum(weights.nbytes + counts.nbytes for weights, counts in self._slots.values())
        return int(total)
