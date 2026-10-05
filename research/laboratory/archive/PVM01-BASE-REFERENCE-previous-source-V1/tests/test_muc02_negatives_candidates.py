"""Conformance of the preregistered causal factor; no experimental model fit."""
import hashlib
import inspect
import subprocess

import pytest

from nextai_autoresearch.candidates.muc02_core import Reader, training_pairs
from nextai_autoresearch.muc02_negatives_stage import PLAN, protocol
from nextai_autoresearch.muc02_negatives_task import fresh_worlds
from nextai_autoresearch.utils import load_json, project_root


def test_negative_sampling_pairing_and_integrity():
    worlds = tuple({"statements": w.statements, "knowledge_size": k, "reasoning_depth": d}
                   for k in (32, 128, 512) for d in (1, 2, 4) for w in fresh_worlds(976, "T", k, d)[:2])
    random_pairs, random_report = training_pairs(worlds, 4096, 976, "random")
    hard_pairs, hard_report = training_pairs(worlds, 4096, 976, "hard")
    assert len(random_pairs) == len(hard_pairs) == 4096
    assert sum(y for _, _, y in random_pairs) == sum(y for _, _, y in hard_pairs) == 2048
    assert [(d, y) for _, d, y in random_pairs] == [(d, y) for _, d, y in hard_pairs]
    assert [(q, d) for q, d, y in random_pairs if y] == [(q, d) for q, d, y in hard_pairs if y]
    for query, document, label in random_pairs + hard_pairs:
        assert bool(label) == (query == document)
    assert all(sum(a != b for a, b in zip(q.split(), d.split(), strict=True)) == 1 for q, d, y in hard_pairs if not y)
    assert hard_report["mismatch_types"] == {"same_subject": 1024, "same_relation": 1024}
    assert random_report["mismatch_types"]["both_different"] > 0
    for name in ("positive_sequence_sha256", "document_and_label_sequence_sha256"):
        assert random_report[name] == hard_report[name]
    assert random_report["pairs_sha256"] != hard_report["pairs_sha256"]
    assert hard_report["worlds_covered"] == hard_report["worlds_available"] == 18
    assert hard_report["cells_covered"] == 9 and hard_report["subjects_covered"] > 4
    assert hard_pairs == training_pairs(worlds, 4096, 976, "hard")[0]
    with pytest.raises(ValueError, match="intervention"):
        training_pairs(worlds, 4096, 976, "other")


def test_model_and_initialization_are_unchanged_and_paired():
    from nextai_autoresearch.candidates.muc02_negatives import Candidate
    previous = subprocess.check_output(["git", "show", "a74dbce:src/nextai_autoresearch/candidates/muc02_core.py"], cwd=project_root()).decode()
    old_reader = previous[previous.index("class Reader("):previous.index("class BM25Index:")].strip()
    assert inspect.getsource(Reader).strip() == old_reader
    p = protocol(project_root())
    random_model = Candidate(977, {**p, "negative_arm": "random"})
    hard_model = Candidate(977, {**p, "negative_arm": "hard"})
    digest = lambda model: hashlib.sha256(b"".join(v.detach().cpu().numpy().tobytes() for v in model.state_dict().values())).hexdigest()
    assert digest(random_model.model) == digest(hard_model.model)
    assert random_model.mode == hard_model.mode == "bm25"
    assert len(random_model.model.encoder.layers) == 6 and random_model.model.width == 384
    assert p["recipe"]["training_pairs"] == 4096 and p["fit_steps_cap"] == 192
    assert p["recipe"]["learning_rate"] == .0003 and p["recipe"]["batch_size"] == 32
    assert load_json(project_root() / PLAN)["new_architectures_authorized"] is False
