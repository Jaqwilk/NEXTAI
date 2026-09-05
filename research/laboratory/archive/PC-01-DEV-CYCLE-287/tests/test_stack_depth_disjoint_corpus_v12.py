from collections import Counter
import hashlib
import json

from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v1 as v1
from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v11 as v11
from nextai_autoresearch.benchmarks import heldout_parallel_masked_infilling_v12 as v12
from nextai_autoresearch.utils import project_root


EVALUATED = {
    "learned_pushdown_masked_byte.py",
    "learned_pushdown_masked_byte_core.py",
    "source_identical_finite_state_pushdown_masked_byte.py",
    "source_identical_frozen_pushdown_masked_byte.py",
    "uniform_masked_byte.py",
    "empirical_unigram_masked_byte.py",
    "left_to_right_ppm_masked_byte.py",
    "context_tree_weighting_masked_byte.py",
    "dense_autoregressive_masked_byte.py",
    "bidirectional_markov_masked_byte.py",
    "parallel_markov_bp_masked_byte.py",
    "privileged_conditional_masked_byte_v2.py",
    "re_pair_grammar_masked_byte.py",
}


def _entries():
    path = project_root() / v12.CORPUS_REGISTRY
    return json.loads(path.read_text(encoding="utf-8"))["entries"]


def test_v12_registry_is_exact_disjoint_and_excludes_evaluated_roles() -> None:
    entries = _entries()
    old_paths = {row[1] for row in v1.CORPUS}
    old_hashes = {row[3] for row in v1.CORPUS}
    paths = {entry["path"] for entry in entries}
    hashes = {entry["sha256"] for entry in entries}
    assert not paths & old_paths
    assert not hashes & old_hashes
    assert len(paths) == len(entries)
    assert not {path.rsplit("/", 1)[-1] for path in paths} & EVALUATED
    for entry in entries:
        data = v12._frozen_entry_bytes(project_root(), entry)
        assert len(data) == entry["size"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]


def test_v12_fills_declared_scales_and_has_three_ood_depths() -> None:
    expected = {
        8: (8192, 1023),
        32: (32709, 4096),
    }
    for size, counts in expected.items():
        training, tests, _ = v12.make_stack_training(size, 123)
        actual = (
            sum(len(file.data) for file in training.train_files),
            sum(len(file.data) for file in training.validation_files),
        )
        assert actual == counts
        assert Counter(depth for _, depth in tests) == {3: 55, 4: 17, 5: 10}


def test_v12_changes_only_corpus_and_preserves_v11_query_routing() -> None:
    assert v12.BENCHMARK_VERSION == "heldout_parallel_masked_infilling_v12"
    assert v12._run_case is v11._run_case
    assert v12.v9._stack_cases is not None
