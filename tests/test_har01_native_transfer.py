from pathlib import Path
import copy
import json

import numpy as np
import pytest
import torch
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.har01_task import feature, transform, episode, load_unit, pairs, arrays_hash
from nextai_autoresearch.har01_analysis import paired_interval
from nextai_autoresearch.benchmarks.har01_native_memory_v1 import source_state, scores, copy_service_state
from nextai_autoresearch.candidates.har01_core import Candidate
from nextai_autoresearch.research_program import _study_scope
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import sha256_file


ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT / "research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((ROOT / STUDY["task_contract_path"]).read_text(encoding="utf-8"))


def fixture_unit():
    rng = np.random.default_rng(112233)
    raw = rng.normal(size=(128, 6, 128)).astype(np.float32)
    return {"T-fit": (raw, np.column_stack((np.zeros(128, dtype=np.int64), np.arange(128)))),
            "T-validation": (raw[:48].copy(), np.column_stack((np.zeros(48, dtype=np.int64), np.arange(48)))),
            "T-calibration": (raw[:80].copy(), np.column_stack((np.zeros(80, dtype=np.int64), np.arange(80)))),
            "D": (raw.copy(), np.column_stack((np.ones(128, dtype=np.int64), np.arange(128)))),
            "mean": np.zeros(64, dtype=np.float32), "scale": np.ones(64, dtype=np.float32),
            "train_subject": 1, "dev_subject": 16}


def test_native_views_use_physical_samples_and_adverse_dropout():
    window = np.repeat(np.arange(128, dtype=np.float32)[None], 6, axis=0)
    write, query = feature(window, "write"), feature(window, "nominal")
    assert write.shape == query.shape == (64,)
    np.testing.assert_array_equal(write[:8], np.arange(8) * 16 + 7)
    np.testing.assert_array_equal(query[:8], np.arange(8) * 16 + 8)
    adverse = feature(window, "adverse")
    assert np.all(adverse[32:40] == 0)
    np.testing.assert_array_equal(window[4], np.arange(128, dtype=np.float32))
    assert not np.array_equal(adverse, query)


def test_episode_pairs_truth_while_retaining_stale_source_arrivals():
    unit = fixture_unit()
    nominal = episode(unit, "a" * 64, "D", 32, 4, 0)
    adverse = episode(unit, "a" * 64, "D", 32, 4, 0, condition="adverse")
    assert nominal.answers == adverse.answers
    assert nominal.target_sources == adverse.target_sources
    assert nominal.target_handles == adverse.target_handles
    np.testing.assert_array_equal(nominal.queries, adverse.queries)
    assert len(nominal.writes) == 32 + 4 * 8 + 8
    for handle in {row[1] for row in nominal.writes}:
        rows = [row for row in nominal.writes if row[1] == handle]
        if len(rows) > 1:
            assert rows[-1][0] < max(row[0] for row in rows)


def test_reserved_subject_or_evaluation_pairs_rejected_before_io(tmp_path):
    with pytest.raises(ValueError, match="screen pairs"):
        load_unit(tmp_path, 5)
    with pytest.raises(ValueError, match="evaluation pairs"):
        pairs(fixture_unit(), "a" * 64, "D", 10)


def test_latest_source_and_value_survive_out_of_order_arrival():
    model = Candidate(444, "native_raw", STUDY["recipe"])
    model.threshold = .5
    session = model.new_session(2)
    key = np.eye(64, dtype=np.float32)[0]
    session.ingest((10, 71, key, 8, "publisher:new"))
    session.ingest((2, 71, key, 3, "publisher:old"))
    answer = session.answer(key)
    assert answer[0] == 8 and answer[-1] == "publisher:new"
    assert session.state_bytes() >= 64 * 4 * 2 + model.state_bytes()
    absent = session.answer(np.eye(64, dtype=np.float32)[1])
    assert absent[0] == -1 and absent[-1] is None


def test_source_errors_cannot_hide_behind_a_correct_numeric_value():
    row = {"answer": 7, "truth": 7, "source": "old", "target_source": "current", "top_handle": 1,
           "target_handle": 1, "top_value": 7, "stratum": "updated"}
    value = scores([row])
    assert value["value_accuracy"] == 1 and value["fact_top1_accuracy"] == 1
    assert value["accuracy"] == value["source_attribution_accuracy"] == value["updated_known_accuracy"] == 0
    assert value["source_errors_at_correct_answer"] == 1


@pytest.mark.parametrize("arm", ["source_trained", "source_untrained", "source_shuffled", "source_ridge"])
def test_actual_source_readout_cannot_modify_source_parameters(arm):
    arrays, provenance = source_state(ROOT, arm, 0, CONTRACT)
    model = Candidate(555, arm, STUDY["recipe"], source_arrays=arrays)
    before = copy.deepcopy(model.source_identity())
    rng = np.random.default_rng(111)
    write = rng.normal(size=(80, 64)).astype(np.float32)
    query = write * np.float32(.9)
    model.fit(write[:64], query[:64], write[64:], query[64:])
    assert provenance["source_unit"] == 0 and provenance["no_source_refit"] is True
    assert model.source_identity() == before
    assert model.report["optimizer_steps"] == 0 and model.report["source_frozen"] is True
    assert len(model.report["classical_grid"]) == 6
    restored = copy_service_state(model)
    assert restored.source_identity() == before
    assert restored.model is not model.model or model.model is None
    assert not np.shares_memory(restored.adapter, model.adapter)


def test_real_dense_architecture_native_context_fit_and_cache_agree():
    recipe = dict(STUDY["recipe"], alignment_steps=1, dense_set_steps=2)
    model = Candidate(666, "target_dense", recipe)
    assert isinstance(model.decoder, torch.nn.TransformerDecoder)
    rng = np.random.default_rng(9988)
    write = rng.normal(size=(40, 64)).astype(np.float32)
    query = write.copy()
    sets = {}
    for size in (16, 32):
        support = np.repeat(write[None, :size], 4, axis=0)
        questions = np.repeat(query[None, :8], 4, axis=0)
        labels = np.repeat(np.arange(8)[None], 4, axis=0)
        sets[size] = support, questions, labels
    model.fit(write[:32], query[:32], write[32:], query[32:], sets)
    assert model.report["optimizer_steps"] == 1 and len(model.report["dense_set_losses"]) == 2
    assert model.device.type == "cpu"
    session = model.new_session(16)
    for i in range(16):
        session.ingest((i, 100 + i, write[i], i, f"source:{i}"))
    with torch.inference_mode():
        embedded = torch.nn.functional.normalize(model.model(torch.as_tensor(query[0])), dim=-1)
        full = model.refine(embedded.reshape(1, 1, 64), session.cached.keys.reshape(1, 16, 64))[0, 0]
        cached = session.cached.decoded(embedded)
        torch.testing.assert_close(full, cached, rtol=1e-5, atol=1e-5)


def test_native_classical_controls_preserve_full_finite_training_grid():
    rng = np.random.default_rng(123123)
    values = rng.normal(size=(144, 64)).astype(np.float32)
    queries = values.copy()
    for arm, expected_grid in (("target_ridge_pca", 6), ("target_kernel", 12)):
        model = Candidate(777, arm, STUDY["recipe"])
        model.fit(values[:128], queries[:128], values[128:], queries[128:])
        assert len(model.report["classical_grid"]) == expected_grid
        assert np.isfinite(model.weights).all() and model.weights.dtype == np.float32
        if arm == "target_ridge_pca":
            assert len(model.report["pca_grid"]) == 6
        else:
            assert len(model.landmarks) == 128


def test_intervals_use_five_units_and_detect_null_or_missing_pairs():
    null = paired_interval([0.] * 5, 4)
    assert null["lower"] == null["upper"] == 0
    positive = paired_interval([.20, .21, .22, .23, .24], 4)
    assert positive["lower"] > 0 and positive["positive_pairs"] == 5
    assert positive["confidence"] == .9875
    with pytest.raises(ValueError, match="Five"):
        paired_interval([.2] * 4, 4)


def native_plan():
    plan = json.loads((ROOT / "research/plans/EXP-20261005-0006.json").read_text(encoding="utf-8"))
    plan.update(benchmark=STUDY["cohort"], candidates=STUDY["candidates"], matrix=STUDY["matrix"])
    plan["research_program_protocol"] = {"authority_path": "research/laboratory/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1.json",
        "program_contract_path": STUDY["program_contract_path"], "program_contract_sha256": STUDY["program_contract_sha256"],
        "study_path": "research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json",
        "study_sha256": sha256_file(ROOT / "research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json"),
        "registration_ticket": 1, **_study_scope(STUDY)}
    return plan


def test_native_schema_accepts_only_frozen_matrix_and_recipe_without_ticket():
    plan = native_plan()
    validate_document("experiment_plan", plan, ROOT)
    changed = copy.deepcopy(plan)
    changed["matrix"]["knowledge_sizes"][-1] = 512
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", changed, ROOT)
    changed = copy.deepcopy(plan)
    changed["research_program_protocol"]["recipe"]["alignment_steps"] = 8192
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", changed, ROOT)


def test_all_native_roles_are_audited_and_private_native_imports_rejected(tmp_path):
    config = load_config(ROOT)
    for name in STUDY["candidates"]:
        assert audit_candidate(name, config, ROOT).ok
    directory = tmp_path / "src/nextai_autoresearch/candidates"
    directory.mkdir(parents=True)
    (directory / "native_leak.py").write_text("from nextai_autoresearch.har01_task import load_unit\nclass Candidate: pass\n", encoding="utf-8")
    rejected = audit_candidate("native_leak", config, tmp_path)
    assert not rejected.ok and any("evaluator" in problem for problem in rejected.problems)
