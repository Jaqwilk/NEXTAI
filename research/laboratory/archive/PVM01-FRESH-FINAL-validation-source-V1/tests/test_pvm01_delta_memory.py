import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from torch.nn import functional as F

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.candidates.pvm01_delta_core import Candidate as Memory, Session
from nextai_autoresearch.candidates.pvm01_optimized_core import Candidate as Optimized
from nextai_autoresearch.benchmarks.paired_view_mutable_memory_v3 import scores, bound_private_path
from nextai_autoresearch.utils import atomic_write_json, sha256_file

ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT / "research/plans/PVM01-DELTA-MEMORY-SCREEN-V1.json").read_text())


def test_delta_overwrites_orthogonal_association_additive_retains_stale_content():
    left, right = Memory(29, "delta", STUDY["recipe"]), Memory(29, "additive", STUDY["recipe"])
    left.arm, right.arm = "delta", "additive"
    # Fixed algebra fixture, not generated PVM train/dev or a scored recipe.
    basis = np.eye(STUDY["recipe"]["memory_feature_dimension"], dtype=np.float32)
    for model in (left, right):
        model.feature = lambda x: basis[int(x[0])]
    first, second = np.zeros(64, np.float32), np.zeros(64, np.float32)
    second[0] = 1
    sessions = [Session(m, 2) for m in (left, right)]
    for session in sessions:
        for row in [(0, 100, first, 3), (1, 200, second, 7), (2, 100, first, 11)]:
            session.ingest(row)
        previous = session.memory.copy()
        session.ingest((1, 100, second, 2))
        np.testing.assert_array_equal(previous, session.memory)
    assert sessions[0].memory[0, 11] == 1 and sessions[0].memory[0, 3] == 0
    assert sessions[1].memory[0, 11] == sessions[1].memory[0, 3] == 1
    assert sessions[0].memory[1, 7] == sessions[1].memory[1, 7] == 1
    assert not any(hasattr(sessions[0], key) for key in ("keys", "values", "labels"))


def test_shared_fitted_transport_and_random_features_are_exactly_identical():
    recipe = copy.deepcopy(STUDY["recipe"])
    recipe["alignment_steps"] = 2
    rng = np.random.default_rng(73)
    query = rng.normal(size=(64, 64)).astype(np.float32)
    write = query[:, ::-1].copy()
    models = [Memory(911, arm, recipe) for arm in ("delta", "additive", "delta_shuffled", "delta_untrained")]
    for model in models:
        model.fit(write, query, write[:12], query[:12])
    assert models[0].report["alignment_losses"] == models[1].report["alignment_losses"]
    assert models[0].report["final_encoder_sha256"] == models[1].report["final_encoder_sha256"]
    assert len({m.feature_hash for m in models}) == 1
    assert models[0].report["final_encoder_sha256"] != models[2].report["final_encoder_sha256"]
    assert models[3].report["optimizer_steps"] == 0
    assert np.linalg.norm(models[0].feature(write[0])) == pytest.approx(1, abs=1e-6)
    assert models[0].device.type == "cpu"


@pytest.mark.parametrize("size", [32, 128])
def test_dense_cache_matches_conventional_decoder_with_nonzero_projections_and_updates(size):
    model = Optimized(139, "dense_cached_cpu", STUDY["recipe"])
    model.arm = model.optimized_arm
    model.model = model.model.cpu().eval()
    model.decoder = model.decoder.cpu().eval()
    model.device = torch.device("cpu")
    for block in model.decoder.layers:
        for projection in (block.self_attn.out_proj, block.multihead_attn.out_proj, block.linear2):
            torch.nn.init.normal_(projection.weight, std=.02)
            torch.nn.init.normal_(projection.bias, std=.02)
    rng = np.random.default_rng(263)
    writes = rng.normal(size=(size, 64)).astype(np.float32)
    session = model.new_session(size)
    for i, row in enumerate(writes):
        session.ingest((i, 1000+i, row, i % 16))
    session.ingest((size, 1000, writes[-1], 13))
    cache = [(k.clone(), v.clone()) for k, v in session.cache]
    session.ingest((0, 1000, writes[0], 2))
    assert all(torch.equal(a, c) and torch.equal(b, d) for (a, b), (c, d) in zip(cache, session.cache))
    with torch.inference_mode():
        for q in rng.normal(size=(4, 64)).astype(np.float32):
            embedded = F.normalize(model.model(torch.as_tensor(q)), dim=-1)
            expected = model.refine(embedded[None, None], session.keys[None])[0, 0]
            actual = session.decoded(embedded)
            torch.testing.assert_close(actual, expected, atol=1e-5, rtol=1e-5)
    assert session.state_bytes() >= 4 * size * 64 * 4


def test_pca_tree_exact_scan_and_mutation_invalidation_charge_own_copies():
    rng = np.random.default_rng(31)
    query = rng.normal(size=(96, 64)).astype(np.float32)
    write = query[:, ::-1].copy()
    systems = [Optimized(21, arm, STUDY["recipe"]) for arm in ("ridge_pca_scan", "ridge_pca_tree")]
    for model in systems:
        model.fit(write, query, write[:12], query[:12])
    np.testing.assert_array_equal(systems[0].projection, systems[1].projection)
    np.testing.assert_array_equal(systems[0].weights, systems[1].weights)
    sessions = [m.new_session(8) for m in systems]
    for session in sessions:
        for i in range(8):
            session.ingest((i, 100+i, write[i], i))
    for q in query[:8]:
        assert sessions[0].read(q)[0:1] == sessions[1].read(q)[0:1]
    assert sessions[1].tree.data.dtype == np.float64
    assert sessions[1].state_bytes() > sessions[0].state_bytes()
    sessions[0].ingest((9, 100, write[8], 13))
    sessions[1].ingest((9, 100, write[8], 13))
    assert sessions[1].dirty
    assert sessions[0].read(query[8]) == sessions[1].read(query[8])
    assert not sessions[1].dirty


def test_compact_value_accuracy_never_implies_record_selection():
    rows = [dict(answer=3, truth=3, top_handle=None, target_handle=11, top_value=3, stratum="updated"),
            dict(answer=-1, truth=-1, top_handle=None, target_handle=None, top_value=2, stratum="absent")]
    result = scores(rows, compact=True)
    assert result["accuracy"] == result["updated_known_accuracy"] == result["dense_unknown_rejection"] == 1
    assert result["fact_top1_accuracy"] is None and result["wrong_fact_errors"] is None
    assert not result["fact_handle_diagnostics_applicable"]


def test_private_path_binding_rejects_wrong_identity_and_hash(tmp_path, monkeypatch):
    import nextai_autoresearch.benchmarks.paired_view_mutable_memory_v3 as benchmark
    monkeypatch.setattr(benchmark, "project_root", lambda: tmp_path)
    identity = "EXP-20261004-9901"
    private = tmp_path / "research/tmp" / identity / "pvm01-private-data.json"
    atomic_write_json(private, {"experiment_id": identity, "unit_nonces": ["fixed-conformance"] * 5})
    plan = dict(experiment_id=identity, pvm01_private_data_path=str(private), pvm01_private_data_sha256=sha256_file(private))
    assert len(bound_private_path(plan)["unit_nonces"]) == 5
    with pytest.raises(ValueError):
        bound_private_path({**plan, "pvm01_private_data_sha256": "0"*64})
    with pytest.raises(ValueError):
        bound_private_path({**plan, "experiment_id": "EXP-20261004-9902"})


def test_real_v3_worker_reads_serialized_path_and_stops_before_data_or_model(tmp_path, monkeypatch):
    import nextai_autoresearch.benchmarks.paired_view_mutable_memory_v3 as benchmark
    from nextai_autoresearch.worker import run_worker
    from nextai_autoresearch import worker_resources
    from nextai_autoresearch.research_program import _study_scope
    identity = "EXP-20990101-9999"
    monkeypatch.setattr(benchmark, "project_root", lambda: tmp_path)
    private = tmp_path / "research/tmp" / identity / "pvm01-private-data.json"
    atomic_write_json(private, {"experiment_id": identity, "unit_nonces": [f"{i:064x}" for i in range(5)]})
    plan = {"experiment_id": identity, "benchmark": STUDY["cohort"],
            "matrix": {**STUDY["matrix"], "seeds": [101, 102, 103, 104, 105]},
            "research_program_protocol": _study_scope(STUDY),
            "pvm01_private_data_path": str(private), "pvm01_private_data_sha256": sha256_file(private)}
    phases = []

    class Boundary(Exception):
        pass

    class Resources:
        def __init__(self, *args):
            pass
        def start(self):
            phases.append("start")
        def phase(self, name):
            phases.append(name)
            raise Boundary("Fixture stops before arrays or model fit")
        def check(self):
            pytest.fail("Fixture cannot complete a model execution")
        def close(self):
            phases.append("close")

    def forbidden(*args, **kwargs):
        pytest.fail("Pre-seed conformance accessed research arrays or model")

    for name in ("pairs", "episode", "training_sets"):
        monkeypatch.setattr(benchmark, name, forbidden)
    monkeypatch.setattr(worker_resources, "WorkerResources", Resources)
    runtime, output = tmp_path / "runtime.json", tmp_path / "worker.json"
    atomic_write_json(runtime, plan)
    assert run_worker(runtime, "pvm01_delta_s0", output) == 1
    result = json.loads(output.read_text())
    assert result["error_type"] == "Boundary" and result["trials"] == []
    assert "paired_view_mutable_memory_v3.py" in result["traceback"]
    assert phases == ["start", "fit", "close"]
    assert not output.with_suffix(".data.jsonl").exists()
    assert not output.with_suffix(".fits.jsonl").exists()


def test_v3_schema_rejects_changed_matrix_or_missing_full_compute_contract():
    from jsonschema import ValidationError
    from nextai_autoresearch.schemas import validate_document
    from nextai_autoresearch.research_program import _study_scope
    plan = json.loads((ROOT / "research/plans/EXP-20261004-0005.json").read_text())
    plan.update(benchmark=STUDY["cohort"], matrix=STUDY["matrix"], candidates=STUDY["candidates"])
    plan["research_program_protocol"].update(_study_scope(STUDY),
        study_path="research/plans/PVM01-DELTA-MEMORY-SCREEN-V1.json",
        study_sha256=sha256_file(ROOT / "research/plans/PVM01-DELTA-MEMORY-SCREEN-V1.json"))
    validate_document("experiment_plan", plan, ROOT)
    changed = copy.deepcopy(plan)
    changed["matrix"]["reasoning_depths"] = [1, 2, 4]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", changed, ROOT)
    changed = copy.deepcopy(plan)
    del changed["research_program_protocol"]["compute_charge_basis"]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", changed, ROOT)


@pytest.mark.parametrize("collision", ["none", "seed", "nonce", "duplicate"])
def test_new_units_reject_consumed_realizations_without_replacement(tmp_path, collision):
    from nextai_autoresearch.research_program import verify_pvm01_fresh_realization
    paths = {
        "EXP-20261004-0004": "research/laboratory/archive/EXP-20261004-0004-runtime/research/tmp/EXP-20261004-0004",
        "EXP-20261004-0005": "research/laboratory/archive/EXP-20261004-0005-runtime",
        "EXP-20261004-0006": "research/laboratory/archive/EXP-20261004-0006-runtime/research/tmp/EXP-20261004-0006",
        "EXP-20261004-0007": "research/laboratory/archive/EXP-20261004-0007-runtime/research/tmp/EXP-20261004-0007",
    }
    for index, (identity, relative) in enumerate(paths.items()):
        directory = tmp_path / relative
        private = directory / "pvm01-private-data.json"
        atomic_write_json(private, {"experiment_id": identity, "unit_nonces": [f"{index+1:064x}"]*5})
        atomic_write_json(directory / "runtime-plan.json", {
            "experiment_id": identity, "matrix": {"seeds": [101+index]},
            "pvm01_private_data_sha256": sha256_file(private)})
    seeds, nonces = list(range(1001, 1006)), [f"{i:064x}" for i in range(2001, 2006)]
    if collision == "seed":
        seeds[0] = 101
    elif collision == "nonce":
        nonces[0] = f"{1:064x}"
    elif collision == "duplicate":
        nonces[0] = nonces[1]
    if collision == "none":
        verify_pvm01_fresh_realization(tmp_path, seeds, nonces)
    else:
        with pytest.raises(ValueError):
            verify_pvm01_fresh_realization(tmp_path, seeds, nonces)


def test_all_new_roles_audited_and_scope_budget_matches_frozen_cap():
    config = load_config(ROOT)
    for name in STUDY["candidates"]:
        result = audit_candidate(name, config, ROOT)
        assert result.ok, (name, result.problems)
    assert len(STUDY["roles"]) == 75
    assert 75 * STUDY["resources"]["worker_charge_ceiling_with_monitor_margin"] == STUDY["resources"]["fit_seconds_study_cap"]
    assert STUDY["economic_gates"]["full_workload_latency_ratio_simultaneous_upper_max"] == .8


def test_compact_json_preserves_all_values_and_default_serialization(tmp_path):
    value = {"a": list(range(12)), "b": {"none": None, "unicode": "żółć"}}
    left, right = tmp_path / "default.json", tmp_path / "compact.json"
    atomic_write_json(left, value)
    atomic_write_json(right, value, compact=True)
    assert json.loads(left.read_text()) == json.loads(right.read_text()) == value
    assert b'\n  "a"' in left.read_bytes() and right.stat().st_size < left.stat().st_size


def test_preregistered_primary_gate_detects_retention_failure_and_serialization(tmp_path):
    spec = importlib.util.spec_from_file_location("delta_analysis_fixture", ROOT / "scripts/analyze_pvm01_delta_memory.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    good = {"updated": module.interval([.25]*5, .9875), "retained": module.interval([0]*5, .9875),
            "untrained": module.interval([.75]*5, .9875), "shuffled": module.interval([.75]*5, .9875)}
    assert all(module.primary_gates(good, STUDY["diagnosis_gates"]).values())
    good["retained"] = module.interval([-.03]*5, .9875)
    assert not module.primary_gates(good, STUDY["diagnosis_gates"])["retention_noninferiority"]
    path = tmp_path / "analysis.json"
    module.persist(path, {1: {"sample": None}})
    before = path.read_bytes()
    module.persist(path, {1: {"sample": None}})
    assert path.read_bytes() == before
    with pytest.raises(ValueError):
        module.persist(path, {1: {"sample": 1}})
