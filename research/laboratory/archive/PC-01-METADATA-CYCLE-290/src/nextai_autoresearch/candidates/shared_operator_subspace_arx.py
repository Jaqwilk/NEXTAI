from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.dronepropa_baselines import (
    RIDGE,
    affine_predict,
    affine_ridge,
)
from nextai_autoresearch.dronepropa_contract import (
    DynamicsTraining,
    FlightExamples,
    validate_examples,
)


RANK = 12


class _Session:
    def __init__(self, operator: np.ndarray, adaptation_ops: float) -> None:
        self.operator = operator
        self.adaptation_ops = adaptation_ops

    def predict(self, features: np.ndarray) -> np.ndarray:
        return affine_predict(self.operator, features)


class Candidate:
    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.mean_operator: np.ndarray | None = None
        self.basis = np.empty((0, 0, 0))
        self.fit_ops = 0.0

    def fit(self, training: DynamicsTraining) -> None:
        if not training.flights:
            raise ValueError("at least one anonymous training flight is required")
        operators = []
        example_count = 0
        for flight in training.flights:
            validate_examples(flight)
            if flight.condition is not None:
                raise ValueError("implementable learner forbids condition metadata")
            operators.append(affine_ridge(flight.features, flight.targets))
            example_count += flight.features.shape[0]
        stacked = np.stack(operators)
        self.mean_operator = stacked.mean(axis=0)
        centered = (stacked - self.mean_operator).reshape(len(stacked), -1)
        rank_cap = min(RANK, max(0, len(stacked) - 1))
        if rank_cap:
            _, singular_values, right = np.linalg.svd(centered, full_matrices=False)
            tolerance = np.finfo(float).eps * max(centered.shape) * singular_values[0]
            rank = min(rank_cap, int(np.count_nonzero(singular_values > tolerance)))
            self.basis = right[:rank].reshape(rank, *self.mean_operator.shape)
        else:
            self.basis = np.empty((0, *self.mean_operator.shape))
        width, outputs = self.mean_operator.shape
        ridge_ops = example_count * (2 * width * width + 2 * width * outputs)
        svd_ops = 2 * len(stacked) * len(stacked) * centered.shape[1]
        self.fit_ops = float(ridge_ops + svd_ops)

    def adapt(self, examples: FlightExamples) -> _Session:
        validate_examples(examples)
        if examples.condition is not None:
            raise ValueError("implementable learner forbids condition metadata")
        if self.mean_operator is None:
            raise RuntimeError("fit must precede adapt")
        residual = examples.targets - affine_predict(self.mean_operator, examples.features)
        rank = len(self.basis)
        if rank:
            design = np.stack(
                [affine_predict(direction, examples.features).reshape(-1) for direction in self.basis],
                axis=1,
            )
            coefficients = np.linalg.solve(
                design.T @ design + np.eye(rank) * RIDGE,
                design.T @ residual.reshape(-1),
            )
            operator = self.mean_operator + np.tensordot(coefficients, self.basis, axes=1)
        else:
            operator = self.mean_operator.copy()
        rows, width = examples.features.shape[0], examples.features.shape[1] + 1
        outputs = examples.targets.shape[1]
        ops = 2 * rows * width * outputs * (rank + 1)
        ops += 2 * rows * outputs * rank * rank + rank**3
        return _Session(operator, float(ops))


def semantic_fixture() -> tuple[float, float]:
    rng = np.random.default_rng(1103)
    mean = rng.normal(scale=0.2, size=(9, 6))
    directions = rng.normal(scale=0.1, size=(2, 9, 6))
    features = rng.normal(size=(256, 8))
    coordinates = ((-2.0, 0.0), (-1.0, 1.0), (0.0, -1.0), (1.0, 1.0), (2.0, -1.0))

    def fitted(order: tuple[int, ...]) -> Candidate:
        flights = []
        for slot in order:
            operator = mean + np.tensordot(coordinates[slot], directions, axes=1)
            flights.append(FlightExamples(slot, features, affine_predict(operator, features)))
        learner = Candidate(7)
        learner.fit(DynamicsTraining(tuple(flights), 0, 0))
        return learner

    target = mean + np.tensordot((0.6, -0.8), directions, axes=1)
    heldout = np.random.default_rng(2207)
    adaptation_x, query_x = heldout.normal(size=(32, 8)), heldout.normal(size=(64, 8))
    adaptation = FlightExamples(99, adaptation_x, affine_predict(target, adaptation_x))
    expected = affine_predict(target, query_x)
    first = fitted((0, 1, 2, 3, 4)).adapt(adaptation).predict(query_x)
    permuted = fitted((4, 2, 0, 3, 1)).adapt(adaptation).predict(query_x)
    recovery_error = float(np.max(np.abs(first - expected)))
    permutation_error = float(np.max(np.abs(first - permuted)))
    if recovery_error > 0.003 or permutation_error > 1e-9:
        raise AssertionError((recovery_error, permutation_error))
    return recovery_error, permutation_error
