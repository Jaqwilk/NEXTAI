from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .base import CandidateMetadata
from .shared_state_core import (
    WIDTH,
    RecurrentPredictiveStateLearner as _LinearState,
    Template,
    _advance,
    _decode,
    _symbols,
)
from nextai_autoresearch.cross_family_transfer_v2_contract import (
    PublicQuery,
)


CAPACITY = 48
TOP_K = 3
EPSILON = 1e-6


@dataclass
class _Dictionary:
    states: np.ndarray
    templates: tuple[Template, ...]


def _compose(model: _Dictionary, distances: np.ndarray) -> Template:
    nearest = np.argsort(distances)[:min(TOP_K, len(distances))]
    width = max(len(model.templates[index]) for index in nearest)
    output = []
    for position in range(width):
        votes: dict[tuple[str, float | int], tuple[float, int]] = {}
        for rank, index in enumerate(nearest):
            template = model.templates[index]
            if position >= len(template):
                continue
            fragment = template[position]
            weight = 1.0 / (float(distances[index]) + EPSILON)
            total, first = votes.get(fragment, (0.0, rank))
            votes[fragment] = (total + weight, first)
        output.append(max(votes, key=lambda item: (votes[item][0], -votes[item][1])))
    return tuple(output)


class RecurrentPredictiveStateLearner(_LinearState):
    metadata = CandidateMetadata(
        "recurrent-fragment-dictionary", "recurrent_predictive_dictionary_composition",
        "Fixed top-3 dictionary composition over the unchanged width-32 state.",
    )

    def _fit_readout(self, examples: list[tuple[np.ndarray, Template]], key: int) -> None:
        if len(examples) > CAPACITY:
            raise ValueError(f"fragment capacity exceeded: {len(examples)} > {CAPACITY}")
        states = np.stack([state for state, _ in examples])
        self.models[key] = _Dictionary(
            states, tuple(template for _, template in examples)
        )
        self.meta_fit_ops += float(states.size)

    def query(self, source: PublicQuery, steps: int) -> tuple[float, ...]:
        del steps
        key = (source.slot, source.tokens)
        if key in self.memo:
            self.last_ops = self.last_bytes_touched = len(self.memo[key])
            return self.memo[key]
        symbols, _, atoms = _symbols(
            source.tokens, self.maps[source.slot], self.atoms[source.slot]
        )
        state, operations = _advance(
            self.supports[source.slot], (7919,) + symbols
        )
        model = self.models[self.slot_models.get(source.slot, 0)]
        distances = np.sum((model.states - state) ** 2, axis=1)
        template = _compose(model, distances)
        answer = _decode(template, atoms)
        composition_ops = min(TOP_K, len(distances)) * max(1, len(template)) * 4
        self.last_ops = float(
            operations + model.states.size * 3 + composition_ops
        )
        self.last_bytes_touched = float(
            8 * (len(source.tokens) + WIDTH + model.states.size)
        )
        return answer

    def state_bytes(self) -> int:
        arrays = [*self.supports.values()]
        arrays.extend(model.states for model in self.models.values())
        maps = sum(len(mapping) for mapping in self.maps.values()) * 16
        templates = sum(
            sum(len(template) for template in model.templates) * 16
            for model in self.models.values()
        )
        return int(sum(array.nbytes for array in arrays) + maps + templates
                   + len(self.memo) * 96)


class Candidate(RecurrentPredictiveStateLearner):
    pass
