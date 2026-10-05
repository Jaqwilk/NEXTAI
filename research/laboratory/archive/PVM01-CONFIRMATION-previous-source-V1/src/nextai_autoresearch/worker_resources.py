"""Trusted v2 fit/device supervision, reusing the bounded telemetry writer."""
from __future__ import annotations

import math
import threading
import time
from pathlib import Path

from .pc01_telemetry import read_device_sample, write_device_sample
from .utils import atomic_write_json, load_json, project_root


class WorkerResources:
    def __init__(self, output: Path, limits: dict, plan: Path):
        self.output, self.limits = output, limits
        self.root = project_root()
        self.device = output.with_suffix(".device.json")
        self.phase_path = output.with_suffix(".phase.json")
        self.stop = threading.Event()
        self.error: BaseException | None = None
        self.fit_started: float | None = None
        self.fit_elapsed = 0.0
        self.phase_name = None
        self.thread = None
        self.torch = None

    def start(self):
        import torch
        self.torch = torch
        if torch.cuda.is_available():
            total = torch.cuda.get_device_properties(0).total_memory
            torch.cuda.set_per_process_memory_fraction(min(1.0, self.limits["max_cuda_reserved_bytes"] / total))
            torch.cuda.reset_peak_memory_stats()
        self.phase("initializing")
        self.thread = threading.Thread(target=self._sample, daemon=True)
        self.thread.start()

    def phase(self, name: str):
        if name not in {"initializing", "fit", "evaluation", "complete"}:
            raise ValueError("Unknown worker phase")
        now = time.monotonic()
        if name == "fit":
            if self.fit_started is not None:
                raise ValueError("Fit may start only once")
            self.fit_started = now
        elif self.phase_name == "fit" and self.fit_started is not None:
            self.fit_elapsed = now - self.fit_started
        self.phase_name = name
        # Reuse Windows sharing-conflict retries; phase has its own schema.
        write_device_sample(self.phase_path, {"phase": name, "fit_started": self.fit_started,
                                            "fit_elapsed": self.fit_elapsed}, self.root)
        self.check()

    def _sample(self):
        try:
            while not self.stop.is_set():
                cuda = self.torch.cuda
                value = {"allocated": int(cuda.max_memory_allocated()) if cuda.is_available() else 0,
                         "reserved": int(cuda.max_memory_reserved()) if cuda.is_available() else 0}
                write_device_sample(self.device, value, self.root)
                if value["reserved"] > self.limits["max_cuda_reserved_bytes"]:
                    raise MemoryError("CUDA reserved memory exceeds frozen cap")
                self.stop.wait(0.1)
        except BaseException as exc:
            self.error = exc

    def check(self):
        if self.error:
            raise RuntimeError("Trusted resource telemetry failed") from self.error
        if self.fit_elapsed > self.limits["fit_seconds_cap"]:
            raise TimeoutError("Fit exceeded frozen deadline")

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=2)


def resource_problem(output: Path, limits: dict, worker_started: float, gap_started: float):
    """Parent clocks never depend on a candidate's self-reported cost counters."""
    now = time.monotonic()
    try:
        sample = read_device_sample(output.with_suffix(".device.json"))
        fresh_device = False
        if sample is not None:
            if sample["reserved"] > limits["max_cuda_reserved_bytes"]:
                return "cuda_limit", gap_started
            # Detect a silent telemetry thread, not merely a missing first sample.
            if time.time() - output.with_suffix(".device.json").stat().st_mtime < 2:
                fresh_device = True
        phase = load_json(output.with_suffix(".phase.json"))
        if (not isinstance(phase, dict) or set(phase) != {"phase", "fit_started", "fit_elapsed"}
                or phase["phase"] not in {"initializing", "fit", "evaluation", "complete"}
                or type(phase["fit_elapsed"]) not in (int, float) or not math.isfinite(phase["fit_elapsed"])
                or phase["fit_elapsed"] < 0):
            return "telemetry_failure", gap_started
        tick = phase["fit_started"]
        if tick is not None:
            if type(tick) not in (int, float) or not math.isfinite(tick) or not worker_started <= tick <= now:
                return "telemetry_failure", gap_started
            elapsed = now - tick if phase["phase"] == "fit" else phase["fit_elapsed"]
            if elapsed > limits["fit_seconds_cap"]:
                return "fit_timeout", gap_started
        # Both observations are required. A live device heartbeat alone cannot
        # conceal a missing phase file and bypass the independent fit clock.
        if fresh_device:
            gap_started = now
    except (FileNotFoundError, PermissionError):
        pass  # Transient reads retain the parent's original continuous gap clock.
    except (ValueError, TypeError, KeyError):
        return "telemetry_failure", gap_started
    if now - gap_started > 30:
        return "telemetry_failure", gap_started
    return None, gap_started
