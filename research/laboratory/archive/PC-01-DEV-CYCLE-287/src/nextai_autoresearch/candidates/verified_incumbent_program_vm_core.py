from __future__ import annotations

from typing import Any, Iterable

from nextai_autoresearch.candidates.amortized_constraint_order_vm_core import (
    AmortizedConstraintOrderVM,
)
from nextai_autoresearch.whole_io_vm_core import (
    IOQuery,
    TrainingExample,
    execute_tape,
    run_program,
    support_key,
)


class VerifiedIncumbentProgramVM(AmortizedConstraintOrderVM):
    """Fixed-order exact proof search; modes change only the initial proposal source."""

    BRANCH_ORDER = tuple(range(8))
    VALUE_ORDER = ((0, 1),) * 8

    def __init__(self, seed: int = 0, proposal_source: str = "meta") -> None:
        super().__init__(seed, "frozen")
        if proposal_source not in {"meta", "support", "frozen"}:
            raise ValueError("unknown incumbent proposal source")
        self.proposal_source = proposal_source
        self.prototypes: tuple[tuple[tuple[Any, ...], tuple[int, ...], int], ...] = ()
        self.last_proposal: tuple[int, ...] | None = None
        self.last_proposal_verified = False

    @staticmethod
    def _verified_score(key, program: tuple[int, ...]):
        if len(program) != 8 or any(value not in (0, 1) for value in program):
            raise ValueError("incumbent proposal is not an eight-bit program")
        mismatches = operations = 0
        for bits, target in key:
            output, used = run_program(program, bits)
            operations += used + 1
            mismatches += output != target
        code = sum(value << bit for bit, value in enumerate(program))
        return (mismatches, 1 + sum(program), code, program), operations

    def fit(self, facts: Iterable[TrainingExample], universe_size: int, max_depth: int) -> None:
        if self.proposal_source != "meta":
            self.fit_ops = 0
            return
        unique: dict[tuple[Any, ...], None] = {}
        operations = 0
        for item in facts:
            key, reads = support_key(item.query.support)
            operations += reads + len(key)
            unique.setdefault(key, None)
        prototypes = []
        for rank, key in enumerate(unique):
            program, used = self._enumerate(key)
            operations += used + len(key)
            prototypes.append((key, program, rank))
        self.prototypes = tuple(prototypes)
        self.fit_ops = operations

    def _meta_proposal(self, key):
        if not self.prototypes:
            return (0,) * 8, 1
        best = None
        operations = 0
        for prototype_key, program, rank in self.prototypes:
            labels = dict(prototype_key)
            disagreement = missing = 0
            for bits, target in key:
                operations += 2
                if bits not in labels:
                    missing += 1
                else:
                    disagreement += labels[bits] != target
            record = (disagreement, missing, rank, program)
            best = record if best is None or record < best else best
        return best[3], operations

    def _support_proposal(self, key):
        program = (0,) * 8
        best, operations = self._verified_score(key, program)
        for bit in self.BRANCH_ORDER:
            candidate = (*program[:bit], 1 - program[bit], *program[bit + 1:])
            score, used = self._verified_score(key, candidate)
            operations += used + 1
            if score[:3] < best[:3]:
                program, best = candidate, score
        return program, operations

    def _proposal(self, key):
        if self.proposal_source == "meta":
            return self._meta_proposal(key)
        if self.proposal_source == "support":
            return self._support_proposal(key)
        return (0,) * 8, 1

    def _induce(self, key):
        proposal, controller_ops = self._proposal(key)
        best, used = self._verified_score(key, proposal)
        controller_ops += used
        self.last_proposal = proposal
        self.last_proposal_verified = True
        nodes = leaves = 0

        def visit(depth: int, partial: dict[int, int]) -> None:
            nonlocal best, nodes, leaves, controller_ops
            nodes += 1
            bound, bound_ops = self._bound(key, partial, best)
            controller_ops += bound_ops + 1
            if bound >= best[:3]:
                return
            if depth == 8:
                program = tuple(partial[bit] for bit in self.BRANCH_ORDER)
                leaves += 1
                best = (*bound, program)
                return
            bit = self.BRANCH_ORDER[depth]
            for value in self.VALUE_ORDER[bit]:
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
        self._record(support_reads, nodes, controller_ops + execution_ops,
                     support_reads + test_reads)
        return output

    def state_bytes(self) -> int:
        prototype_bytes = sum(
            8 + sum(len(bits) + 2 for bits, _ in key)
            for key, _, _ in self.prototypes
        )
        return super().state_bytes() + prototype_bytes


class Candidate(VerifiedIncumbentProgramVM):
    """Audit-visible default; scored roles use explicit proposal-source wrappers."""
