"""Synthetic telemetry only: no optimizer, corpus, model or scored result."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from nextai_autoresearch.utils import atomic_write_json, load_json

FIXTURE = Path(__file__).parent / "fixtures/pc01_telemetry_fixture.py"


def start_reader(work, mode="hold", seconds=0.3):
    process = subprocess.Popen([sys.executable, str(FIXTURE), "--work", str(work),
                                "--mode", mode, "--seconds", str(seconds)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 5
    while not (work / "reader-ready").exists():
        if process.poll() is not None or time.monotonic() > deadline:
            process.kill()
            raise AssertionError(process.communicate(timeout=2))
        time.sleep(0.002)
    return process


@pytest.mark.skipif(os.name != "nt", reason="Requires actual Windows file sharing")
def test_legacy_writer_reproduces_windows_reader_denial(tmp_path, record_property):
    path = tmp_path / "device.json"
    atomic_write_json(path, {"allocated": 0, "reserved": 0})
    reader = start_reader(tmp_path)
    try:
        with pytest.raises(PermissionError) as caught:
            atomic_write_json(path, {"allocated": 1, "reserved": 2})
        assert caught.value.winerror in {5, 32, 33}
        record_property("reproduced_winerror", caught.value.winerror)
        assert load_json(path) == {"allocated": 0, "reserved": 0}
    finally:
        reader.communicate(timeout=3)
    assert reader.returncode == 0


@pytest.mark.skipif(os.name != "nt", reason="Requires actual Windows file sharing")
def test_transient_reader_lock_recovers_without_partial_json(tmp_path, capsys, record_property):
    from nextai_autoresearch.pc01_telemetry import write_device_sample
    path = tmp_path / "device.json"
    atomic_write_json(path, {"allocated": 0, "reserved": 0})
    reader = start_reader(tmp_path)
    try:
        retries = write_device_sample(path, {"allocated": 1, "reserved": 2}, tmp_path)
        assert retries > 0
        record_property("retries", retries)
        assert load_json(path) == {"allocated": 1, "reserved": 2}
        assert "telemetry recovered" in capsys.readouterr().out
    finally:
        reader.communicate(timeout=3)
    assert reader.returncode == 0


@pytest.mark.skipif(os.name != "nt", reason="Requires actual Windows file sharing")
def test_persistent_reader_lock_fails_at_bounded_deadline(tmp_path):
    from nextai_autoresearch.pc01_telemetry import write_device_sample
    path = tmp_path / "device.json"
    atomic_write_json(path, {"allocated": 0, "reserved": 0})
    reader = start_reader(tmp_path, seconds=2)
    started = time.monotonic()
    try:
        with pytest.raises(TimeoutError, match="telemetry retry deadline") as caught:
            write_device_sample(path, {"allocated": 1, "reserved": 2}, tmp_path)
        assert 0.9 <= time.monotonic() - started < 1.5
        assert isinstance(caught.value.__cause__, PermissionError)
        assert load_json(path) == {"allocated": 0, "reserved": 0}
    finally:
        reader.communicate(timeout=3)


@pytest.mark.parametrize("failure", [5, 32, 33, 112, None])
def test_retry_error_classification_and_deadline_are_exact(tmp_path, monkeypatch, failure):
    from types import SimpleNamespace
    from nextai_autoresearch import pc01_telemetry as telemetry
    now, attempts = [0.0], []
    def write(*args):
        attempts.append(now[0])
        error = OSError("synthetic error")
        if failure is not None:
            error.winerror = failure
        raise error
    monkeypatch.setattr(telemetry, "atomic_write_json", write)
    monkeypatch.setattr(telemetry, "time", SimpleNamespace(monotonic=lambda: now[0], sleep=lambda n: now.__setitem__(0, now[0]+n)))
    if failure in {5, 32, 33}:
        with pytest.raises(TimeoutError):
            telemetry.write_device_sample(tmp_path / "device.json", {}, tmp_path)
        assert now[0] == pytest.approx(1)
        assert len(attempts) <= 101 and max(attempts) < 1
    else:
        with pytest.raises(OSError, match="synthetic"):
            telemetry.write_device_sample(tmp_path / "device.json", {}, tmp_path)
        assert attempts == [0] and now == [0]


@pytest.mark.parametrize("gate", ["STOP", "PAUSE"])
def test_stop_and_pause_interrupt_telemetry_retry(tmp_path, monkeypatch, gate):
    from types import SimpleNamespace
    from nextai_autoresearch import pc01_telemetry as telemetry
    attempts = []
    def write(*args):
        attempts.append(1)
        error = PermissionError("fixture sharing")
        error.winerror = 32
        raise error
    monkeypatch.setattr(telemetry, "atomic_write_json", write)
    monkeypatch.setattr(telemetry, "time", SimpleNamespace(monotonic=lambda: 0, sleep=lambda n: (tmp_path / gate).touch()))
    with pytest.raises(RuntimeError, match=gate):
        telemetry.write_device_sample(tmp_path / "device.json", {}, tmp_path)
    assert len(attempts) == 1 and not (tmp_path / "device.json").exists()


@pytest.mark.parametrize("repetition", range(3))
def test_concurrent_reader_and_two_thousand_device_writes(tmp_path, repetition, record_property):
    from nextai_autoresearch.pc01_telemetry import write_device_sample
    path = tmp_path / "device.json"
    atomic_write_json(path, {"allocated": 0, "reserved": 0})
    reader = start_reader(tmp_path, mode="reader")
    started, retries = time.monotonic(), 0
    try:
        for index in range(1, 2001):
            assert time.monotonic() - started < 30, "stress wall budget"
            retries += write_device_sample(path, {"allocated": index, "reserved": 2*index}, tmp_path)
    finally:
        (tmp_path / "reader-stop").touch()
        stdout, stderr = reader.communicate(timeout=5)
    assert reader.returncode == 0, stderr
    stats = json.loads(stdout)
    assert stats["reads"] > 0
    assert load_json(path) == {"allocated": 2000, "reserved": 4000}
    assert not list(tmp_path.glob(".device.json.*.tmp"))
    record_property("writes", 2000)
    record_property("reads", stats["reads"])
    record_property("retry_count", retries)
    record_property("seconds", time.monotonic()-started)


@pytest.mark.parametrize("mode,reason", [("producer-loop", "fit_timeout"), ("producer-cuda", "cuda_limit"), ("producer-denied", None)])
def test_supervisor_retains_deadlines_limits_and_worker_failure(tmp_path, mode, reason):
    from nextai_autoresearch.pc01_execution import supervise, Limits
    if mode == "producer-denied" and os.name != "nt":
        pytest.skip("Actual Windows file sharing")
    work = tmp_path / "work"
    result = supervise([sys.executable, str(FIXTURE), "--work", str(work), "--mode", mode], tmp_path, work,
                       limits=Limits(fit_seconds=2 if mode == "producer-denied" else 0.4,
                                     worker_seconds=5, disk_reserve_bytes=0))
    assert result["termination_reason"] == reason
    assert result["return_code"] != 0
    assert result["worker_seconds"] < 5
    if mode == "producer-denied":
        assert "telemetry retry deadline" in (work / "worker.log").read_text()
        assert result["fit_seconds_charged"] == 2


def test_supervisor_stop_during_device_publication(tmp_path):
    import threading
    from nextai_autoresearch.pc01_execution import supervise, Limits
    work = tmp_path / "work"
    def stop_after_fit():
        deadline = time.monotonic() + 4
        while not (work / "fit-granted.json").exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        (tmp_path / "STOP").touch()
    thread = threading.Thread(target=stop_after_fit)
    thread.start()
    try:
        result = supervise([sys.executable, str(FIXTURE), "--work", str(work), "--mode", "producer-loop"], tmp_path, work,
                           limits=Limits(fit_seconds=3, worker_seconds=5, disk_reserve_bytes=0))
    finally:
        thread.join(timeout=5)
    assert result["termination_reason"] == "stop_gate"
    assert result["return_code"] != 0
