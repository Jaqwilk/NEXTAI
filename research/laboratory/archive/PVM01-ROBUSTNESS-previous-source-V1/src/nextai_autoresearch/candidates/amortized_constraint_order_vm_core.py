from __future__ import annotations

from typing import Any, Iterable

from nextai_autoresearch.whole_io_vm_core import (
    IOQuery,
    PROGRAMS,
    TrainingExample,
    WholeIOBase,
    execute_tape,
    run_program,
    support_key,
)


class AmortizedConstraintOrderVM(WholeIOBase):
    """Complete MDL search; modes change traversal order only."""

    def __init__(self, seed: int = 0, mode: str = "meta") -> None:
        super().__init__(seed)
        self.mode = mode
        self.cache: dict[tuple[Any, ...], tuple[int, ...]] = {}
        self.bit_order = tuple(range(8))
        self.value_order = ((0, 1),) * 8

    @staticmethod
    def _possible_outputs(bits: tuple[int, ...], partial: dict[int, int]) -> tuple[set[int], int]:
        states, operations = {(0, 0)}, 0
        for symbol in bits:
            following = set()
            for state, _ in states:
                index = 2 * state + symbol
                transitions = (partial[index],) if index in partial else (0, 1)
                outputs = (partial[4 + index],) if 4 + index in partial else (0, 1)
                for transition in transitions:
                    for output in outputs:
                        following.add((transition, output))
                        operations += 1
            states = following
        return {output for _, output in states}, operations

    @classmethod
    def _single_bit_stats(cls, key, bit: int, value: int) -> tuple[int, int, int]:
        wrong = correct = operations = 0
        for bits, target in key:
            outputs, used = cls._possible_outputs(bits, {bit: value})
            operations += used
            wrong += target not in outputs
            correct += outputs == {target}
        return wrong, correct, operations

    @staticmethod
    def _enumerate(key) -> tuple[tuple[int, ...], int]:
        best, operations = None, 0
        for code, program in enumerate(PROGRAMS):
            mismatches = 0
            for bits, target in key:
                output, used = run_program(program, bits)
                operations += used + 1
                mismatches += output != target
            score = (mismatches, 1 + sum(program), code, program)
            best = score if best is None or score < best else best
        return best[3], operations

    def fit(self, facts: Iterable[TrainingExample], universe_size: int, max_depth: int) -> None:
        if self.mode != "meta":
            self.fit_ops = 0
            return
        unique, operations = {}, 0
        for item in facts:
            key, reads = support_key(item.query.support)
            operations += reads
            unique[key] = None
        programs = []
        utilities = [0.0] * 8
        for key in unique:
            program, used = self._enumerate(key)
            operations += used
            programs.append(program)
            for bit, value in enumerate(program):
                _, correct, used = self._single_bit_stats(key, bit, value)
                operations += used
                utilities[bit] += correct
        count = max(1, len(programs))
        probabilities = [(1 + sum(program[bit] for program in programs)) / (count + 2) for bit in range(8)]
        means = [value / count for value in utilities]
        self.bit_order = tuple(sorted(range(8), key=lambda bit: (-means[bit], -4 * probabilities[bit] * (1 - probabilities[bit]), bit)))
        self.value_order = tuple((1, 0) if probabilities[bit] > 0.5 else (0, 1) for bit in range(8))
        self.fit_ops = operations + 8 * count

    def _support_order(self, key) -> tuple[tuple[int, ...], tuple[tuple[int, int], ...], int]:
        if self.mode == "meta":
            return self.bit_order, self.value_order, 0
        if self.mode == "frozen":
            return tuple(range(8)), ((0, 1),) * 8, 0
        records, operations = [], 0
        for bit in range(8):
            zero = self._single_bit_stats(key, bit, 0)
            one = self._single_bit_stats(key, bit, 1)
            operations += zero[2] + one[2]
            values = (0, 1) if (zero[0], -zero[1], 0) <= (one[0], -one[1], 1) else (1, 0)
            records.append((abs(zero[0] - one[0]), max(zero[1], one[1]), bit, values))
        records.sort(key=lambda row: (-row[0], -row[1], row[2]))
        order = tuple(row[2] for row in records)
        values_by_bit = {row[2]: row[3] for row in records}
        return order, tuple(values_by_bit[bit] for bit in range(8)), operations

    @classmethod
    def _bound(cls, key, partial: dict[int, int], best) -> tuple[tuple[int, int, int], int]:
        mismatches = operations = 0
        for bits, target in key:
            outputs, used = cls._possible_outputs(bits, partial)
            operations += used + 1
            mismatches += target not in outputs
            if best is not None and mismatches > best[0]:
                break
        ones = sum(partial.values())
        code = sum(value << bit for bit, value in partial.items())
        return (mismatches, 1 + ones, code), operations

    def _induce(self, key) -> tuple[tuple[int, ...], int, int, int]:
        order, values, controller_ops = self._support_order(key)
        best = None
        nodes = leaves = 0

        def visit(depth: int, partial: dict[int, int]) -> None:
            nonlocal best, nodes, leaves, controller_ops
            nodes += 1
            bound, used = self._bound(key, partial, best)
            controller_ops += used + 1
            if best is not None and bound >= best[:3]:
                return
            if depth == 8:
                program = tuple(partial[bit] for bit in range(8))
                leaves += 1
                best = (*bound, program)
                return
            bit = order[depth]
            for value in values[bit]:
                partial[bit] = value
                visit(depth + 1, partial)
            partial.pop(bit)

        visit(0, {})
        return best[3], nodes, controller_ops, leaves

    def query(self, source: IOQuery, steps: int) -> int:
        key, support_reads = support_key(source.support)
        if key in self.cache:
            program, nodes, controller_ops, leaves = self.cache[key], 1, 1, 0
        else:
            program, nodes, controller_ops, leaves = self._induce(key)
            self.cache[key] = program
        output, execution_ops, test_reads, _ = execute_tape(program, source.tape)
        self.last_program = program
        self.last_program_evaluations = leaves
        self.last_nodes = nodes
        self._record(support_reads, nodes, controller_ops + execution_ops, support_reads + test_reads)
        return output

    def update(self, source: TrainingExample, target: int) -> None:
        self.query(source.query, len(source.query.tape))
        self.update_ops = self.last_ops

    def state_bytes(self) -> int:
        cache_bytes = sum(sum(len(bits) + 1 for bits, _ in key) + 8 for key in self.cache)
        return 256 + 8 * 24 + cache_bytes


class Candidate(AmortizedConstraintOrderVM):
    """Audit-visible default; scored roles use the explicit thin wrappers."""
