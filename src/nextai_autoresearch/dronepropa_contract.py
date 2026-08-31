from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class FlightExamples:
    slot: int
    features: np.ndarray
    targets: np.ndarray
    condition: int | None = None


@dataclass(frozen=True)
class DynamicsTraining:
    flights: tuple[FlightExamples, ...]
    acquisition_bytes: int
    preprocessing_ops: int


@dataclass(frozen=True)
class DynamicsPrediction:
    mean: np.ndarray
    variance: np.ndarray


class DynamicsSession(Protocol):
    def predict(self, features: np.ndarray) -> DynamicsPrediction | np.ndarray: ...


class DynamicsLearner(Protocol):
    def fit(self, training: DynamicsTraining) -> None: ...

    def adapt(self, examples: FlightExamples) -> DynamicsSession: ...


def validate_examples(examples: FlightExamples) -> None:
    if examples.features.ndim != 2 or examples.targets.ndim != 2:
        raise ValueError("features and targets must be matrices")
    if examples.features.shape[0] != examples.targets.shape[0] or examples.targets.shape[1] != 6:
        raise ValueError("examples must align and have six state targets")
    if not np.isfinite(examples.features).all() or not np.isfinite(examples.targets).all():
        raise ValueError("examples must be finite")
