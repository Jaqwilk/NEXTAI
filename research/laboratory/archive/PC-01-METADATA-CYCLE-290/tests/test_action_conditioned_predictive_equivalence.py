from nextai_autoresearch.benchmarks.action_conditioned_predictive_equivalence_v1 import (
    BASE, best_action, make_dataset, make_tasks, outcome_map, rollout,
)
from nextai_autoresearch.predictive_state_core import (
    CSSRStateReconstructor, ContextTreeState, EmpiricalBisimulationState,
    InformationBottleneckState, SpectralPSRState,
)


def test_raw_records_hide_state_and_alias_observations() -> None:
    data, _, _ = make_dataset(8, 1103)
    assert len(data.records) == 128
    assert not hasattr(data.records[0], "state")
    outcomes = outcome_map(1103)
    assert outcomes[0] == outcomes[2]


def test_near_histories_are_observationally_aliased_but_predictively_distinct() -> None:
    task = make_tasks(8, 4, 1, 1103)[0]
    assert task.history[-1] == task.near_history[-1]
    assert task.expected != task.near_expected


def test_classical_predictive_states_compose_held_out_actions() -> None:
    data, _, _ = make_dataset(8, 1103)
    task = make_tasks(8, 6, 1, 1103)[0]
    for model in (ContextTreeState(), CSSRStateReconstructor(),
                  EmpiricalBisimulationState(), SpectralPSRState(),
                  InformationBottleneckState()):
        model.fit(data, 8, 6)
        assert model.query(task.history, task.actions, 6) == (task.expected, task.best_action)
        assert model.query(task.near_history, task.actions, 6) == (task.near_expected, task.near_best_action)


def test_raw_local_update_changes_one_transition_without_latent_labels() -> None:
    data, _, histories = make_dataset(8, 1103)
    changed = dict(BASE)
    changed[(0, 1)] = 3
    delta, _, _ = make_dataset(8, 1103, changed, {(0, 1)})
    model = CSSRStateReconstructor()
    model.fit(data, 8, 4)
    model.update(delta)
    actions = (1, 1, 1, 1)
    expected = rollout(0, actions, changed, outcome_map(1103))
    assert model.query(histories[0][0], actions, 4)[0] == expected


def test_registered_planner_tie_break_is_deterministic() -> None:
    outcomes = outcome_map(1103)
    assert best_action(0, 4, BASE, outcomes) in (0, 1)
    assert best_action(0, 4, BASE, outcomes) == best_action(0, 4, BASE, outcomes)
