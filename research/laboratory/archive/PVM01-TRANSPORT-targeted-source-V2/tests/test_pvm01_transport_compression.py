import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.candidates.pvm01_transport_compression_core import Candidate
from nextai_autoresearch.pvm01_task import episode, episode_hash, arrays_hash
from nextai_autoresearch.pvm01_adverse_task import episode as adverse_episode
from nextai_autoresearch.benchmarks.paired_view_mutable_memory_v6 import run_suite
from nextai_autoresearch.research_program import _study_scope
from nextai_autoresearch.schemas import validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT / "research/plans/PVM01-TRANSPORT-COMPRESSION-ADVERSE-V2.json").read_text())


def analyzer():
    spec = importlib.util.spec_from_file_location("transport_analyzer_fixture", ROOT / "scripts/analyze_pvm01_transport.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize("updates", [0, 1, 4])
def test_noise_pair_preserves_old_law_truth_and_draw_direction(updates):
    nonce = "0" * 64  # Fixed public fixture, never a research nonce.
    old = episode(nonce, "D", 32, updates, 0)
    base = adverse_episode(nonce, "D", 32, updates, 0, noise=.02)
    hard = adverse_episode(nonce, "D", 32, updates, 0, noise=.04)
    assert episode_hash(old) == episode_hash(base)
    assert base.answers == hard.answers and base.target_handles == hard.target_handles and base.strata == hard.strata
    assert [(r[0], r[1], r[3]) for r in base.writes] == [(r[0], r[1], r[3]) for r in hard.writes]
    assert arrays_hash(base.queries) != arrays_hash(hard.queries)
    assert all(arrays_hash(a[2]) != arrays_hash(b[2]) for a, b in zip(base.writes, hard.writes, strict=True))
    # Signal=2*base-hard; the same latent identity repeated in updates has the same signal.
    signals = {}
    for a, b in zip(base.writes, hard.writes, strict=True):
        signal = 2 * a[2] - b[2]
        if a[1] in signals:
            np.testing.assert_allclose(signal, signals[a[1]], rtol=0, atol=3e-7)
        signals[a[1]] = signal
    with pytest.raises(ValueError):
        adverse_episode(nonce, "D", 32, updates, 0, noise=.03)


def test_same_transport_fit_and_write_only_PCA_across_learning_controls(monkeypatch):
    recipe = {**STUDY["recipe"], "alignment_steps": 2, "alignment_batch": 8}
    rng = np.random.default_rng(312)
    writes = np.zeros((128, 64), dtype=np.float32)
    writes[:, :16] = rng.normal(size=(128, 16))
    queries = writes[:, ::-1].copy()
    reports = {}
    for arm in ("transport_pca", "transport_full", "transport_pca_untrained", "transport_pca_shuffled"):
        system = Candidate(1103, arm, recipe)
        system.model = system.model.to("cpu")
        system.device = torch.device("cpu")
        reports[arm] = system.fit(writes, queries, writes[:16], queries[:16])
        assert system.device.type == "cpu"
    trained, full, frozen, shuffled = (reports[a] for a in reports)
    assert trained["alignment_losses"] == full["alignment_losses"]
    assert trained["final_encoder_sha256"] == full["final_encoder_sha256"]
    assert trained["pca_choice"]["rank"] == 16
    assert all(r["pca_projection_sha256"] == trained["pca_projection_sha256"] for r in (frozen, shuffled))
    assert frozen["optimizer_steps"] == 0 and frozen["final_encoder_sha256"] == frozen["initial_parameters_sha256"]
    assert shuffled["initial_parameters_sha256"] == trained["initial_parameters_sha256"]
    assert shuffled["alignment_losses"] != trained["alignment_losses"]


def test_compressed_record_retrieval_updates_staleness_absence_and_accounting(monkeypatch):
    systems = [Candidate(1103, arm, STUDY["recipe"]) for arm in ("transport_pca", "transport_full")]
    for system in systems:
        system.model = system.model.to("cpu")
        system.device = torch.device("cpu")
        with torch.no_grad():
            for parameter in system.model.parameters():
                parameter.zero_()
            system.model.linear.weight.copy_(torch.eye(64))
    systems[0].projection = np.eye(64, dtype=np.float32)[:, :16].copy()
    sessions = [system.new_session(2) for system in systems]
    a, b, absent = np.eye(64, dtype=np.float32)[:3]
    for session in sessions:
        session.ingest((0, 30001, a, 2)); session.ingest((1, 70111, b, 5))
        assert session.answer(a)[:2] == (2, 30001)
        assert session.answer(b)[:2] == (5, 70111)
        assert session.answer(absent)[0] == -1
        session.ingest((2, 30001, a, 11)); session.ingest((0, 30001, b, 1))
        assert session.answer(a)[:2] == (11, 30001)
        assert session.answer(b)[:2] == (5, 70111)
        assert len(session.handles) == 2
        assert session.state_bytes() >= session.system.state_bytes() + session.keys.nbytes + session.values.nbytes
    # Projection/model state is charged as well as compressed record storage.
    assert systems[0].state_bytes() == systems[1].state_bytes() + 64 * 16 * 4
    assert sessions[0].keys.nbytes == sessions[1].keys.nbytes // 4


def test_v6_all70_roles_audited_and_schema_before_registration():
    config = load_config(ROOT)
    for name in STUDY["candidates"]:
        audit = audit_candidate(name, config, ROOT)
        assert audit.ok, audit.problems
    plan = json.loads((ROOT / "research/plans/EXP-20261004-0008.json").read_text())
    plan["benchmark"] = STUDY["cohort"]
    plan["candidates"] = STUDY["candidates"]
    plan["research_program_protocol"].update(_study_scope(STUDY))
    validate_document("experiment_plan", plan, ROOT)


def test_v6_rejects_private_path_before_any_array_or_model():
    plan = {"experiment_id": "EXP-20990101-9901", "matrix": {"knowledge_sizes": [32,128,512], "reasoning_depths": [1,2,3], "seeds": [1103,1709,2909,3109,4109]}, "research_program_protocol": {}, "pvm01_private_data_path": str(ROOT / "program.md")}
    with pytest.raises(ValueError, match="Runner-private path"):
        run_suite(STUDY["candidates"][0], plan)


def test_frozen_intervals_detect_null_missing_endpoint_and_analysis_rewrite(tmp_path):
    module = analyzer()
    contrasts = {}
    for noise in ("0.02", "0.04"):
        for control, metric in (("untrained", "accuracy"), ("shuffled", "accuracy"), ("full", "accuracy"), ("full", "retained")):
            contrasts[f"{noise}:{control}:{metric}"] = module.interval([.3 if control != "full" else 0] * 5, .99375)
    assert all(module.primary_gates(contrasts, STUDY["diagnosis_gates"]).values())
    contrasts["0.04:untrained:accuracy"] = module.interval([0] * 5, .99375)
    assert not module.primary_gates(contrasts, STUDY["diagnosis_gates"])["0.04:untrained:accuracy"]
    del contrasts["0.04:full:retained"]
    assert not module.primary_gates(contrasts, STUDY["diagnosis_gates"])["all_eight_endpoints"]
    path = tmp_path / "analysis.json"
    module.persist(path, {"value": 1}); before = path.read_bytes(); module.persist(path, {"value": 1})
    assert path.read_bytes() == before
    with pytest.raises(ValueError): module.persist(path, {"value": 2})


def test_exact_fit_gate_rejects_tiny_decoder_loss_or_weight_drift():
    module = analyzer()
    report = {"initial_parameters_sha256": "init", "final_encoder_sha256": "trained", "alignment_losses": [.1,.05], "optimizer_steps": 2, "final_decoder_sha256": "decoder", "dense_set_losses": [.2,.1], "pca_projection_sha256": "PCA", "pca_grid": [{"rank":16}], "pca_choice": {"rank":16}, "fp32_ridge_weights_sha256": "ridge"}
    arms = ["transport_pca", "transport_full", "transport_pca_untrained", "transport_pca_shuffled", "dense", "dense_cached_cpu", "dense_cached_cuda", "delta", "ridge32", "ridge_pca_scan", "ridge_pca_tree"]
    reports = {a: dict(report) for a in arms}
    reports["transport_pca_untrained"].update(final_encoder_sha256="init", optimizer_steps=0, alignment_losses=[])
    assert all(module.exact_fit_checks(reports, 2, 2).values())
    reports["dense_cached_cpu"]["dense_set_losses"] = [.2, .10000000000000001 + 1e-8]
    assert not module.exact_fit_checks(reports, 2, 2)["exact_dense_cache_fit"]


def test_v6_freshness_rejects_last_consumed_unit_without_changing_old_scope():
    from nextai_autoresearch.research_program import verify_pvm01_fresh_realization
    previous = json.loads((ROOT / "research/laboratory/archive/EXP-20261004-0008-runtime/research/tmp/EXP-20261004-0008/runtime-plan.json").read_text())
    seeds = [previous["matrix"]["seeds"][0], 31001, 31002, 31003, 31004]
    nonces = [f"{i:064x}" for i in range(31001, 31006)]
    verify_pvm01_fresh_realization(ROOT, seeds, nonces)
    with pytest.raises(ValueError, match="collision"):
        verify_pvm01_fresh_realization(ROOT, seeds, nonces, include_latest=True)
    reports["dense_cached_cpu"]["dense_set_losses"] = [.2,.1]
    reports["dense_cached_cuda"]["final_decoder_sha256"] = "different"
    assert not module.exact_fit_checks(reports, 2, 2)["exact_dense_cache_fit"]
