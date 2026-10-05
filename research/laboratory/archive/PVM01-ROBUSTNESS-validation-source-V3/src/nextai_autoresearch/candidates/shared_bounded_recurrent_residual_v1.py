from __future__ import annotations

import numpy as np

from ..three_family_tensor_contract import Tensor, Training


RIDGE = 1e-3
RESIDUAL_BOUND = 4.0
WIDTH = 32
DESIGN = WIDTH + 1


def _add(
    grams: np.ndarray, rhs: np.ndarray, source: Tensor, target: Tensor,
) -> float:
    x = np.where(source.mask, source.values, 0.0).astype(np.float64)
    design = np.column_stack((np.ones(len(x)), x))
    operations = 0.0
    for output in np.flatnonzero(target.mask.any(axis=0)):
        visible = target.mask[:, output]
        local = design[visible]
        grams[output] += local.T @ local
        rhs[:, output] += local.T @ target.values[visible, output]
        operations += float(len(local) * DESIGN * (DESIGN + 1))
    return operations


class Candidate:
    """Source-identical affine recurrence bounded around mechanical persistence."""

    RIDGE = RIDGE
    RESIDUAL_BOUND = RESIDUAL_BOUND

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.fit_ops = self.adaptation_ops = self.last_ops = 0.0
        self.last_bytes_touched = 0.0
        self.last_stable = True

    def fit(self, training: Training) -> None:
        if not isinstance(training, Training):
            raise ValueError("recurrent residual fit requires anonymous tensor training")
        self._grams = np.zeros((WIDTH, DESIGN, DESIGN), dtype=np.float64)
        self._rhs = np.zeros((DESIGN, WIDTH), dtype=np.float64)
        for world in training.worlds:
            self.fit_ops += _add(self._grams, self._rhs, world.support_input, world.support_target)

    def adapt(self, support_input: Tensor, support_target: Tensor) -> dict[str, np.ndarray]:
        grams, rhs = self._grams.copy(), self._rhs.copy()
        self.adaptation_ops = _add(grams, rhs, support_input, support_target)
        weights = np.zeros((DESIGN, WIDTH), dtype=np.float64)
        output_mask = support_target.mask.any(axis=0)
        identity = np.eye(DESIGN)
        for output in np.flatnonzero(output_mask):
            weights[:, output] = np.linalg.solve(grams[output] + RIDGE * identity, rhs[:, output])
            self.adaptation_ops += float(DESIGN ** 3)
        return {
            "weights": weights,
            "input_mask": support_input.mask.any(axis=0),
            "output_mask": output_mask,
        }

    @staticmethod
    def _base(current: np.ndarray, state: np.ndarray, outputs: np.ndarray) -> np.ndarray:
        base = np.zeros(len(outputs), dtype=np.float64)
        count = min(len(state), len(outputs))
        base[:count] = current[state[:count]]
        return base

    def predict(self, session: dict[str, np.ndarray], history: Tensor, future_public: Tensor) -> np.ndarray:
        weights = session["weights"]
        inputs = session["input_mask"]
        outputs = np.flatnonzero(session["output_mask"])
        public = future_public.mask.any(axis=0) & inputs
        state = np.flatnonzero(inputs & ~public)
        current = np.where(history.mask[-1] & inputs, history.values[-1], 0.0).astype(np.float64)
        result = np.zeros((50, WIDTH), dtype=np.float64)
        for step in range(50):
            base = self._base(current, state, outputs)
            proposed = np.r_[1.0, current] @ weights[:, outputs]
            following = base + np.clip(proposed - base, -RESIDUAL_BOUND, RESIDUAL_BOUND)
            result[step, outputs] = following
            current[:] = 0.0
            current[public] = future_public.values[step, public]
            count = min(len(state), len(following))
            current[state[:count]] = following[:count]
        self.last_stable = bool(np.isfinite(result).all())
        if not self.last_stable:
            raise ValueError("recurrent residual prediction is non-finite")
        self.last_ops = float(50 * (2 * DESIGN * max(1, len(outputs)) + 4 * len(outputs)))
        self.last_bytes_touched = float(
            weights.nbytes + history.values.nbytes + future_public.values.nbytes + result.nbytes
        )
        return result.astype(np.float32)

    def state_bytes(self) -> int:
        return int(self._grams.nbytes + self._rhs.nbytes)
