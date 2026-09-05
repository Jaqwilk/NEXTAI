from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from .candidates.base import CandidateBase, CandidateMetadata


SENTINEL = 2
PROGRAMS = tuple(tuple((code >> bit) & 1 for bit in range(8)) for code in range(256))


def _strings(minimum: int, maximum: int):
    return tuple(
        tuple((code >> (width - 1 - bit)) & 1 for bit in range(width))
        for width in range(minimum, maximum + 1)
        for code in range(1 << width)
    )


SUPPORT_INPUTS = _strings(2, 4)


@dataclass(frozen=True)
class Support:
    tape: tuple[int, ...]
    target: int


@dataclass(frozen=True)
class IOQuery:
    support: tuple[Support, ...]
    tape: tuple[int, ...]


@dataclass(frozen=True)
class TrainingExample:
    query: IOQuery
    target: int


@dataclass(frozen=True)
class OracleInput:
    query: IOQuery
    program: tuple[int, ...]


def active_bits(tape: tuple[int, ...]):
    bits = []
    for reads, value in enumerate(tape, 1):
        if value == SENTINEL:
            return tuple(bits), reads
        bits.append(value)
    return tuple(bits), len(tape)


def run_program(program: tuple[int, ...], bits: tuple[int, ...]):
    state = output = 0
    for bit in bits:
        index = 2 * state + bit
        output = program[4 + index]
        state = program[index]
    return output, 5 * len(bits)


def execute_tape(program: tuple[int, ...], tape: tuple[int, ...], dense: bool = False):
    bits, prefix_reads = active_bits(tape)
    reads = len(tape) if dense else prefix_reads
    output, controller_ops = run_program(program, bits)
    return output, reads + controller_ops, reads, len(bits)


def support_key(support: tuple[Support, ...]):
    key, reads = [], 0
    for example in support:
        bits, used = active_bits(example.tape)
        key.append((bits, example.target))
        reads += used
    return tuple(key), reads


class WholeIOBase(CandidateBase):
    metadata = CandidateMetadata("whole_io_base", "control", "Whole-I/O program control")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.last_program: tuple[int, ...] | None = None
        self.last_support_ops = self.last_search_ops = self.last_controller_ops = 0
        self.last_memory_reads = self.last_bytes_loaded = self.last_program_evaluations = 0

    def _record(self, support_ops: int, search_ops: int, controller_ops: int, reads: int):
        self.last_support_ops = support_ops
        self.last_search_ops = search_ops
        self.last_controller_ops = controller_ops
        self.last_memory_reads = reads
        self.last_bytes_loaded = reads
        self.last_ops = support_ops + search_ops + controller_ops


class RandomWholeIO(WholeIOBase):
    metadata = CandidateMetadata("random_whole_io", "random", "Deterministic random whole-I/O guess")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: IOQuery, steps: int) -> int:
        bits, reads = active_bits(source.tape)
        self.last_program = None
        self._record(0, 0, reads + 1, reads)
        return (self.seed + sum((index + 1) * bit for index, bit in enumerate(bits))) & 1

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 64


class NearestWholeIO(RandomWholeIO):
    metadata = CandidateMetadata("nearest_whole_io", "memory", "Nearest support sequence output")

    def query(self, source: IOQuery, steps: int) -> int:
        test, test_reads = active_bits(source.tape)
        best, support_reads, comparisons = None, 0, 0
        for example in source.support:
            seen, reads = active_bits(example.tape)
            support_reads += reads
            width = max(len(test), len(seen))
            distance = abs(len(test) - len(seen)) + sum(
                test[index] != seen[index] for index in range(min(len(test), len(seen)))
            )
            comparisons += width + 2
            choice = (distance, len(seen), example.target)
            best = choice if best is None or choice < best else best
        self.last_program = None
        self._record(support_reads, 0, comparisons + test_reads, support_reads + test_reads)
        return int(best[2])


class DenseWholeIO(WholeIOBase):
    metadata = CandidateMetadata("dense_whole_io", "dense", "Dense random-feature whole-I/O predictor")

    def _encode(self, query: IOQuery):
        labels, reads = {}, 0
        for example in query.support:
            bits, _ = active_bits(example.tape)
            labels[bits] = example.target
            reads += len(example.tape)
        signature = [2.0 * labels[item] - 1.0 if item in labels else 0.0 for item in SUPPORT_INPUTS]
        tape = [0.0 if value == SENTINEL else 2.0 * value - 1.0 for value in query.tape]
        return np.asarray([1.0, *signature, *tape]), reads + len(query.tape)

    def fit(self, facts: Iterable[TrainingExample], universe_size: int, max_depth: int) -> None:
        examples = tuple(facts)
        rows, targets = zip(*((self._encode(item.query)[0], item.target) for item in examples))
        inputs, outputs = np.asarray(rows), 2.0 * np.asarray(targets) - 1.0
        width, dimension = 48, inputs.shape[1]
        rng = np.random.default_rng(self.seed)
        self.weights = rng.normal(0.0, 1.0 / math.sqrt(dimension), (dimension, width))
        self.bias = rng.normal(0.0, 0.2, width)
        hidden = np.tanh(inputs @ self.weights + self.bias)
        ridge = hidden.T @ hidden + 0.2 * np.eye(width)
        self.readout = np.linalg.solve(ridge, hidden.T @ outputs)
        samples = len(examples)
        self.fit_ops = int(samples * (2 * dimension * width + 2 * width * width) + 2 * width**3 / 3)

    def query(self, source: IOQuery, steps: int) -> int:
        encoded, reads = self._encode(source)
        width = self.weights.shape[1]
        controller = 2 * len(encoded) * width + 2 * width
        hidden = np.tanh(encoded @ self.weights + self.bias)
        self.last_program = None
        self._record(reads, 0, controller, reads)
        return int(hidden @ self.readout >= 0.0)

    def update(self, source: Any, target: int) -> None:
        self.update_ops = int(self.weights.shape[0])

    def state_bytes(self) -> int:
        return int(self.weights.nbytes + self.bias.nbytes + self.readout.nbytes)


class EnumerativeMDLVM(WholeIOBase):
    metadata = CandidateMetadata("enumerative_mdl_vm", "symbolic", "Complete noisy MDL search over two-state programs")

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.cache: dict[tuple[Any, ...], tuple[int, ...]] = {}

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    @staticmethod
    def _induce(key):
        ranked, operations = [], 0
        for code, program in enumerate(PROGRAMS):
            mismatches = 0
            for bits, target in key:
                output, used = run_program(program, bits)
                operations += used + 1
                mismatches += output != target
            ranked.append((mismatches, 1 + sum(program), code, program))
        return min(ranked)[3], operations

    def query(self, source: IOQuery, steps: int) -> int:
        key, support_reads = support_key(source.support)
        if key in self.cache:
            program, search_ops, evaluations = self.cache[key], 1, 0
        else:
            program, search_ops = self._induce(key)
            self.cache[key], evaluations = program, len(PROGRAMS)
        output, execution_ops, test_reads, _ = execute_tape(program, source.tape)
        self.last_program, self.last_program_evaluations = program, evaluations
        self._record(support_reads, search_ops, execution_ops, support_reads + test_reads)
        return output

    def update(self, source: TrainingExample, target: int) -> None:
        self.query(source.query, len(source.query.tape))
        self.update_ops = self.last_ops

    def state_bytes(self) -> int:
        items = sum(sum(len(bits) + 1 for bits, _ in key) + 8 for key in self.cache)
        return 128 + items


class LearnedLatentVM(EnumerativeMDLVM):
    metadata = CandidateMetadata("learned_latent_vm", "learned_vm", "Differentiable latent two-state VM with discrete repair")
    OPTIMIZATION_STEPS = 80

    def fit(self, facts: Iterable[TrainingExample], universe_size: int, max_depth: int) -> None:
        examples = tuple(facts)
        mean = (sum(item.target for item in examples) + 1) / (len(examples) + 2)
        bias = math.log(mean / (1.0 - mean))
        self.initial_logits = [0.12, -0.12, -0.08, 0.08, bias + 0.06, bias - 0.06, bias + 0.03, bias - 0.03]
        self.fit_ops = 2 * len(examples) + 8

    @staticmethod
    def _forward(logits, bits):
        probabilities = [1.0 / (1.0 + math.exp(-value)) for value in logits]
        state, state_grad, operations = 0.0, [0.0] * 8, 8
        output, output_grad = 0.5, [0.0] * 8
        for bit in bits:
            low, high = bit, 2 + bit
            out_low, out_high = 4 + bit, 6 + bit
            t0, t1 = probabilities[low], probabilities[high]
            o0, o1 = probabilities[out_low], probabilities[out_high]
            output = o0 + state * (o1 - o0)
            output_grad = [value * (o1 - o0) for value in state_grad]
            output_grad[out_low] += (1.0 - state) * o0 * (1.0 - o0)
            output_grad[out_high] += state * o1 * (1.0 - o1)
            next_grad = [value * (t1 - t0) for value in state_grad]
            next_grad[low] += (1.0 - state) * t0 * (1.0 - t0)
            next_grad[high] += state * t1 * (1.0 - t1)
            state, state_grad = t0 + state * (t1 - t0), next_grad
            operations += 72
        return output, output_grad, operations

    def _induce(self, key):
        logits, operations = list(self.initial_logits), 0
        for _ in range(self.OPTIMIZATION_STEPS):
            gradient = [0.0] * 8
            for bits, target in key:
                output, derivative, used = self._forward(logits, bits)
                residual = 2.0 * (output - target)
                for index in range(8):
                    gradient[index] += residual * derivative[index]
                operations += used + 17
            scale = 0.8 / len(key)
            for index in range(8):
                logits[index] = max(-8.0, min(8.0, logits[index] - scale * gradient[index]))
            operations += 24
        program = tuple(int(value >= 0.0) for value in logits)

        def score(item):
            nonlocal operations
            mismatches = 0
            for bits, target in key:
                output, used = run_program(item, bits)
                operations += used + 1
                mismatches += output != target
            return mismatches

        current = score(program)
        for _ in range(8):
            choices = []
            for bit in range(8):
                candidate = (*program[:bit], 1 - program[bit], *program[bit + 1 :])
                choices.append((score(candidate), bit, candidate))
            best, _, candidate = min(choices)
            if best >= current:
                break
            current, program = best, candidate
        return program, operations

    def state_bytes(self) -> int:
        return 64 + 8 * 8 + super().state_bytes()


class OracleLatentVM(WholeIOBase):
    metadata = CandidateMetadata("oracle_latent_vm", "oracle", "True two-state program with active-prefix execution")

    def fit(self, facts: Iterable[Any], universe_size: int, max_depth: int) -> None:
        self.fit_ops = 0

    def query(self, source: OracleInput, steps: int) -> int:
        output, operations, reads, _ = execute_tape(source.program, source.query.tape)
        self.last_program = source.program
        self._record(0, 0, operations, reads)
        return output

    def update(self, source: Any, target: int) -> None:
        self.update_ops = 1

    def state_bytes(self) -> int:
        return 72
