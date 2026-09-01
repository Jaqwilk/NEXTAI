from __future__ import annotations

import math
import random
from typing import Any, Iterable

from .base import CandidateBase, CandidateMetadata


CHANNELS = 4
RAW_WIDTH = 12
PROGRAM_COUNT = 256
MAX_TERMS = 3
COEFFICIENTS = (-1.0, -0.5, -0.25, 0.25, 0.5, 1.0)
OUTPUT_BOUND = 1.5
PROPOSAL_SALT = 0xE701
SHUFFLE_SALT = 0x5A17

# (kind, first coordinate, second coordinate, coefficient)
Term = tuple[int, int, int, float]
Program = tuple[Term, ...]


def term_count(index: int) -> int:
    if index < 0 or index >= PROGRAM_COUNT:
        raise IndexError(index)
    return 1 if index < 64 else 2 if index < 160 else 3


def make_population(seed: int, output: int) -> tuple[Program, ...]:
    rng = random.Random(seed ^ PROPOSAL_SALT ^ (output * 0x9E37))
    programs: list[Program] = [((0, CHANNELS + output, 0, 1.0),)]
    for index in range(1, PROGRAM_COUNT):
        terms = []
        for _ in range(term_count(index)):
            terms.append((
                rng.randrange(3), rng.randrange(RAW_WIDTH), rng.randrange(RAW_WIDTH),
                COEFFICIENTS[rng.randrange(len(COEFFICIENTS))],
            ))
        programs.append(tuple(terms))
    return tuple(programs)


def make_shuffle(seed: int, output: int) -> tuple[int, ...]:
    order = list(range(PROGRAM_COUNT))
    random.Random(seed ^ SHUFFLE_SALT ^ (output * 0x7F4A)).shuffle(order)
    return tuple(order)


def evaluate_program(program: Program, raw: tuple[float, ...]) -> tuple[float, int]:
    total = 0.0
    operations = 0
    for kind, first, second, coefficient in program:
        if kind == 0:
            primitive = raw[first]
            operations += 1
        elif kind == 1:
            primitive = math.tanh(raw[first])
            operations += 5
        else:
            primitive = raw[first] * raw[second]
            operations += 3
        total += coefficient * primitive
        operations += 2
    return max(-OUTPUT_BOUND, min(OUTPUT_BOUND, total)), operations + 2


def program_operation_count(program: Program) -> int:
    return 2 + sum((1 if term[0] == 0 else 5 if term[0] == 1 else 3) + 2 for term in program)


class PopulationLocalRule(CandidateBase):
    metadata = CandidateMetadata(
        "population_local_rule", "continuous_cellular",
        "Source-identical fitness-selected anonymous local rule programs",
    )

    def __init__(self, seed: int = 0, *, mode: str = "true") -> None:
        super().__init__(seed)
        if mode not in {"true", "shuffled", "frozen"}:
            raise ValueError(mode)
        self.mode = mode
        self.populations = tuple(make_population(seed, output) for output in range(CHANNELS))
        self.shuffles = tuple(make_shuffle(seed, output) for output in range(CHANNELS))
        self.scores = [[0.0] * PROGRAM_COUNT for _ in range(CHANNELS)]
        self.selected = [0] * CHANNELS
        self.last_bytes_touched = 0
        self._proposal_ops = sum(
            1 + 5 * len(program) for population in self.populations for program in population
        ) + CHANNELS * (PROGRAM_COUNT - 1)

    @staticmethod
    def _raw(row: Any) -> tuple[float, ...]:
        return tuple((*row.left, *row.center, *row.right))

    def assigned_scores(self, output: int) -> tuple[float, ...]:
        scores = self.scores[output]
        if self.mode == "shuffled":
            return tuple(scores[index] for index in self.shuffles[output])
        return tuple(scores)

    def _select(self) -> None:
        if self.mode == "frozen":
            self.selected = [0] * CHANNELS
            return
        self.selected = [
            min(range(PROGRAM_COUNT), key=lambda index: (assigned[index], index))
            for output in range(CHANNELS)
            for assigned in (self.assigned_scores(output),)
        ]

    def _accumulate(self, rows: Iterable[Any]) -> int:
        operations = 0
        for row in rows:
            if not all(hasattr(row, field) for field in ("left", "center", "right", "target")):
                raise TypeError("population local rule requires Transition rows")
            raw = self._raw(row)
            operations += RAW_WIDTH
            for output, population in enumerate(self.populations):
                target = float(row.target[output])
                for index, program in enumerate(population):
                    prediction, work = evaluate_program(program, raw)
                    difference = prediction - target
                    self.scores[output][index] += difference * difference
                    operations += work + 3
        self._select()
        return operations + CHANNELS * (PROGRAM_COUNT - 1)

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        del universe_size
        if max_depth != 16:
            raise ValueError("population local rule requires frozen maximum depth 16")
        rows = tuple(facts)
        if not rows:
            raise ValueError("population local rule requires training rows")
        self.scores = [[0.0] * PROGRAM_COUNT for _ in range(CHANNELS)]
        self.fit_ops = self._proposal_ops + self._accumulate(rows)

    def _predict(self, left: tuple[float, ...], center: tuple[float, ...],
                 right: tuple[float, ...]) -> tuple[tuple[float, ...], int]:
        raw = tuple((*left, *center, *right))
        if not any(raw):
            return (0.0,) * CHANNELS, RAW_WIDTH
        values = []
        operations = RAW_WIDTH
        for output, index in enumerate(self.selected):
            value, work = evaluate_program(self.populations[output][index], raw)
            values.append(value)
            operations += work
        return tuple(values), operations

    def query(self, source: Any, steps: int) -> tuple[float, ...]:
        if not all(hasattr(source, field) for field in ("size", "target", "initial")):
            raise TypeError("population local rule requires a sparse public Task")
        zero = (0.0,) * CHANNELS
        state = dict(source.initial)
        operations = len(state) * CHANNELS
        touched = len(state) * CHANNELS * 8
        for _ in range(steps):
            active = set(state)
            positions = active | {(position - 1) % source.size for position in active} \
                | {(position + 1) % source.size for position in active}
            updated = {}
            for position in positions:
                value, work = self._predict(
                    state.get((position - 1) % source.size, zero),
                    state.get(position, zero),
                    state.get((position + 1) % source.size, zero),
                )
                updated[position] = value
                operations += work
                touched += (RAW_WIDTH + CHANNELS) * 8
            state = updated
        self.last_ops = int(operations)
        self.last_bytes_touched = int(touched)
        return state.get(source.target, zero)

    def update(self, source: Any, target: Any) -> None:
        del target
        self.update_ops = self._accumulate((source,))

    def state_bytes(self) -> int:
        terms = sum(len(program) for population in self.populations for program in population)
        return int(terms * 32 + CHANNELS * PROGRAM_COUNT * (16 + 8) + CHANNELS * 8 + 64)


class Candidate(PopulationLocalRule):
    """Auditable default entry for the shared implementation module."""
