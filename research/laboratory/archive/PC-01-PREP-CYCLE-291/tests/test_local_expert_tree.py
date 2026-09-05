import numpy as np

from nextai_autoresearch.benchmarks.continuous_local_cellular_v1 import Transition
from nextai_autoresearch.candidates.error_novelty_split_local_expert_tree_v1 import Candidate as Aligned
from nextai_autoresearch.candidates.local_expert_tree_core import (
    MAX_LEAVES, MIN_CHILD, MIN_LEAF, MIN_RELATIVE_GAIN, NOVELTY_SPAN,
    OUTPUT_BOUND, RIDGE, SHUFFLE_SALT, UPDATE_ETA, LocalExpertTree,
)
from nextai_autoresearch.candidates.source_identical_frozen_partition_local_expert_tree_v1 import Candidate as Frozen
from nextai_autoresearch.candidates.source_identical_shuffled_split_local_expert_tree_v1 import Candidate as Shuffled


def _rows(reverse: bool = False):
    rows = []
    values = np.linspace(-1.0, 1.0, 96)
    for index, value in enumerate(values):
        nuisance = ((index * 17) % 101) / 50 - 1
        left = (nuisance, 0.2 * value, 0.0, 0.0)
        center = (value, nuisance * 0.1, 0.0, 0.0)
        right = (-0.1 * value, nuisance * 0.2, 0.0, 0.0)
        first = 0.8 * value - 0.6 if value <= 0 else -0.7 * value + 0.7
        rows.append(Transition(left, center, right, (first, 0.2 * value, 0.0, 0.0)))
    return tuple(reversed(rows)) if reverse else tuple(rows)


def test_aligned_piecewise_error_triggers_a_bounded_split() -> None:
    candidate = Aligned(7)
    candidate.fit(_rows(), 64, 16)
    assert 1 < len(candidate.leaves) <= MAX_LEAVES
    assert candidate.root.feature is not None
    assert candidate.fit_ops > 0 and candidate.state_bytes() > 0


def test_source_identical_wrappers_share_core_and_frozen_stays_one_leaf() -> None:
    assert all(issubclass(role, LocalExpertTree) for role in (Aligned, Shuffled, Frozen))
    assert (RIDGE, MAX_LEAVES, MIN_LEAF, MIN_CHILD, NOVELTY_SPAN,
            MIN_RELATIVE_GAIN, UPDATE_ETA, OUTPUT_BOUND, SHUFFLE_SALT) == (
        0.001, 8, 48, 24, 0.20, 0.05, 0.05, 1.5, 0x51E17,
    )
    frozen = Frozen(7)
    frozen.fit(_rows(), 64, 16)
    assert len(frozen.leaves) == 1 and frozen.root.feature is None


def test_shuffled_mode_reassigns_only_the_complete_gain_vector() -> None:
    aligned, shuffled = Aligned(11), Shuffled(11)
    x, y = aligned._design(_rows())
    for candidate in (aligned, shuffled):
        weights, _, _ = __import__(
            "nextai_autoresearch.candidates.local_expert_tree_core",
            fromlist=["_ridge"],
        )._ridge(x, y)
        candidate.root.weights = weights
        candidate._leaf_indices = {(): np.arange(len(x))}
    proposals, _ = aligned._proposals(x, y)
    shuffled_proposals, _ = shuffled._proposals(x, y)
    gains = aligned.assigned_gains(proposals)
    reassigned = shuffled.assigned_gains(shuffled_proposals)
    assert sorted(gains) == sorted(reassigned)
    assert gains != reassigned


def test_row_reordering_preserves_aligned_tree_and_predictions() -> None:
    first, second = Aligned(3), Aligned(3)
    first.fit(_rows(), 64, 16)
    second.fit(_rows(True), 64, 16)
    signature = lambda model: [(leaf.path, np.round(leaf.weights, 10).tolist()) for leaf in model.leaves]
    assert signature(first) == signature(second)


def test_update_changes_exactly_one_routed_leaf() -> None:
    candidate = Aligned(5)
    rows = _rows()
    candidate.fit(rows, 64, 16)
    before = {leaf.path: leaf.weights.copy() for leaf in candidate.leaves}
    candidate.update(rows[-1], None)
    changed = [leaf.path for leaf in candidate.leaves if not np.array_equal(before[leaf.path], leaf.weights)]
    assert len(changed) == 1
    assert candidate.update_ops > 0 and candidate.last_update_bytes > 0
