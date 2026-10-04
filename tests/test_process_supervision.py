import ctypes
import os
from pathlib import Path
import shutil
import sys
import time

import psutil
import pytest

from nextai_autoresearch import process_supervision as supervision


pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object boundary")
ROOT = Path(__file__).resolve().parents[1]
CHILD = ROOT / "tests/fixtures/process_tree_child.py"


def run(tmp_path, command, timeout=5):
    return supervision.run_bounded(command, cwd=ROOT, env=os.environ.copy(),
                                  stdout_path=tmp_path / "stdout", stderr_path=tmp_path / "stderr",
                                  timeout_seconds=timeout)


@pytest.mark.parametrize("code", [0, 7])
def test_exit_preserves_binary_output_and_code(tmp_path, code):
    child = f"import os,sys;os.write(1,b'a\\x00b\\r\\n');os.write(2,b'x\\r\\n');sys.exit({code})"
    result = run(tmp_path, [sys.executable, "-c", child])
    assert (result.returncode, result.root_returncode, result.reason) == (code, code, "exited")
    assert (tmp_path / "stdout").read_bytes() == b"a\x00b\r\n"
    assert (tmp_path / "stderr").read_bytes() == b"x\r\n"


@pytest.mark.parametrize("early_exit,through_uv", [(False, False), (True, False), (False, True)])
def test_timeout_and_exited_parent_kill_all_generations(tmp_path, early_exit, through_uv):
    command = [sys.executable, str(CHILD), str(tmp_path), "parent", "yes" if early_exit else "no"]
    if through_uv:
        uv = shutil.which("uv")
        assert uv is not None, "The installed actual wrapper is required"
        command = [uv, "run", "--no-sync", "python", *command[1:]]
    result = run(tmp_path, command)
    assert result.returncode == 124
    assert result.reason == ("lingering_descendants" if early_exit else "timeout")
    assert result.elapsed_seconds <= 8.
    assert result.processes_created >= 3
    pids = [int((tmp_path / f"{role}.pid").read_text()) for role in ("parent", "child", "grandchild")]
    assert not any(psutil.pid_exists(pid) for pid in pids)
    heartbeat = {p.name: p.read_bytes() for p in tmp_path.glob("*.heartbeat")}
    time.sleep(.12)
    assert heartbeat == {p.name: p.read_bytes() for p in tmp_path.glob("*.heartbeat")}


@pytest.mark.parametrize("stage", ["assign", "resume"])
def test_startup_failure_never_executes_suspended_child(tmp_path, monkeypatch, stage):
    def fail(*args):
        raise RuntimeError("Injected pre-execution failure")
    monkeypatch.setattr(supervision._Job if stage == "assign" else supervision,
                        "assign" if stage == "assign" else "_resume_initial_process", fail)
    marker = tmp_path / "executed"
    with pytest.raises(RuntimeError, match="Injected"):
        run(tmp_path, [sys.executable, "-c", f"from pathlib import Path;Path({str(marker)!r}).write_text('bad')"])
    assert not marker.exists()


def test_windows_structures_match_documented_native_layout():
    assert ctypes.sizeof(supervision._BasicLimits) == 64
    assert ctypes.sizeof(supervision._IOCounters) == 48
    assert ctypes.sizeof(supervision._ExtendedLimits) == 144
    assert ctypes.sizeof(supervision._Accounting) == 48
