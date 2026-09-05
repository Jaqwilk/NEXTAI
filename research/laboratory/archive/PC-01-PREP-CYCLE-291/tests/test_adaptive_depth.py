from nextai_autoresearch.benchmarks.adaptive_depth_v1 import make_world, run_trial
from nextai_autoresearch.candidates.learned_local_halt import Candidate
from nextai_autoresearch.candidates.oracle_modular_router import (
    Candidate as ModularCandidate,
)


def test_world_has_hidden_depth_and_is_deterministic() -> None:
    world = make_world(64, 16, 1103)
    assert world == make_world(64, 16, 1103)
    current = world.source
    for _ in range(16):
        current = dict(world.facts)[current]
    assert current == world.terminal
    assert dict(world.facts)[current] == current


def test_controls_separate_adaptive_and_fixed_compute() -> None:
    adaptive = run_trial("adaptive_indexed", 64, 1, 2, 1103, 16)
    fixed = run_trial("fixed_max_indexed", 64, 1, 2, 1103, 16)
    short = run_trial("fixed_short_indexed", 64, 16, 2, 1103, 16)
    assert adaptive["accuracy"] == fixed["accuracy"] == 1.0
    assert adaptive["mean_query_ops"] == 1.0
    assert fixed["mean_query_ops"] == 16.0
    assert short["accuracy"] == 0.0


def test_learned_halt_rule_transfers_beyond_four_training_predecessors() -> None:
    world = make_world(64, 16, 1103)
    candidate = Candidate(1103)
    candidate.fit(world.facts, 64, 16)
    assert candidate.query(world.source, 0) == world.terminal
    assert candidate.last_ops == 85
    candidate.update(64, 64)
    assert candidate.query(64, 0) == 64
    assert candidate.last_ops == 5


def test_oracle_modular_router_activates_one_expert_per_hop() -> None:
    world = make_world(64, 16, 1103)
    candidate = ModularCandidate(1103)
    candidate.fit(world.facts, 64, 16)
    assert all(len(module) <= 16 for module in candidate.modules)
    assert candidate.query(world.source, 0) == world.terminal
    assert candidate.last_ops == 32
