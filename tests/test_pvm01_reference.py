import copy
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from nextai_autoresearch.pvm01_task import maps, pairs, episode, episode_hash
from nextai_autoresearch.candidates.pvm01_core import Candidate
from nextai_autoresearch.benchmarks.paired_view_mutable_memory_v1 import scores
from nextai_autoresearch.research_program import _study_scope, _execution_fit
from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config

ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT / "research/plans/PVM01-REFERENCE-V1.json").read_text())


def test_private_maps_and_fresh_views_have_legal_boundaries():
    first, second = maps("unit-test-entropy")
    assert np.allclose(first.T @ first, np.eye(16), atol=1e-6)
    assert not np.allclose(first, second)
    train = pairs("unit-test-entropy", "T-fit", 32)
    held = pairs("unit-test-entropy", "T-validation", 32)
    assert not np.array_equal(train[0], held[0])
    item = episode("unit-test-entropy", "D", 32, 4, 0)
    assert item.queries.shape == (64, 64) and item.queries.dtype == np.float32
    assert all(len(row) == 4 and row[2].shape == (64,) and 0 <= row[3] < 16 for row in item.writes)
    assert item.strata.count("updated") == 24 and item.strata.count("retained") == 24 and item.strata.count("absent") == 16
    assert episode_hash(item) == episode_hash(episode("unit-test-entropy", "D", 32, 4, 0))
    assert episode_hash(item) != episode_hash(episode("unit-test-other", "D", 32, 4, 0))
    with pytest.raises(ValueError):
        episode("unit-test-entropy", "final", 32, 0, 0)


def test_replacement_is_timestamped_and_only_current_values_reach_output():
    system = Candidate(7, "raw", STUDY["recipe"])
    system.threshold = .5
    session = system.new_session(2)
    observation = np.eye(64, dtype=np.float32)[0]
    other = np.eye(64, dtype=np.float32)[1]
    session.ingest((0, 9182, observation, 3))
    session.ingest((1, 8342, other, 7))
    session.ingest((2, 9182, observation, 11))
    session.ingest((0, 9182, other, 1))
    assert session.answer(observation)[0] == 11
    assert len(session.handles) == 2 and session.slots[9182] == 0
    assert session.answer(np.eye(64, dtype=np.float32)[2])[0] == -1
    with pytest.raises(ValueError):
        session.answer(observation.astype(np.float64))


def test_ranking_and_value_collision_do_not_mask_absence_or_wrong_fact():
    rows = [dict(answer=3, truth=3, top_handle=8, target_handle=7, top_value=3, stratum="retained"),
            dict(answer=-1, truth=4, top_handle=9, target_handle=9, top_value=4, stratum="updated"),
            dict(answer=1, truth=-1, top_handle=8, target_handle=None, top_value=1, stratum="absent")]
    value = scores(rows)
    assert value["accuracy"] == 1 / 3
    assert value["fact_top1_accuracy"] == .5 and value["known_false_abstention"] == .5
    assert value["dense_unknown_rejection"] == 0 and value["wrong_fact_errors"] == 1
    assert value["stale_or_value_errors_at_correct_handle"] == 0


def test_classical_transport_is_fitted_only_on_supplied_pairs():
    rng = np.random.default_rng(73)
    inputs = rng.normal(size=(96, 64)).astype(np.float32)
    rotation = np.linalg.qr(rng.normal(size=(64, 64)))[0]
    target = (inputs @ rotation + .2).astype(np.float32)
    query = rng.normal(size=(12, 64)).astype(np.float32)
    answer = (query @ rotation + .2).astype(np.float32)
    model = Candidate(3, "ridge", STUDY["recipe"])
    model.fit(target, inputs, answer, query)
    predicted = np.column_stack([query, np.ones(12)]) @ model.weights
    assert np.max(np.abs(predicted - answer)) < 1e-4
    assert len(model.grid) == 3 and model.report["optimizer_steps"] == 0
    assert model.report["fit_operations_estimate"] > 0


def test_neural_source_identity_and_real_dense_transformer():
    recipe = copy.deepcopy(STUDY["recipe"])
    recipe["alignment_steps"] = 2
    rng = np.random.default_rng(17)
    inputs = rng.normal(size=(48, 64)).astype(np.float32)
    target = inputs[:, ::-1].copy()
    pointer = Candidate(91, "pointer", recipe)
    exact = Candidate(91, "exact_nn", recipe)
    shuffled = Candidate(91, "shuffled", recipe)
    dense = Candidate(91, "dense", recipe)
    assert pointer.initial_hash == exact.initial_hash == shuffled.initial_hash == dense.initial_hash
    pointer.fit(target, inputs, target[:12], inputs[:12])
    exact.fit(target, inputs, target[:12], inputs[:12])
    shuffled.fit(target, inputs, target[:12], inputs[:12])
    assert pointer.report["final_encoder_sha256"] == exact.report["final_encoder_sha256"]
    assert pointer.report["alignment_losses"] == exact.report["alignment_losses"]
    assert shuffled.report["final_encoder_sha256"] != pointer.report["final_encoder_sha256"]
    assert isinstance(dense.decoder, torch.nn.TransformerDecoder) and len(dense.decoder.layers) == 2
    assert all(block.self_attn.num_heads == 4 and block.multihead_attn.num_heads == 4 for block in dense.decoder.layers)


def test_every_role_is_audited_and_private_task_import_is_blocked(tmp_path):
    config = load_config(ROOT)
    for name in STUDY["candidates"]:
        result = audit_candidate(name, config, ROOT)
        assert result.ok, (name, result.problems)
    from nextai_autoresearch.audit import FORBIDDEN_INTERNAL_PREFIXES
    assert "nextai_autoresearch.pvm01_task" in FORBIDDEN_INTERNAL_PREFIXES


def test_new_compute_basis_preserves_old_fit_accounting():
    assert _execution_fit([{"execution": {"supervised_fit_seconds": 4}}]) == 4
    assert _execution_fit([{"execution": {"supervised_fit_seconds": 4, "research_compute_seconds": 13}}]) == 13
    value = _study_scope(STUDY)
    assert value["compute_charge_basis"] == "full_worker_wall_v1"
    assert value["task_contract_sha256"] == STUDY["task_contract_sha256"]
    assert value["data"]["axis_encoding"] == {"1": 0, "2": 1, "3": 4}
    assert STUDY["reference_gates"]["mean_full_answer_accuracy_min"] == .95
    assert STUDY["resources"]["worker_charge_ceiling_with_monitor_margin"] * len(STUDY["roles"]) == STUDY["resources"]["fit_seconds_study_cap"]


def test_kernel_transport_uses_nystrom_whitening_and_reserved_selection():
    rng = np.random.default_rng(83)
    inputs = rng.normal(size=(32, 64)).astype(np.float32) * .05
    target = (inputs[:, ::-1] + .1).copy()
    query = inputs[:8].copy()
    model = Candidate(7, "kernel", STUDY["recipe"])
    model.fit(target, inputs, target[:8], query)
    assert len(model.grid) == 6 and model.landmarks.shape == (32, 64)
    assert np.isfinite(model.weights).all()
    assert min(row["validation_mse"] for row in model.grid) < .001


def test_new_plan_schema_accepts_exact_scope_without_real_registration():
    from jsonschema import ValidationError
    from nextai_autoresearch.schemas import validate_document
    from nextai_autoresearch.utils import sha256_file
    plan = json.loads((ROOT / "research/plans/EXP-20261004-0003.json").read_text())
    plan.update(benchmark=STUDY["cohort"], candidates=STUDY["candidates"], matrix=STUDY["matrix"])
    protocol = plan["research_program_protocol"]
    protocol.update(_study_scope(STUDY), study_path="research/plans/PVM01-REFERENCE-V1.json",
                    study_sha256=sha256_file(ROOT / "research/plans/PVM01-REFERENCE-V1.json"))
    validate_document("experiment_plan", plan, ROOT)
    changed = copy.deepcopy(plan)
    changed["matrix"]["reasoning_depths"] = [1, 2, 4]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", changed, ROOT)
    changed = copy.deepcopy(plan)
    del changed["research_program_protocol"]["compute_charge_basis"]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", changed, ROOT)


def test_dense_batched_queries_equal_independent_single_queries():
    model = Candidate(619, "dense", STUDY["recipe"])
    for block in model.decoder.layers:
        for projection in (block.self_attn.out_proj, block.multihead_attn.out_proj, block.linear2):
            torch.nn.init.normal_(projection.weight, std=.02)
    model.decoder.eval()
    embedded = torch.nn.functional.normalize(torch.randn(1, 8, 64, device=model.device), dim=-1)
    keys = torch.nn.functional.normalize(torch.randn(1, 32, 64, device=model.device), dim=-1)
    with torch.inference_mode():
        batched = model.refine(embedded, keys)
        single = torch.cat([model.refine(embedded[:, i:i + 1], keys) for i in range(8)], dim=1)
        changed = embedded.clone()
        changed[:, 1:] *= -1
        other = model.refine(changed, keys)
    assert torch.allclose(batched, single, atol=1e-5, rtol=1e-5)
    assert torch.allclose(batched[:, 0], other[:, 0], atol=1e-5, rtol=1e-5)


def test_dense_training_updates_decoder_without_changing_frozen_encoder():
    recipe = copy.deepcopy(STUDY["recipe"])
    recipe.update(alignment_steps=2, dense_set_steps=2)
    rng = np.random.default_rng(319)
    queries = rng.normal(size=(64, 64)).astype(np.float32)
    writes = queries[:, ::-1].copy()
    sets = {}
    for size in (32, 128):
        support = rng.normal(size=(4, size, 64)).astype(np.float32)
        questions = rng.normal(size=(4, 8, 64)).astype(np.float32)
        labels = np.tile([0, 1, 2, 3, 4, 5, size, size], (4, 1))
        sets[size] = (support, questions, labels)
    dense = Candidate(321, "dense", recipe)
    pointer = Candidate(321, "pointer", recipe)
    before = dense.decoder.layers[0].multihead_attn.out_proj.weight.detach().clone()
    dense.fit(writes, queries, writes[:8], queries[:8], sets)
    pointer.fit(writes, queries, writes[:8], queries[:8])
    assert len(dense.report["dense_set_losses"]) == 2
    assert all(np.isfinite(dense.report["dense_set_losses"]))
    assert not torch.equal(before, dense.decoder.layers[0].multihead_attn.out_proj.weight)
    assert dense.report["final_encoder_sha256"] == pointer.report["final_encoder_sha256"]
