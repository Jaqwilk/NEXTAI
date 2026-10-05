from __future__ import annotations

import itertools
import random
from collections import Counter

from .base import CandidateBase, CandidateMetadata


STATE_COUNT = 12


def _compose(left, right):
    return tuple(left[right[index]] for index in range(STATE_COUNT))


def _cycles(table):
    seen, sizes = set(), []
    for start in range(STATE_COUNT):
        if start not in seen:
            node, size = start, 0
            while node not in seen:
                seen.add(node)
                node, size = table[node], size + 1
            sizes.append(size)
    return tuple(sorted(sizes))


def _fingerprints(traces):
    return {token: tuple(sorted(_cycles(_compose(table, other))
                         for other_token, other in traces if other_token != token))
            for token, table in traces}


def _macro(programs):
    counts = Counter(pair for program in programs for pair in zip(program, program[1:]))
    return max(counts, key=lambda pair: (counts[pair], pair)) if counts else ()


class ConjugacyCandidate(CandidateBase):
    metadata = CandidateMetadata("conjugacy-library", "program-induction", "Opaque-DSL library transfer")

    def __init__(self, seed: int = 0, mode: str = "primitive") -> None:
        super().__init__(seed)
        self.mode, self.tables, self.library, self.cache = mode, {}, (), {}
        self.last_nodes = self.last_comparisons = self.last_bytes_touched = 0
        self.learned_state = 0

    @staticmethod
    def _map_by_fingerprint(reference, traces):
        left, right = _fingerprints(reference), _fingerprints(traces)
        inverse = {value: token for token, value in right.items()}
        return {token: inverse[value] for token, value in left.items()}

    @staticmethod
    def _exhaustive_map(reference, traces):
        left, right = _fingerprints(reference), _fingerprints(traces)
        left_tokens, right_tokens = sorted(left), sorted(right)
        best, best_score, operations = None, -1, 0
        for permutation in itertools.permutations(right_tokens):
            score = 0
            for source, target in zip(left_tokens, permutation):
                score += left[source] == right[target]
                operations += 1
            if score > best_score:
                best, best_score = permutation, score
        return dict(zip(left_tokens, best)), operations

    def fit(self, facts, universe_size: int, max_depth: int) -> None:
        del universe_size, max_depth
        oracle = self.mode == "oracle"
        public = facts.public if oracle else facts
        self.tables, self.cache, self.library = dict(public.target_traces), {}, ()
        raw_ops = sum(len(table) for domain in public.training for _, table in domain.traces)
        raw_ops += sum(len(program) for domain in public.training for program in domain.programs)
        raw_ops += sum(len(table) for _, table in public.target_traces)
        self.fit_ops, self.learned_state = raw_ops, 0
        if self.mode in ("primitive", "memo", "random"):
            return
        if oracle:
            self.library = (facts.target_by_role[0], facts.target_by_role[1])
            self.fit_ops = 0
            return
        reference = public.training[0].traces
        if self.mode == "syntactic":
            fragment = _macro(public.training[0].programs)
            self.library = fragment if all(token in self.tables for token in fragment) else ()
            return
        if self.mode == "unary":
            fragment = _macro(public.training[0].programs)
            target = sorted(self.tables)
            source = sorted(token for token, _ in reference)
            mapping = dict(zip(source, target))
            self.library = tuple(mapping[token] for token in fragment)
            return
        mappings, alignment_ops = [], 0
        for domain in public.training:
            if self.mode == "bayesian":
                mapping, operations = self._exhaustive_map(reference, domain.traces)
                alignment_ops += operations
            else:
                mapping = self._map_by_fingerprint(reference, domain.traces)
                alignment_ops += len(reference) ** 2 * STATE_COUNT
            mappings.append({target: source for source, target in mapping.items()})
        canonical = [tuple(mappings[index][token] for token in program)
                     for index, domain in enumerate(public.training) for program in domain.programs]
        fragment = _macro(canonical)
        if self.mode == "bayesian":
            target_map, operations = self._exhaustive_map(reference, public.target_traces)
            alignment_ops += operations
        else:
            target_map = self._map_by_fingerprint(reference, public.target_traces)
            alignment_ops += len(reference) ** 2 * STATE_COUNT
        self.library = tuple(target_map[token] for token in fragment)
        extraction_ops = sum(max(0, len(program) - 1) for program in canonical)
        self.fit_ops += alignment_ops + extraction_ops
        if self.mode == "learned":
            self.fit_ops += len(reference) * len(public.training) * 5
            self.learned_state = len(reference) * len(_fingerprints(reference)) * 8

    def _programs(self, length: int):
        grammar = tuple((token,) for token in sorted(self.tables)) + ((self.library,) if self.library else ())
        maximum = max(map(len, grammar))
        self.last_nodes = 0

        def visit(prefix, expanded, remaining):
            if remaining == 0:
                if expanded == length:
                    yield tuple(itertools.chain.from_iterable(prefix))
                return
            if expanded + remaining > length or expanded + remaining * maximum < length:
                return
            for token in grammar:
                self.last_nodes += 1
                if expanded + len(token) <= length:
                    yield from visit((*prefix, token), expanded + len(token), remaining - 1)

        for description_length in range(1, length + 1):
            yield from visit((), 0, description_length)

    def _matches(self, program, examples):
        operations = comparisons = 0
        for source, target in examples:
            value = source
            for token in program:
                value = self.tables[token][value]
                operations += 1
            comparisons += 1
            if value != target:
                return False, operations, comparisons
        return True, operations, comparisons

    def query(self, source, steps: int):
        del steps
        if self.mode == "oracle":
            self.last_ops = self.last_nodes = self.last_comparisons = 1
            self.last_bytes_touched = 8 * len(source.program)
            return source.program
        task = source
        if task.signature in self.cache:
            self.last_ops = self.last_nodes = self.last_comparisons = 1
            self.last_bytes_touched = 8
            return self.cache[task.signature]
        if self.mode == "random":
            rng = random.Random(self.seed ^ task.signature)
            answer = tuple(rng.choice(tuple(self.tables)) for _ in range(task.length))
            self.last_ops = self.last_nodes = 1
            self.last_comparisons, self.last_bytes_touched = 0, 8 * task.length
            return answer
        operations = comparisons = 0
        for program in self._programs(task.length):
            matched, used, compared = self._matches(program, task.examples)
            operations, comparisons = operations + used, comparisons + compared
            if matched:
                self.last_ops = operations + self.last_nodes
                self.last_comparisons, self.last_bytes_touched = comparisons, 8 * operations
                if self.mode == "memo":
                    self.cache[task.signature] = program
                return program
        self.last_ops, self.last_comparisons = operations + self.last_nodes, comparisons
        self.last_bytes_touched = 8 * operations
        return ()

    def update(self, source, target) -> None:
        del target
        if self.mode == "oracle":
            task, program = source.public, source.program
        else:
            task, program = source
        self.cache[task.signature] = tuple(program)
        self.update_ops = 1 + len(program)

    def state_bytes(self) -> int:
        return 256 + len(self.tables) * STATE_COUNT * 8 + len(self.library) * 8 \
            + len(self.cache) * 160 + self.learned_state


class Candidate(ConjugacyCandidate):
    def __init__(self, seed: int):
        super().__init__(seed, "primitive")
