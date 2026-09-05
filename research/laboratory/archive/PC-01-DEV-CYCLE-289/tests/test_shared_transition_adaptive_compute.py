import numpy as np

from nextai_autoresearch.adaptive_transition_core import (
    ACTPonderHalt, FixedMaxSharedTransition, FixedShortSharedTransition,
    LearnedAdaptiveHalt, ResidualSharedTransition, TransitionGateHalt,
)
from nextai_autoresearch.benchmarks.shared_transition_adaptive_compute_v2 import (
    make_dataset, make_tasks,
)


def fitted(model, dimensions=8):
    model.fit(make_dataset(dimensions, 1103), dimensions, 6)
    return model


def test_every_control_uses_identical_learned_transition() -> None:
    models = [fitted(cls()) for cls in (FixedMaxSharedTransition, ResidualSharedTransition,
                                         TransitionGateHalt, LearnedAdaptiveHalt, ACTPonderHalt)]
    assert len({model.transition_signature for model in models}) == 1
    assert all(np.array_equal(models[0].kernel.encoder, model.kernel.encoder) for model in models[1:])


def test_adaptive_policies_transfer_beyond_train_depth() -> None:
    task = make_tasks(8, 6, 1, 1103)[0]
    for model in (fitted(TransitionGateHalt()), fitted(LearnedAdaptiveHalt()), fitted(ACTPonderHalt())):
        assert np.allclose(model.query(task.state), task.target)
        assert model.last_transition_calls == 6


def test_fixed_short_exposes_ood_failure_and_fixed_max_remains_exact() -> None:
    task = make_tasks(8, 6, 1, 1103)[0]
    short, maximum = fitted(FixedShortSharedTransition()), fitted(FixedMaxSharedTransition())
    assert not np.allclose(short.query(task.state), task.target)
    assert np.allclose(maximum.query(task.state), task.target)
    assert short.last_transition_calls == 4
    assert maximum.last_transition_calls == 6


def test_gate_saves_full_transition_work_on_easy_tasks() -> None:
    task = make_tasks(32, 1, 1, 1103)[0]
    gate, maximum = fitted(TransitionGateHalt(), 32), fitted(FixedMaxSharedTransition(), 32)
    assert np.allclose(gate.query(task.state), task.target)
    assert np.allclose(maximum.query(task.state), task.target)
    assert gate.last_transition_calls == 1
    assert gate.last_ops < maximum.last_ops


def test_near_boundary_is_safe_for_learned_halt() -> None:
    task = make_tasks(8, 4, 1, 1103)[0]
    model = fitted(LearnedAdaptiveHalt())
    assert np.allclose(model.query(task.near_state), task.near_target)
    assert model.last_transition_calls == task.required_depth
