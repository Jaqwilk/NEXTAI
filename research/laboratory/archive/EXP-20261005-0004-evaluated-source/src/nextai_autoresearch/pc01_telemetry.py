"""Bounded local device-sample persistence; no change to generic ledger writes."""
from pathlib import Path
import os
import time

from .utils import atomic_write_json, load_json


def read_device_sample(path: Path) -> dict | None:
    """One nonblocking attempt; None requires bounded parent-side gap handling."""
    try:
        value = load_json(path)
    except FileNotFoundError:
        # Atomic replacement can make the snapshot path briefly absent. The
        # parent retains its independent one-second continuous-gap deadline.
        return None
    except PermissionError as exc:
        if os.name == "nt" and (getattr(exc, "winerror", None) in {5, 32, 33} or exc.errno == 13):
            return None
        raise
    if (not isinstance(value, dict) or set(value) != {"allocated", "reserved"}
            or any(type(value[key]) is not int for key in value)
            or not 0 <= value["allocated"] <= value["reserved"]):
        raise ValueError("Malformed device telemetry sample")
    return value


def write_device_sample(path: Path, value: dict, root: Path) -> int:
    """Retry only Windows access/sharing conflicts, within the existing fit clock.

    Atomic replacement keeps readers on a complete old/new JSON document. Never
    truncate in place, ignore a permanent error, or reset the supervisor clocks.
    The one-second bound limits retry waiting, not arbitrary OS call latency;
    the parent retains its independent worker and fit deadlines.
    """
    started = time.monotonic()
    deadline = started + 1.0
    failures, last_error = 0, None
    while True:
        for name in ("STOP", "PAUSE"):
            if (root / name).exists():
                raise RuntimeError(f"{name} during device telemetry persistence")
        if failures and time.monotonic() >= deadline:
            raise TimeoutError(f"device telemetry retry deadline: {failures} failed replacements") from last_error
        try:
            atomic_write_json(path, value)
        except OSError as exc:
            if getattr(exc, "winerror", None) not in {5, 32, 33}:
                raise
            failures += 1
            last_error = exc
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
        else:
            if failures:
                print(f"PC-01 telemetry recovered: retries={failures}, elapsed_seconds={time.monotonic()-started:.6f}", flush=True)
            return failures
