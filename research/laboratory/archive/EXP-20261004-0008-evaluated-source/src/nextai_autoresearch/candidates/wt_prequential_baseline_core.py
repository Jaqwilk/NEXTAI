from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase
from nextai_autoresearch.wt_prequential_contract import WTQuery, WTReveal, WTTraining


MAX_HORIZON = 96
FIT_HORIZON = 32
RIDGE = 1e-3
REPLAY_CAP = 16


def _array(value) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != 10:
        raise ValueError("WT tensors must have ten anonymous channels")
    return result


def _feature(history, control: float) -> np.ndarray:
    x = _array(history)
    return np.concatenate(([1.0], x[-1], x.mean(axis=0), x[-1] - x[0], [float(control)]))


def _level(value: float) -> str:
    return f"{float(value):.6f}"


def _expand(curve: np.ndarray) -> np.ndarray:
    curve = _array(curve)
    if len(curve) >= MAX_HORIZON:
        return curve[:MAX_HORIZON]
    return np.concatenate((curve, np.repeat(curve[-1][None, :], MAX_HORIZON - len(curve), axis=0)))


class Baseline(CandidateBase):
    mode = "persistence"

    def __init__(self, seed: int = 0):
        super().__init__(seed=int(seed))
        self.fit_ops = self.meta_fit_ops = self.last_ops = self.update_ops = 0.0
        self.last_bytes_touched = self.last_update_bytes = 0.0
        self._state: dict[int, object] = {}

    def fit(self, training: WTTraining, knowledge_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(knowledge_size):
            raise ValueError("WT fit must receive exactly K frozen episodes")
        episodes = list(training.episodes)
        self._episodes = [(_feature(ep.history, ep.control), _array(ep.target),
                           _array(ep.history), float(ep.control)) for ep in episodes]
        self._precision = self._weights = self._mean = None
        self._level_bank, self._prototypes, self._transition, self._transition_count, self._replay = {}, {}, {}, {}, []
        q = FIT_HORIZON * 10
        self.fit_ops = 0.0
        if self.mode == "pooled_mean":
            self._mean = np.mean([item[1] for item in self._episodes], axis=0)
            self.fit_ops = float(len(episodes) * q)
        if self.mode in {"control_level", "transition_bank"}:
            for level in sorted({_level(item[3]) for item in self._episodes}):
                selected = [item for item in self._episodes if _level(item[3]) == level]
                self._level_bank[level] = np.mean(
                    [target - history[-1] for _, target, history, _ in selected], axis=0
                )
            self.fit_ops = float(len(episodes) * q)
        if self.mode in {"ridge_fir", "lms", "rls"}:
            x = np.stack([item[0] for item in self._episodes])
            y = np.stack([item[1].reshape(-1) for item in self._episodes])
            p = x.shape[1]
            self._precision = np.linalg.inv(x.T @ x + RIDGE * np.eye(p))
            self._weights = self._precision @ x.T @ y
            self.fit_ops = float(len(episodes) * (p * p + p * q))
        if self.mode == "transition_bank":
            self._prototypes = {
                level: np.mean([target[-16:].mean(axis=0) for _, target, _, control in self._episodes
                                if _level(control) == level], axis=0)
                for level in self._level_bank
            }
            transition: dict[tuple[str, str], list[np.ndarray]] = {}
            for _, target, history, control in self._episodes:
                prior = min(self._prototypes, key=lambda key: float(
                    np.square(history.mean(axis=0) - self._prototypes[key]).sum()
                ))
                transition.setdefault((prior, _level(control)), []).append(target - history[-1])
            self._transition = {key: np.mean(values, axis=0) for key, values in transition.items()}
            self._transition_count = {key: len(values) for key, values in transition.items()}
            self.fit_ops += float(len(episodes) * (len(self._prototypes) * 10 + q))
        if self.mode == "bounded_replay":
            self._replay = self._episodes[-REPLAY_CAP:]
            self.fit_ops = float(len(self._replay) * (32 * 10 + q))
        self.meta_fit_ops = self.fit_ops

    def _slot_linear(self, slot: int):
        if slot not in self._state:
            precision = None if self.mode == "lms" else self._precision.copy()
            self._state[slot] = (precision, self._weights.copy())
        return self._state[slot]

    def query(self, query: WTQuery, steps: int):
        if not isinstance(query, WTQuery) or query.horizon not in (16, 32, 96):
            raise ValueError("invalid anonymous WT query")
        history, horizon = _array(query.history), int(query.horizon)
        feature = _feature(history, query.control)
        q = MAX_HORIZON * 10
        if self.mode == "persistence":
            prediction = np.repeat(history[-1][None, :], MAX_HORIZON, axis=0)
            ops = q
        elif self.mode == "pooled_mean":
            prediction, ops = _expand(self._mean), q
        elif self.mode == "control_level":
            prediction = _expand(history[-1] + self._level_bank[_level(query.control)])
            ops = 2 * q
        elif self.mode in {"ridge_fir", "lms", "rls"}:
            weights = self._slot_linear(query.slot)[1] if self.mode in {"lms", "rls"} else self._weights
            prediction, ops = _expand((feature @ weights).reshape(FIT_HORIZON, 10)), 2 * len(feature) * q
        elif self.mode == "transition_bank":
            prior = min(self._prototypes, key=lambda key: float(
                np.square(history.mean(axis=0) - self._prototypes[key]).sum()
            ))
            local = self._state.get(query.slot)
            bank = local["bank"] if isinstance(local, dict) else self._transition
            residual = bank.get((prior, _level(query.control)), self._level_bank[_level(query.control)])
            prediction, ops = _expand(history[-1] + residual), len(self._prototypes) * 30 + 2 * q
        elif self.mode == "bounded_replay":
            replay = self._state.get(query.slot, self._replay)
            _, target, stored_history, _ = min(
                replay, key=lambda item: float(np.square(item[2] - history).sum())
                + 32 * float(item[3] - query.control) ** 2
            )
            prediction, ops = _expand(history[-1] + target - stored_history[-1]), len(replay) * 322 + 2 * q
        else:
            raise ValueError(f"unknown WT baseline mode {self.mode}")
        if not np.isfinite(prediction).all():
            raise ValueError("WT baseline produced non-finite prediction")
        self.last_ops = float(ops)
        self.last_bytes_touched = float((history.size + prediction.size) * 8)
        return prediction[:horizon].tolist()

    def update(self, reveal: WTReveal) -> None:
        if not isinstance(reveal, WTReveal):
            raise ValueError("WT update requires a post-prediction reveal")
        feature = _feature(reveal.history, reveal.control)
        target_matrix = _array(reveal.target)[:FIT_HORIZON]
        target = target_matrix.reshape(-1)
        p, q = len(feature), len(target)
        self.update_ops = self.last_update_bytes = 0.0
        if self.mode == "lms":
            precision, weights = self._slot_linear(reveal.slot)
            residual = target - feature @ weights[:, :q]
            weights[:, :q] += (0.5 / (1.0 + float(feature @ feature))) * feature[:, None] * residual
            self.update_ops, self.last_update_bytes = float(2 * p * q), float(weights.nbytes)
        elif self.mode == "rls":
            precision, weights = self._slot_linear(reveal.slot)
            gain = precision @ feature / (1.0 + feature @ precision @ feature)
            weights[:, :q] += gain[:, None] * (target - feature @ weights[:, :q])
            precision -= np.outer(gain, feature @ precision)
            self.update_ops = float(2 * p * q + 4 * p * p)
            self.last_update_bytes = float(weights.nbytes + precision.nbytes)
        elif self.mode == "bounded_replay":
            replay = list(self._state.get(reveal.slot, self._replay))
            replay.append((feature, _array(reveal.target), _array(reveal.history), float(reveal.control)))
            self._state[reveal.slot] = replay[-REPLAY_CAP:]
            self.update_ops = float(_array(reveal.target).size)
            self.last_update_bytes = float((_array(reveal.target).size + _array(reveal.history).size) * 8)
        elif self.mode == "transition_bank":
            local = self._state.get(reveal.slot)
            if not isinstance(local, dict):
                local = {"bank": {key: value.copy() for key, value in self._transition.items()},
                         "count": dict(self._transition_count)}
                self._state[reveal.slot] = local
            history = _array(reveal.history)
            prior = min(self._prototypes, key=lambda key: float(
                np.square(history.mean(axis=0) - self._prototypes[key]).sum()
            ))
            key = (prior, _level(reveal.control))
            residual = target_matrix - history[-1]
            count = int(local["count"].get(key, 0)) + 1
            old = local["bank"].get(key, np.zeros_like(residual))
            updated = old.copy()
            updated[:len(residual)] += (residual - old[:len(residual)]) / count
            local["bank"][key] = updated
            local["count"][key] = count
            self.update_ops = float(2 * residual.size)
            self.last_update_bytes = float(residual.nbytes)

    def state_bytes(self) -> int:
        total = sum(array.nbytes for array in (self._precision, self._weights, self._mean)
                    if array is not None)
        total += sum(value.nbytes for value in self._level_bank.values())
        total += sum(value.nbytes for value in self._transition.values())
        for value in self._state.values():
            if isinstance(value, tuple):
                total += sum(item.nbytes for item in value if item is not None)
            elif isinstance(value, list):
                total += sum(item[0].nbytes + item[1].nbytes + item[2].nbytes + 8 for item in value)
            elif isinstance(value, dict):
                total += sum(item.nbytes + 8 for item in value["bank"].values())
        return int(total)


class Candidate(Baseline):
    """Auditable standalone persistence entry for the shared baseline core."""
