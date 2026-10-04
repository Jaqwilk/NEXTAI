from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from nextai_autoresearch.utils import project_root


SHARED = "shared_recurrent_predictive_state"
INDEPENDENT = "independent_recurrent_predictive_state"


def _paths() -> tuple[Path, Path]:
    root = project_root() / "src" / "nextai_autoresearch" / "candidates"
    return root / f"{SHARED}.py", root / f"{INDEPENDENT}.py"


def test_v3_future_ablation_is_source_identical_and_family_blind() -> None:
    paths = _paths()
    if not all(path.is_file() for path in paths):
        pytest.skip("v3 candidates are intentionally implemented only after preregistration")
    shared = importlib.import_module(f"nextai_autoresearch.candidates.{SHARED}").Candidate
    independent = importlib.import_module(
        f"nextai_autoresearch.candidates.{INDEPENDENT}"
    ).Candidate
    assert shared.__bases__ == independent.__bases__
    assert shared.__bases__[0].__name__ == "RecurrentPredictiveStateLearner"
    shared_instance, independent_instance = shared(7), independent(7)
    assert shared_instance.mode == "shared"
    assert independent_instance.mode == "independent"
    assert shared_instance.state_width == independent_instance.state_width == 32
    for path in paths:
        source = path.read_text(encoding="utf-8").lower()
        assert all(value not in source for value in (
            "probabilistic", "predictive", "local", "program", "nativeworld"
        ))
