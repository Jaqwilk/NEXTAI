from __future__ import annotations

import numpy as np

from ..three_family_tensor_contract import Tensor, Training


def _rls_weights(design: np.ndarray, values: np.ndarray, visible: np.ndarray) -> np.ndarray:
    """Run one exact covariance trajectory per identical target-visibility mask."""
    weights = np.zeros((design.shape[1], values.shape[1]))
    groups: dict[bytes, list[int]] = {}
    for target in range(values.shape[1]):
        groups.setdefault(visible[:, target].tobytes(), []).append(target)
    for targets in groups.values():
        rows = visible[:, targets[0]]
        precision = np.eye(design.shape[1]) * 1000.0
        local = np.zeros((design.shape[1], len(targets)))
        for row, target_values in zip(design[rows], values[rows][:, targets]):
            projected = precision @ row
            gain = projected / (1.0 + row @ precision @ row)
            for index, target_value in enumerate(target_values):
                local[:, index] += gain * (target_value - row @ local[:, index])
            precision -= np.outer(gain, row @ precision)
        weights[:, targets] = local
    return weights


class TensorBaseline:
    def __init__(self, seed: int, variant: str) -> None:
        self.seed, self.variant = seed, variant
        self.fit_ops = self.adaptation_ops = self.last_ops = 0.0
        self.last_bytes_touched = 0.0
        self.last_stable = True
        self._training: list[tuple[Tensor, Tensor]] = []

    def fit(self, training: Training) -> None:
        self._training = [(world.support_input, world.support_target) for world in training.worlds]
        self.fit_ops = float(sum(x.values.size + y.values.size for x, y in self._training))

    @staticmethod
    def _pairs(pairs: list[tuple[Tensor, Tensor]]) -> tuple[np.ndarray, ...]:
        if not pairs:
            empty = np.empty((0, 32))
            return empty, empty, empty.astype(bool), empty.astype(bool)
        x = np.concatenate([item[0].values for item in pairs]).astype(np.float64)
        y = np.concatenate([item[1].values for item in pairs]).astype(np.float64)
        xm = np.concatenate([item[0].mask for item in pairs])
        ym = np.concatenate([item[1].mask for item in pairs])
        return x, y, xm, ym

    def adapt(self, support_input: Tensor, support_target: Tensor) -> dict[str, np.ndarray]:
        x, y, xm, ym = self._pairs([*self._training, (support_input, support_target)])
        self.adaptation_ops = float(support_input.values.size + support_target.values.size)
        return self._fit(x, y, xm, ym, support_input.mask, support_target.mask)

    def _fit(self, x: np.ndarray, y: np.ndarray, xm: np.ndarray, ym: np.ndarray,
             support_x_mask: np.ndarray, support_y_mask: np.ndarray) -> dict[str, np.ndarray]:
        input_width = int(support_x_mask.any(axis=0).sum())
        output_width = int(support_y_mask.any(axis=0).sum())
        if self.variant == "persistence" or not len(x):
            return {"input_width": np.array(input_width), "output_width": np.array(output_width)}
        active_x, active_y = x[:, :input_width], y[:, :output_width]
        active_x = np.where(xm[:, :input_width], active_x, 0.0)
        design = np.column_stack((np.ones(len(active_x)), active_x))
        if self.variant in {"empirical_joint", "contextual_chow_liu"}:
            complete = ym[:, :output_width].all(axis=1)
            design, active_x, active_y = design[complete], active_x[complete], active_y[complete]
            if not len(design):
                return {"input_width": np.array(input_width), "output_width": np.array(output_width)}
            joined = np.column_stack((active_x, active_y))
            mean = joined.mean(axis=0)
            scale = joined.std(axis=0)
            scale[scale < 1e-9] = 1.0
            standardized = (joined - mean) / scale
            covariance = np.cov(standardized, rowvar=False) + 1e-6 * np.eye(joined.shape[1])
            if self.variant == "contextual_chow_liu":
                correlation = np.clip(covariance, -0.999999, 0.999999)
                parent = [-1] * joined.shape[1]
                remaining = set(range(1, joined.shape[1]))
                while remaining:
                    child, source = max(
                        ((child, source) for child in remaining for source in range(joined.shape[1])
                         if source not in remaining),
                        key=lambda pair: abs(correlation[pair[0], pair[1]]),
                    )
                    parent[child] = source
                    remaining.remove(child)
                adjacency = [[] for _ in range(joined.shape[1])]
                for child, source in enumerate(parent[1:], 1):
                    edge = float(correlation[child, source])
                    adjacency[child].append((source, edge))
                    adjacency[source].append((child, edge))
                covariance = np.eye(joined.shape[1])
                for source in range(joined.shape[1]):
                    stack = [(source, -1, 1.0)]
                    while stack:
                        node, previous, product = stack.pop()
                        covariance[source, node] = product
                        stack.extend((child, node, product * edge)
                                     for child, edge in adjacency[node] if child != previous)
            xx = covariance[:input_width, :input_width]
            yx = covariance[input_width:, :input_width]
            coefficient = (scale[input_width:, None] * yx) @ np.linalg.inv(xx) / scale[:input_width]
            intercept = mean[input_width:] - coefficient @ mean[:input_width]
            weights = np.vstack((intercept, coefficient.T))
        elif self.variant == "rls":
            weights = _rls_weights(design, active_y, ym[:, :output_width])
        else:
            ridge = 1e-3
            weights = np.zeros((design.shape[1], output_width))
            for target in range(output_width):
                local = design[ym[:, target]]
                values = active_y[ym[:, target], target]
                gram = local.T @ local + ridge * np.eye(local.shape[1])
                weights[:, target] = np.linalg.solve(gram, local.T @ values)
        self.fit_ops += float(design.size * output_width)
        return {"weights": weights, "input_width": np.array(input_width),
                "output_width": np.array(output_width)}

    def predict(self, session: dict[str, np.ndarray], history: Tensor,
                future_public: Tensor) -> np.ndarray:
        self.last_stable = True
        input_width = int(session["input_width"])
        output_width = int(session["output_width"])
        controls = int(future_public.mask.any(axis=0).sum())
        current = history.values[-1, :input_width].astype(np.float64).copy()
        output = np.zeros((50, 32), dtype=np.float64)
        for step in range(50):
            if self.variant == "persistence" or "weights" not in session:
                prediction = current[controls:controls + output_width]
                if len(prediction) < output_width:
                    prediction = np.pad(prediction, (0, output_width - len(prediction)))
            else:
                prediction = np.r_[1.0, current] @ session["weights"]
            stable = bool(np.isfinite(prediction).all() and np.max(np.abs(prediction)) <= 1e6)
            self.last_stable = self.last_stable and stable
            prediction = np.nan_to_num(prediction, nan=0.0, posinf=1e6, neginf=-1e6)
            prediction = np.clip(prediction, -1e6, 1e6)
            output[step, :output_width] = prediction
            current[:] = 0.0
            current[:controls] = future_public.values[step, :controls]
            room = max(0, min(output_width, input_width - controls))
            current[controls:controls + room] = prediction[:room]
        self.last_ops = float(50 * (input_width + 1) * max(1, output_width))
        self.last_bytes_touched = float(history.values.nbytes + future_public.values.nbytes + output.nbytes)
        return output.astype(np.float32)

    def state_bytes(self) -> int:
        return int(sum(x.values.nbytes + y.values.nbytes for x, y in self._training))


class Candidate(TensorBaseline):
    """Auditable default entry; scored controls use the explicit thin modules."""

    def __init__(self, seed: int) -> None:
        super().__init__(seed, "ridge")
