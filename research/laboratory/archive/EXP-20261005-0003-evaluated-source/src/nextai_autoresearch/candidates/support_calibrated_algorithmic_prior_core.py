from __future__ import annotations

import numpy as np

from ..three_family_tensor_contract import Tensor, Training, World, pad
from .tensor_baseline_core import TensorBaseline


ATOMS = ("persistence", "ridge", "rls")
CALIBRATION_ROWS = 72
TEMPERATURE = 1.0
PRIOR_BLEND = 0.5
MAX_SESSION_BYTES = 3 * 33 * 32 * 8


def _slice(tensor: Tensor, start: int, stop: int) -> Tensor:
    return Tensor(tensor.values[start:stop], tensor.mask[start:stop])


def _runtime(variant: str, inputs: Tensor, targets: Tensor) -> tuple[TensorBaseline, dict, float]:
    atom = TensorBaseline(0, variant)
    atom.fit(Training(()))
    session = atom.adapt(inputs, targets)
    return atom, session, float(atom.fit_ops + atom.adaptation_ops)


def _calibration_weights(inputs: Tensor, targets: Tensor) -> tuple[np.ndarray, float]:
    fit_x, fit_y = _slice(inputs, 0, CALIBRATION_ROWS), _slice(targets, 0, CALIBRATION_ROWS)
    width_x = int(inputs.mask.any(axis=0).sum())
    width_y = int(targets.mask.any(axis=0).sum())
    truth = targets.values[CALIBRATION_ROWS:, :width_y].astype(np.float64)
    mask = targets.mask[CALIBRATION_ROWS:, :width_y]
    predictions, operations = [], 0.0
    for variant in ATOMS:
        _, session, atom_ops = _runtime(variant, fit_x, fit_y)
        if variant == "persistence":
            prediction = targets.values[CALIBRATION_ROWS - 1 : -1, :width_y].astype(np.float64)
        else:
            design = np.column_stack((
                np.ones(len(truth)),
                inputs.values[CALIBRATION_ROWS:, :width_x].astype(np.float64),
            ))
            prediction = design @ session["weights"]
            operations += float(design.size * max(1, width_y))
        predictions.append(prediction)
        operations += atom_ops
    losses = np.asarray([
        float(np.mean(np.square(prediction[mask] - truth[mask])))
        for prediction in predictions
    ])
    weights = np.exp(-(losses - losses.min()) / TEMPERATURE)
    weights /= weights.sum()
    operations += float(len(losses) * (len(truth) * max(1, width_y) * 3 + 3))
    return weights, operations


class Candidate:
    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.prior: np.ndarray | None = None
        self.fit_ops = self.adaptation_ops = self.last_ops = 0.0
        self.last_bytes_touched = 0.0
        self.last_stable = True

    def fit(self, training: Training) -> None:
        fitted, operations = [], 0.0
        for world in training.worlds:
            weights, local_ops = _calibration_weights(
                world.support_input, world.support_target
            )
            fitted.append(weights)
            operations += local_ops
        if not fitted:
            self.prior, self.fit_ops = None, 0.0
            return
        ordered = np.asarray(sorted(tuple(row) for row in fitted), dtype=np.float64)
        self.prior = ordered.mean(axis=0)
        self.prior /= self.prior.sum()
        self.fit_ops = operations + float(ordered.size + len(self.prior))

    def adapt(self, support_input: Tensor, support_target: Tensor) -> dict:
        local, operations = _calibration_weights(support_input, support_target)
        weights = local if self.prior is None else (
            PRIOR_BLEND * self.prior + (1.0 - PRIOR_BLEND) * local
        )
        weights = weights / weights.sum()
        runtimes = []
        for variant in ATOMS:
            atom, session, atom_ops = _runtime(variant, support_input, support_target)
            runtimes.append((atom, session))
            operations += atom_ops
        self.adaptation_ops = operations + float(len(weights) * 3)
        return {"weights": weights, "runtimes": tuple(runtimes)}

    def predict(self, session: dict, history: Tensor, future_public: Tensor) -> np.ndarray:
        predictions = np.asarray([
            atom.predict(atom_session, history, future_public)
            for atom, atom_session in session["runtimes"]
        ], dtype=np.float64)
        output = np.tensordot(session["weights"], predictions, axes=(0, 0))
        self.last_stable = bool(
            np.isfinite(output).all() and np.max(np.abs(output)) <= 1e6
        )
        output = np.nan_to_num(output, nan=0.0, posinf=1e6, neginf=-1e6)
        output = np.clip(output, -1e6, 1e6)
        self.last_ops = float(
            sum(atom.last_ops for atom, _ in session["runtimes"])
            + predictions.size * 2
        )
        self.last_bytes_touched = float(
            sum(atom.last_bytes_touched for atom, _ in session["runtimes"])
            + predictions.nbytes + session["weights"].nbytes + output.nbytes
        )
        return output.astype(np.float32)

    def state_bytes(self) -> int:
        return MAX_SESSION_BYTES + (0 if self.prior is None else int(self.prior.nbytes))


def semantic_fixture() -> dict[str, float | bool | list[float]]:
    def world(slot: int, coefficient: float) -> World:
        control = np.sin(np.linspace(0, 4, 108))
        target = np.empty(108)
        target[0] = 0.1
        for index in range(1, 108):
            target[index] = coefficient * target[index - 1] + 0.1 * control[index]
        support_input = np.column_stack((control, np.r_[target[0], target[:-1]]))
        history = support_input[-32:]
        future = np.zeros((50, 1))
        return World(slot, pad(support_input, 108), pad(target[:, None], 108),
                     pad(history, 32), pad(future, 50), pad(np.zeros((50, 1)), 50))

    worlds = (world(0, 0.4), world(1, 0.6), world(2, 0.8))
    first, reordered, repeated = Candidate(7), Candidate(7), Candidate(999)
    first.fit(Training(worlds))
    reordered.fit(Training(tuple(reversed(worlds))))
    repeated.fit(Training(worlds))
    order_error = float(np.max(np.abs(first.prior - reordered.prior)))
    deterministic_error = float(np.max(np.abs(first.prior - repeated.prior)))
    session = first.adapt(worlds[0].support_input, worlds[0].support_target)
    prediction = first.predict(session, worlds[0].history, worlds[0].future_public)
    weights = np.asarray(session["weights"])
    valid = bool(
        order_error <= 1e-15
        and deterministic_error <= 1e-15
        and np.isfinite(weights).all()
        and np.all(weights >= 0)
        and abs(float(weights.sum()) - 1.0) <= 1e-12
        and prediction.shape == (50, 32)
        and np.isfinite(prediction).all()
        and first.last_stable
        and first.fit_ops > 0
        and first.adaptation_ops > 0
        and first.last_ops > 0
        and first.last_bytes_touched > 0
        and first.state_bytes() >= MAX_SESSION_BYTES
    )
    if not valid:
        raise AssertionError((order_error, deterministic_error, weights, first.last_stable))
    return {
        "order_error": order_error,
        "deterministic_error": deterministic_error,
        "weights": [float(value) for value in weights],
        "weights_sum": float(weights.sum()),
        "rollout_finite": bool(np.isfinite(prediction).all()),
        "rollout_stable": first.last_stable,
        "fit_ops": first.fit_ops,
        "adaptation_ops": first.adaptation_ops,
        "query_ops": first.last_ops,
        "bytes_touched": first.last_bytes_touched,
        "state_bytes": float(first.state_bytes()),
    }
