from __future__ import annotations

from typing import Any, Iterator

from .base import CandidateBase, CandidateMetadata
from ..masked_refinement_contract import MASK, MaskedQuery, MaskedTraining


ALPHABET = 256
EXPECTED_SYMBOLS = 7
BOUNDED_DEPTH = 2


def directed_pairings(values: tuple[int, ...]) -> Iterator[dict[int, int]]:
    if not values:
        yield {}
        return
    first = values[0]
    for index in range(1, len(values)):
        partner = values[index]
        rest = values[1:index] + values[index + 1:]
        for suffix in directed_pairings(rest):
            yield {first: partner, **suffix}
            yield {partner: first, **suffix}


class Candidate(CandidateBase):
    ROLE = "learned_pushdown_masked_byte"
    MODE = "learned"
    STACK_LIMIT: int | None = None

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.metadata = CandidateMetadata(self.ROLE, "masked_byte", self.ROLE)
        self.alphabet: tuple[int, ...] = ()
        self.separator: int | None = None
        self.pairs: dict[int, int] = {}
        self.fit_ops = self.meta_fit_ops = 0
        self.last_ops = self.last_bytes_touched = 0
        self.last_critical_path_steps = 1

    @staticmethod
    def _records(sequences: tuple[tuple[int, ...], ...], separator: int):
        output, operations = [], 0
        for sequence in sequences:
            current = []
            for value in sequence:
                operations += 1
                if value == separator:
                    if current:
                        output.append(tuple(current))
                        current = []
                else:
                    current.append(value)
            if current:
                output.append(tuple(current))
        return tuple(output), operations

    @staticmethod
    def _score(records: tuple[tuple[int, ...], ...], pairs: dict[int, int]):
        closes = {value: key for key, value in pairs.items()}
        valid_bytes = valid_records = violations = operations = 0
        for record in records:
            stack = []
            for value in record:
                operations += 1
                if value in pairs:
                    stack.append(value)
                elif value in closes and stack and pairs[stack[-1]] == value:
                    stack.pop()
                else:
                    violations += 1
            violations += len(stack)
            if not stack and all(value in pairs or value in closes for value in record):
                probe = []
                exact = True
                for value in record:
                    if value in pairs:
                        probe.append(value)
                    elif not probe or pairs[probe.pop()] != value:
                        exact = False
                        break
                if exact and not probe:
                    valid_bytes += len(record)
                    valid_records += 1
        return (valid_bytes, valid_records, -violations), operations

    def fit(self, facts: Any, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, MaskedTraining):
            raise TypeError("pushdown learner requires MaskedTraining")
        sequences = tuple(tuple(item.data) for item in facts.train_files)
        seen, alphabet, operations = set(), [], 0
        for sequence in sequences:
            for value in sequence:
                operations += 1
                if value not in seen:
                    seen.add(value)
                    alphabet.append(value)
        if len(alphabet) != EXPECTED_SYMBOLS:
            raise ValueError("pushdown contract requires exactly seven observed symbols")
        self.alphabet = tuple(alphabet)
        if self.MODE == "frozen":
            self.separator = self.alphabet[0]
            self.pairs = dict(zip(self.alphabet[1:4], self.alphabet[4:7]))
            self.fit_ops = self.meta_fit_ops = operations + EXPECTED_SYMBOLS
            return

        best_score, best = None, None
        for separator in self.alphabet:
            records, split_ops = self._records(sequences, separator)
            operations += split_ops
            possible_bytes = sum(map(len, records))
            for pairs in directed_pairings(tuple(value for value in self.alphabet
                                                   if value != separator)):
                score, parse_ops = self._score(records, pairs)
                operations += parse_ops + len(pairs)
                if best_score is None or score > best_score:
                    best_score, best = score, (separator, pairs)
                if score[:2] == (possible_bytes, len(records)) and score[2] == 0:
                    break
            if best_score == (possible_bytes, len(records), 0):
                break
        if best is None:
            raise ValueError("no pushdown grammar candidate")
        self.separator, self.pairs = best
        self.fit_ops = self.meta_fit_ops = operations

    def query(self, source: Any, steps: int) -> list[list[float]]:
        if not isinstance(source, MaskedQuery):
            raise TypeError("pushdown learner requires MaskedQuery")
        closes = {value: key for key, value in self.pairs.items()}
        wanted, predictions, stack = set(source.masked_positions), {}, []
        operations = 0
        for position, value in enumerate(source.snapshot):
            operations += 1
            if value == self.separator:
                stack.clear()
            elif value in self.pairs:
                stack.append(value)
                if self.STACK_LIMIT is not None:
                    stack[:] = stack[-self.STACK_LIMIT:]
            elif value in closes:
                if stack and self.pairs[stack[-1]] == value:
                    stack.pop()
                else:
                    stack.clear()
            elif value == MASK:
                if position in wanted and stack:
                    predictions[position] = self.pairs[stack[-1]]
                if stack:
                    stack.pop()
        output = []
        for position in source.masked_positions:
            prediction = predictions.get(position)
            if prediction is None:
                output.append([1.0 / ALPHABET] * ALPHABET)
            else:
                row = [0.0] * ALPHABET
                row[prediction] = 1.0
                output.append(row)
        self.last_ops = operations + len(output) * ALPHABET
        self.last_bytes_touched = len(source.snapshot) + len(output) * ALPHABET * 8
        self.last_critical_path_steps = max(1, len(source.snapshot) + 1)
        return output

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 0

    def state_bytes(self) -> int:
        return 512 + len(self.alphabet) * 8 + len(self.pairs) * 16
