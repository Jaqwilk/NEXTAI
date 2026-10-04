from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase, CandidateMetadata
from nextai_autoresearch.wt_prequential_contract import WTQuery, WTReveal, WTTraining


RANK = 4
RIDGE = 1e-3
UPDATE_ETA = 0.25
FIT_HORIZON = 32
MAX_HORIZON = 96
CSSR_BINS = 4
CSSR_MAX_SUFFIX = 3
CSSR_TV_THRESHOLD = 0.15


def _array(value: Any) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != 10:
        raise ValueError("WT tensors must have ten anonymous channels")
    return result


def _history_feature(history: Any) -> np.ndarray:
    values = _array(history)
    return np.concatenate(([1.0], values[-1], values.mean(axis=0), values[-1] - values[0]))


def _expand(curve: np.ndarray) -> np.ndarray:
    curve = _array(curve)
    return np.concatenate((curve, np.repeat(curve[-1][None, :], MAX_HORIZON - len(curve), axis=0)))


def _fit_curve(curve: Any) -> np.ndarray:
    values = _array(curve)
    if len(values) >= FIT_HORIZON:
        return values[:FIT_HORIZON]
    return np.concatenate((values, np.repeat(values[-1][None, :], FIT_HORIZON - len(values), axis=0)))


def _levels(values: np.ndarray) -> tuple[float, ...]:
    return tuple(sorted(set(map(float, values))))


def _nearest_level(levels: tuple[float, ...], value: float) -> int:
    return min(range(len(levels)), key=lambda index: (abs(levels[index] - value), index))


class SpectralPSR(CandidateBase):
    metadata = CandidateMetadata("wt_coverage_aware_spectral_psr_v1", "baseline", "Coverage-balanced two-stage spectral predictive state")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.fit_ops = self.meta_fit_ops = self.last_ops = self.update_ops = 0.0
        self.last_bytes_touched = self.last_update_bytes = 0.0
        self.slot_weights: dict[int, np.ndarray] = {}

    @staticmethod
    def coverage_weights(controls: np.ndarray) -> np.ndarray:
        counts = Counter(map(float, controls))
        weights = np.asarray([1.0 / counts[float(value)] for value in controls], dtype=float)
        return weights / weights.sum()

    def fit(self, training: WTTraining, knowledge_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(knowledge_size):
            raise ValueError("spectral PSR requires exactly K train-only WT episodes")
        histories = np.stack([_history_feature(ep.history) for ep in training.episodes])
        controls = np.asarray([ep.control for ep in training.episodes], dtype=float)
        futures = np.stack([
            (_array(ep.target)[:FIT_HORIZON] - _array(ep.history)[-1]).reshape(-1)
            for ep in training.episodes
        ])
        weights = self.coverage_weights(controls)
        self.history_mean = weights @ histories
        self.future_mean = weights @ futures
        centered_h = histories - self.history_mean
        centered_f = futures - self.future_mean
        cross = centered_h.T @ (weights[:, None] * centered_f)
        left, singular, _ = np.linalg.svd(cross, full_matrices=False)
        rank = min(RANK, int(np.sum(singular > 1e-12)))
        self.projection = left[:, :max(1, rank)]
        states = centered_h @ self.projection
        design = np.column_stack((np.ones(len(states)), states, controls, states * controls[:, None]))
        gram = design.T @ (weights[:, None] * design)
        self.readout = np.linalg.solve(gram + RIDGE * np.eye(gram.shape[0]), design.T @ (weights[:, None] * centered_f))
        p, q, r = histories.shape[1], futures.shape[1], self.projection.shape[1]
        self.fit_ops = float(len(histories) * (p * q + p * r + (2 * r + 2) * q) + p * p * q)
        self.meta_fit_ops = self.fit_ops

    def _state_feature(self, history: Any, control: float) -> np.ndarray:
        state = (_history_feature(history) - self.history_mean) @ self.projection
        return np.concatenate(([1.0], state, [float(control)], state * float(control)))

    def query(self, query: WTQuery, steps: int):
        if not isinstance(query, WTQuery) or query.horizon not in (16, 32, 96):
            raise ValueError("invalid anonymous WT query")
        feature = self._state_feature(query.history, query.control)
        weights = self.slot_weights.get(query.slot, self.readout)
        residual = self.future_mean + feature @ weights
        curve = _array(query.history)[-1] + residual.reshape(FIT_HORIZON, 10)
        prediction = _expand(curve)
        self.last_ops = float(len(feature) * residual.size * 2 + self.projection.size)
        self.last_bytes_touched = float((_array(query.history).size + weights.size + prediction.size) * 8)
        return prediction[:query.horizon].tolist()

    def update(self, reveal: WTReveal) -> None:
        if not isinstance(reveal, WTReveal):
            raise ValueError("spectral PSR update requires post-artifact reveal")
        feature = self._state_feature(reveal.history, reveal.control)
        weights = self.slot_weights.setdefault(reveal.slot, self.readout.copy())
        target = (_fit_curve(reveal.target) - _array(reveal.history)[-1]).reshape(-1) - self.future_mean
        error = target - feature @ weights
        weights += (UPDATE_ETA / (1.0 + float(feature @ feature))) * np.outer(feature, error)
        self.update_ops = float(3 * feature.size * target.size)
        self.last_update_bytes = float(weights.nbytes)

    def state_bytes(self) -> int:
        fixed = sum(value.nbytes for value in (self.history_mean, self.future_mean, self.projection, self.readout))
        return int(fixed + sum(value.nbytes for value in self.slot_weights.values()) + 128)


class DiscretizedCSSR(CandidateBase):
    metadata = CandidateMetadata("wt_train_only_discretized_cssr_v1", "baseline", "Train-only finite-sample CSSR")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.fit_ops = self.meta_fit_ops = self.last_ops = self.update_ops = 0.0
        self.last_bytes_touched = self.last_update_bytes = 0.0
        self.local_banks: dict[int, tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], int]]] = {}

    def _symbol(self, row: np.ndarray) -> tuple[int, ...]:
        return tuple(int(np.searchsorted(self.response_thresholds[:, channel], row[channel], side="right"))
                     for channel in range(10))

    def _control(self, value: float) -> int:
        return int(np.searchsorted(self.control_thresholds, value, side="right"))

    @staticmethod
    def _distribution(counter: Counter, vocabulary: tuple[tuple[int, ...], ...]) -> np.ndarray:
        total = sum(counter.values())
        return np.asarray([counter.get(symbol, 0) / total for symbol in vocabulary], dtype=float)

    def _lookup_suffix(self, control: int, suffix: tuple[tuple[int, ...], ...], labels: dict | None = None) -> tuple[int, int]:
        mapping = self.suffix_state if labels is None else labels
        for width in range(min(CSSR_MAX_SUFFIX, len(suffix)), 0, -1):
            key = (control, suffix[-width:])
            if key in mapping:
                return key
        candidates = sorted(key for key in mapping if key[0] == control)
        return candidates[0]

    def fit(self, training: WTTraining, knowledge_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(knowledge_size):
            raise ValueError("CSSR requires exactly K train-only WT episodes")
        histories = [_array(ep.history) for ep in training.episodes]
        pooled = np.concatenate(histories)
        self.response_thresholds = np.quantile(pooled, (0.25, 0.5, 0.75), axis=0)
        controls = np.asarray([ep.control for ep in training.episodes], dtype=float)
        self.control_thresholds = np.quantile(controls, (0.25, 0.5, 0.75))
        sequences = [tuple(self._symbol(row) for row in history) for history in histories]
        vocabulary = tuple(sorted({symbol for sequence in sequences for symbol in sequence}))
        counts: dict[tuple[int, tuple[tuple[int, ...], ...]], Counter] = {}
        for episode, sequence in zip(training.episodes, sequences):
            control = self._control(episode.control)
            for index in range(1, len(sequence)):
                for width in range(1, min(CSSR_MAX_SUFFIX, index) + 1):
                    key = (control, sequence[index - width:index])
                    counts.setdefault(key, Counter())[sequence[index]] += 1
        groups: list[np.ndarray] = []
        labels: dict[tuple[int, tuple[tuple[int, ...], ...]], int] = {}
        for key in sorted(counts):
            distribution = self._distribution(counts[key], vocabulary)
            compatible = [index for index, reference in enumerate(groups)
                          if 0.5 * float(np.abs(distribution - reference).sum()) <= CSSR_TV_THRESHOLD]
            if compatible:
                labels[key] = compatible[0]
            else:
                labels[key] = len(groups)
                groups.append(distribution)
        # CSSR determinization: refine predictive groups until symbol-labelled successors agree.
        for _ in range(len(labels)):
            signatures = {}
            for key in sorted(labels):
                control, suffix = key
                transitions = []
                # Finite-sample CSSR determinizes only empirically supported
                # symbol-labelled transitions; zero-count transitions are undefined.
                for symbol in sorted(counts[key]):
                    next_key = self._lookup_suffix(control, (*suffix, symbol), labels)
                    transitions.append((symbol, labels[next_key]))
                signatures[key] = (labels[key], tuple(transitions))
            unique = {value: index for index, value in enumerate(sorted(set(signatures.values())))}
            refined = {key: unique[signatures[key]] for key in labels}
            if refined == labels:
                break
            labels = refined
        self.suffix_state = labels
        self.vocabulary = vocabulary
        residuals: dict[tuple[int, int], list[np.ndarray]] = {}
        for episode, history, sequence in zip(training.episodes, histories, sequences):
            control = self._control(episode.control)
            key = self._lookup_suffix(control, sequence)
            state = labels[key]
            residuals.setdefault((control, state), []).append(_array(episode.target)[:FIT_HORIZON] - history[-1])
        self.bank = {key: np.mean(values, axis=0) for key, values in residuals.items()}
        self.counts = {key: len(values) for key, values in residuals.items()}
        self.global_residual = np.mean([value for values in residuals.values() for value in values], axis=0)
        supported_edges = sum(len(counts[key]) for key in counts)
        self.fit_ops = float(sum(len(sequence) * CSSR_MAX_SUFFIX for sequence in sequences)
                             + supported_edges * max(1, len(set(labels.values()))))
        self.meta_fit_ops = self.fit_ops

    def state_for_history(self, history: Any, control: float) -> tuple[int, int]:
        sequence = tuple(self._symbol(row) for row in _array(history))
        key = self._lookup_suffix(self._control(control), sequence)
        return key[0], self.suffix_state[key]

    def query(self, query: WTQuery, steps: int):
        if not isinstance(query, WTQuery) or query.horizon not in (16, 32, 96):
            raise ValueError("invalid anonymous WT query")
        key = self.state_for_history(query.history, query.control)
        local = self.local_banks.get(query.slot)
        bank = local[0] if local else self.bank
        residual = bank.get(key, self.global_residual)
        prediction = _expand(_array(query.history)[-1] + residual)
        self.last_ops = float(32 * 10 * CSSR_MAX_SUFFIX + len(self.suffix_state))
        self.last_bytes_touched = float((_array(query.history).size + residual.size + len(self.suffix_state) * 16) * 8)
        return prediction[:query.horizon].tolist()

    def update(self, reveal: WTReveal) -> None:
        if not isinstance(reveal, WTReveal):
            raise ValueError("CSSR update requires post-artifact reveal")
        key = self.state_for_history(reveal.history, reveal.control)
        if reveal.slot not in self.local_banks:
            self.local_banks[reveal.slot] = ({name: value.copy() for name, value in self.bank.items()}, dict(self.counts))
        bank, counts = self.local_banks[reveal.slot]
        residual = _fit_curve(reveal.target) - _array(reveal.history)[-1]
        count = counts.get(key, 0) + 1
        old = bank.get(key, self.global_residual.copy())
        bank[key] = old + (residual - old) / count
        counts[key] = count
        self.update_ops = float(2 * residual.size)
        self.last_update_bytes = float(residual.nbytes)

    def state_bytes(self) -> int:
        fixed = self.response_thresholds.nbytes + self.control_thresholds.nbytes + self.global_residual.nbytes
        fixed += sum(value.nbytes + 24 for value in self.bank.values()) + len(self.suffix_state) * 96
        local = sum(sum(value.nbytes + 24 for value in bank.values()) for bank, _ in self.local_banks.values())
        return int(fixed + local + 128)


class Candidate(SpectralPSR):
    """Auditable default entry for the shared control implementation."""
