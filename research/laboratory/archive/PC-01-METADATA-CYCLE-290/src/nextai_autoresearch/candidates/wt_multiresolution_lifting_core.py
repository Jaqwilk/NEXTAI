from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase
from nextai_autoresearch.wt_prequential_contract import WTQuery, WTReveal, WTTraining


LENGTH = 32
WIDTH = 10
RETAINED = 16
FEATURES = RETAINED + 1
RIDGE = 1e-3
UPDATE_SCALE = 0.25
CLIP = 8.0
HAAR_OPS = 4 * (LENGTH - 1) * WIDTH


def _matrix(value, *, pad: bool = False) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != WIDTH or not np.isfinite(result).all():
        raise ValueError("WT lifting tensors must be finite ten-channel matrices")
    if pad:
        result = result[:LENGTH]
        if len(result) < LENGTH:
            result = np.concatenate((result, np.repeat(result[-1:], LENGTH - len(result), axis=0)))
    if len(result) != LENGTH:
        raise ValueError("WT lifting tensors must have length 32")
    return result


def haar(value: np.ndarray) -> np.ndarray:
    result = _matrix(value).copy()
    size = LENGTH
    scale = 2.0 ** -0.5
    while size > 1:
        half = size // 2
        even, odd = result[:size:2].copy(), result[1:size:2].copy()
        result[:half] = (even + odd) * scale
        result[half:size] = (even - odd) * scale
        size = half
    return result


def inverse_haar(value: np.ndarray) -> np.ndarray:
    result = _matrix(value).copy()
    scale = 2.0 ** -0.5
    size = 2
    while size <= LENGTH:
        half = size // 2
        mean, detail = result[:half].copy(), result[half:size].copy()
        result[:size:2] = (mean + detail) * scale
        result[1:size:2] = (mean - detail) * scale
        size *= 2
    return result


class LiftingCandidate(CandidateBase):
    mode = "multiresolution"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.fit_ops = self.meta_fit_ops = self.last_ops = self.update_ops = 0.0
        self.last_bytes_touched = self.last_update_bytes = 0.0
        self._weights = np.zeros((FEATURES, RETAINED), dtype=np.float64)
        self._weights[:RETAINED] = np.eye(RETAINED)
        self._slots: dict[int, np.ndarray] = {}

    def _xy(self, history, control: float, target=None) -> tuple[np.ndarray, np.ndarray | None]:
        coefficients = haar(_matrix(history))[:RETAINED].T
        x = np.column_stack((coefficients, np.full(WIDTH, float(control))))
        y = None if target is None else haar(_matrix(target, pad=True))[:RETAINED].T
        if self.mode == "single_scale":
            x[:, 1:RETAINED] = 0.0
            if y is not None:
                y[:, 1:] = 0.0
        return x, y

    def fit(self, training: WTTraining, universe_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(universe_size):
            raise ValueError("WT lifting fit requires exactly K frozen episodes")
        xs, ys = [], []
        for episode in training.episodes:
            x, y = self._xy(episode.history, episode.control, episode.target)
            xs.append(x)
            ys.append(y)
        x, y = np.concatenate(xs), np.concatenate(ys)
        solved = np.linalg.solve(x.T @ x + RIDGE * np.eye(FEATURES), x.T @ y)
        if self.mode != "frozen_lifting":
            self._weights = solved
        rows = len(x)
        self.fit_ops = self.meta_fit_ops = float(
            2 * len(training.episodes) * HAAR_OPS
            + 2 * rows * FEATURES * FEATURES
            + 2 * rows * FEATURES * RETAINED
            + FEATURES ** 3
        )
        self._slots.clear()

    def _slot(self, slot: int) -> np.ndarray:
        if slot not in self._slots:
            self._slots[slot] = self._weights.copy()
        return self._slots[slot]

    def query(self, source: WTQuery, steps: int):
        if not isinstance(source, WTQuery) or int(steps) != source.horizon:
            raise ValueError("invalid WT lifting query")
        current = _matrix(source.history)
        weights = self._slot(source.slot)
        blocks = []
        for _ in range((int(steps) + LENGTH - 1) // LENGTH):
            x, _ = self._xy(current, source.control)
            coefficients = np.zeros((LENGTH, WIDTH), dtype=np.float64)
            coefficients[:RETAINED] = (x @ weights).T
            block = np.clip(inverse_haar(coefficients), -CLIP, CLIP)
            blocks.append(block)
            current = block
        prediction = np.concatenate(blocks)[:int(steps)]
        if not np.isfinite(prediction).all():
            raise ValueError("WT lifting query produced non-finite state")
        per_block = 2 * HAAR_OPS + 2 * WIDTH * FEATURES * RETAINED + LENGTH * WIDTH
        self.last_ops = float(len(blocks) * per_block)
        self.last_bytes_touched = float(len(blocks) * (
            2 * LENGTH * WIDTH * 8 + FEATURES * RETAINED * 8
            + WIDTH * (FEATURES + RETAINED) * 8
        ))
        return prediction.tolist()

    def update(self, source: WTReveal) -> None:
        if not isinstance(source, WTReveal):
            raise ValueError("WT lifting update requires a post-prediction reveal")
        weights = self._slot(source.slot)
        x, y = self._xy(source.history, source.control, source.target)
        residual = y - x @ weights
        steps = UPDATE_SCALE / (1.0 + np.einsum("ij,ij->i", x, x))
        delta = x.T @ (steps[:, None] * residual) / WIDTH
        if self.mode == "single_scale":
            delta[1:RETAINED] = 0.0
            delta[:, 1:] = 0.0
        if self.mode != "frozen_lifting":
            weights += delta
        self.update_ops = float(
            2 * HAAR_OPS + 4 * WIDTH * FEATURES * RETAINED + 3 * WIDTH * FEATURES
        )
        self.last_update_bytes = float(
            2 * LENGTH * WIDTH * 8 + weights.nbytes
            + WIDTH * (FEATURES + 2 * RETAINED) * 8
        )

    def state_bytes(self) -> int:
        return int(self._weights.nbytes + sum(value.nbytes for value in self._slots.values()))


class Candidate(LiftingCandidate):
    """Auditable standalone entry for the shared lifting implementation."""
