"""Trusted read-only NVIDIA probe. Extra environment is confined to its child."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from .utils import utc_now

FIELDS = "index,uuid,name,driver_version,clocks.sm,clocks.mem,utilization.gpu,memory.used"
ARGS = (f"--query-gpu={FIELDS}", "--format=csv,noheader,nounits")
TIMEOUT_SECONDS = 5


def _program_files_64() -> str:
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                        r"SOFTWARE\Microsoft\Windows\CurrentVersion", 0,
                        winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
        value, kind = winreg.QueryValueEx(key, "ProgramFilesDir")
    if kind != winreg.REG_SZ or not isinstance(value, str) or not Path(value).is_absolute() or not Path(value).is_dir():
        raise ValueError("Invalid registry ProgramFilesDir for the metadata subprocess")
    return value


def probe_environment() -> tuple[dict[str, str], str]:
    environment = dict(os.environ)
    if os.name == "nt":
        # Neither os.environ nor the candidate/worker environment is modified.
        environment = {k: v for k, v in environment.items() if k.upper() != "PROGRAMW6432"}
        environment["ProgramW6432"] = _program_files_64()
        return environment, "nvidia_child_only_registry_ProgramW6432"
    return environment, "unchanged_non_windows"


def parse_gpu(stdout: str) -> dict:
    rows = list(csv.reader(stdout.strip().splitlines(), skipinitialspace=True))
    if len(rows) != 1 or len(rows[0]) != 8:
        raise ValueError("Exactly one GPU and all eight metadata fields are required")
    index, uuid, name, driver, sm, memory_clock, utilization, memory = [v.strip() for v in rows[0]]
    if index != "0" or not re.fullmatch(r"GPU-[a-fA-F0-9-]+", uuid):
        raise ValueError("Invalid or ambiguous GPU identity")
    if not name or name in ("N/A", "[N/A]") or not re.fullmatch(r"\d+(?:\.\d+)+", driver):
        raise ValueError("GPU name or driver is missing")
    numbers = []
    for value in (sm, memory_clock, utilization, memory):
        if not re.fullmatch(r"\d+", value):
            raise ValueError("GPU clocks/load/memory must be finite nonnegative integers")
        numbers.append(int(value))
    if numbers[0] <= 0 or numbers[1] <= 0 or numbers[2] > 100:
        raise ValueError("GPU clocks/load are outside the declared range")
    return dict(index=0, uuid=uuid, name=name, driver_version=driver,
                sm_clock_mhz=numbers[0], memory_clock_mhz=numbers[1],
                utilization_percent=numbers[2], memory_used_mib=numbers[3])


def probe_gpu() -> dict:
    start = time.monotonic()
    record = dict(schema_version=1, kind="pc01_gpu_metadata", started_at=utc_now(),
                  status="error", executable=None, arguments=list(ARGS),
                  environment_policy=None, return_code=None, stdout="", stderr="", gpu=None, error=None)
    try:
        executable = shutil.which("nvidia-smi")
        if not executable:
            raise FileNotFoundError("nvidia-smi not found")
        record["executable"] = str(Path(executable).resolve())
        environment, policy = probe_environment()
        record["environment_policy"] = policy
        output = subprocess.run([record["executable"], *ARGS], capture_output=True, text=True,
                                timeout=TIMEOUT_SECONDS, check=False, env=environment)
        record.update(return_code=output.returncode, stdout=output.stdout, stderr=output.stderr)
        if output.returncode != 0:
            raise ValueError(f"nvidia-smi exit code {output.returncode}")
        record["gpu"] = parse_gpu(output.stdout)
        record["status"] = "complete"
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        if isinstance(exc, subprocess.TimeoutExpired):
            record["stdout"] = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            record["stderr"] = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        record["error"] = f"{type(exc).__name__}: {exc}"
    record.update(completed_at=utc_now(), elapsed_seconds=time.monotonic()-start)
    return record


def validate_snapshot(record: dict) -> None:
    import math
    if (not isinstance(record, dict) or record.get("schema_version") != 1
            or record.get("kind") != "pc01_gpu_metadata" or record.get("status") != "complete"
            or type(record.get("return_code")) is not int or record["return_code"] != 0
            or record.get("error") is not None or record.get("arguments") != list(ARGS)
            or record.get("environment_policy") not in ("nvidia_child_only_registry_ProgramW6432", "unchanged_non_windows")
            or not isinstance(record.get("executable"), str) or not Path(record["executable"]).is_absolute()
            or not isinstance(record.get("stderr"), str)):
        raise ValueError("GPU metadata probe is missing, failed or incomplete")
    elapsed = record.get("elapsed_seconds")
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("Invalid GPU metadata elapsed time")
    try:
        dates = [datetime.fromisoformat(record[k]) for k in ("started_at", "completed_at")]
        if any(d.utcoffset() != timezone.utc.utcoffset(d) for d in dates) or dates[1] < dates[0]:
            raise ValueError("GPU metadata timestamps must be ordered UTC")
        if parse_gpu(record["stdout"]) != record["gpu"]:
            raise ValueError("GPU metadata differs from raw query")
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Incomplete GPU metadata evidence") from exc


def validate_pair(pair: dict) -> None:
    if not isinstance(pair, dict) or set(pair) != {"before_fit", "after_timing"}:
        raise ValueError("Both GPU metadata snapshots are required")
    for record in pair.values():
        validate_snapshot(record)
    before, after = pair["before_fit"], pair["after_timing"]
    if any(before["gpu"][key] != after["gpu"][key] for key in ("index", "uuid", "name", "driver_version")):
        raise ValueError("GPU identity/driver changed between snapshots")
    if datetime.fromisoformat(after["started_at"]) < datetime.fromisoformat(before["completed_at"]):
        raise ValueError("GPU metadata stages are out of order")


def capture_required(work: Path, stage: str, root: Path) -> dict:
    from .gates import stop_gate_problems
    from .pc01_execution import new_json
    if stage not in ("before_fit", "after_timing"):
        raise ValueError("Unknown GPU metadata stage")
    if stop_gate_problems(root):
        raise ValueError("STOP/PAUSE forbids GPU metadata capture")
    record = probe_gpu()
    new_json(work / f"gpu-{stage}.json", record)  # Retain errors before rejecting.
    validate_snapshot(record)
    return record
