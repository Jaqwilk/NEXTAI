import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.benchmarks import paired_view_mutable_memory_v8 as suite
from nextai_autoresearch.candidates.pvm01_dense_noise_core import Candidate, arrays_hash, mixed_training_sets
from nextai_autoresearch.candidates.pvm01_repro_core import Candidate as Reference
from nextai_autoresearch.candidates.pvm01_core import parameter_hash
from nextai_autoresearch.config import load_config
from nextai_autoresearch.integrity import protected_files
from nextai_autoresearch.research_program import _study_scope, verify_pvm01_fresh_realization
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import sha256_file

ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT / "research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json").read_text())
POLICY = STUDY["recipe"]["dense_noise_augmentation"]


def analyzer(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("dense_noise_analysis_fixture", ROOT / "scripts/analyze_pvm01_dense_noise.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixed_sets():
    rng = np.random.default_rng(314)
    return {k: (rng.normal(0, .02, (128, k, 64)).astype(np.float32),
                rng.normal(0, .02, (128, 8, 64)).astype(np.float32),
                np.tile(np.array([0, 1, 2, 3, 4, 5, k, k], dtype=np.int64), (128, 1))) for k in (32, 128)}


def test_augmentation_preserves_labels_shapes_inputs_and_noise_law():
    sets = fixed_sets()
    hashes = {k: arrays_hash(*v) for k, v in sets.items()}
    changed = mixed_training_sets(sets, 1103, POLICY)
    assert {k: arrays_hash(*v) for k, v in sets.items()} == hashes
    for k, values in changed.items():
        np.testing.assert_array_equal(values[2], sets[k][2])
        for a, b in zip(values[:2], sets[k][:2], strict=True):
            np.testing.assert_array_equal(a[::2], b[::2])
            assert not np.array_equal(a[1::2], b[1::2]) and not np.shares_memory(a, b)
            assert abs(float(a[::2].std()) - .02) < .001
            assert abs(float(a[1::2].std()) - .04) < .001
            assert abs(float((a[1::2] - b[1::2]).std()) - POLICY["independent_added_gaussian_std"]) < .001


def test_augmentation_is_seeded_independent_and_does_not_touch_torch_rng():
    sets = fixed_sets()
    torch.manual_seed(1709)
    before = torch.random.get_rng_state().clone()
    first = mixed_training_sets(sets, 1103, POLICY)
    assert torch.equal(before, torch.random.get_rng_state())
    same = mixed_training_sets(sets, 1103, POLICY)
    other = mixed_training_sets(sets, 1709, POLICY)
    assert all(arrays_hash(*first[k]) == arrays_hash(*same[k]) != arrays_hash(*other[k]) for k in sets)
    assert all(np.array_equal(first[k][2], other[k][2]) for k in sets)


@pytest.mark.parametrize("change", ["missing", "extra", "shape", "dtype", "target_dtype", "nonfinite"])
def test_augmentation_rejects_noncontract_inputs(change):
    sets = fixed_sets()
    if change == "missing":
        del sets[128]
    elif change == "extra":
        sets[512] = sets[128]
    else:
        values = list(sets[32])
        if change == "shape": values[0] = values[0][:-1]
        elif change == "dtype": values[1] = values[1].astype(np.float64)
        elif change == "target_dtype": values[2] = values[2].astype(np.int32)
        else: values[0][0, 0, 0] = np.nan
        sets[32] = tuple(values)
    with pytest.raises(ValueError): mixed_training_sets(sets, 1103, POLICY)


def test_mixed_dense_cache_fit_is_exact_and_alignment_is_unchanged(monkeypatch):
    recipe = {**STUDY["recipe"], "alignment_steps": 2, "dense_set_steps": 2, "alignment_batch": 8}
    rng = np.random.default_rng(3141)
    writes = rng.normal(size=(32, 64)).astype(np.float32)
    queries, sets = writes[:, ::-1].copy(), fixed_sets()
    reports, initial_decoder = {}, None
    for arm in ("dense", "dense_mixed", "dense_cached_cpu_mixed", "dense_cached_cuda_mixed"):
        system = (Reference if arm == "dense" else Candidate)(1103, arm, recipe)
        system.model, system.decoder = system.model.to("cpu"), system.decoder.to("cpu")
        system.device = torch.device("cpu")
        digest = parameter_hash(system.decoder)
        assert initial_decoder in (None, digest)
        initial_decoder = digest
        reports[arm] = system.fit(writes, queries, writes[:8], queries[:8], sets)
        reports[arm]["final_decoder_sha256"] = parameter_hash(system.decoder)
        reports[arm]["training_sets_sha256"] = {str(k): arrays_hash(*v) for k, v in sets.items()}
    mixed = [reports[a] for a in ("dense_mixed", "dense_cached_cpu_mixed", "dense_cached_cuda_mixed")]
    assert all(r["dense_set_losses"] == mixed[0]["dense_set_losses"] for r in mixed)
    assert all(r["final_decoder_sha256"] == mixed[0]["final_decoder_sha256"] for r in mixed)
    assert mixed[0]["dense_set_losses"] != reports["dense"]["dense_set_losses"]
    assert all(analyzer(monkeypatch).mixed_fit_checks(reports, POLICY, 2, 2).values())
    reports["dense_cached_cpu_mixed"]["dense_set_losses"] = [v + 1e-8 for v in mixed[0]["dense_set_losses"]]
    assert not analyzer(monkeypatch).mixed_fit_checks(reports, POLICY, 2, 2)["same_mixed_fit_and_inputs"]


def test_new_cohort_delegates_unchanged_measurements_and_all_sinks(monkeypatch):
    called = []
    monkeypatch.setattr(suite.selected, "run_suite", lambda *args: called.append(args) or "passed")
    plan, sinks = {"benchmark": suite.BENCHMARK_VERSION}, [object() for _ in range(4)]
    assert suite.run_suite("candidate", plan, *sinks) == "passed"
    assert called == [("candidate", plan, *sinks)]
    with pytest.raises(ValueError): suite.run_suite("candidate", {"benchmark": "paired_view_mutable_memory_v7"}, *sinks)


@pytest.mark.parametrize("change", ["missing", "old_path", "old_hash", "old_pair"])
def test_new_schema_rejects_crossed_bindings_without_changing_history(change):
    plan = json.loads((ROOT / "research/plans/EXP-20261005-0002.json").read_text())
    validate_document("experiment_plan", plan, ROOT)
    original = copy.deepcopy(plan["research_program_protocol"])
    plan["benchmark"] = STUDY["cohort"]
    plan["candidates"] = STUDY["candidates"]
    plan["research_program_protocol"].update(_study_scope(STUDY))
    validate_document("experiment_plan", plan, ROOT)
    protocol = plan["research_program_protocol"]
    if change == "missing": del protocol["classical_economic_contract_sha256"]
    else:
        for key in ("classical_economic_contract_path", "classical_economic_contract_sha256"):
            if change == "old_pair" or change == "old_path" and key.endswith("path") or change == "old_hash" and key.endswith("sha256"):
                protocol[key] = original[key]
    with pytest.raises(ValidationError): validate_document("experiment_plan", plan, ROOT)


@pytest.fixture
def historic_units(tmp_path):
    identities = [f"EXP-20261004-{i:04d}" for i in range(4, 9)] + ["EXP-20261005-0001", "EXP-20261005-0002"]
    directories = {}
    for i, identity in enumerate(identities):
        directory = tmp_path / f"research/laboratory/archive/{identity}-runtime"
        if identity != "EXP-20261004-0005": directory /= f"research/tmp/{identity}"
        directory.mkdir(parents=True)
        private = directory / "pvm01-private-data.json"
        private.write_text(json.dumps({"experiment_id": identity, "unit_nonces": [f"{1000+i:064x}"]}))
        (directory / "runtime-plan.json").write_text(json.dumps({"experiment_id": identity, "matrix": {"seeds": [1000+i]}, "pvm01_private_data_sha256": sha256_file(private)}))
        directories[identity] = directory
    return tmp_path, directories, [9000+i for i in range(5)], [f"{9000+i:064x}" for i in range(5)]


@pytest.mark.parametrize("change", ["seed", "nonce", "tamper", "missing", "scope", "valid"])
def test_latest_history_is_required_before_arrays_without_widening_old_scope(historic_units, change):
    root, directories, seeds, nonces = historic_units
    if change == "seed": seeds[0] = 1006
    elif change == "nonce": nonces[0] = f"{1006:064x}"
    elif change == "tamper":
        private = directories["EXP-20261005-0002"] / "pvm01-private-data.json"
        private.write_text(private.read_text() + " ")
    elif change == "missing": (directories["EXP-20261005-0002"] / "pvm01-private-data.json").unlink()
    if change in ("seed", "nonce", "tamper", "missing"):
        verify_pvm01_fresh_realization(root, seeds, nonces, include_latest=True, include_transport=True)
    if change == "valid":
        verify_pvm01_fresh_realization(root, seeds, nonces, include_latest=True, include_transport=True, include_replication=True)
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            verify_pvm01_fresh_realization(root, seeds, nonces, include_latest=change != "scope", include_transport=True, include_replication=True)


def fixture_analysis():
    arms = {}
    for arm in ("dense", "dense_cached_cpu", "dense_cached_cuda", "dense_mixed", "dense_cached_cpu_mixed", "dense_cached_cuda_mixed"):
        mixed = arm.endswith("_mixed")
        cell = {"accuracy": .99 if mixed else .97, "unknown": .99, "false_abstention": .001 if mixed else .02}
        unit = {**cell, "by_K": {str(k): copy.deepcopy(cell) for k in (32, 128, 512)}}
        arms[arm] = {noise: {str(i): copy.deepcopy(unit) for i in range(5)} for noise in ("0.02", "0.04")}
    return {"valid_comparison": True, "arms": arms}


def test_selection_distinguishes_adequacy_improvement_and_null(monkeypatch):
    module, analysis = analyzer(monkeypatch), fixture_analysis()
    result = module.reference_selection(analysis, STUDY)
    assert result["adequate_for_prospective_selection"] and result["causal_false_abstention_improvement"]
    assert len(result["primary_simultaneous_intervals"]) == 6
    for arm in ("dense", "dense_cached_cpu", "dense_cached_cuda"):
        for units in analysis["arms"][arm].values():
            for unit in units.values(): unit["false_abstention"] = .001
    result = module.reference_selection(analysis, STUDY)
    assert result["adequate_for_prospective_selection"] and not result["causal_false_abstention_improvement"]


@pytest.mark.parametrize("change", ["invalid", "missing", "known_FA", "quality", "unknown", "cache_quality", "wide_interval"])
def test_selection_rejects_unqualified_or_unknown_only_evidence(monkeypatch, change):
    analysis = fixture_analysis()
    if change == "invalid": analysis["valid_comparison"] = False
    elif change == "missing": del analysis["arms"]["dense_mixed"]["0.04"]["0"]
    elif change == "wide_interval": analysis["arms"]["dense_mixed"]["0.04"]["0"]["accuracy"] = .9
    else:
        arm = "dense_cached_cuda_mixed" if change == "cache_quality" else "dense_mixed"
        field, value = {"known_FA": ("false_abstention", .03), "quality": ("accuracy", .8), "unknown": ("unknown", .8), "cache_quality": ("accuracy", .8)}[change]
        analysis["arms"][arm]["0.04"]["0"][field] = value
    result = analyzer(monkeypatch).reference_selection(analysis, STUDY)
    assert not result["adequate_for_prospective_selection"]
    assert not result["causal_false_abstention_improvement"]


def test_all85_roles_audited_and_analyzers_protected_before_data():
    config = load_config(ROOT)
    assert len(STUDY["roles"]) == len(STUDY["candidates"]) == 85
    for name in STUDY["candidates"]:
        result = audit_candidate(name, config, ROOT)
        assert result.ok, result.problems
    protected = protected_files(ROOT)
    assert all(name in protected for name in ("scripts/analyze_pvm01_replication.py", "scripts/run_pvm01_replication_check.py", "scripts/analyze_pvm01_dense_noise.py", "scripts/run_pvm01_dense_noise_check.py"))
    assert all(sha256_file(ROOT / name) == digest for name, digest in STUDY["parent_evidence"]["scientific_source_sha256_unchanged"].items())
