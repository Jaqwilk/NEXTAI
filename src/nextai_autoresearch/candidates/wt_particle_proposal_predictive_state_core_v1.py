from __future__ import annotations

import numpy as np

from nextai_autoresearch.candidates.base import CandidateBase
from nextai_autoresearch.wt_prequential_contract import WTQuery, WTReveal, WTTraining


WINDOW = 32
WIDTH = 10
PARTICLES = 8
FEATURES = 1 + 3 * WIDTH
FEATURE_CLIP = 4.0
OUTPUT_CLIP = 8.0
EVIDENCE_DECAY = 0.5
TEMPERATURE_DENOMINATOR = 2.0 * FEATURES


def _matrix(value, *, length: int | None = None) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != WIDTH or not np.isfinite(result).all():
        raise ValueError("particle-state tensors must be finite ten-channel matrices")
    if length is not None and len(result) != length:
        raise ValueError(f"particle-state tensor must have length {length}")
    return result


def _feature(history, control: float) -> np.ndarray:
    past = _matrix(history, length=WINDOW)
    feature = np.concatenate((
        np.asarray([float(control)]), past[-1], past.mean(axis=0), past[-1] - past[0],
    ))
    if not np.isfinite(feature).all():
        raise ValueError("particle-state feature must be finite")
    return np.clip(feature, -FEATURE_CLIP, FEATURE_CLIP)


def _extend(particles: np.ndarray, horizon: int) -> np.ndarray:
    if horizon <= WINDOW:
        return particles[:, :horizon]
    tail = np.repeat(particles[:, -1:], horizon - WINDOW, axis=1)
    return np.concatenate((particles, tail), axis=1)


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    flat = values.reshape(PARTICLES, -1)
    order = np.argsort(flat, axis=0, kind="stable")
    ordered_values = np.take_along_axis(flat, order, axis=0)
    ordered_weights = np.take_along_axis(
        np.broadcast_to(weights[:, None], flat.shape), order, axis=0,
    )
    positions = np.argmax(np.cumsum(ordered_weights, axis=0) >= 0.5, axis=0)
    return ordered_values[positions, np.arange(flat.shape[1])].reshape(values.shape[1:])


class ParticleProposalPredictiveState(CandidateBase):
    mode = "learned_proposal"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.meta_fit_ops = 0.0
        self.last_bytes_touched = self.last_update_bytes = 0.0
        self._slot_evidence: dict[int, np.ndarray] = {}

    def fit(self, training: WTTraining, knowledge_size: int, max_depth: int) -> None:
        if not isinstance(training, WTTraining) or len(training.episodes) != int(knowledge_size):
            raise ValueError("particle state requires exactly K train-only WT episodes")
        if knowledge_size < PARTICLES:
            raise ValueError("particle state requires at least eight episodes")
        features = np.stack([_feature(ep.history, ep.control) for ep in training.episodes])
        residuals = np.stack([
            _matrix(ep.target)[:WINDOW] - _matrix(ep.history, length=WINDOW)[-1]
            for ep in training.episodes
        ])
        if residuals.shape[1:] != (WINDOW, WIDTH):
            raise ValueError("training targets must contain at least 32 rows")

        flat = residuals.reshape(knowledge_size, -1)
        selected = [0]
        minimum = np.sum((flat - flat[0]) ** 2, axis=1)
        for _ in range(1, PARTICLES):
            eligible = minimum.copy()
            eligible[selected] = -np.inf
            chosen = int(np.argmax(eligible))
            selected.append(chosen)
            minimum = np.minimum(minimum, np.sum((flat - flat[chosen]) ** 2, axis=1))
        seeds = flat[selected]
        distances = np.sum((flat[:, None] - seeds[None, :]) ** 2, axis=2)
        assignment = np.argmin(distances, axis=1)
        assignment[np.asarray(selected)] = np.arange(PARTICLES)

        self.particles = np.empty((PARTICLES, WINDOW, WIDTH), dtype=np.float64)
        self.centroids = np.empty((PARTICLES, FEATURES), dtype=np.float64)
        self.counts = np.empty(PARTICLES, dtype=np.float64)
        for particle in range(PARTICLES):
            members = assignment == particle
            self.particles[particle] = residuals[members].mean(axis=0)
            self.centroids[particle] = features[members].mean(axis=0)
            self.counts[particle] = float(np.sum(members))
        self._slot_evidence.clear()
        k = float(knowledge_size)
        residual_width = WINDOW * WIDTH
        self.fit_ops = self.meta_fit_ops = float(
            k * (4 * WINDOW * WIDTH + FEATURES)
            + 3 * k * PARTICLES * residual_width
            + 2 * k * (residual_width + FEATURES)
        )

    def _weights(self, feature: np.ndarray, slot: int) -> np.ndarray:
        log_weights = np.log(self.counts / self.counts.sum())
        if self.mode != "bootstrap_proposal":
            log_weights = log_weights - np.sum((self.centroids - feature) ** 2, axis=1) / TEMPERATURE_DENOMINATOR
        log_weights = log_weights + self._slot_evidence.get(slot, np.zeros(PARTICLES))
        weights = np.exp(log_weights - np.max(log_weights))
        return weights / weights.sum()

    def query(self, source: WTQuery, steps: int):
        if not isinstance(source, WTQuery) or int(steps) != source.horizon or source.horizon not in (16, 32, 96):
            raise ValueError("invalid anonymous WT particle-state query")
        history = _matrix(source.history, length=WINDOW)
        feature = _feature(history, source.control)
        weights = self._weights(feature, source.slot)
        particles = _extend(self.particles, source.horizon)
        if self.mode == "deterministic_posterior_mean":
            residual = np.tensordot(weights, particles, axes=(0, 0))
            aggregate_ops = 2 * PARTICLES * source.horizon * WIDTH
        elif self.mode in {"learned_proposal", "bootstrap_proposal"}:
            residual = _weighted_median(particles, weights)
            aggregate_ops = 3 * PARTICLES * source.horizon * WIDTH
        else:
            raise ValueError(f"unknown particle-state intervention: {self.mode}")
        prediction = np.clip(history[-1] + residual, -OUTPUT_CLIP, OUTPUT_CLIP)
        proposal_ops = 6 * PARTICLES + (0 if self.mode == "bootstrap_proposal" else 3 * PARTICLES * FEATURES)
        self.last_ops = float(4 * WINDOW * WIDTH + FEATURES + proposal_ops + aggregate_ops)
        self.last_bytes_touched = float(
            history.nbytes + feature.nbytes + self.particles.nbytes + self.centroids.nbytes
            + self.counts.nbytes + weights.nbytes + prediction.nbytes
            + self._slot_evidence.get(source.slot, np.empty(0)).nbytes
        )
        return prediction.tolist()

    def update(self, source: WTReveal) -> None:
        if not isinstance(source, WTReveal):
            raise ValueError("particle-state update requires a post-artifact reveal")
        history = _matrix(source.history, length=WINDOW)
        target = _matrix(source.target)
        horizon = min(WINDOW, len(target))
        if horizon < 1:
            raise ValueError("particle-state reveal target cannot be empty")
        residual = target[:horizon] - history[-1]
        errors = np.mean((self.particles[:, :horizon] - residual) ** 2, axis=(1, 2))
        previous = self._slot_evidence.get(source.slot, np.zeros(PARTICLES))
        evidence = EVIDENCE_DECAY * previous - errors / 2.0
        self._slot_evidence[source.slot] = evidence - np.max(evidence)
        self.update_ops = float(3 * PARTICLES * horizon * WIDTH + 4 * PARTICLES)
        self.last_update_bytes = float(
            history.nbytes + target[:horizon].nbytes + self.particles[:, :horizon].nbytes
            + previous.nbytes + self._slot_evidence[source.slot].nbytes
        )

    def state_bytes(self) -> int:
        fixed = self.particles.nbytes + self.centroids.nbytes + self.counts.nbytes
        return int(fixed + sum(value.nbytes for value in self._slot_evidence.values()) + 128)


class Candidate(ParticleProposalPredictiveState):
    """Shared source-identical entry point for all three preregistered roles."""
