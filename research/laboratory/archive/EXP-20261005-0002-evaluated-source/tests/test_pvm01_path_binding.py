"""Runtime JSON/worker regression without research data generation or fit."""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from nextai_autoresearch.benchmarks import paired_view_mutable_memory_v1 as legacy
from nextai_autoresearch.benchmarks import paired_view_mutable_memory_v2 as repaired
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import atomic_write_json, sha256_file

ROOT = Path(__file__).resolve().parents[1]


class FitBoundary(Exception):
    """A test stops before any research data/model/optimizer access."""


@pytest.fixture
def bound_runtime(tmp_path, monkeypatch):
    plan = json.loads((ROOT / "research/plans/EXP-20261004-0004.json").read_text())
    plan.update(experiment_id="EXP-20990101-9999", benchmark=repaired.BENCHMARK_VERSION)
    plan["matrix"]["seeds"] = [101, 102, 103, 104, 105]
    private = tmp_path / "research/tmp" / plan["experiment_id"] / "pvm01-private-data.json"
    atomic_write_json(private, {"experiment_id": plan["experiment_id"],
                                "unit_nonces": [f"{i:064x}" for i in range(5)]})
    plan.update(pvm01_private_data_path=str(private), pvm01_private_data_sha256=sha256_file(private))
    monkeypatch.setattr(repaired, "project_root", lambda: tmp_path)
    monkeypatch.setattr(legacy.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(legacy.torch.backends.cuda.matmul, "allow_tf32", False)

    def forbidden(*args, **kwargs):
        pytest.fail("Research data generation or model construction reached by boundary test")

    for name in ("pairs", "episode", "training_sets"):
        monkeypatch.setattr(legacy, name, forbidden)
    from nextai_autoresearch.candidates.pvm01_core import Candidate
    monkeypatch.setattr(Candidate, "__init__", forbidden)
    return plan, private


def stop_before_fit(phase):
    assert phase == "fit"
    raise FitBoundary("No scientific data or model accessed")


@pytest.mark.parametrize("path_type", [str, Path])
def test_bound_json_path_reaches_same_pre_fit_boundary(bound_runtime, path_type):
    plan, private = bound_runtime
    plan["pvm01_private_data_path"] = path_type(private)
    with pytest.raises(FitBoundary):
        repaired.run_suite("pvm01_dense_s0", plan, phase_sink=stop_before_fit)
    assert isinstance(plan["pvm01_private_data_path"], path_type)


def test_legacy_json_failure_is_reproduced_without_research_fit(bound_runtime):
    plan, private = bound_runtime
    with pytest.raises(AttributeError, match="open"):
        legacy.run_suite("pvm01_dense_s0", plan, phase_sink=stop_before_fit)
    with pytest.raises(FitBoundary):
        legacy.run_suite("pvm01_dense_s0", {**plan, "pvm01_private_data_path": private}, phase_sink=stop_before_fit)


@pytest.mark.parametrize("corruption", ["hash", "identity", "outside", "traversal"])
def test_bad_runtime_binding_rejected_before_fit(bound_runtime, tmp_path, corruption):
    plan, private = bound_runtime
    if corruption == "hash":
        plan["pvm01_private_data_sha256"] = "0" * 64
    elif corruption == "identity":
        atomic_write_json(private, {"experiment_id": "EXP-20990101-9998", "unit_nonces": ["0" * 64] * 5})
        plan["pvm01_private_data_sha256"] = sha256_file(private)
    elif corruption == "outside":
        outside = tmp_path / "outside.json"
        outside.write_bytes(private.read_bytes())
        plan["pvm01_private_data_path"] = str(outside)
    else:
        plan["experiment_id"] = "../outside"
    with pytest.raises(ValueError, match="(binding|path|identity)"):
        repaired.run_suite("pvm01_dense_s0", plan, phase_sink=stop_before_fit)


def test_real_worker_consumes_serialized_runtime_and_stops_before_fit(bound_runtime, tmp_path, monkeypatch):
    from nextai_autoresearch.worker import run_worker
    from nextai_autoresearch import worker_resources
    plan, _ = bound_runtime
    phases = []

    class TestResources:
        def __init__(self, *args):
            pass

        def start(self):
            phases.append("start")

        def phase(self, phase):
            phases.append(phase)
            stop_before_fit(phase)

        def check(self):
            pytest.fail("Boundary should stop before final resource check")

        def close(self):
            phases.append("close")

    monkeypatch.setattr(worker_resources, "WorkerResources", TestResources)
    runtime, output = tmp_path / "runtime-plan.json", tmp_path / "worker.json"
    atomic_write_json(runtime, plan)
    assert run_worker(runtime, "pvm01_dense_s0", output) == 1
    result = json.loads(output.read_text())
    assert result["error_type"] == "FitBoundary" and result["trials"] == []
    assert "paired_view_mutable_memory_v2.py" in result["traceback"]
    assert phases == ["start", "fit", "close"]
    assert not output.with_suffix(".fits.jsonl").exists()
    assert not output.with_suffix(".data.jsonl").exists()
    assert not output.with_suffix(".trials.jsonl").exists()


def test_v2_schema_preserves_frozen_matrix_and_compute_requirements():
    plan = json.loads((ROOT / "research/plans/EXP-20261004-0004.json").read_text())
    plan["benchmark"] = repaired.BENCHMARK_VERSION
    validate_document("experiment_plan", plan, ROOT)
    for field in ("compute_charge_basis", "task_contract_path", "task_contract_sha256"):
        changed = copy.deepcopy(plan)
        del changed["research_program_protocol"][field]
        with pytest.raises(ValidationError):
            validate_document("experiment_plan", changed, ROOT)
    changed = copy.deepcopy(plan)
    changed["matrix"]["reasoning_depths"] = [1, 2, 4]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", changed, ROOT)


def test_failed_v1_source_core_and_result_remain_byte_exact():
    preserved = {
        "src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v1.py": "98568a00c81fc70a79227d3a1a98b3c6a52bae772b38cef57a8837957dfe7a59",
        "src/nextai_autoresearch/candidates/pvm01_core.py": "773bf869e9dd2a5dea9bdcbf7dfbc32cdb79745634603dc57b7571f0dbf9fa15",
        "research/results/EXP-20261004-0004.json": "264183fa8c6d970f432f071b0719e9d76ddce2a8915b7606e26aa53b704a7bf0",
    }
    for relative, digest in preserved.items():
        assert sha256_file(ROOT / relative) == digest
