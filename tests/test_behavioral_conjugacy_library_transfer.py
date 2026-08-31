import importlib

import pytest

from nextai_autoresearch.benchmarks.behavioral_conjugacy_library_transfer_v1 import (
    BASE, cycle_type, execute, make_tasks, make_world, relational_fingerprints,
)


def test_roles_are_unary_ambiguous_but_relationally_identifiable() -> None:
    public, _, _, _ = make_world(8, 1103)
    assert len({cycle_type(table) for _, table in public.target_traces}) == 1
    assert len(set(relational_fingerprints(public.target_traces).values())) == len(BASE)


def test_relational_roles_survive_domain_conjugacy_and_token_permutation() -> None:
    public, _, _, _ = make_world(8, 1103)
    reference = set(relational_fingerprints(public.training[0].traces).values())
    assert all(set(relational_fingerprints(domain.traces).values()) == reference
               for domain in (*public.training[1:], type("Target", (), {"traces": public.target_traces})()))


def test_target_programs_are_executable_and_trace_order_is_irrelevant() -> None:
    _, _, tables, roles = make_world(8, 1103)
    for task, near, _, _, program in make_tasks(tables, roles, 6, 1103, 8):
        expected = execute(program, tables)
        assert tuple(target for _, target in sorted(task.examples)) == expected
        assert sorted(task.examples) == sorted(near.examples)


def test_candidate_bundle_when_present() -> None:
    try:
        core = importlib.import_module("nextai_autoresearch.candidates.conjugacy_library_core")
    except ModuleNotFoundError:
        pytest.skip("candidate bundle is added only after protocol-v2 preregistration")
    public, oracle, tables, roles = make_world(8, 1103)
    tasks = make_tasks(tables, roles, 6, 1103, 2)
    for mode in ("primitive", "memo", "relational", "bayesian", "learned", "oracle"):
        candidate = core.ConjugacyCandidate(1103, mode)
        candidate.fit(oracle if mode == "oracle" else public, 8, 6)
        source = tasks[0][2] if mode == "oracle" else tasks[0][0]
        assert execute(candidate.query(source, 6), tables) == execute(tasks[0][4], tables)
