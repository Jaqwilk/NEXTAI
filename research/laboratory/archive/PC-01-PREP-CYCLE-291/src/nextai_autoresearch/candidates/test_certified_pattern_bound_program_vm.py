from nextai_autoresearch.candidates.certified_pattern_bound_program_vm_core import (
    CertifiedPatternBoundProgramVM,
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


def _query(program, size=16):
    support = tuple(
        Support(_tape(bits, size), run_program(program, bits)[0])
        for bits in SUPPORT_INPUTS
    )
    bits = (1, 0, 1, 1)
    return IOQuery(support, _tape(bits, size))


def test_joint_pair_bound_is_strict_on_repeated_zero_path() -> None:
    candidate = CertifiedPatternBoundProgramVM(1, "frozen")
    pair = ((0, 0), (0, 0, 0))
    key = (((0, 0), 0), ((0, 0, 0), 1))
    base, _ = candidate._bound(key, {0: 0}, None)
    joint, _ = candidate._certified_bound(key, pair, {0: 0}, None)
    assert base[0] == 0
    assert joint[0] == 1


def test_underapproximated_pattern_mask_fails_certificate() -> None:
    pair = ((0, 0), (0, 0, 0))
    valid, _ = CertifiedPatternBoundProgramVM._check_certificate(
        pair, {0: 0}, frozenset({(0, 0)}), 128
    )
    assert not valid


def test_all_sources_prove_the_same_enumerative_optimum() -> None:
    program = PROGRAMS[173]
    query = _query(program)
    target = run_program(program, (1, 0, 1, 1))[0]
    exact = EnumerativeMDLVM(7)
    exact.fit((), 16, 6)
    exact.query(query, 4)
    training = (TrainingExample(query, target),)
    for source in ("meta", "support", "frozen"):
        candidate = CertifiedPatternBoundProgramVM(7, source)
        candidate.fit(training, 16, 6)
        candidate.query(query, 4)
        assert candidate.last_program == exact.last_program
        assert candidate.last_certificate_rejections == 0


def test_roles_share_constants_and_differ_only_by_pattern_source() -> None:
    roles = [CertifiedPatternBoundProgramVM(1, source) for source in ("meta", "support", "frozen")]
    assert {role.pattern_source for role in roles} == {"meta", "support", "frozen"}
    assert all(role.PATTERN_COUNT == 1 for role in roles)
    assert all(role.BRANCH_ORDER == tuple(range(8)) for role in roles)
    assert all(role.VALUE_ORDER == ((0, 1),) * 8 for role in roles)


class Candidate(CertifiedPatternBoundProgramVM):
    """Makes this candidate-bundle semantic fixture independently auditable."""
