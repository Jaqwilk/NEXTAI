from __future__ import annotations

from nextai_autoresearch.candidates.contextual_chow_liu import Candidate as ChowLiu
from nextai_autoresearch.candidates.cssr_state_reconstructor import Candidate as CSSR
from nextai_autoresearch.candidates.empirical_autoregressive_table import Candidate as Autoregressive
from nextai_autoresearch.candidates.empirical_joint_table import Candidate as Joint
from nextai_autoresearch.candidates.exact_finite_state_propagation import Candidate as ExactLocal
from nextai_autoresearch.candidates.oracle_conjugacy_library import Candidate as OracleProgram
from nextai_autoresearch.candidates.oracle_context_spn import Candidate as OracleProbability
from nextai_autoresearch.candidates.oracle_local_state_rule import Candidate as OracleLocal
from nextai_autoresearch.candidates.oracle_predictive_state import Candidate as OraclePredictive
from nextai_autoresearch.candidates.relational_graph_mdl_library import Candidate as RelationalProgram


def _suite(name: str):
    module = __import__(f"nextai_autoresearch.candidates.{name}", fromlist=["Candidate"])
    return module.Candidate(7)


def _assert_shared_native_controls(candidate, probability_type) -> None:
    assert isinstance(candidate._model("probabilistic"), probability_type)
    assert isinstance(candidate._model("predictive"), CSSR)
    assert isinstance(candidate._model("local"), ExactLocal)
    assert isinstance(candidate._model("program"), RelationalProgram)


def test_specialist_contextual_chow_liu_suite_v2_semantics() -> None:
    candidate = _suite("specialist_contextual_chow_liu_suite_v2")
    assert candidate.probability_mode == "contextual"
    _assert_shared_native_controls(candidate, ChowLiu)


def test_specialist_empirical_joint_suite_v2_semantics() -> None:
    candidate = _suite("specialist_empirical_joint_suite_v2")
    assert candidate.probability_mode == "joint"
    _assert_shared_native_controls(candidate, Joint)


def test_specialist_autoregressive_suite_v2_semantics() -> None:
    candidate = _suite("specialist_autoregressive_suite_v2")
    assert candidate.probability_mode == "autoregressive"
    _assert_shared_native_controls(candidate, Autoregressive)


def test_oracle_cross_family_suite_v2_semantics() -> None:
    candidate = _suite("oracle_cross_family_suite_v2")
    assert candidate.probability_mode == "oracle"
    assert isinstance(candidate._model("probabilistic"), OracleProbability)
    assert isinstance(candidate._model("predictive"), OraclePredictive)
    assert isinstance(candidate._model("local"), OracleLocal)
    assert isinstance(candidate._model("program"), OracleProgram)
