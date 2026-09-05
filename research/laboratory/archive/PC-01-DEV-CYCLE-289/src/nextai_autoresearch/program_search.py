from __future__ import annotations

import itertools
import random
from collections import Counter


DOMAIN_SIZE = 31
PRIMITIVE_COUNT = 4
TARGET_MACRO = (0, 1)
MISMATCHED_MACRO = (3, 3)


def _make_permutations() -> tuple[tuple[int, ...], ...]:
    tables = []
    for seed in range(PRIMITIVE_COUNT):
        table = list(range(DOMAIN_SIZE))
        random.Random(7919 + seed).shuffle(table)
        tables.append(tuple(table))
    return tuple(tables)


PRIMITIVES = _make_permutations()


def execute(program: tuple[int, ...], value: int) -> int:
    for primitive in program:
        value = PRIMITIVES[primitive][value]
    return value


def extract_macro(programs: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], int]:
    counts: Counter[tuple[int, ...]] = Counter()
    operations = 0
    for program in programs:
        for width in (2, 3):
            for start in range(len(program) - width + 1):
                counts[program[start : start + width]] += 1
                operations += 1
    if not counts:
        return (), operations
    fragment = max(
        counts,
        key=lambda item: ((len(item) - 1) * counts[item] - len(item), counts[item], item),
    )
    score = (len(fragment) - 1) * counts[fragment] - len(fragment)
    return (fragment if score > 0 else ()), operations


class ProgramSearchCandidate:
    def __init__(self, seed: int, mode: str) -> None:
        self.seed = seed
        self.mode = mode
        self.library: tuple[tuple[int, ...], ...] = ()
        self.corpus: tuple[tuple[int, ...], ...] = ()
        self.cache: dict[tuple[object, ...], int] = {}
        self.last_ops = self.fit_ops = self.update_ops = 0
        self.last_nodes = self.last_description_length = 0

    def fit(self, programs, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        data = tuple(tuple(program) for program in programs)
        self.cache.clear()
        self.corpus = data if self.mode == "learned" else ()
        self.fit_ops = 0
        if self.mode == "learned":
            fragment, self.fit_ops = extract_macro(data)
            self.library = (fragment,) if fragment else ()
        elif self.mode == "oracle":
            self.library = (TARGET_MACRO,)
        elif self.mode == "mismatch":
            self.library = (MISMATCHED_MACRO,)
        else:
            self.library = ()

    def _programs(self, length: int):
        grammar = tuple((index,) for index in range(PRIMITIVE_COUNT)) + self.library
        maximum_token = max(map(len, grammar))
        self.last_nodes = 0

        def visit(prefix, expanded: int, remaining: int):
            if remaining == 0:
                if expanded == length:
                    yield tuple(itertools.chain.from_iterable(prefix))
                return
            if expanded + remaining > length or expanded + remaining * maximum_token < length:
                return
            for token in grammar:
                self.last_nodes += 1
                new_length = expanded + len(token)
                if new_length <= length:
                    yield from visit((*prefix, token), new_length, remaining - 1)

        for description_length in range(1, length + 1):
            self.last_description_length = description_length
            yield from visit((), 0, description_length)

    def query(self, examples, test_input: int, length: int) -> int | None:
        key = (tuple(examples), test_input, length)
        if self.mode == "memo" and key in self.cache:
            self.last_ops = self.last_nodes = 1
            return self.cache[key]
        if self.mode == "random":
            self.last_ops = self.last_nodes = 1
            return (test_input + self.seed + len(examples)) % DOMAIN_SIZE

        operations = 0
        for program in self._programs(length):
            matched = True
            for source, target in examples:
                operations += len(program)
                if execute(program, source) != target:
                    matched = False
                    break
            if matched:
                operations += len(program)
                result = execute(program, test_input)
                self.last_ops = operations + self.last_nodes
                if self.mode == "memo":
                    self.cache[key] = result
                return result
        self.last_ops = operations + self.last_nodes
        return None

    def update(self, program: tuple[int, ...]) -> None:
        if self.mode == "learned":
            self.corpus = (*self.corpus, tuple(program))
            fragment, operations = extract_macro(self.corpus)
            self.library = (fragment,) if fragment else ()
            self.update_ops = 1 + operations
        else:
            self.update_ops = 1

    def state_bytes(self) -> int:
        corpus_items = sum(len(program) for program in self.corpus)
        library_items = sum(len(fragment) for fragment in self.library)
        return 256 + 28 * (corpus_items + library_items) + 160 * len(self.cache)
