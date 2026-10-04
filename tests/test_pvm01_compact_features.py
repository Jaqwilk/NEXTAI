import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.candidates.pvm01_compact_core import Candidate, delta_unroll, fourier, training_loss
from nextai_autoresearch.candidates.pvm01_core import unit
from nextai_autoresearch.research_program import _study_scope, verify_pvm01_fresh_realization
from nextai_autoresearch.utils import atomic_write_json, sha256_file

ROOT = Path(__file__).resolve().parents[1]
STUDY_PATH = ROOT / "research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json"
STUDY = json.loads(STUDY_PATH.read_text())


def test_feature_unroll_matches_numpy_write_inference_and_overwrite():
    rng = np.random.default_rng(29)
    keys = unit(rng.normal(size=(2, 5, 8))).astype(np.float32)
    keys[:, 4] = keys[:, 0]
    labels = np.array([[1, 3, 5, 8, 14], [2, 4, 6, 9, 15]], np.int64)
    queries = keys[:, [0, 2]]
    expected = []
    for batch in range(2):
        memory = np.zeros((8, 16), np.float32)
        for key, label in zip(keys[batch], labels[batch], strict=True):
            target = np.eye(16, dtype=np.float32)[label]
            memory += key[:, None] * (target - key @ memory)[None]
        expected.append(queries[batch] @ memory)
    actual = delta_unroll(torch.as_tensor(keys), torch.as_tensor(labels), torch.as_tensor(queries))
    np.testing.assert_allclose(actual.numpy(), expected, atol=3e-7, rtol=3e-7)
    assert actual[0, 0].argmax() == 14 and actual[1, 0].argmax() == 15


def test_gradient_through_early_writes_and_queries_matches_finite_difference():
    torch.manual_seed(53)
    projection = torch.randn(3, 2, dtype=torch.float64, requires_grad=True)
    support = torch.randn(1, 3, 3, dtype=torch.float64)
    question = torch.randn(1, 2, 3, dtype=torch.float64)
    labels = torch.tensor([[2, 5, 8]])
    function = lambda r: delta_unroll(fourier(support, r), labels, fourier(question, r))
    assert torch.autograd.gradcheck(function, (projection,), eps=1e-6, atol=1e-5, rtol=1e-4)
    keys = fourier(support, projection).detach().requires_grad_(True)
    reads = fourier(question, projection).detach().requires_grad_(True)
    delta_unroll(keys, labels, reads).square().sum().backward()
    assert keys.grad[0, 0].abs().sum() > 0 and reads.grad.abs().sum() > 0


def test_fourier_unit_norm_and_torch_numpy_inference_agree():
    rng = np.random.default_rng(83)
    values = rng.normal(size=(7, 64)).astype(np.float32)
    projection = rng.normal(size=(64, 256)).astype(np.float32)
    angles = unit(values) @ projection
    expected = np.concatenate((np.cos(angles), np.sin(angles)), axis=1) / np.sqrt(256)
    actual = fourier(torch.as_tensor(values), torch.as_tensor(projection)).numpy()
    np.testing.assert_allclose(actual, expected, atol=3e-7, rtol=2e-5)
    np.testing.assert_allclose(np.sum(actual**2, axis=1), 1, atol=3e-7)


def test_same_transport_features_draws_and_additive_fit_on_fixed_cpu_fixture():
    recipe = {**STUDY["recipe"], "alignment_steps": 2, "alignment_batch": 8,
              "compact_feature_steps": 2, "compact_feature_batch": 2}
    rng = np.random.default_rng(113)
    query = rng.normal(size=(48, 64)).astype(np.float32)
    write = query[:, ::-1].copy()
    sets = {size: (rng.normal(size=(4, size, 64)).astype(np.float32),
                   rng.normal(size=(4, 8, 64)).astype(np.float32),
                   np.tile(np.array([0, 1, 2, 3, 4, 5, size, size]), (4, 1))) for size in (32, 128)}
    systems, reports = [], []
    for arm in ("compact_learned", "compact_frozen", "compact_shuffled", "compact_additive"):
        model = Candidate(127, arm, recipe)
        model.model = model.model.cpu()
        model.device = torch.device("cpu")
        reports.append(model.fit(write, query, write[:8], query[:8], sets))
        systems.append(model)
    for key in ("initial_parameters_sha256", "final_encoder_sha256", "alignment_losses", "compact_initial_features_sha256", "compact_precomputed_sha256"):
        assert all(r[key] == reports[0][key] for r in reports)
    for key in ("compact_final_features_sha256", "compact_feature_losses", "compact_batch_value_draws_sha256"):
        assert reports[0][key] == reports[3][key]
    assert reports[0]["compact_batch_value_draws_sha256"] == reports[2]["compact_batch_value_draws_sha256"]
    assert reports[1]["compact_final_features_sha256"] == reports[1]["compact_initial_features_sha256"]
    assert reports[0]["compact_final_features_sha256"] != reports[0]["compact_initial_features_sha256"]
    assert reports[0]["compact_final_features_sha256"] != reports[2]["compact_final_features_sha256"]
    assert not systems[0].model.training and not any(p.requires_grad for p in systems[0].model.parameters())
    assert systems[0].new_session(4).memory.shape == (512, 16)
    assert systems[3].arm == "additive"


def test_null_supervision_distinguishes_correct_from_corrupt_value_or_abstention():
    recipe = STUDY["recipe"]
    scores = torch.zeros((1, 2, 16))
    scores[0, 0, 3] = 1
    correct = torch.tensor([[3, 16]])
    assert training_loss(scores, correct, recipe) < training_loss(scores, torch.tensor([[4, 16]]), recipe)
    assert training_loss(scores, correct, recipe) < training_loss(scores, torch.tensor([[16, 3]]), recipe)


def test_v4_schema_and_all_roles_are_audited_before_registration():
    from nextai_autoresearch.schemas import validate_document
    from jsonschema import ValidationError
    plan = json.loads((ROOT / "research/plans/EXP-20261004-0006.json").read_text())
    plan.update(benchmark=STUDY["cohort"], matrix=STUDY["matrix"], candidates=STUDY["candidates"])
    plan["research_program_protocol"].update(_study_scope(STUDY), study_path=STUDY_PATH.relative_to(ROOT).as_posix(), study_sha256=sha256_file(STUDY_PATH))
    validate_document("experiment_plan", plan, ROOT)
    wrong = copy.deepcopy(plan)
    wrong["matrix"]["knowledge_sizes"] = [32, 128, 256]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", wrong, ROOT)
    wrong = copy.deepcopy(plan)
    del wrong["research_program_protocol"]["compute_charge_basis"]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", wrong, ROOT)
    for name in STUDY["candidates"]:
        audit = audit_candidate(name, load_config(ROOT), ROOT)
        assert audit.ok, (name, audit.problems)
    assert len(STUDY["roles"]) == 75
    assert 75 * STUDY["resources"]["worker_charge_ceiling_with_monitor_margin"] == STUDY["resources"]["fit_seconds_study_cap"]


def test_real_v4_worker_rejects_private_binding_before_arrays_or_model(tmp_path, monkeypatch):
    from nextai_autoresearch import worker_resources
    from nextai_autoresearch.worker import run_worker
    import nextai_autoresearch.benchmarks.paired_view_mutable_memory_v3 as common
    import nextai_autoresearch.benchmarks.paired_view_mutable_memory_v4 as benchmark
    identity = "EXP-20990101-9904"
    monkeypatch.setattr(common, "project_root", lambda: tmp_path)
    private = tmp_path / "research/tmp" / identity / "pvm01-private-data.json"
    atomic_write_json(private, {"experiment_id": identity, "unit_nonces": ["fixed-fixture"] * 5})
    plan = {"benchmark":STUDY["cohort"], "experiment_id":identity,
            "matrix":{**STUDY["matrix"], "seeds":list(range(1001,1006))},
            "research_program_protocol":_study_scope(STUDY),
            "pvm01_private_data_path":str(private), "pvm01_private_data_sha256":"0"*64}
    touched = []
    monkeypatch.setattr(benchmark, "pairs", lambda *a: touched.append(True))
    monkeypatch.setattr(worker_resources.WorkerResources, "start", lambda self: None)
    monkeypatch.setattr(worker_resources.WorkerResources, "close", lambda self: None)
    monkeypatch.setattr(worker_resources.WorkerResources, "phase", lambda self, phase: None)
    path, output = tmp_path / "fixture-plan.json", tmp_path / "output.json"
    atomic_write_json(path, plan)
    assert run_worker(path, STUDY["candidates"][0], output) == 1
    value = json.loads(output.read_text())
    assert value["error_type"] == "ValueError" and "binding" in value["error"]
    assert not touched and not value["trials"]


@pytest.mark.parametrize("collision", ["none", "seed", "nonce", "tamper"])
def test_latest_consumed_units_reject_collisions_and_tampering(tmp_path, collision):
    paths = {"EXP-20261004-0004":"research/laboratory/archive/EXP-20261004-0004-runtime/research/tmp/EXP-20261004-0004",
             "EXP-20261004-0005":"research/laboratory/archive/EXP-20261004-0005-runtime",
             "EXP-20261004-0006":"research/laboratory/archive/EXP-20261004-0006-runtime/research/tmp/EXP-20261004-0006"}
    for index, (identity, relative) in enumerate(paths.items()):
        directory = tmp_path / relative
        private = directory / "pvm01-private-data.json"
        atomic_write_json(private, {"experiment_id":identity, "unit_nonces":[f"{index+1:064x}"]*5})
        atomic_write_json(directory / "runtime-plan.json", {"experiment_id":identity,
            "matrix":{"seeds":[101+index]}, "pvm01_private_data_sha256":sha256_file(private)})
    seeds, nonces = list(range(1001,1006)), [f"{i:064x}" for i in range(2001,2006)]
    if collision == "seed":
        seeds[0] = 103
    elif collision == "nonce":
        nonces[0] = f"{3:064x}"
    elif collision == "tamper":
        atomic_write_json(tmp_path / paths["EXP-20261004-0006"] / "pvm01-private-data.json", {"experiment_id":"wrong"})
    if collision == "none":
        verify_pvm01_fresh_realization(tmp_path, seeds, nonces)
    else:
        with pytest.raises((ValueError, KeyError)):
            verify_pvm01_fresh_realization(tmp_path, seeds, nonces)


def test_frozen_primary_gates_detect_feature_capacity_and_retention_failures(tmp_path):
    spec = importlib.util.spec_from_file_location("compact_analysis_fixture", ROOT / "scripts/analyze_pvm01_compact_features.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    good = {name: module.interval([.1]*5,.9875) for name in ("frozen", "shuffled", "K512_updated")}
    good["retained"] = module.interval([0]*5,.9875)
    assert all(module.primary_gates(good, STUDY["diagnosis_gates"]).values())
    good["K512_updated"] = module.interval([0]*5,.9875)
    assert not module.primary_gates(good, STUDY["diagnosis_gates"])["K512_updated"]
    good["retained"] = module.interval([-.03]*5,.9875)
    assert not module.primary_gates(good, STUDY["diagnosis_gates"])["retention_noninferiority"]
    path = tmp_path / "analysis.json"
    module.persist(path, {1: {"sample":None}})
    before = path.read_bytes()
    module.persist(path, {1: {"sample":None}})
    assert path.read_bytes() == before
    with pytest.raises(ValueError):
        module.persist(path, {1: {"sample":1}})
