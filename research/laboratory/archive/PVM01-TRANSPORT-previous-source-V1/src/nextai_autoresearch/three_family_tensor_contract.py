from __future__ import annotations

from dataclasses import dataclass

import numpy as np


ROWS = {"support": 108, "history": 32, "future": 50}
WIDTH = 32


@dataclass(frozen=True)
class Tensor:
    values: np.ndarray
    mask: np.ndarray


@dataclass(frozen=True)
class World:
    slot: int
    support_input: Tensor
    support_target: Tensor
    history: Tensor
    future_public: Tensor
    output: Tensor | None = None


@dataclass(frozen=True)
class Training:
    worlds: tuple[World, ...]


def pad(values: np.ndarray, rows: int) -> Tensor:
    source = np.asarray(values, dtype=np.float32)
    if source.ndim != 2 or source.shape[0] != rows or source.shape[1] > WIDTH:
        raise ValueError(f"native tensor must have shape ({rows}, <= {WIDTH})")
    if not np.isfinite(source).all():
        raise ValueError("native tensor must be finite")
    output = np.zeros((rows, WIDTH), dtype=np.float32)
    mask = np.zeros((rows, WIDTH), dtype=np.bool_)
    output[:, : source.shape[1]] = source
    mask[:, : source.shape[1]] = True
    return Tensor(output, mask)


@dataclass(frozen=True)
class Normalizer:
    means: tuple[np.ndarray, ...]
    scales: tuple[np.ndarray, ...]

    def apply(self, world: World) -> World:
        names = ("support_input", "support_target", "history", "future_public", "output")
        tensors = []
        for index, name in enumerate(names):
            tensor = getattr(world, name)
            if tensor is None:
                tensors.append(None)
                continue
            values = np.where(
                tensor.mask,
                (tensor.values - self.means[index]) / self.scales[index],
                0.0,
            ).astype(np.float32)
            tensors.append(Tensor(values, tensor.mask.copy()))
        return World(world.slot, *tensors)


def fit_normalizer(worlds: tuple[World, ...]) -> Normalizer:
    if not worlds:
        zeros = tuple(np.zeros(WIDTH, dtype=np.float32) for _ in range(5))
        ones = tuple(np.ones(WIDTH, dtype=np.float32) for _ in range(5))
        return Normalizer(zeros, ones)
    names = ("support_input", "support_target", "history", "future_public", "output")
    means, scales = [], []
    for name in names:
        columns = []
        for world in worlds:
            tensor = getattr(world, name)
            if tensor is not None:
                columns.append((tensor.values, tensor.mask))
        mean = np.zeros(WIDTH, dtype=np.float64)
        scale = np.ones(WIDTH, dtype=np.float64)
        if columns:
            for column in range(WIDTH):
                values = np.concatenate([
                    array[:, column][mask[:, column]]
                    for array, mask in columns if mask[:, column].any()
                ]) if any(mask[:, column].any() for _, mask in columns) else np.empty(0)
                if values.size:
                    mean[column] = float(values.mean())
                    deviation = float(values.std())
                    scale[column] = deviation if deviation >= 1e-9 else 1.0
        means.append(mean.astype(np.float32))
        scales.append(scale.astype(np.float32))
    return Normalizer(tuple(means), tuple(scales))


def masked_mse(prediction: np.ndarray, target: Tensor) -> float:
    predicted = np.asarray(prediction, dtype=np.float64)
    if predicted.shape != target.values.shape or not np.isfinite(predicted).all():
        raise ValueError("prediction must be a finite output-shaped matrix")
    error = np.square(predicted[target.mask] - target.values[target.mask])
    if not error.size:
        raise ValueError("output mask is empty")
    return float(error.mean())
