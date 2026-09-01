from __future__ import annotations

import numpy as np
import torch

from nextai_autoresearch.candidates.selective_diagonal_state_space_byte_core_v1 import SelectiveDiagonalStateSpaceByte
from nextai_autoresearch.candidates.selective_diagonal_state_space_byte_v1 import Candidate as Selective
from nextai_autoresearch.candidates.source_identical_fixed_selection_state_space_byte_v1 import Candidate as Fixed
from nextai_autoresearch.candidates.source_identical_recurrence_disabled_state_space_byte_v1 import Candidate as Disabled
from nextai_autoresearch.repository_sequence_contract import ByteContext, ByteFile, CompressionTraining


def _training(data: tuple[int, ...]) -> CompressionTraining:
    return CompressionTraining((ByteFile(11, data),), (), len(data))


def test_roles_share_one_core_and_byte_invariant_initialization() -> None:
    roles = [Selective(), Fixed(), Disabled()]
    assert all(isinstance(role, SelectiveDiagonalStateSpaceByte) for role in roles)
    for role in roles:
        assert torch.equal(role.input_map, role.input_map[:1].repeat(256, 1))
        assert torch.count_nonzero(role.gate_map) == 0
        assert torch.count_nonzero(role.readout) == 0
        assert torch.count_nonzero(role.bias) == 0
    assert [role.SELECTION for role in roles] == ["input", "fixed", "disabled"]


def test_fit_learns_input_selection_and_causal_ablations_are_distinct() -> None:
    data = tuple([1, 2, 1, 3] * 80)
    main, fixed, disabled = Selective(), Fixed(), Disabled()
    for role in (main, fixed, disabled):
        role.fit(_training(data), 1, 16)
    assert float(main.gate_map.abs().max()) > 1e-4
    zero, one = torch.zeros(16), torch.ones(16)
    assert not torch.allclose(main._transition(zero, 1), main._transition(zero, 2))
    fixed_retention = torch.sigmoid(fixed.decay_logit)
    assert torch.allclose(fixed._transition(one, 1) - fixed._transition(zero, 1), fixed_retention)
    assert torch.allclose(disabled._transition(zero, 1), disabled._transition(one, 1))
    assert main._transition_ops() > fixed._transition_ops() > disabled._transition_ops()


def test_byte_relabeling_equivariance_after_training() -> None:
    data = tuple([1, 2, 1, 3] * 80)
    permutation = list(range(256))
    permutation[1], permutation[2] = 2, 1
    left, right = Selective(), Selective()
    left.fit(_training(data), 1, 16)
    right.fit(_training(tuple(permutation[value] for value in data)), 1, 16)
    p_left = np.asarray(left.query(ByteContext(21, (1, 2, 1, 3)), 1))
    p_right = np.asarray(right.query(ByteContext(22, tuple(permutation[x] for x in (1, 2, 1, 3))), 1))
    assert np.allclose(p_left, p_right[permutation], atol=2e-6, rtol=2e-6)


def test_predict_then_reveal_is_slot_local_and_slow_weights_freeze() -> None:
    candidate = Selective()
    candidate.fit(_training(tuple([4, 5, 4, 6] * 80)), 1, 16)
    frozen = [parameter.clone() for parameter in candidate.parameters]
    context = ByteContext(31, (4, 5, 4))
    before = candidate.query(context, 1)
    candidate.update(context, 6)
    after = candidate.query(context, 1)
    other = candidate.query(ByteContext(32, (4, 5, 4)), 1)
    assert not np.allclose(before, after)
    assert np.allclose(before, other)
    assert all(torch.equal(old, new) for old, new in zip(frozen, candidate.parameters))
    assert candidate.update_ops > 0 and candidate.last_update_bytes > 0


def test_bounded_sequence_smoke_is_finite_and_accounted() -> None:
    data = tuple(range(256)) * 32
    training = _training(data)
    candidate = Selective(1103)
    candidate.fit(training, 8, 16)
    probabilities = np.asarray(candidate.query(ByteContext(41, training.train_files[0].data[-16:]), 1))
    assert np.isfinite(probabilities).all() and np.all(probabilities >= 0)
    assert abs(float(probabilities.sum()) - 1.0) < 1e-5
    assert candidate.fit_ops > 0 and candidate.last_ops > 0
    assert candidate.state_bytes() < 4_194_304


class Candidate(SelectiveDiagonalStateSpaceByte):
    """Makes the candidate-bundle semantic fixture independently auditable."""
