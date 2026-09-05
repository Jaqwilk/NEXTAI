import importlib.util
import shutil

import pytest

from nextai_autoresearch import laboratory
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import project_root, sha256_bytes, utc_now
from test_lab_restart import _lab_fixture


def test_repair_authority_never_reopens_scoring(tmp_path):
    _lab_fixture(tmp_path)
    path = tmp_path / laboratory.REPAIR_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(project_root() / laboratory.REPAIR_PATH, path)
    assert laboratory.laboratory_problems(tmp_path)
    event = {"event": "laboratory_maintenance_started", "action_id": "PC-01-TELEMETRY-REPAIR",
             "plan_path": laboratory.REPAIR_PATH, "plan_sha256": laboratory.REPAIR_SHA256, "created_at": utc_now()}
    append_jsonl(tmp_path / "research/events.jsonl", event)
    assert laboratory.laboratory_problems(tmp_path) == []
    assert laboratory.laboratory_problems(tmp_path, scoring=True)
    config = tmp_path / "config/research.toml"
    config.write_text(config.read_text().replace('benchmark_status = "maintenance"', 'benchmark_status = "active"'))
    assert laboratory.laboratory_problems(tmp_path)
    append_jsonl(tmp_path / "research/events.jsonl", event)
    with pytest.raises(ValueError, match="repeated"):
        laboratory.telemetry_repair_status(tmp_path)


def test_prefix_validator_accepts_append_but_never_rewrite_or_truncation(tmp_path):
    spec = importlib.util.spec_from_file_location("telemetry_history", project_root() / "scripts/validate_pc01_telemetry_repair.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_bytes(b"old\n")
    fixed = tmp_path / "result.json"
    fixed.write_bytes(b"immutable")
    snapshot = {"immutable_files": {"ledger.jsonl": sha256_bytes(b"old\n"), "result.json": sha256_bytes(b"immutable")},
                "prefixes": {"ledger.jsonl": {"bytes": 4, "sha256": sha256_bytes(b"old\n")}}}
    ledger.write_bytes(b"old\nnew\n")
    assert module.verify_snapshot(tmp_path, snapshot) == 1
    for changed in (b"bad\nnew\n", b"ol"):
        ledger.write_bytes(changed)
        with pytest.raises(ValueError, match="prefix"):
            module.verify_snapshot(tmp_path, snapshot)
    ledger.write_bytes(b"old\nnew\n")
    fixed.write_bytes(b"changed")
    with pytest.raises(ValueError, match="artifact"):
        module.verify_snapshot(tmp_path, snapshot)
