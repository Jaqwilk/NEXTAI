from __future__ import annotations

import importlib
import subprocess
import types

import numpy as np
import pytest

from nextai_autoresearch.benchmarks import wt01_causal_factorial_diagnostic_v1 as diagnostic
from nextai_autoresearch.wt01_factorial_core import (
    FactorialCandidate, VAR2RLSBoundCandidate,
)
from nextai_autoresearch.utils import project_root
from nextai_autoresearch.wt_prequential_contract import (
    WTEpisode, WTQuery, WTReveal, WTTraining,
)


def _fixture():
    rng = np.random.default_rng(4409)
    episodes = []
    for _ in range(4):
        history = rng.normal(size=(8, 10))
        target = rng.normal(size=(6, 10))
        episodes.append(WTEpisode(tuple(map(tuple, history)), float(rng.normal()), tuple(map(tuple, target))))
    training = WTTraining(tuple(episodes), 0, 0)
    history = tuple(map(tuple, rng.normal(size=(8, 10))))
    query = WTQuery(1701, history, 0.25, 16)
    reveal = WTReveal(1701, history, 0.25, tuple(map(tuple, rng.normal(size=(16, 10)))))
    return training, query, reveal


def _historical_candidate():
    source = subprocess.check_output([
        "git", "show",
        "49525156586e765c07f96e2f41ea17c709a3debb:src/nextai_autoresearch/candidates/wt_candidate_under_test.py",
    ], cwd=project_root())
    assert __import__("hashlib").sha256(source).hexdigest() == (
        "4471f2a999f9432e9d2e6fb56d309ebe7af52cca6dff246ab1b439b38f035104"
    )
    module = types.ModuleType("wt01_exact_historical_git_candidate")
    exec(compile(source, "4952515:wt_candidate_under_test.py", "exec"), module.__dict__)
    return module.Candidate(17)


def test_r1_u1_c1_is_exact_historical_source_on_synthetic_fixture():
    training, query, reveal = _fixture()
    historical, current = _historical_candidate(), FactorialCandidate(17)
    historical.fit(training, 4, 96)
    current.fit(training, 4, 96)
    assert np.array_equal(historical._weights, current._weights)
    assert np.array_equal(historical._precision, current._precision)
    assert historical.query(query, 16) == current.query(query, 16)
    assert (historical.fit_ops, historical.last_ops, historical.last_bytes_touched,
            historical.state_bytes()) == (current.fit_ops, current.last_ops,
                                            current.last_bytes_touched, current.state_bytes())
    historical.update(reveal)
    current.update(reveal)
    for old, new in zip(historical._slots[1701], current._slots[1701]):
        assert np.array_equal(old, new)
    assert (historical.update_ops, historical.last_update_bytes, historical.state_bytes()) == (
        current.update_ops, current.last_update_bytes, current.state_bytes()
    )


def test_classical_var2_arx_is_numerically_equivalent_to_historical_cell():
    training, query, reveal = _fixture()
    residual, classical = FactorialCandidate(17), VAR2RLSBoundCandidate(17)
    residual.fit(training, 4, 96)
    classical.fit(training, 4, 96)
    assert np.allclose(residual.query(query, 16), classical.query(query, 16), rtol=1e-12, atol=1e-12)
    residual.update(reveal)
    classical.update(reveal)
    for left, right in zip(residual._slots[1701], classical._slots[1701]):
        assert np.array_equal(left, right)


def test_all_eight_wrappers_share_one_core_and_only_switch_three_factors():
    realized = {}
    for r in (0, 1):
        for u in (0, 1):
            for c in (0, 1):
                name = f"wt01_r{r}_u{u}_c{c}_v1"
                candidate = importlib.import_module(
                    f"nextai_autoresearch.candidates.{name}"
                ).Candidate(1)
                assert isinstance(candidate, FactorialCandidate)
                realized[name] = candidate.factors
    assert set(realized.values()) == set(
        (bool(r), bool(u), bool(c)) for r in (0, 1) for u in (0, 1) for c in (0, 1)
    )


def test_r0_holds_one_step_prediction_and_u0_never_changes_local_state():
    training, query, reveal = _fixture()
    cls = importlib.import_module(
        "nextai_autoresearch.candidates.wt01_r0_u0_c1_v1"
    ).Candidate
    candidate = cls(17)
    candidate.fit(training, 4, 96)
    prediction = np.asarray(candidate.query(query, 16))
    assert np.array_equal(prediction, np.repeat(prediction[:1], 16, axis=0))
    before = tuple(value.copy() for value in candidate._slots[1701])
    candidate.update(reveal)
    assert candidate.update_ops == candidate.last_update_bytes == 0.0
    for left, right in zip(before, candidate._slots[1701]):
        assert np.array_equal(left, right)


def test_slot_updates_are_isolated_and_unclipped_nonfinite_fails_closed():
    training, query, reveal = _fixture()
    candidate = FactorialCandidate(17)
    candidate.fit(training, 4, 96)
    other = WTQuery(1802, query.history, query.control, query.horizon)
    candidate.query(query, 16)
    candidate.query(other, 16)
    other_before = tuple(value.copy() for value in candidate._slots[1802])
    candidate.update(reveal)
    for before, after in zip(other_before, candidate._slots[1802]):
        assert np.array_equal(before, after)

    unclipped = importlib.import_module(
        "nextai_autoresearch.candidates.wt01_r1_u0_c0_v1"
    ).Candidate(17)
    unclipped.fit(training, 4, 96)
    unclipped._weights.fill(1e308)
    with pytest.raises(ValueError, match="diverged|non-finite"):
        unclipped.query(query, 16)


def test_diagnostic_identity_is_visible_not_hidden_and_threshold_is_exact():
    assert diagnostic.BENCHMARK_VERSION == "wt01_causal_factorial_diagnostic_v1"
    assert diagnostic.VISIBLE_DIAGNOSTIC_SEEDS == (8, 9)
    assert diagnostic.CAUSAL_ATTRIBUTION_THRESHOLD == 0.03343253453162794
    assert diagnostic.PRIMARY_CONTRAST == ("wt01_r0_u1_c1_v1", "wt01_r1_u1_c1_v1")
    assert len(diagnostic.FACTORIAL_CANDIDATES) == 8
