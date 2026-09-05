from __future__ import annotations

import math

import pytest

from nextai_autoresearch.candidates.masked_baselines import CTWByteModel, PPMDModel
from nextai_autoresearch.masked_refinement_contract import (
    MASK,
    ByteFile,
    MaskedQuery,
    MaskedTraining,
    PrivilegedMaskedQuery,
)


def _training(data: tuple[int, ...]) -> MaskedTraining:
    return MaskedTraining((ByteFile(1, data),), (), len(data))


def _candidate(name: str, data: tuple[int, ...]):
    module = __import__(f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"])
    candidate = module.Candidate(7)
    candidate.fit(_training(data), 8, 6)
    return candidate


def test_uniform_masked_byte_reference() -> None:
    candidate = _candidate("uniform_masked_byte", (1, 2, 3))
    row = candidate.query(MaskedQuery(1, (4, MASK, 5), (1,), 0, 1), 1)[0]
    assert row == [1 / 256] * 256


def test_empirical_unigram_masked_byte_reference() -> None:
    candidate = _candidate("empirical_unigram_masked_byte", (1, 1, 1, 2))
    row = candidate.query(MaskedQuery(1, (4, MASK, 5), (1,), 0, 1), 1)[0]
    assert row[1] > row[2] > row[3]


def _ppm_reference(model) -> None:
    row = model.distribution((7, 1))
    assert row[2] == pytest.approx(0.5, abs=1e-12)
    assert row[3] == pytest.approx(0.25, abs=1e-12)
    assert sum(row) == pytest.approx(1.0, abs=1e-12)


def test_ppm_d_order5_reference_backoff_and_full_exclusion() -> None:
    model = PPMDModel(5)
    for data in ((7, 1, 2), (8, 1, 3)):
        history: tuple[int, ...] = ()
        for target in data:
            model.update(history, target)
            history = (*history, target)
    _ppm_reference(model)


def _log_kt(counts: tuple[int, ...]) -> float:
    total = sum(counts)
    return (
        math.lgamma(128) - math.lgamma(total + 128)
        + sum(math.lgamma(count + 0.5) - math.lgamma(0.5)
              for count in counts if count)
    )


def test_ctw_byte_depth2_reference_recursive_mixture() -> None:
    # A depth-1 instance makes the root/child recursion hand-checkable.
    data = (0, 0, 1, 2, 0, 2)
    model = CTWByteModel(depth=1)
    model.fit_file(data)
    model.finalize()
    root_log_kt = _log_kt((2, 1, 2))
    child_log_kt = _log_kt((1, 1, 1)) + _log_kt((0, 0, 1)) + _log_kt((1,))
    maximum = max(root_log_kt, child_log_kt)
    normalizer = maximum + math.log(
        math.exp(root_log_kt - maximum) + math.exp(child_log_kt - maximum)
    )
    root_weight = math.exp(root_log_kt - normalizer)
    expected = root_weight * (1.5 / 133) + (1 - root_weight) * (1.5 / 131)
    row = model.distribution((0,))
    assert row[1] == pytest.approx(expected, rel=1e-12)
    assert row[1] != pytest.approx(1.5 / 131, rel=1e-6)
    assert sum(row) == pytest.approx(1.0, abs=1e-12)


def test_first_order_markov_cannot_claim_ppm_or_ctw_conformance() -> None:
    class FirstOrderOnly:
        def distribution(self, history):
            row = [0.0] * 256
            row[2] = row[3] = 0.5
            return row

    with pytest.raises(AssertionError):
        _ppm_reference(FirstOrderOnly())


def test_dense_autoregressive_masked_byte_reference() -> None:
    candidate = _candidate("dense_autoregressive_masked_byte", (1, 2) * 100)
    first = candidate.query(MaskedQuery(1, (1, MASK, 9), (1,), 0, 1), 1)[0]
    second = candidate.query(MaskedQuery(1, (2, MASK, 9), (1,), 0, 1), 1)[0]
    assert first[2] > second[2]


def test_bidirectional_markov_masked_byte_reference() -> None:
    candidate = _candidate("bidirectional_markov_masked_byte", (1, 2, 3) * 100)
    row = candidate.query(MaskedQuery(1, (1, MASK, 3), (1,), 0, 1), 1)[0]
    assert row[2] == max(row)


def test_parallel_markov_bp_matches_exact_first_order_reference() -> None:
    exact = _candidate("bidirectional_markov_masked_byte", (1, 2, 3) * 100)
    parallel = _candidate("parallel_markov_bp_masked_byte", (1, 2, 3) * 100)
    query = MaskedQuery(1, (1, MASK, MASK, 3), (1, 2), 0, 1)
    for expected, observed in zip(exact.query(query, 1), parallel.query(query, 1)):
        assert observed == pytest.approx(expected, rel=2e-5, abs=1e-9)


def test_oracle_conditional_masked_byte_reference() -> None:
    candidate = _candidate("oracle_conditional_masked_byte", ())
    public = MaskedQuery(1, (9, MASK, 8), (1,), 0, 1)
    row = candidate.query(PrivilegedMaskedQuery(public, (7,)), 1)[0]
    assert row[7] == 1.0 and sum(row) == 1.0
