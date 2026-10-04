from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from nextai_autoresearch.utils import project_root


ROOT = project_root()
SCRIPT = ROOT / "research/audits/real_system_calibration_v1.py"
SPEC = importlib.util.spec_from_file_location("real_system_calibration_v1", SCRIPT)
assert SPEC and SPEC.loader
calibration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(calibration)


def test_calibration_contract_is_frozen_and_non_evidential() -> None:
    path = ROOT / calibration.CONTRACT
    assert hashlib.sha256(path.read_bytes()).hexdigest() == calibration.CONTRACT_SHA256
    contract = json.loads(path.read_text(encoding="utf-8"))
    assert contract["cycle"] == 228
    assert contract["scientific_evidence"] is False
    assert contract["g1_window_increment"] is False
    assert set(contract["models"]) == {
        "small_dense_transformer", "bounded_local_retrieval", "ppm_d_order5",
        "ctw_depth2", "dense_autoregressive_order5",
    }


def test_examples_never_cross_file_boundaries() -> None:
    xs, ys = calibration._examples([("a", b"abcd"), ("b", b"WXYZ")], 2)
    assert xs.tolist() == [[97, 98], [98, 99], [87, 88], [88, 89]]
    assert ys.tolist() == [99, 100, 89, 90]


def test_local_retrieval_is_bounded_and_uses_kt_smoothing() -> None:
    model = calibration.LocalRetrieval(context=3, bucket_cap=2, nearest=1)
    model.fit([("a", b"abcxabcxabcx")])
    row = model.distribution(calibration.np.asarray([97, 98, 99], dtype="uint8"))
    assert len(model.buckets[b"bc"]) == 2
    assert row[120] > row[0] > 0.0
    assert abs(sum(row) - 1.0) < 1e-12


def test_completed_calibration_remains_outside_scientific_evidence() -> None:
    result = json.loads((ROOT / calibration.OUTPUT).read_text(encoding="utf-8"))
    assert result["calibration_id"] == calibration.CALIBRATION_ID
    assert result["scientific_evidence"] is False
    assert result["g1_window_increment"] is False
    assert {row["model"] for row in result["models"]} == {
        "small_dense_transformer", "bounded_local_retrieval", "ppm_d_order5",
        "ctw_depth2", "dense_autoregressive_order5",
    }

    for relative in ("AGENTS.md", "program.md", "docs/ROADMAP.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "CAL-20260901-0001" in text
