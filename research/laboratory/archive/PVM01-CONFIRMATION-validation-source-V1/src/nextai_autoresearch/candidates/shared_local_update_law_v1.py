from __future__ import annotations

import numpy as np

from ..three_family_tensor_contract import Tensor, Training


BIN_EDGES = np.array((-4.0, -2.0, 0.0, 2.0, 4.0))
RATE_GRID = np.array((0.03125, 0.0625, 0.125, 0.25, 0.5, 1.0, 2.0))
DEFAULT_RATE = 1.0
WIDTH = 32
DESIGN = WIDTH + 1
CONSTANTS = (tuple(BIN_EDGES), tuple(RATE_GRID), DEFAULT_RATE)


def _bin(error: np.ndarray, target: np.ndarray) -> int:
    ratio = float(np.mean(error * error) / (np.mean(target * target) + 1e-12))
    return int(np.searchsorted(BIN_EDGES, np.log2(max(ratio, 1e-12)), side="right"))


def _step(weights: np.ndarray, row: np.ndarray, target: np.ndarray,
          visible: np.ndarray, rate: float) -> None:
    error = target[visible] - row @ weights[:, visible]
    weights[:, visible] += rate * np.outer(row, error) / (float(row @ row) + 1e-12)


class Candidate:
    """Learns only a coordinate-aggregate local NLMS update-rate table."""

    CONSTANTS = CONSTANTS

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rates = np.full(len(BIN_EDGES) + 1, DEFAULT_RATE)
        self.fit_ops = self.adaptation_ops = self.last_ops = 0.0
        self.last_bytes_touched = 0.0
        self.last_stable = True

    def fit(self, training: Training) -> None:
        if not isinstance(training, Training):
            raise ValueError("local update law requires anonymous tensor training")
        observations: list[list[float]] = [[] for _ in self.rates]
        self.fit_ops = 0.0
        for world in training.worlds:
            x = np.where(world.support_input.mask, world.support_input.values, 0.0).astype(np.float64)
            y = world.support_target.values.astype(np.float64)
            visible = world.support_target.mask
            weights = np.zeros((DESIGN, WIDTH), dtype=np.float64)
            design = np.column_stack((np.ones(len(x)), x))
            for index in range(len(design) - 1):
                mask, next_mask = visible[index], visible[index + 1]
                if not mask.any() or not next_mask.any():
                    continue
                row, following = design[index], design[index + 1]
                error = y[index, mask] - row @ weights[:, mask]
                bucket = _bin(error, y[index, mask])
                direction = np.zeros_like(weights)
                direction[:, mask] = np.outer(row, error) / (float(row @ row) + 1e-12)
                losses = [
                    float(np.mean((y[index + 1, next_mask]
                                   - following @ (weights + rate * direction)[:, next_mask]) ** 2))
                    for rate in RATE_GRID
                ]
                rate = float(RATE_GRID[int(np.argmin(losses))])
                observations[bucket].append(rate)
                weights += rate * direction
                self.fit_ops += float(len(RATE_GRID) * DESIGN * max(1, next_mask.sum())
                                      + 2 * DESIGN * max(1, mask.sum()))
        self.rates = np.array([
            float(np.median(values)) if values else DEFAULT_RATE for values in observations
        ])

    def adapt(self, support_input: Tensor, support_target: Tensor) -> dict[str, np.ndarray]:
        x = np.where(support_input.mask, support_input.values, 0.0).astype(np.float64)
        y = support_target.values.astype(np.float64)
        design = np.column_stack((np.ones(len(x)), x))
        weights = np.zeros((DESIGN, WIDTH), dtype=np.float64)
        self.adaptation_ops = 0.0
        for row, target, visible in zip(design, y, support_target.mask):
            if not visible.any():
                continue
            error = target[visible] - row @ weights[:, visible]
            rate = float(self.rates[_bin(error, target[visible])])
            _step(weights, row, target, visible, rate)
            self.adaptation_ops += float(2 * DESIGN * max(1, visible.sum()) + 2 * DESIGN)
        return {
            "weights": weights,
            "input_mask": support_input.mask.any(axis=0),
            "output_mask": support_target.mask.any(axis=0),
        }

    def predict(self, session: dict[str, np.ndarray], history: Tensor,
                future_public: Tensor) -> np.ndarray:
        weights = session["weights"]
        inputs = session["input_mask"]
        outputs = np.flatnonzero(session["output_mask"])
        public = future_public.mask.any(axis=0) & inputs
        state = np.flatnonzero(inputs & ~public)
        current = np.where(history.mask[-1] & inputs, history.values[-1], 0.0).astype(np.float64)
        result = np.zeros((50, WIDTH), dtype=np.float64)
        self.last_stable = True
        for index in range(50):
            prediction = np.r_[1.0, current] @ weights[:, outputs]
            self.last_stable = self.last_stable and bool(
                np.isfinite(prediction).all() and np.max(np.abs(prediction), initial=0.0) <= 1e6
            )
            prediction = np.clip(np.nan_to_num(prediction, nan=0.0, posinf=1e6, neginf=-1e6), -1e6, 1e6)
            result[index, outputs] = prediction
            current[:] = 0.0
            current[public] = future_public.values[index, public]
            count = min(len(state), len(prediction))
            current[state[:count]] = prediction[:count]
        self.last_ops = float(50 * DESIGN * max(1, len(outputs)))
        self.last_bytes_touched = float(
            self.rates.nbytes + weights.nbytes + history.values.nbytes
            + future_public.values.nbytes + result.nbytes
        )
        return result.astype(np.float32)

    def state_bytes(self) -> int:
        return int(self.rates.nbytes + DESIGN * WIDTH * np.dtype(np.float64).itemsize)
