"""Public synthetic cost receipts only; never invoke the scientific driver."""
import importlib.util
import json
from pathlib import Path

import pytest

from nextai_autoresearch.utils import atomic_write_json


@pytest.fixture
def driver():
    path = Path(__file__).resolve().parents[1] / "scripts/run_c_science.py"
    spec = importlib.util.spec_from_file_location("c_scientific_driver_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _result(base, rows):
    path = base / "research/results/EXP-SYNTHETIC.json"
    atomic_write_json(path, {"candidates": rows})
    return path


def _row(name, full, fit, **execution):
    return {"candidate": name, "status": "crash", "execution": {
        "started": True, "research_compute_seconds": full, "supervised_fit_seconds": fit, **execution}}


def test_registration_failure_has_explicit_no_worker_identity(driver, tmp_path):
    assert driver.worker_costs(tmp_path, None) == (0., 0., 0)


def test_complete_result_keeps_failed_partial_and_skips_only_explicit_unstarted(driver, tmp_path):
    rows = [_row("complete", 8., 2.), _row("failed_partial", 3., 0.),
            {"candidate": "unstarted", "status": "not_started_stage_stop", "execution": {"started": False}}]
    _result(tmp_path, rows)
    assert driver.worker_costs(tmp_path, "EXP-SYNTHETIC") == (11., 2., 3)


def test_partial_supervisors_preserved_without_result(driver, tmp_path):
    directory = tmp_path / "research/tmp/EXP-SYNTHETIC"
    atomic_write_json(directory / "first.supervisor.json", _row("first", 4., 1.))
    atomic_write_json(directory / "crash.supervisor.json", _row("crash", 7., 2.))
    assert driver.worker_costs(tmp_path, "EXP-SYNTHETIC") == (11., 3., 2)


def test_wall_fallback_has_measured_fit_and_missing_fit_requires_recovery(driver, tmp_path):
    rows = [{"candidate": "older_receipt", "execution": {
        "started": True, "wall_seconds": 5., "supervised_fit_seconds": 2.}}]
    _result(tmp_path, rows)
    assert driver.worker_costs(tmp_path, "EXP-SYNTHETIC") == (5., 2., 1)
    del rows[0]["execution"]["supervised_fit_seconds"]
    _result(tmp_path, rows)
    with pytest.raises(ValueError):
        driver.worker_costs(tmp_path, "EXP-SYNTHETIC")


def test_missing_full_telemetry_never_becomes_optimistic_zero(driver, tmp_path):
    for row in ({"candidate": "missing_execution"}, {"candidate": "empty_execution", "execution": {}},
                {"candidate": "missing_full", "execution": {"started": True, "supervised_fit_seconds": 0.}},
                {"candidate": "fit_only", "execution": {"supervised_fit_seconds": 2.}}):
        _result(tmp_path, [row])
        with pytest.raises(ValueError):
            driver.worker_costs(tmp_path, "EXP-SYNTHETIC")


def test_registered_identity_with_no_worker_receipts_or_empty_result_is_unknown(driver, tmp_path):
    with pytest.raises(ValueError):
        driver.worker_costs(tmp_path, "EXP-SYNTHETIC")
    _result(tmp_path, [])
    with pytest.raises(ValueError):
        driver.worker_costs(tmp_path, "EXP-SYNTHETIC")


def test_invalid_nonfinite_boolean_negative_or_fit_greater_than_full_rejected(driver, tmp_path):
    for full, fit in ((True, 0), (1, True), (float("nan"), 0), (1, float("inf")),
                      (-1, 0), (1, -1), (1, 2), (None, 0), (1, None)):
        _result(tmp_path, [_row("invalid", full, fit)])
        with pytest.raises(ValueError):
            driver.worker_costs(tmp_path, "EXP-SYNTHETIC")


def test_corrupt_or_malformed_result_and_supervisor_are_not_zero(driver, tmp_path):
    result_path = _result(tmp_path, [])
    for raw in ("{broken", json.dumps({"candidates": None}), json.dumps({"candidates": [None]}),
                json.dumps({"candidates": [{"execution": "bad"}]})):
        result_path.write_text(raw, encoding="utf-8")
        with pytest.raises(ValueError):
            driver.worker_costs(tmp_path, "EXP-SYNTHETIC")
    result_path.unlink()
    partial = tmp_path / "research/tmp/EXP-SYNTHETIC/broken.supervisor.json"
    partial.parent.mkdir(parents=True, exist_ok=True)
    partial.write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError):
        driver.worker_costs(tmp_path, "EXP-SYNTHETIC")


def test_result_and_supervisor_are_alternatives_not_added_twice(driver, tmp_path):
    row = _row("same", 9., 3.)
    _result(tmp_path, [row])
    atomic_write_json(tmp_path / "research/tmp/EXP-SYNTHETIC/same.supervisor.json", row)
    assert driver.worker_costs(tmp_path, "EXP-SYNTHETIC") == (9., 3., 1)
