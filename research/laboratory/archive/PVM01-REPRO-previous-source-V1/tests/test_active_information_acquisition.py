from nextai_autoresearch.active_acquisition_core import (
    CertifiedDecisionTree, CodebookUpdate, EntropyGreedyProbe, LearnedValueProbePolicy,
    PassiveObserveAll, ProbeBatch, ProbeSession,
)
from nextai_autoresearch.benchmarks.active_information_acquisition_v1 import make_codebook


def batch(codebook, labels):
    return ProbeBatch(tuple(ProbeSession(codebook.rows[label]) for label in labels))


def test_codebook_is_unique_and_contains_balanced_probes() -> None:
    codebook = make_codebook(8, 1103)
    assert len(set(codebook.rows)) == 8
    assert sum(sum(row[column] for row in codebook.rows) == 4 for column in range(len(codebook.rows[0]))) >= 3


def test_exact_active_policies_reach_the_log_bound() -> None:
    codebook = make_codebook(8, 1103)
    for policy in (EntropyGreedyProbe(), CertifiedDecisionTree(), LearnedValueProbePolicy()):
        policy.fit(codebook, 8, 1)
        assert policy.query(batch(codebook, range(8)), 8) == tuple(range(8))
        assert policy.last_probe_count == 8 * 3


def test_passive_control_reads_every_column() -> None:
    codebook = make_codebook(8, 1103)
    policy = PassiveObserveAll()
    policy.fit(codebook, 8, 1)
    assert policy.query(batch(codebook, (3,)), 1) == (3,)
    assert policy.last_probe_count == len(codebook.rows[0])


def test_local_swap_updates_without_forgetting() -> None:
    codebook = make_codebook(8, 1103)
    policy = LearnedValueProbePolicy()
    policy.fit(codebook, 8, 1)
    rows = list(codebook.rows)
    rows[0], rows[1] = rows[1], rows[0]
    policy.update(CodebookUpdate(((0, rows[0]), (1, rows[1]))))
    updated = type(codebook)(tuple(rows))
    assert policy.query(batch(updated, (0, 7)), 2) == (0, 7)


def test_classical_certificate_dominates_learned_accounting() -> None:
    codebook = make_codebook(32, 1103)
    classical, learned = CertifiedDecisionTree(), LearnedValueProbePolicy()
    classical.fit(codebook, 32, 1)
    learned.fit(codebook, 32, 1)
    assert classical.fit_ops < learned.fit_ops
    assert classical.state_bytes() < learned.state_bytes()
    classical.query(batch(codebook, (5,)), 1)
    learned.query(batch(codebook, (5,)), 1)
    assert classical.last_ops < learned.last_ops

