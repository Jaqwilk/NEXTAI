from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np

from .candidates.base import CandidateBase


@dataclass(frozen=True)
class TransitionPair:
    source: np.ndarray
    target: np.ndarray


@dataclass(frozen=True)
class TransitionDataset:
    pairs: tuple[TransitionPair, ...]
    width: int
    max_depth: int


@dataclass(frozen=True)
class OracleQuery:
    state: np.ndarray
    required_depth: int


class SharedTransition:
    def __init__(self, width: int = 8) -> None:
        self.width = width
        self.encoder = np.empty((0, 0))
        self.decoder = np.empty((0, 0))
        self.fit_ops = 0.0

    def fit(self, data: TransitionDataset) -> None:
        dimensions = len(data.pairs[0].source)
        deltas = [row.source - row.target for row in data.pairs
                  if not np.allclose(row.source, row.target, atol=1e-10)]
        direction = np.mean(np.vstack(deltas), axis=0)
        scale = float(direction @ direction)
        self.encoder = np.zeros((self.width, dimensions))
        self.decoder = np.zeros((dimensions, self.width))
        self.encoder[0] = direction / scale
        self.decoder[:, 0] = direction
        self.fit_ops = float(len(data.pairs) * 3 * dimensions + 2 * dimensions * self.width)

    @property
    def dimensions(self) -> int:
        return int(self.encoder.shape[1])

    @property
    def encode_ops(self) -> float:
        return float(2 * self.dimensions * self.width)

    @property
    def decode_ops(self) -> float:
        return float(2 * self.dimensions * self.width + self.dimensions + self.width)

    def encode(self, state: np.ndarray) -> np.ndarray:
        return self.encoder @ state

    def decode(self, state: np.ndarray, hidden: np.ndarray) -> np.ndarray:
        activation = np.zeros(self.width)
        activation[0] = float(hidden[0] > 0.5)
        return state - self.decoder @ activation

    def step(self, state: np.ndarray) -> tuple[np.ndarray, float]:
        hidden = self.encode(state)
        return self.decode(state, hidden), self.encode_ops + self.decode_ops

    def state_bytes(self) -> int:
        return int(self.encoder.nbytes + self.decoder.nbytes)

    def signature(self) -> float:
        return float(np.round(np.abs(self.encoder).sum() + np.abs(self.decoder).sum(), 12))


class SharedTransitionSolver(CandidateBase):
    policy = "fixed_max"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.kernel = SharedTransition()
        self.max_depth = 0
        self.halt_weight = np.zeros(8)
        self.halt_bias = 0.0
        self.last_transition_calls = self.last_controller_ops = 0.0
        self.transition_signature = 0.0

    def _train_halt(self, data: TransitionDataset) -> float:
        self.halt_weight = np.zeros(self.kernel.width)
        self.halt_bias = 0.0
        examples = [(self.kernel.encode(row.source),
                     1.0 if np.allclose(row.source, row.target, atol=1e-10) else -1.0)
                    for row in data.pairs]
        ops = float(len(examples) * self.kernel.encode_ops)
        for _ in range(8):
            mistakes = 0
            for hidden, label in examples:
                score = float(self.halt_weight @ hidden + self.halt_bias)
                ops += 2 * self.kernel.width + 2
                if label * score <= 0:
                    self.halt_weight += label * hidden
                    self.halt_bias += label
                    ops += self.kernel.width + 1
                    mistakes += 1
            if not mistakes:
                break
        return ops

    def fit(self, data: TransitionDataset, universe_size: int, max_depth: int) -> None:
        self.kernel.fit(data)
        self.max_depth = max_depth
        self.fit_ops = self.kernel.fit_ops
        if self.policy in {"learned", "act"}:
            self.fit_ops += self._train_halt(data)
        self.transition_signature = self.kernel.signature()

    def _fixed(self, state: np.ndarray, steps: int) -> np.ndarray:
        operations = 0.0
        for _ in range(steps):
            state, cost = self.kernel.step(state)
            operations += cost
        self.last_transition_calls = float(steps)
        self.last_controller_ops = 0.0
        self.last_ops = operations
        return state

    def _gate(self, state: np.ndarray, learned: bool = False, act: bool = False) -> np.ndarray:
        operations = calls = controller = 0.0
        for _ in range(self.max_depth + 2):
            hidden = self.kernel.encode(state)
            operations += self.kernel.encode_ops
            if learned:
                score = float(self.halt_weight @ hidden + self.halt_bias)
                cost = float(2 * self.kernel.width + 2)
                halt = score >= 0.0
                if act:
                    probability = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, score))))
                    halt = probability >= 0.5
                    cost += 6.0
                operations += cost
                controller += cost
            else:
                halt = bool(hidden[0] <= 0.5)
                operations += 1.0
                controller += 1.0
            if halt:
                break
            state = self.kernel.decode(state, hidden)
            operations += self.kernel.decode_ops
            calls += 1.0
        self.last_transition_calls = calls
        self.last_controller_ops = controller
        self.last_ops = operations
        return state

    def _residual(self, state: np.ndarray) -> np.ndarray:
        operations = calls = controller = 0.0
        for _ in range(self.max_depth + 2):
            following, cost = self.kernel.step(state)
            calls += 1.0
            residual = float(np.abs(following - state).sum())
            residual_ops = float(2 * self.kernel.dimensions)
            operations += cost + residual_ops
            controller += residual_ops
            if residual <= 1e-9:
                break
            state = following
        self.last_transition_calls = calls
        self.last_controller_ops = controller
        self.last_ops = operations
        return state

    def query(self, source, steps: int = 0):
        oracle_depth = source.required_depth if isinstance(source, OracleQuery) else None
        state = np.array(source.state if isinstance(source, OracleQuery) else source, copy=True)
        if self.policy == "random":
            count = random.Random(self.seed ^ int(abs(state.sum()) * 1000)).randrange(self.max_depth + 1)
            return self._fixed(state, count)
        if self.policy == "fixed_short":
            return self._fixed(state, 4)
        if self.policy == "fixed_max":
            return self._fixed(state, self.max_depth)
        if self.policy == "residual":
            return self._residual(state)
        if self.policy == "gate":
            return self._gate(state)
        if self.policy == "learned":
            return self._gate(state, learned=True)
        if self.policy == "act":
            return self._gate(state, learned=True, act=True)
        if self.policy == "oracle":
            return self._fixed(state, int(oracle_depth))
        raise ValueError(self.policy)

    def update(self, data: TransitionDataset, target=None) -> None:
        self.kernel.fit(data)
        self.update_ops = self.kernel.fit_ops
        self.transition_signature = self.kernel.signature()

    def state_bytes(self) -> int:
        controller = self.halt_weight.nbytes + 8 if self.policy in {"learned", "act"} else 0
        return self.kernel.state_bytes() + int(controller) + 64


class RandomSharedHalt(SharedTransitionSolver):
    policy = "random"


class FixedShortSharedTransition(SharedTransitionSolver):
    policy = "fixed_short"


class FixedMaxSharedTransition(SharedTransitionSolver):
    policy = "fixed_max"


class ResidualSharedTransition(SharedTransitionSolver):
    policy = "residual"


class TransitionGateHalt(SharedTransitionSolver):
    policy = "gate"


class LearnedAdaptiveHalt(SharedTransitionSolver):
    policy = "learned"


class ACTPonderHalt(SharedTransitionSolver):
    policy = "act"


class OracleSharedHalt(SharedTransitionSolver):
    policy = "oracle"
