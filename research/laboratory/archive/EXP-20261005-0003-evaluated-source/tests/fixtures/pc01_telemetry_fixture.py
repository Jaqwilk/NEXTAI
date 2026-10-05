"""Synthetic Windows file contention / supervised producer; no model or data."""
import argparse
import contextlib
import ctypes
import json
from pathlib import Path
import time


@contextlib.contextmanager
def deny_delete(path):
    """A real Windows reader explicitly sharing read/write but not delete."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                       ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    create.restype = ctypes.c_void_p
    close = kernel.CloseHandle
    close.argtypes = [ctypes.c_void_p]
    close.restype = ctypes.c_int
    handle = create(str(path), 0x80000000, 3, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        yield
    finally:
        close(handle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--seconds", type=float, default=0.3)
    args = parser.parse_args()
    work = args.work
    path = work / "device.json"
    if args.mode == "hold":
        with deny_delete(path):
            (work / "reader-ready").touch()
            time.sleep(args.seconds)
        return
    if args.mode == "reader":
        from nextai_autoresearch.pc01_telemetry import read_device_sample
        reads, previous = 0, -1
        unavailable = None
        (work / "reader-ready").touch()
        deadline = time.monotonic() + 35
        while not (work / "reader-stop").exists():
            if time.monotonic() > deadline:
                raise TimeoutError("reader deadline")
            value = read_device_sample(path)
            if value is None:
                unavailable = unavailable or time.monotonic()
                assert time.monotonic() - unavailable < 1, "persistent read failure"
                time.sleep(0.0005)
                continue
            unavailable = None
            assert value["reserved"] == value["allocated"] * 2
            assert value["allocated"] >= previous
            previous = value["allocated"]
            reads += 1
            time.sleep(0.0005)
        print(json.dumps({"reads": reads, "last": previous}))
        return
    from nextai_autoresearch.pc01_telemetry import write_device_sample
    from nextai_autoresearch.utils import atomic_write_json
    atomic_write_json(work / "fit-request.json", {"fixture": True})
    deadline = time.monotonic() + 5
    while not (work / "fit-granted.json").exists():
        if time.monotonic() > deadline:
            raise TimeoutError("grant deadline")
        time.sleep(0.005)
    atomic_write_json(path, {"allocated": 0, "reserved": 0})
    if args.mode == "producer-denied":
        with deny_delete(path):
            write_device_sample(path, {"allocated": 1, "reserved": 2}, work.parent)
        raise AssertionError("persistent denial silently passed")
    if args.mode == "producer-cuda":
        write_device_sample(path, {"allocated": 20 * 1024**3, "reserved": 20 * 1024**3}, work.parent)
        time.sleep(5)
        return
    until = time.monotonic() + 5
    while time.monotonic() < until:
        write_device_sample(path, {"allocated": 1, "reserved": 2}, work.parent)
    atomic_write_json(work / "fit-finished.json", {"fixture": True})


if __name__ == "__main__":
    main()
