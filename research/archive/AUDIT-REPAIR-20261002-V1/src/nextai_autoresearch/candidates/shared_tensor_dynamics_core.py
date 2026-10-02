from __future__ import annotations

import numpy as np

from ..three_family_tensor_contract import Tensor, Training, World, pad


RIDGE = 1e-3
PRIOR_WEIGHT = 0.25
RESIDUAL_CLIP = 0.25
STATE_CLIP = 8.0


def _coefficients(target: Tensor) -> tuple[np.ndarray, float]:
    width = int(target.mask.any(axis=0).sum())
    values = target.values[:, :width].astype(np.float64)
    valid = target.mask[:, :width]
    previous, delta = values[:-1], values[1:] - values[:-1]
    usable = valid[:-1] & valid[1:]
    z = previous[usable]
    design = np.column_stack((np.ones(len(z)), z, np.tanh(z)))
    response = delta[usable]
    if not len(response):
        return np.zeros(3, dtype=np.float64), 0.0
    gram = design.T @ design + RIDGE * np.eye(3)
    coefficients = np.linalg.solve(gram, design.T @ response)
    ops = float(len(response) * (2 * 3**2 + 2 * 3) + 3**3)
    return coefficients, ops


class Candidate:
    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.prior: np.ndarray | None = None
        self.fit_ops = self.adaptation_ops = self.last_ops = 0.0
        self.last_bytes_touched = 0.0
        self.last_stable = True

    def fit(self, training: Training) -> None:
        fitted, ops = [], 0.0
        for world in training.worlds:
            local, local_ops = _coefficients(world.support_target)
            fitted.append(local)
            ops += local_ops
        if not fitted:
            self.prior = None
            self.fit_ops = 0.0
            return
        stack = np.asarray(sorted((tuple(row) for row in fitted)), dtype=np.float64)
        self.prior = stack.mean(axis=0)
        self.fit_ops = ops + float(stack.size)

    def adapt(self, support_input: Tensor, support_target: Tensor) -> dict[str, np.ndarray]:
        local, ops = _coefficients(support_target)
        coefficients = local if self.prior is None else (
            PRIOR_WEIGHT * self.prior + (1.0 - PRIOR_WEIGHT) * local
        )
        input_width = int(support_input.mask.any(axis=0).sum())
        output_width = int(support_target.mask.any(axis=0).sum())
        self.adaptation_ops = ops + (0.0 if self.prior is None else 6.0)
        return {
            "coefficients": coefficients,
            "input_width": np.array(input_width),
            "output_width": np.array(output_width),
            "support_last": support_target.values[-1, :output_width].astype(np.float64),
        }

    def predict(self, session: dict[str, np.ndarray], history: Tensor,
                future_public: Tensor) -> np.ndarray:
        input_width = int(session["input_width"])
        output_width = int(session["output_width"])
        future_width = int(future_public.mask.any(axis=0).sum())
        if input_width - future_width >= output_width:
            current = history.values[-1, input_width - output_width:input_width].astype(np.float64)
        else:
            current = session["support_last"].astype(np.float64).copy()
        output = np.zeros((50, 32), dtype=np.float64)
        coefficients = session["coefficients"]
        self.last_stable = True
        for step in range(50):
            features = np.stack((np.ones(output_width), current, np.tanh(current)), axis=1)
            residual = np.clip(features @ coefficients, -RESIDUAL_CLIP, RESIDUAL_CLIP)
            current = np.clip(current + residual, -STATE_CLIP, STATE_CLIP)
            self.last_stable = self.last_stable and bool(np.isfinite(current).all())
            output[step, :output_width] = current
        self.last_ops = float(50 * output_width * 10)
        self.last_bytes_touched = float(
            history.values.nbytes + future_public.values.nbytes + output.nbytes
            + coefficients.nbytes + session["support_last"].nbytes
        )
        return output.astype(np.float32)

    def state_bytes(self) -> int:
        return 0 if self.prior is None else int(self.prior.nbytes)


def semantic_fixture() -> tuple[float, float, float]:
    def world(slot: int, offset: float = 0.0) -> World:
        t = np.linspace(-1.0, 1.0, 108)[:, None]
        y = np.column_stack((t[:, 0] + offset, np.tanh(t[:, 0]) - offset))
        return World(slot, pad(y, 108), pad(y, 108), pad(np.tile(y[-1], (32, 1)), 32),
                     pad(np.zeros((50, 1)), 50), pad(np.zeros((50, 2)), 50))

    worlds = (world(0), world(1, 0.2), world(2, -0.1))
    first, reordered = Candidate(7), Candidate(7)
    first.fit(Training(worlds))
    reordered.fit(Training(tuple(reversed(worlds))))
    order_error = float(np.max(np.abs(first.prior - reordered.prior)))

    base = worlds[0]
    session = first.adapt(base.support_input, base.support_target)
    original = first.predict(session, base.history, base.future_public)[:, :2]
    permutation = np.array([1, 0])
    permuted_world = World(3, pad(base.support_input.values[:, :2][:, permutation], 108),
                           pad(base.support_target.values[:, :2][:, permutation], 108),
                           pad(base.history.values[:, :2][:, permutation], 32),
                           base.future_public, base.output)
    permuted_session = first.adapt(permuted_world.support_input, permuted_world.support_target)
    permuted = first.predict(permuted_session, permuted_world.history,
                             permuted_world.future_public)[:, :2]
    permutation_error = float(np.max(np.abs(original[:, permutation] - permuted)))
    maximum = float(np.max(np.abs(permuted)))
    if order_error > 1e-15 or permutation_error > 1e-6 or not np.isfinite(permuted).all() or maximum > STATE_CLIP:
        raise AssertionError((order_error, permutation_error, maximum))
    return order_error, permutation_error, maximum
