"""Launcher-aware public exit diagnostics; V1 and monitor remain unchanged."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import psutil
import pytest

from nextai_autoresearch.process_supervision import run_bounded


pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object diagnostic")
ROOT = Path(__file__).resolve().parents[1]


def _run(tmp_path, command):
    result = run_bounded(command, cwd=ROOT, env=os.environ.copy(),
        stdout_path=tmp_path / "stdout.txt", stderr_path=tmp_path / "stderr.txt",
        timeout_seconds=5.)
    (tmp_path / "supervision-result.json").write_text(
        json.dumps(asdict(result), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def test_ordinary_exit_zero_remains_zero(tmp_path):
    result = _run(tmp_path, [sys.executable, "-c", "import os;os.write(1,b'normal\\n')"])
    assert (result.returncode, result.root_returncode, result.reason) == (0, 0, "exited")
    assert result.exit_live_descendant_pids == () and result.processes_created >= 1
    assert result.elapsed_seconds <= 8.
    assert (tmp_path / "stdout.txt").read_bytes() == b"normal\n"
    assert (tmp_path / "stderr.txt").read_bytes() == b""


def test_root_failure_without_child_remains_one(tmp_path):
    code = "import os,sys;os.write(2,b'synthetic root failure\\n');sys.exit(1)"
    result = _run(tmp_path, [sys.executable, "-c", code])
    assert (result.returncode, result.root_returncode, result.reason) == (1, 1, "exited")
    assert result.exit_live_descendant_pids == () and result.processes_created >= 1
    assert result.elapsed_seconds <= 8.
    assert (tmp_path / "stderr.txt").read_bytes() == b"synthetic root failure\n"


def test_root_failure_with_ready_child_records_linger_then_drains(tmp_path):
    child = tmp_path / "public-child.py"
    ready, heartbeat = tmp_path / "child.pid", tmp_path / "child.heartbeat"
    ancestry_path = tmp_path / "launcher-ancestry.json"
    child.write_text(
        "import os,sys,time\n"
        "from pathlib import Path\n"
        "ready,heartbeat=map(Path,sys.argv[1:3])\n"
        "heartbeat.write_text('0',encoding='ascii')\n"
        "pending=ready.with_suffix('.pending')\n"
        "pending.write_text(str(os.getpid()),encoding='ascii')\n"
        "pending.replace(ready)\n"
        "deadline=time.monotonic()+60.\n"
        "counter=0\n"
        "while time.monotonic()<deadline:\n"
        "    counter+=1\n"
        "    heartbeat.write_text(str(counter),encoding='ascii')\n"
        "    time.sleep(.01)\n", encoding="utf-8")
    parent = (
        "import json,os,subprocess,sys,time\n"
        "import psutil\n"
        "from pathlib import Path\n"
        "child=subprocess.Popen([sys.executable,*sys.argv[1:]])\n"
        "ready=Path(sys.argv[2])\n"
        "deadline=time.monotonic()+3.\n"
        "while not ready.exists() and time.monotonic()<deadline:\n"
        "    time.sleep(.01)\n"
        "assert ready.exists(),'Synthetic child failed readiness handshake'\n"
        "worker_pid=int(ready.read_text(encoding='ascii'))\n"
        "descendants=sorted(p.pid for p in psutil.Process(child.pid).children(recursive=True))\n"
        "owned=worker_pid==child.pid or worker_pid in descendants\n"
        "record={'launcher_pid':child.pid,'worker_pid':worker_pid,'launcher_descendant_pids':descendants,'worker_in_launcher_tree':owned}\n"
        "Path(sys.argv[4]).write_text(json.dumps(record,sort_keys=True),encoding='utf-8')\n"
        "assert owned,'Actual worker is outside its launcher descendant tree'\n"
        "os.write(1,b'root failed with living child\\n')\n"
        "sys.exit(1)\n")
    result = _run(tmp_path, [sys.executable, "-c", parent, str(child), str(ready), str(heartbeat), str(ancestry_path)])
    ancestry = json.loads(ancestry_path.read_text(encoding="utf-8"))
    pid = int(ready.read_text(encoding="ascii"))
    alive_after_return = psutil.pid_exists(pid)
    heartbeat_before = heartbeat.read_bytes()
    time.sleep(.12)
    heartbeat_after = heartbeat.read_bytes()
    recorded_pids = {ancestry["launcher_pid"], ancestry["worker_pid"], *ancestry["launcher_descendant_pids"]}
    alive_recorded_pids = sorted(pid for pid in recorded_pids if psutil.pid_exists(pid))
    proof = {"supervision": asdict(result), "child_pid": pid, "launcher_ancestry": ancestry,
        "recorded_launcher_tree_pids_alive_after_stability_check": alive_recorded_pids,
        "child_pid_alive_after_return": alive_after_return,
        "child_pid_alive_after_stability_check": psutil.pid_exists(pid),
        "heartbeat_stable_after_return": heartbeat_before == heartbeat_after,
        "heartbeat_sha256_before": hashlib.sha256(heartbeat_before).hexdigest(),
        "heartbeat_sha256_after": hashlib.sha256(heartbeat_after).hexdigest(),
        "snapshot_is_before_cleanup": True, "supervisor_source_changed": False}
    (tmp_path / "post-return-drain-proof.json").write_text(
        json.dumps(proof, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    assert (result.returncode, result.root_returncode, result.reason) == (124, 1, "lingering_descendants")
    assert pid in result.exit_live_descendant_pids and result.exit_job_active_process_count >= 1
    assert result.processes_created >= 2 and result.elapsed_seconds <= 8.
    assert ancestry["worker_pid"] == pid and ancestry["worker_in_launcher_tree"] is True
    assert not alive_recorded_pids
    assert not alive_after_return and not proof["child_pid_alive_after_stability_check"]
    assert proof["heartbeat_stable_after_return"]
