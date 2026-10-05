from __future__ import annotations

import itertools
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .candidates.base import CandidateBase


Context = tuple[int, int, int]


@dataclass(frozen=True)
class TransitionRecord:
    history: tuple[int, ...]
    action: int
    outcome: int
    next_history: tuple[int, ...]


@dataclass(frozen=True)
class PredictiveDataset:
    records: tuple[TransitionRecord, ...]


@dataclass(frozen=True)
class OracleDataset(PredictiveDataset):
    context_states: dict[Context, int]
    transitions: dict[tuple[int, int], int]
    outcomes: dict[int, int]


def context(history: tuple[int, ...]) -> Context:
    return tuple(history[-3:])  # type: ignore[return-value]


def mode(counter: Counter):
    return min(counter, key=lambda value: (-counter[value], value))


class Predictor(CandidateBase):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.fit_ops = self.update_ops = self.last_ops = 0.0
        self.last_input_ops = self.last_search_ops = self.last_execution_ops = 0.0

    def state_bytes(self) -> float:
        return 0.0

    def _finish(self, input_ops: float, search_ops: float, execution_ops: float) -> None:
        self.last_input_ops, self.last_search_ops = input_ops, search_ops
        self.last_execution_ops = execution_ops
        self.last_ops = input_ops + search_ops + execution_ops

    def query(self, history: tuple[int, ...], actions: tuple[int, ...], plan_depth: int):
        raise NotImplementedError


class RandomHistoryPolicy(Predictor):
    def fit(self, data: PredictiveDataset, knowledge_size: int, max_depth: int) -> None:
        self.fit_ops = float(sum(len(row.history) for row in data.records))

    def query(self, history: tuple[int, ...], actions: tuple[int, ...], plan_depth: int):
        rng = random.Random(self.seed ^ sum(history) ^ len(actions) * 131)
        outputs = tuple(rng.randrange(4) for _ in actions)
        self._finish(len(history), 0.0, len(actions) + 1.0)
        return outputs, rng.randrange(2)

    def update(self, data: PredictiveDataset) -> None:
        self.update_ops = float(sum(len(row.history) for row in data.records))


class PartitionedPredictor(Predictor):
    strategy = "context"

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.records: list[TransitionRecord] = []
        self.context_state: dict[Context, int] = {}
        self.transitions: dict[tuple[int, int], tuple[int, int]] = {}
        self.contexts: tuple[Context, ...] = ()
        self.extra_state = 0

    def _raw(self, records: Iterable[TransitionRecord]):
        counts: dict[tuple[Context, int], Counter] = defaultdict(Counter)
        for row in records:
            counts[(context(row.history), row.action)][(row.outcome, context(row.next_history))] += 1
        contexts = sorted({key[0] for key in counts})
        raw = {(ctx, action): mode(counts[(ctx, action)]) for ctx in contexts for action in (0, 1)}
        return contexts, counts, raw

    @staticmethod
    def _future_matrix(contexts: list[Context], raw, horizon: int = 2) -> np.ndarray:
        programs = [program for depth in range(1, horizon + 1)
                    for program in itertools.product((0, 1), repeat=depth)]
        matrix = np.zeros((len(contexts), len(programs) * 4), dtype=float)
        for row, start in enumerate(contexts):
            for column, program in enumerate(programs):
                current = start
                for action in program:
                    outcome, current = raw[(current, action)]
                matrix[row, column * 4 + outcome] = 1.0
        return matrix

    def _partition(self, contexts: list[Context], counts, raw) -> dict[Context, int]:
        if self.strategy == "context":
            return {ctx: index for index, ctx in enumerate(contexts)}
        if self.strategy == "cssr":
            signatures = {}
            for ctx in contexts:
                signature = []
                for action in (0, 1):
                    total = sum(counts[(ctx, action)].values())
                    signature.extend(round(sum(n for (out, _), n in counts[(ctx, action)].items()
                                               if out == value) / total, 3) for value in range(4))
                signatures[ctx] = tuple(signature)
            unique = {value: index for index, value in enumerate(sorted(set(signatures.values())))}
            return {ctx: unique[signatures[ctx]] for ctx in contexts}
        if self.strategy == "bisimulation":
            labels = {ctx: tuple(raw[(ctx, action)][0] for action in (0, 1)) for ctx in contexts}
            for _ in contexts:
                unique = {value: index for index, value in enumerate(sorted(set(labels.values())))}
                partition = {ctx: unique[labels[ctx]] for ctx in contexts}
                refined = {ctx: tuple((raw[(ctx, action)][0], partition[raw[(ctx, action)][1]])
                                      for action in (0, 1)) for ctx in contexts}
                if refined == labels:
                    break
                labels = refined
            unique = {value: index for index, value in enumerate(sorted(set(labels.values())))}
            return {ctx: unique[labels[ctx]] for ctx in contexts}

        features = self._future_matrix(contexts, raw)
        if self.strategy == "spectral":
            u, singular, _ = np.linalg.svd(features, full_matrices=False)
            rank = max(1, int(np.sum(singular > 1e-8)))
            embedding = u[:, :rank] * singular[:rank]
            self.extra_state = embedding.size * 8
            self.fit_ops += float(features.size * rank)
        elif self.strategy == "contrastive":
            marginal = np.maximum(features.mean(axis=0, keepdims=True), 1e-6)
            contrast = np.log((features + 0.05) / marginal)
            u, singular, _ = np.linalg.svd(contrast, full_matrices=False)
            rank = min(4, max(1, int(np.sum(singular > 1e-8))))
            embedding = u[:, :rank] * singular[:rank]
            self.extra_state = embedding.size * 8
            self.fit_ops += float(features.size * (rank + len(contexts)))
        else:  # information bottleneck: the predictive vector is the sufficient statistic.
            embedding = features
            self.fit_ops += float(len(contexts) ** 2 * features.shape[1])
        rounded = [tuple(np.round(row, 7)) for row in embedding]
        unique = {value: index for index, value in enumerate(sorted(set(rounded)))}
        return {ctx: unique[rounded[index]] for index, ctx in enumerate(contexts)}

    def _rebuild(self, records: Iterable[TransitionRecord]) -> None:
        contexts, counts, raw = self._raw(records)
        self.contexts = tuple(contexts)
        self.context_state = self._partition(contexts, counts, raw)
        compiled: dict[tuple[int, int], Counter] = defaultdict(Counter)
        for ctx in contexts:
            state = self.context_state[ctx]
            for action in (0, 1):
                outcome, next_ctx = raw[(ctx, action)]
                compiled[(state, action)][(outcome, self.context_state[next_ctx])] += 1
        self.transitions = {key: mode(value) for key, value in compiled.items()}

    def fit(self, data: PredictiveDataset, knowledge_size: int, max_depth: int) -> None:
        self.records = list(data.records)
        self.fit_ops = float(sum(len(row.history) + 6 for row in self.records))
        self.extra_state = 0
        self._rebuild(self.records)
        self.fit_ops += float(len(self.contexts) ** 2 if self.strategy in {"cssr", "bisimulation"} else 0)

    def _state(self, history: tuple[int, ...]) -> tuple[int, float]:
        key = context(history)
        if key in self.context_state:
            return self.context_state[key], 1.0
        candidates = [ctx for ctx in self.contexts if ctx[-1] == key[-1]]
        chosen = min(candidates or list(self.contexts))
        return self.context_state[chosen], float(len(self.contexts))

    def _rollout(self, state: int, actions: tuple[int, ...]):
        outputs, reward, ops = [], 0, 0.0
        for action in actions:
            outcome, state = self.transitions[(state, action)]
            outputs.append(outcome)
            reward += outcome & 1
            ops += 3.0
        return tuple(outputs), reward, ops

    def query(self, history: tuple[int, ...], actions: tuple[int, ...], plan_depth: int):
        state, search = self._state(history)
        outputs, _, execution = self._rollout(state, actions)
        scored = []
        for program in itertools.product((0, 1), repeat=plan_depth):
            _, reward, ops = self._rollout(state, program)
            execution += ops
            scored.append((reward, tuple(-item for item in program), program[0]))
        action = max(scored)[2]
        self._finish(len(history), search, execution)
        return outputs, action

    def update(self, data: PredictiveDataset) -> None:
        changed = {(context(row.history), row.action) for row in data.records}
        self.records = [row for row in self.records
                        if (context(row.history), row.action) not in changed] + list(data.records)
        self.update_ops = float(sum(len(row.history) + 6 for row in self.records))
        before = self.fit_ops
        self._rebuild(self.records)
        self.update_ops += self.fit_ops - before

    def state_bytes(self) -> float:
        return float(len(self.context_state) * 32 + len(self.transitions) * 40 + self.extra_state)


class ContextTreeState(PartitionedPredictor):
    strategy = "context"


class CSSRStateReconstructor(PartitionedPredictor):
    strategy = "cssr"


class SpectralPSRState(PartitionedPredictor):
    strategy = "spectral"


class EmpiricalBisimulationState(PartitionedPredictor):
    strategy = "bisimulation"


class ContrastivePredictiveState(PartitionedPredictor):
    strategy = "contrastive"


class InformationBottleneckState(PartitionedPredictor):
    strategy = "bottleneck"


class RecurrentHistoryEncoder(Predictor):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.records: list[TransitionRecord] = []
        self.width = 24
        rng = np.random.default_rng(seed)
        self.recurrent = rng.normal(0, 0.18, (self.width, self.width))
        self.input = rng.normal(0, 0.45, (self.width, 16))
        self.weights = np.zeros((2, self.width + 1, 4))

    def _encode(self, history: tuple[int, ...]) -> tuple[np.ndarray, float]:
        state = np.zeros(self.width)
        for token in history:
            state = np.tanh(self.recurrent @ state + self.input[:, token % 16])
        return np.r_[state, 1.0], float(len(history) * self.width * (self.width + 1))

    def _train(self) -> float:
        ops = 0.0
        for action in (0, 1):
            rows = [row for row in self.records if row.action == action]
            x = np.vstack([self._encode(row.history)[0] for row in rows])
            y = np.eye(4)[[row.outcome for row in rows]]
            self.weights[action] = np.linalg.solve(x.T @ x + 1e-3 * np.eye(self.width + 1), x.T @ y)
            ops += float(len(rows) * (self.width + 1) ** 2 + (self.width + 1) ** 3)
        return ops

    def fit(self, data: PredictiveDataset, knowledge_size: int, max_depth: int) -> None:
        self.records = list(data.records)
        self.fit_ops = self._train() + sum(self._encode(row.history)[1] for row in self.records)

    def _step(self, history: tuple[int, ...], action: int):
        encoded, ops = self._encode(history)
        outcome = int(np.argmax(encoded @ self.weights[action]))
        return (*history, 4 + action, outcome), outcome, ops + (self.width + 1) * 4

    def _rollout(self, history: tuple[int, ...], actions: tuple[int, ...]):
        outputs, reward, ops = [], 0, 0.0
        for action in actions:
            history, outcome, step_ops = self._step(history, action)
            outputs.append(outcome)
            reward += outcome & 1
            ops += step_ops
        return tuple(outputs), reward, ops

    def query(self, history: tuple[int, ...], actions: tuple[int, ...], plan_depth: int):
        outputs, _, ops = self._rollout(history, actions)
        scored = []
        for program in itertools.product((0, 1), repeat=plan_depth):
            _, reward, cost = self._rollout(history, program)
            ops += cost
            scored.append((reward, tuple(-item for item in program), program[0]))
        self._finish(len(history), 0.0, ops)
        return outputs, max(scored)[2]

    def update(self, data: PredictiveDataset) -> None:
        changed = {(context(row.history), row.action) for row in data.records}
        self.records = [row for row in self.records
                        if (context(row.history), row.action) not in changed] + list(data.records)
        self.update_ops = self._train() + sum(self._encode(row.history)[1] for row in self.records)

    def state_bytes(self) -> float:
        return float(self.recurrent.nbytes + self.input.nbytes + self.weights.nbytes)


class OraclePredictiveState(Predictor):
    def fit(self, data: OracleDataset, knowledge_size: int, max_depth: int) -> None:
        self.context_states = dict(data.context_states)
        self.transitions = dict(data.transitions)
        self.outcomes = dict(data.outcomes)
        self.fit_ops = 0.0

    def _rollout(self, state: int, actions: tuple[int, ...]):
        outputs, reward = [], 0
        for action in actions:
            state = self.transitions[(state, action)]
            outcome = self.outcomes[state]
            outputs.append(outcome)
            reward += outcome & 1
        return tuple(outputs), reward

    def query(self, history: tuple[int, ...], actions: tuple[int, ...], plan_depth: int):
        state = self.context_states[context(history)]
        outputs, _ = self._rollout(state, actions)
        scored = [(self._rollout(state, program)[1], tuple(-item for item in program), program[0])
                  for program in itertools.product((0, 1), repeat=plan_depth)]
        execution = float(len(actions) + plan_depth * 2 ** plan_depth)
        self._finish(len(history), 1.0, execution)
        return outputs, max(scored)[2]

    def update(self, data: OracleDataset) -> None:
        self.context_states.update(data.context_states)
        self.transitions.update(data.transitions)
        self.outcomes.update(data.outcomes)
        self.update_ops = float(len(data.transitions))

    def state_bytes(self) -> float:
        return float(len(self.context_states) * 24 + len(self.transitions) * 24)
