from nextai_autoresearch.candidates.verified_incumbent_program_vm_core import (
    VerifiedIncumbentProgramVM,
)
from nextai_autoresearch.whole_io_vm_core import (
    EnumerativeMDLVM,
    IOQuery,
    PROGRAMS,
    SUPPORT_INPUTS,
    Support,
    TrainingExample,
    run_program,
)


def _tape(bits, size):
    return (*bits, 2, *((0,) * (size - len(bits) - 1)))


def _query(program, *, size=16, seed=123) -> IOQuery:
    bits = (1, 0, 1, 1)
    support = tuple(
        Support(_tape(item, size), run_program(program, item)[0])
        for item in SUPPORT_INPUTS
    )
    return IOQuery(support, _tape(bits, size))


def test_meta_proposal_is_verified_before_exact_proof() -> None:
    program = PROGRAMS[173]
    query = _query(program)
    target = run_program(program, (1, 0, 1, 1))[0]
    candidate = VerifiedIncumbentProgramVM(7, "meta")
    exact = EnumerativeMDLVM(7)
    candidate.fit((TrainingExample(query, target),), 16, 6)
    exact.fit((), 16, 6)
    exact.query(query, 4)
    assert candidate.query(query, 4) == target
    assert candidate.last_proposal == exact.last_program
    assert candidate.last_proposal_verified
    assert candidate.last_program == exact.last_program


def test_wrong_frozen_proposal_falls_back_to_enumerative_optimum() -> None:
    program = PROGRAMS[173]
    query = _query(program)
    frozen = VerifiedIncumbentProgramVM(7, "frozen")
    exact = EnumerativeMDLVM(7)
    frozen.fit((), 16, 6)
    exact.fit((), 16, 6)
    assert frozen.query(query, 4) == exact.query(query, 4)
    assert frozen.last_proposal == (0,) * 8
    assert frozen.last_proposal_verified
    assert frozen.last_program == exact.last_program


def test_roles_freeze_one_branch_order_and_differ_only_by_source() -> None:
    roles = [VerifiedIncumbentProgramVM(1, source) for source in ("meta", "support", "frozen")]
    assert {role.proposal_source for role in roles} == {"meta", "support", "frozen"}
    assert all(role.BRANCH_ORDER == tuple(range(8)) for role in roles)
    assert all(role.VALUE_ORDER == ((0, 1),) * 8 for role in roles)


class Candidate(VerifiedIncumbentProgramVM):
    """Makes this candidate-bundle semantic fixture independently auditable."""
