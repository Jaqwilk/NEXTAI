from __future__ import annotations

from nextai_autoresearch.candidates.vsa_superposition import Candidate


def _cycle(size: int) -> list[tuple[int, int]]:
    return [(index, (index + 1) % size) for index in range(size)]


def test_vsa_is_deterministic_for_a_fixed_seed() -> None:
    left = Candidate(seed=1103)
    right = Candidate(seed=1103)
    facts = _cycle(16)
    left.fit(facts, universe_size=16, max_depth=16)
    right.fit(facts, universe_size=16, max_depth=16)
    assert left.codebook.tolist() == right.codebook.tolist()
    assert left.memory.tolist() == right.memory.tolist()
    assert [left.query(source, 1) for source in range(16)] == [
        right.query(source, 1) for source in range(16)
    ]


def test_vsa_accounts_for_global_cleanup_scaling() -> None:
    small = Candidate(seed=7)
    small.fit(_cycle(16), universe_size=16, max_depth=1)
    small.query(0, 1)
    small_ops = small.last_ops
    small_state = small.state_bytes()

    large = Candidate(seed=7)
    large.fit(_cycle(64), universe_size=64, max_depth=1)
    large.query(0, 1)
    assert large.last_ops > 3 * small_ops
    assert large.state_bytes() > 3 * small_state


def test_vsa_append_update_expands_state_and_is_charged() -> None:
    candidate = Candidate(seed=19)
    candidate.fit(_cycle(8), universe_size=8, max_depth=4)
    previous_state = candidate.state_bytes()
    candidate.update(8, 8)
    assert candidate.codebook.shape == (9, candidate.dimension)
    assert candidate.state_bytes() > previous_state
    assert candidate.update_ops == 4 * candidate.dimension

