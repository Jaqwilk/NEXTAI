from __future__ import annotations

import numpy as np

from ..three_family_tensor_contract import Tensor, Training


BUCKET_COUNT = 32
BUCKET_CAP = 8
CODE_BITS = 5
RIDGE = 1e-3


def _canonical(values: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Permutation-invariant numeric key; no channel names or roles are used."""
    return np.sort(np.where(mask, values, np.inf), axis=-1)


def _order(x: np.ndarray, xm: np.ndarray, y: np.ndarray, ym: np.ndarray) -> np.ndarray:
    keys = np.column_stack((_canonical(x, xm), _canonical(y, ym)))
    return np.lexsort(tuple(keys[:, index] for index in range(keys.shape[1] - 1, -1, -1)))


def _operator(x: np.ndarray, y: np.ndarray, xm: np.ndarray, ym: np.ndarray) -> np.ndarray:
    weights = np.zeros((33, 32), dtype=np.float64)
    if not len(x):
        return weights
    design = np.column_stack((np.ones(len(x)), np.where(xm, x, 0.0)))
    for target in range(32):
        visible = ym[:, target]
        if not visible.any():
            continue
        local = design[visible]
        gram = local.T @ local + RIDGE * np.eye(33)
        weights[:, target] = np.linalg.solve(gram, local.T @ y[visible, target])
    return weights


class IndexedLocalOperator:
    """Fixed-cap exact raw index or matched random-projection hash control."""

    def __init__(self, seed: int, variant: str) -> None:
        if variant not in {"raw", "random"}:
            raise ValueError("unknown index control")
        self.seed, self.variant = seed, variant
        self.fit_ops = self.adaptation_ops = self.last_ops = 0.0
        self.last_bytes_touched = 0.0
        self.last_stable = True
        self._model: dict[str, object] = {}

    @staticmethod
    def _rows(pairs: list[tuple[Tensor, Tensor]]) -> tuple[np.ndarray, ...]:
        if not pairs:
            empty = np.empty((0, 32), dtype=np.float64)
            return empty, empty, empty.astype(bool), empty.astype(bool)
        return (
            np.concatenate([x.values for x, _ in pairs]).astype(np.float64),
            np.concatenate([y.values for _, y in pairs]).astype(np.float64),
            np.concatenate([x.mask for x, _ in pairs]),
            np.concatenate([y.mask for _, y in pairs]),
        )

    def _bucket(self, row: np.ndarray, mask: np.ndarray, model: dict[str, object]) -> int:
        if self.variant == "raw":
            prototypes = np.asarray(model["prototypes"])
            prototype_masks = np.asarray(model["prototype_masks"])
            if not len(prototypes):
                return 0
            overlap = prototype_masks & mask
            distance = np.square(np.where(overlap, prototypes - row, 0.0)).sum(axis=1)
            distance += 1e6 * np.logical_xor(prototype_masks, mask).sum(axis=1)
            return int(np.argmin(distance))
        key = np.where(np.isfinite(_canonical(row, mask)), _canonical(row, mask), 0.0)
        bits = np.asarray(model["projection"]) @ key >= 0.0
        return int(sum((1 << index) for index, value in enumerate(bits) if value))

    def _build(self, x: np.ndarray, y: np.ndarray, xm: np.ndarray, ym: np.ndarray) -> dict[str, object]:
        order = _order(x, xm, y, ym) if len(x) else np.empty(0, dtype=int)
        if self.variant == "raw" and len(x):
            selected = order[np.linspace(0, len(order) - 1, min(BUCKET_COUNT, len(order)), dtype=int)]
            prototypes, prototype_masks = x[selected].copy(), xm[selected].copy()
        else:
            prototypes = np.empty((0, 32), dtype=np.float64)
            prototype_masks = np.empty((0, 32), dtype=bool)
        rng = np.random.default_rng(self.seed)
        projection = rng.choice((-1.0, 1.0), size=(CODE_BITS, 32))
        model: dict[str, object] = {
            "prototypes": prototypes,
            "prototype_masks": prototype_masks,
            "projection": projection,
            "buckets": [],
        }
        assignments = np.array([self._bucket(x[index], xm[index], model) for index in order], dtype=int)
        buckets = []
        for bucket in range(BUCKET_COUNT):
            chosen = order[assignments == bucket][:BUCKET_CAP]
            bx, by, bxm, bym = x[chosen], y[chosen], xm[chosen], ym[chosen]
            buckets.append({"x": bx, "y": by, "xm": bxm, "ym": bym,
                            "weights": _operator(bx, by, bxm, bym)})
            self.fit_ops += float(len(chosen) * 33 * 32 * 2)
        model["buckets"] = buckets
        return model

    def fit(self, training: Training) -> None:
        pairs = [(world.support_input, world.support_target) for world in training.worlds]
        x, y, xm, ym = self._rows(pairs)
        self.fit_ops = float(len(x) * 64)
        self._model = self._build(x, y, xm, ym)

    def adapt(self, support_input: Tensor, support_target: Tensor) -> dict[str, object]:
        x, y, xm, ym = self._rows([(support_input, support_target)])
        model = {
            "prototypes": np.asarray(self._model["prototypes"]).copy(),
            "prototype_masks": np.asarray(self._model["prototype_masks"]).copy(),
            "projection": np.asarray(self._model["projection"]).copy(),
            "buckets": [{key: np.asarray(value).copy() for key, value in bucket.items()}
                        for bucket in self._model["buckets"]],
        }
        if self.variant == "raw" and not len(np.asarray(model["prototypes"])):
            support_order = _order(x, xm, y, ym)
            selected = support_order[np.linspace(0, len(support_order) - 1,
                                                 min(BUCKET_COUNT, len(support_order)), dtype=int)]
            model["prototypes"], model["prototype_masks"] = x[selected], xm[selected]
        assignments = np.array([self._bucket(row, mask, model) for row, mask in zip(x, xm)])
        touched = 0
        for bucket_id in np.unique(assignments):
            bucket = model["buckets"][int(bucket_id)]
            selected = np.flatnonzero(assignments == bucket_id)
            support_order = _order(x[selected], xm[selected], y[selected], ym[selected])
            selected = selected[support_order[:BUCKET_CAP]]
            remaining = BUCKET_CAP - len(selected)
            bx = np.concatenate((x[selected], bucket["x"][:remaining]))
            by = np.concatenate((y[selected], bucket["y"][:remaining]))
            bxm = np.concatenate((xm[selected], bucket["xm"][:remaining]))
            bym = np.concatenate((ym[selected], bucket["ym"][:remaining]))
            bucket.update(x=bx, y=by, xm=bxm, ym=bym,
                          weights=_operator(bx, by, bxm, bym))
            touched += len(bx)
        self.adaptation_ops = float(len(x) * 64 + touched * 33 * 32 * 2)
        model["input_mask"] = support_input.mask.any(axis=0)
        model["output_mask"] = support_target.mask.any(axis=0)
        return model

    def predict(self, session: dict[str, object], history: Tensor,
                future_public: Tensor) -> np.ndarray:
        self.last_stable = True
        input_mask = np.asarray(session["input_mask"])
        output_mask = np.asarray(session["output_mask"])
        output_width = int(output_mask.sum())
        controls = int(future_public.mask.any(axis=0).sum())
        current = history.values[-1].astype(np.float64).copy()
        output = np.zeros((50, 32), dtype=np.float64)
        touched = ops = 0.0
        for step in range(50):
            bucket_id = self._bucket(current, input_mask, session)
            bucket = session["buckets"][bucket_id]
            weights = np.asarray(bucket["weights"])
            if len(np.asarray(bucket["x"])):
                prediction = np.r_[1.0, current] @ weights[:, :output_width]
            else:
                prediction = current[controls:controls + output_width]
            stable = bool(np.isfinite(prediction).all() and np.max(np.abs(prediction), initial=0.0) <= 1e6)
            self.last_stable = self.last_stable and stable
            prediction = np.clip(np.nan_to_num(prediction, nan=0.0, posinf=1e6, neginf=-1e6), -1e6, 1e6)
            output[step, :output_width] = prediction
            current[:] = 0.0
            current[:controls] = future_public.values[step, :controls]
            room = min(output_width, max(0, 32 - controls))
            current[controls:controls + room] = prediction[:room]
            index_ops = (len(np.asarray(session["prototypes"])) * 96
                         if self.variant == "raw" else CODE_BITS * 64)
            ops += index_ops + 33 * max(1, output_width)
            touched += weights.nbytes + (np.asarray(session["prototypes"]).nbytes
                                          if self.variant == "raw"
                                          else np.asarray(session["projection"]).nbytes)
        self.last_ops, self.last_bytes_touched = float(ops), float(touched)
        return output.astype(np.float32)

    def state_bytes(self) -> int:
        def size(value: object) -> int:
            if isinstance(value, np.ndarray):
                return value.nbytes
            if isinstance(value, list):
                return sum(size(item) for item in value)
            if isinstance(value, dict):
                return sum(size(item) for item in value.values())
            return 0
        return size(self._model)


class Candidate(IndexedLocalOperator):
    def __init__(self, seed: int) -> None:
        super().__init__(seed, "raw")
