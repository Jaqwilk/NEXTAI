from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .base import CandidateBase, CandidateMetadata
from nextai_autoresearch.cross_family_transfer_v2_contract import (
    PublicQuery, PublicTraining, PublicUpdate,
)


WIDTH = 32
Template = tuple[tuple[str, float | int], ...]


def _mix(value: int) -> int:
    value = (value ^ (value >> 16)) * 0x45D9F3B
    value = (value ^ (value >> 16)) * 0x45D9F3B
    return value ^ (value >> 16)


def _symbols(tokens: tuple[int, ...], known: dict[int, int] | None = None,
             known_atoms: tuple[int, ...] = ()):
    mapping = {} if known is None else dict(known)
    atoms = list(known_atoms)
    output = []
    integer_value = False
    for token in tokens:
        if integer_value:
            if token not in mapping:
                mapping[token] = len(mapping)
                atoms.append(token)
            symbol = 32 + mapping[token]
        elif token < 0:
            symbol = -token
        else:
            symbol = 16 + abs(token) % 509
        output.append(symbol)
        integer_value = token == -5
    return tuple(output), mapping, tuple(atoms)


def _advance(state: np.ndarray, symbols: tuple[int, ...], phase: int = 0):
    state = state.copy()
    for offset, symbol in enumerate(symbols):
        index = (17 * symbol + 5 * (phase + offset)) % WIDTH
        source = (index - 1) % WIDTH
        signal = ((_mix(symbol) & 1023) / 511.5) - 1.0
        state[index] = math.tanh(
            0.67 * state[index] + 0.21 * state[source] + 0.35 * signal
        )
        coupled = (index + 11) % WIDTH
        state[coupled] = 0.91 * state[coupled] + 0.09 * state[index]
    return state, 9 * len(symbols)


def _template(target: tuple[float, ...], mapping: dict[int, int]) -> Template:
    output = []
    for value in target:
        rounded = round(value)
        if abs(value - rounded) < 1e-9 and rounded in mapping:
            output.append(("pointer", mapping[rounded]))
        else:
            output.append(("scalar", float(value)))
    return tuple(output)


def _decode(template: Template, atoms: tuple[int, ...]) -> tuple[float, ...]:
    return tuple(
        float(atoms[int(value)])
        if kind == "pointer" and int(value) < len(atoms) else float(value)
        for kind, value in template
    ) or (0.0,)


@dataclass
class _Readout:
    weights: np.ndarray
    templates: tuple[Template, ...]


class RecurrentPredictiveStateLearner(CandidateBase):
    metadata = CandidateMetadata(
        "recurrent-predictive-state", "shared_recurrent_predictive_state_transfer",
        "One tied width-32 recurrent state and supervised predictive readout.",
    )
    state_width = WIDTH

    def __init__(self, seed: int = 0, mode: str = "shared") -> None:
        super().__init__(seed)
        self.mode = mode
        self.supports: dict[int, np.ndarray] = {}
        self.maps: dict[int, dict[int, int]] = {}
        self.atoms: dict[int, tuple[int, ...]] = {}
        self.models: dict[int, _Readout] = {}
        self.slot_models: dict[int, int] = {}
        self.memo: dict[tuple[int, tuple[int, ...]], tuple[float, ...]] = {}
        self.meta_fit_ops = self.last_bytes_touched = 0.0

    def _fit_readout(self, examples: list[tuple[np.ndarray, Template]], key: int) -> None:
        templates = tuple(dict.fromkeys(template for _, template in examples))
        labels = {template: index for index, template in enumerate(templates)}
        x = np.stack([np.append(state, 1.0) for state, _ in examples])
        y = np.zeros((len(examples), len(templates)))
        for row, (_, template) in enumerate(examples):
            y[row, labels[template]] = 1.0
        ridge = 0.05 * np.eye(WIDTH + 1)
        weights = np.linalg.solve(x.T @ x + ridge, x.T @ y)
        self.models[key] = _Readout(weights, templates)
        self.meta_fit_ops += float(
            len(examples) * (WIDTH + 1) ** 2 + (WIDTH + 1) ** 3
        )

    def fit(self, facts: PublicTraining, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        if not isinstance(facts, PublicTraining):
            raise TypeError("implementable learner accepts only PublicTraining")
        self.supports, self.maps, self.atoms = {}, {}, {}
        self.models, self.slot_models, self.memo = {}, {}, {}
        self.meta_fit_ops = 0.0
        pooled = []
        groups: list[list[tuple[np.ndarray, Template]]] = []
        training_states = []
        operations = 0
        for world in facts.training_worlds:
            symbols, mapping, atoms = _symbols(world.support)
            support, used = _advance(np.zeros(WIDTH), symbols)
            operations += used
            local = []
            for example in world.examples:
                query_symbols, full_map, _ = _symbols(example.query, mapping, atoms)
                state, used = _advance(support, (7919,) + query_symbols, len(symbols))
                item = (state, _template(example.target, full_map))
                local.append(item)
                pooled.append(item)
                operations += used + len(example.target)
            training_states.append(support)
            groups.append(local)
        for world in facts.test_worlds:
            symbols, mapping, atoms = _symbols(world.support)
            support, used = _advance(np.zeros(WIDTH), symbols)
            self.supports[world.slot] = support
            self.maps[world.slot] = mapping
            self.atoms[world.slot] = atoms
            operations += used

        if self.mode == "independent":
            for index, examples in enumerate(groups):
                self._fit_readout(examples, index)
            for slot, support in self.supports.items():
                self.slot_models[slot] = min(
                    range(len(training_states)),
                    key=lambda index: float(np.sum((support - training_states[index]) ** 2)),
                )
            operations += len(self.supports) * len(training_states) * WIDTH * 3
        else:
            self._fit_readout(pooled, 0)
        self.fit_ops = float(operations) + self.meta_fit_ops

    def query(self, source: PublicQuery, steps: int) -> tuple[float, ...]:
        del steps
        key = (source.slot, source.tokens)
        if key in self.memo:
            self.last_ops = self.last_bytes_touched = len(self.memo[key])
            return self.memo[key]
        symbols, mapping, atoms = _symbols(
            source.tokens, self.maps[source.slot], self.atoms[source.slot]
        )
        state, operations = _advance(
            self.supports[source.slot], (7919,) + symbols
        )
        model = self.models[self.slot_models.get(source.slot, 0)]
        scores = np.append(state, 1.0) @ model.weights
        answer = _decode(model.templates[int(np.argmax(scores))], atoms)
        self.last_ops = float(operations + model.weights.size)
        self.last_bytes_touched = float(
            8 * (len(source.tokens) + WIDTH + model.weights.size)
        )
        return answer

    def update(self, source: PublicUpdate, target: object) -> None:
        del target
        self.memo[source.query.slot, source.query.tokens] = tuple(source.target)
        self.update_ops += float(len(source.query.tokens) + len(source.target))

    def state_bytes(self) -> int:
        arrays = [*self.supports.values()]
        arrays.extend(model.weights for model in self.models.values())
        maps = sum(len(mapping) for mapping in self.maps.values()) * 16
        templates = sum(
            sum(len(template) for template in model.templates) * 16
            for model in self.models.values()
        )
        return int(sum(array.nbytes for array in arrays) + maps + templates
                   + len(self.memo) * 96)


class Candidate(RecurrentPredictiveStateLearner):
    pass
