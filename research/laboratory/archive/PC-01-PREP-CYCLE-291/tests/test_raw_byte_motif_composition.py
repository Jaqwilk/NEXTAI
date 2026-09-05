from nextai_autoresearch.benchmarks.raw_byte_motif_composition_v1 import (
    make_episode,
    make_motifs,
    make_tasks,
    run_trial,
)
from nextai_autoresearch.byte_motif_core import (
    ContrastiveMotifComposer,
    DenseRecurrentComposer,
    ExactSuffixComposer,
    FixedTrigramComposer,
)


def test_raw_family_is_variable_length_unsegmented_and_held_out():
    motifs = make_motifs(1103)
    episode = make_episode(8, 1103, motifs)
    tasks = make_tasks(6, 1103, 8, motifs)
    assert sorted(map(len, motifs.values())) == [4, 5, 6, 7]
    assert all(len(demo.labels) >= 2 for demo in episode.supports)
    assert all(task.target not in {demo.labels for demo in episode.supports} for task in tasks)


def test_exact_fixed_and_contrastive_compose_held_out_sequences():
    motifs = make_motifs(1103)
    episode = make_episode(8, 1103, motifs)
    tasks = make_tasks(6, 1103, 8, motifs)
    for candidate in (FixedTrigramComposer(), ContrastiveMotifComposer(), ExactSuffixComposer()):
        candidate.fit(episode, 8, 6)
        assert all(candidate.query(task.cold, 6) == task.target for task in tasks)
        assert all(candidate.query(task.near, 6) == task.near_target for task in tasks)


def test_distractor_growth_is_charged_during_discovery():
    motifs = make_motifs(1103)
    small, large = ContrastiveMotifComposer(), ContrastiveMotifComposer()
    small.fit(make_episode(8, 1103, motifs), 8, 6)
    large.fit(make_episode(32, 1103, motifs), 32, 6)
    assert large.fit_ops > small.fit_ops


def test_dense_recurrent_control_has_no_symbolic_oracle():
    motifs = make_motifs(1103)
    candidate = DenseRecurrentComposer(1103)
    candidate.fit(make_episode(8, 1103, motifs), 8, 6)
    answer = candidate.query(make_tasks(4, 1103, 1, motifs)[0].cold, 4)
    assert len(answer) == 4
    assert candidate.state_bytes() > 64


def test_exact_update_learns_new_spelling_and_retains_unchanged_motif():
    motifs = make_motifs(1103)
    candidate = ExactSuffixComposer()
    candidate.fit(make_episode(8, 1103, motifs), 8, 6)
    updated = dict(motifs)
    updated[1] = (91, 92, 93, 94)
    candidate.update(make_episode(8, 2207, updated))
    tasks = make_tasks(4, 2207, 4, updated)
    assert all(candidate.query(task.cold, 4) == task.target for task in tasks)


def test_trial_reports_exact_safe_reuse_for_strong_controls():
    for name in ("fixed_trigram_composer", "contrastive_motif_composer", "exact_suffix_composer"):
        trial = run_trial(name, 8, 4, 4, 1103, 6)
        assert trial["accuracy"] == trial["warm_accuracy"] == trial["near_equivalent_accuracy"] == 1.0
        assert trial["reuse_precision"] == trial["reuse_coverage"] == 1.0
        assert trial["false_reuse_rate"] == 0.0
