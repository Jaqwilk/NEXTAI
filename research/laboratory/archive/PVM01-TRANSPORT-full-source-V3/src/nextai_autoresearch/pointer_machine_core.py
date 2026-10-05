from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .candidates.base import CandidateBase, CandidateMetadata


NEXT, ALT, READ_NEXT, BRANCH = range(4)
PRIMITIVES = (NEXT, ALT, READ_NEXT, BRANCH)
Memory = tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class Demo:
    token: int
    memory: Memory
    start: int
    accumulator: int
    expected: int


@dataclass(frozen=True)
class Task:
    memory: Memory
    start: int
    accumulator: int
    program: tuple[int, ...]
    mode: str


def encode(pointer: int, accumulator: int) -> int:
    return 2 * pointer + accumulator


def _cell(memory: Memory, pointer: int, dense: bool) -> tuple[tuple[int, int, int], int]:
    if not dense:
        return memory[pointer], 1
    selected = memory[0]
    for address, cell in enumerate(memory):
        if address == pointer:
            selected = cell
    return selected, len(memory)


def step(memory: Memory, pointer: int, accumulator: int, action: int, dense: bool = False):
    (bit, next_pointer, alt_pointer), reads = _cell(memory, pointer, dense)
    if action == NEXT:
        return next_pointer, accumulator, reads + 1, reads
    if action == ALT:
        return alt_pointer, accumulator, reads + 1, reads
    if action == READ_NEXT:
        return next_pointer, accumulator ^ bit, reads + 2, reads
    if action == BRANCH:
        return (alt_pointer if bit else next_pointer), accumulator, reads + 2, reads
    raise ValueError(f"unknown action {action}")


def execute(task: Task, mapping: dict[int, int], *, dense: bool, lookup_cost: int = 1):
    pointer, accumulator, operations, reads = task.start, task.accumulator, 0, 0
    for token in task.program:
        if token not in mapping:
            return None, operations + lookup_cost, reads
        pointer, accumulator, action_ops, action_reads = step(
            task.memory, pointer, accumulator, mapping[token], dense
        )
        operations += lookup_cost + action_ops
        reads += action_reads
    return encode(pointer, accumulator), operations, reads


class LearnedPointer(CandidateBase):
    metadata = CandidateMetadata("learned_hard_pointer", "learned_vm", "Learned opaque actions with hard memory")
    dense = False

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.mapping: dict[int, int] = {}
        self.last_visited_nodes = 0
        self.last_memory_reads = 0

    @staticmethod
    def _prediction(demo: Demo, action: int, dense: bool):
        pointer, accumulator, operations, reads = step(
            demo.memory, demo.start, demo.accumulator, action, dense
        )
        return encode(pointer, accumulator), operations + 1, reads

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        demos = tuple(facts)
        self.fit_ops = 0
        for token in sorted({demo.token for demo in demos}):
            valid = []
            for action in PRIMITIVES:
                matches = True
                for demo in (item for item in demos if item.token == token):
                    prediction, operations, _ = self._prediction(demo, action, self.dense)
                    self.fit_ops += operations
                    matches &= prediction == demo.expected
                if matches:
                    valid.append(action)
            if len(valid) == 1:
                self.mapping[token] = valid[0]

    def query(self, source: Task, steps: int) -> int | None:
        answer, self.last_ops, self.last_memory_reads = execute(
            source, self.mapping, dense=self.dense
        )
        self.last_visited_nodes = len(source.program)
        return answer

    def update(self, source: Demo, target: int) -> None:
        valid, self.update_ops = [], 0
        for action in PRIMITIVES:
            prediction, operations, _ = self._prediction(source, action, self.dense)
            self.update_ops += operations
            if prediction == source.expected:
                valid.append(action)
        if len(valid) == 1:
            self.mapping[source.token] = valid[0]

    def state_bytes(self) -> int:
        return 64 + 16 * len(self.mapping)


class DensePointer(LearnedPointer):
    metadata = CandidateMetadata("dense_pointer_controller", "learned_vm", "Same learned actions with dense memory scan")
    dense = True


class OraclePointer(LearnedPointer):
    metadata = CandidateMetadata("oracle_pointer_machine", "oracle", "Known actions with hard memory")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.mapping = dict(tuple(facts)[0])
        self.fit_ops = 0

    def query(self, source: Task, steps: int) -> int | None:
        answer, self.last_ops, self.last_memory_reads = execute(
            source, self.mapping, dense=False, lookup_cost=0
        )
        self.last_visited_nodes = len(source.program)
        return answer

    def update(self, source: Demo, target: int) -> None:
        self.update_ops = 1


class TraceMemorizer(CandidateBase):
    metadata = CandidateMetadata("pointer_trace_memorizer", "memory", "Whole primitive-demo lookup")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.examples: dict[Any, int] = {}
        self.last_visited_nodes = 0
        self.last_memory_reads = 0

    @staticmethod
    def _key(memory: Memory, start: int, accumulator: int, program: tuple[int, ...]):
        return memory, start, accumulator, program

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        for demo in facts:
            self.examples[self._key(demo.memory, demo.start, demo.accumulator, (demo.token,))] = demo.expected
            self.fit_ops += len(demo.memory) + 5

    def query(self, source: Task, steps: int) -> int:
        self.last_ops = len(source.memory) + len(source.program) + 1
        self.last_visited_nodes = len(source.program)
        return self.examples.get(
            self._key(source.memory, source.start, source.accumulator, source.program),
            encode(source.start, source.accumulator),
        )

    def update(self, source: Demo, target: int) -> None:
        self.examples[self._key(source.memory, source.start, source.accumulator, (source.token,))] = source.expected
        self.update_ops = len(source.memory) + 5

    def state_bytes(self) -> int:
        return 64 + sum(64 + 24 * len(key[0]) for key in self.examples)


class RandomPointer(CandidateBase):
    metadata = CandidateMetadata("random_pointer_guess", "random", "Deterministic random-like output control")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_visited_nodes = 0
        self.last_memory_reads = 0

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: Task, steps: int) -> int:
        self.last_ops = 1
        value = self.seed + source.start + source.accumulator + sum(source.program)
        return value % (2 * len(source.memory))

    def update(self, source: Demo, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64
