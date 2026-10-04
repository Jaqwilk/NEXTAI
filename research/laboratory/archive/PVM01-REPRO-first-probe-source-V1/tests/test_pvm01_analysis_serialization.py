"""Regression of stored-result serialization; no model or data generation."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from nextai_autoresearch.utils import atomic_write_json, sha256_file, sha256_json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("pvm01_analysis_v2_test", ROOT / "scripts/analyze_pvm01_reference_v2.py")
repaired = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repaired)


def test_numeric_unit_keys_and_existing_analysis_use_same_json_representation(tmp_path, monkeypatch):
    value = {"arms": {"pointer": {0: {"accuracy": 0.5}}}, "learning_gate": False}
    monkeypatch.setattr(repaired, "legacy_analyze", lambda *args: value)
    destination = tmp_path / "research/reviews/EXP-20990101-9999-PVM01-reference-analysis.json"
    atomic_write_json(destination, json.loads(json.dumps(value)))
    before = sha256_file(destination)
    result = repaired.persist(tmp_path, "EXP-20990101-9999")
    assert result["arms"]["pointer"]["0"]["accuracy"] == 0.5
    assert sha256_file(destination) == before


def test_different_existing_analysis_is_rejected_without_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(repaired, "legacy_analyze", lambda *args: {"arms": {0: 0.5}})
    destination = tmp_path / "research/reviews/EXP-20990101-9999-PVM01-reference-analysis.json"
    atomic_write_json(destination, {"arms": {"0": 0.4}})
    before = sha256_file(destination)
    with pytest.raises(ValueError, match="preserve"):
        repaired.persist(tmp_path, "EXP-20990101-9999")
    assert sha256_file(destination) == before


@pytest.mark.parametrize("experiment_id", ["EXP-20261004-0004", "EXP-20261004-0005"])
def test_real_completed_and_failed_analysis_reproduces_without_write(experiment_id):
    destination = ROOT / "research/reviews" / f"{experiment_id}-PVM01-reference-analysis.json"
    before = sha256_file(destination)
    stored = json.loads(destination.read_text(encoding="utf-8"))
    result = repaired.persist(ROOT, experiment_id)
    assert result == stored
    assert sha256_json(result) == sha256_json(repaired.legacy_analyze(ROOT, experiment_id))
    assert sha256_file(destination) == before


def test_prospective_repair_preserves_frozen_v1_science_and_results():
    plan = json.loads((ROOT / "research/plans/PVM01-ANALYSIS-SERIALIZATION-REPAIR-V1.json").read_text())
    for relative, digest in plan["unchanged_raw_sha256"].items():
        assert sha256_file(ROOT / relative) == digest
