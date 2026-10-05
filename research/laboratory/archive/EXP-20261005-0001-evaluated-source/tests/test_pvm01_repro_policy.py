from pathlib import Path

import pytest
import torch

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.candidates.pvm01_repro_core import Candidate, Reference


@pytest.mark.parametrize("raises", [False, True])
def test_fit_policy_restores_global_flags_even_after_failure(monkeypatch, raises):
    initial = (torch.are_deterministic_algorithms_enabled(), torch.is_deterministic_algorithms_warn_only_enabled())
    backend = (torch.backends.cuda.math_sdp_enabled(), torch.backends.cuda.flash_sdp_enabled(), torch.backends.cuda.mem_efficient_sdp_enabled(), torch.backends.cuda.cudnn_sdp_enabled())
    candidate = Candidate.__new__(Candidate)
    candidate.optimized_arm = "dense"
    def fake_fit(*args):
        assert torch.are_deterministic_algorithms_enabled()
        assert not torch.is_deterministic_algorithms_warn_only_enabled()
        assert torch.backends.cuda.math_sdp_enabled()
        assert not torch.backends.cuda.flash_sdp_enabled()
        assert not torch.backends.cuda.mem_efficient_sdp_enabled()
        if raises:
            raise RuntimeError("Fixture failure")
        return {"unchanged": True}
    monkeypatch.setattr(Reference, "fit", fake_fit)
    try:
        torch.use_deterministic_algorithms(False, warn_only=True)
        if raises:
            with pytest.raises(RuntimeError, match="Fixture failure"):
                candidate.fit(None, None, None, None)
        else:
            assert candidate.fit(None, None, None, None) == {"unchanged": True}
        assert not torch.are_deterministic_algorithms_enabled()
        assert torch.is_deterministic_algorithms_warn_only_enabled()
        assert backend == (torch.backends.cuda.math_sdp_enabled(), torch.backends.cuda.flash_sdp_enabled(), torch.backends.cuda.mem_efficient_sdp_enabled(), torch.backends.cuda.cudnn_sdp_enabled())
    finally:
        torch.use_deterministic_algorithms(initial[0], warn_only=initial[1])


def test_repro_adapter_remains_within_candidate_boundary():
    root = Path(__file__).resolve().parents[1]
    result = audit_candidate("pvm01_repro_core", load_config(root), root)
    assert result.ok, result.problems


def test_adapter_rejects_unrelated_arms_before_model_construction():
    with pytest.raises(ValueError):
        Candidate(1, "unrelated", {})
