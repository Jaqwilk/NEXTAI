import copy
import importlib.util
import json
from pathlib import Path

from jsonschema.exceptions import ValidationError
import pytest

from nextai_autoresearch.benchmarks import paired_view_mutable_memory_v7 as replica
from nextai_autoresearch.research_program import _study_scope, verify_pvm01_fresh_realization
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import sha256_file

ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT / "research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json").read_text())


def analyzer(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("replication_analyzer_fixture", ROOT / "scripts/analyze_pvm01_replication.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_replication_delegates_unchanged_suite_and_every_sink(monkeypatch):
    received = []
    monkeypatch.setattr(replica.selected, "run_suite", lambda *args: received.append(args) or "result")
    plan = {"benchmark": replica.BENCHMARK_VERSION}
    sinks = [object() for _ in range(4)]
    assert replica.run_suite("candidate", plan, *sinks) == "result"
    assert received == [("candidate", plan, *sinks)]
    with pytest.raises(ValueError, match="cohort"):
        replica.run_suite("candidate", {"benchmark": "paired_view_mutable_memory_v6"}, *sinks)
    assert len(received) == 1


@pytest.mark.parametrize("change", ["missing", "old_path", "old_hash", "old_pair"])
def test_replication_schema_rejects_crossed_or_missing_bindings(change):
    plan = json.loads((ROOT / "research/plans/EXP-20261005-0001.json").read_text())
    old = copy.deepcopy(plan["research_program_protocol"])
    plan["benchmark"] = STUDY["cohort"]
    plan["research_program_protocol"].update(_study_scope(STUDY))
    validate_document("experiment_plan", plan, ROOT)
    protocol = plan["research_program_protocol"]
    if change == "missing":
        del protocol["classical_economic_contract_sha256"]
    else:
        for key in ("classical_economic_contract_path", "classical_economic_contract_sha256"):
            if change == "old_pair" or change == "old_path" and key.endswith("path") or change == "old_hash" and key.endswith("sha256"):
                protocol[key] = old[key]
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", plan, ROOT)


def test_historical_v6_binding_remains_required():
    plan = json.loads((ROOT / "research/plans/EXP-20261005-0001.json").read_text())
    validate_document("experiment_plan", plan, ROOT)
    plan["research_program_protocol"].update(_study_scope(STUDY))
    with pytest.raises(ValidationError):
        validate_document("experiment_plan", plan, ROOT)


@pytest.fixture
def historic_units(tmp_path):
    identities = [f"EXP-20261004-{i:04d}" for i in range(4, 9)] + ["EXP-20261005-0001"]
    directories = {}
    for i, identity in enumerate(identities):
        directory = tmp_path / f"research/laboratory/archive/{identity}-runtime"
        if identity != "EXP-20261004-0005":
            directory /= f"research/tmp/{identity}"
        directory.mkdir(parents=True)
        private = directory / "pvm01-private-data.json"
        private.write_text(json.dumps({"experiment_id": identity, "unit_nonces": [f"{1000+i:064x}"]}))
        (directory / "runtime-plan.json").write_text(json.dumps({"experiment_id": identity,
            "matrix": {"seeds": [1000+i]}, "pvm01_private_data_sha256": sha256_file(private)}))
        directories[identity] = directory
    return tmp_path, directories, [9000+i for i in range(5)], [f"{9000+i:064x}" for i in range(5)]


def test_latest_replication_history_checked_without_widening_v6(historic_units):
    root, _, seeds, nonces = historic_units
    verify_pvm01_fresh_realization(root, seeds, nonces, include_latest=True, include_transport=True)
    seeds[0] = 1005
    verify_pvm01_fresh_realization(root, seeds, nonces, include_latest=True)
    with pytest.raises(ValueError, match="collision"):
        verify_pvm01_fresh_realization(root, seeds, nonces, include_latest=True, include_transport=True)


@pytest.mark.parametrize("change", ["nonce", "tamper", "missing", "scope"])
def test_replication_freshness_fails_closed(historic_units, change):
    root, directories, seeds, nonces = historic_units
    private = directories["EXP-20261005-0001"] / "pvm01-private-data.json"
    if change == "nonce":
        nonces[0] = f"{1005:064x}"
    elif change == "tamper":
        private.write_text(private.read_text() + " ")
    elif change == "missing":
        private.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        verify_pvm01_fresh_realization(root, seeds, nonces, include_latest=change != "scope", include_transport=True)


def fixture_analysis():
    arms = {}
    for arm in ("ridge_pca_scan", "dense", "dense_cached_cpu", "dense_cached_cuda", "ridge", "ridge32", "ridge_pca_tree", "kernel", "transport_pca"):
        cost = 1 if arm == "ridge_pca_scan" else 10 if "dense" in arm else 2
        cell = {"accuracy": .99, "unknown": .99, "false_abstention": .001,
                "full_workload_seconds": cost, "p95_us": cost * 10, "state_bytes": 100}
        unit = {**cell, "by_K": {str(k): copy.deepcopy(cell) for k in (32, 128, 512)}}
        arms[arm] = {noise: {str(i): copy.deepcopy(unit) for i in range(5)} for noise in ("0.02", "0.04")}
    return {"valid_comparison": True, "arms": arms}


def test_selected_route_fixed_family_sizes_and_all_guards(monkeypatch):
    result = analyzer(monkeypatch).confirm_selected_route(fixture_analysis(), STUDY)
    assert result["screen_qualified"] and result["family_sizes_ok"]
    assert len(result["economic_simultaneous_intervals"]) == 18
    assert len(result["matched_quality_intervals"]) * 2 == 60
    assert not result["economic_advantage_claim"] and not result["families_joint_95_percent_claim"]


@pytest.mark.parametrize("change", ["quality", "unknown", "false_abstention", "cost", "p95", "dominator", "missing", "invalid", "reference"])
def test_selected_route_rejects_unqualified_or_incomplete_evidence(monkeypatch, change):
    analysis = fixture_analysis()
    arm = "ridge" if change == "dominator" else "dense_cached_cpu" if change == "reference" else "ridge_pca_scan"
    if change == "invalid":
        analysis["valid_comparison"] = False
    elif change == "missing":
        del analysis["arms"][arm]["0.02"]["0"]
    else:
        field, value = {"quality": ("accuracy", .93), "unknown": ("unknown", .94),
            "false_abstention": ("false_abstention", .03), "cost": ("full_workload_seconds", 9),
            "p95": ("p95_us", 95), "dominator": ("full_workload_seconds", .5),
            "reference": ("accuracy", .8)}[change]
        for units in analysis["arms"][arm].values():
            for unit in units.values():
                unit[field] = value
                for cell in unit["by_K"].values():
                    cell[field] = value
    result = analyzer(monkeypatch).confirm_selected_route(analysis, STUDY)
    assert not result["screen_qualified"]
    if change == "dominator":
        assert result["matched_quality_dominators"] == ["ridge"]


def test_all_scientific_sources_identical_to_preregistered_parent():
    expected = STUDY["independent_replication"]["scientific_source_sha256_unchanged"]
    assert len(expected) == 80
    assert all(sha256_file(ROOT / path) == digest for path, digest in expected.items())
