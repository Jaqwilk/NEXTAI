from __future__ import annotations

import json
from pathlib import Path

import pytest
import psutil

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.ledger import RunLock, ensure_layout
from nextai_autoresearch.runner import _rss_tree
from nextai_autoresearch.utils import load_json, project_root
from nextai_autoresearch.worker import run_worker


def test_source_audit_rejects_network_import_and_file_access(tmp_path: Path) -> None:
    candidate_dir = tmp_path / "src" / "nextai_autoresearch" / "candidates"
    candidate_dir.mkdir(parents=True)
    (candidate_dir / "unsafe_candidate.py").write_text(
        "import socket\n"
        "class Candidate:\n"
        "    def run(self):\n"
        "        return open('secret.txt').read()\n",
        encoding="utf-8",
    )
    result = audit_candidate(
        "unsafe_candidate", load_config(project_root()), root=tmp_path
    )
    assert result.ok is False
    assert any("forbidden import 'socket'" in item for item in result.problems)
    assert any("forbidden builtin 'open'" in item for item in result.problems)


def test_source_audit_follows_transitive_local_imports(tmp_path: Path) -> None:
    package = tmp_path / "src" / "nextai_autoresearch"
    candidate_dir = package / "candidates"
    candidate_dir.mkdir(parents=True)
    (package / "hidden_core.py").write_text(
        "import socket\nclass Hidden: pass\n", encoding="utf-8"
    )
    (candidate_dir / "transitive_candidate.py").write_text(
        "from nextai_autoresearch.hidden_core import Hidden\n"
        "class Candidate(Hidden):\n"
        "    pass\n",
        encoding="utf-8",
    )
    result = audit_candidate(
        "transitive_candidate", load_config(project_root()), root=tmp_path
    )
    assert result.ok is False
    assert any("hidden_core.py" in item and "socket" in item for item in result.problems)


def test_run_lock_prevents_overlap_and_is_released(tmp_path: Path) -> None:
    ensure_layout(tmp_path)
    lock_path = tmp_path / "research" / "run.lock"
    with RunLock(tmp_path, stale_seconds=3600):
        assert lock_path.exists()
        with pytest.raises(RuntimeError, match="Research run lock is active"):
            with RunLock(tmp_path, stale_seconds=3600):
                pass
    assert not lock_path.exists()


def test_worker_records_structured_crash_for_missing_candidate(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    output_path = tmp_path / "result.json"
    plan_path.write_text(
        json.dumps(
            {
                "benchmark": "successor_graph_v1",
                "matrix": {
                    "knowledge_sizes": [4, 8],
                    "reasoning_depths": [1, 2],
                    "queries_per_cell": 1,
                    "seeds": [0],
                },
            }
        ),
        encoding="utf-8",
    )
    assert run_worker(plan_path, "candidate_that_does_not_exist", output_path) == 1
    result = load_json(output_path)
    assert result["status"] == "crash"
    assert result["error_type"] == "ModuleNotFoundError"
    assert result["summary"]["status"] == "failed"


def test_rss_monitor_tolerates_a_process_exit_race() -> None:
    class GoneProcess:
        def children(self, recursive: bool):
            raise psutil.NoSuchProcess(1)

    assert _rss_tree(GoneProcess()) == 0
