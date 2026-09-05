"""Process-only conformance fixture. No corpus, torch, model or training.

The fit handshake names exercise supervision only. Metrics, when supplied by a
test, are explicitly synthetic and only ever written inside pytest's temp root.
"""
import argparse
import json
import os
from pathlib import Path
import time


def write(path, value):
    temporary = path.with_suffix(".partial")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--measurement", type=Path)
    args = parser.parse_args()
    work = args.work
    if args.mode == "worker_hang":
        time.sleep(10)
    if args.mode == "crash_before_fit":
        raise RuntimeError("intentional fixture crash before fit")
    write(work / "fit-request.json", {"fixture": True})
    while not (work / "fit-granted.json").exists():
        time.sleep(0.01)
    if args.mode == "fit_hang":
        time.sleep(10)
    if args.mode == "crash":
        raise RuntimeError("intentional fixture crash")
    if args.mode == "rss":
        allocation = bytearray(32*1024**2)
        time.sleep(10)
    if args.mode == "payload":
        folder = Path.cwd() / "research/pc01_payload"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "fixture.bin").write_bytes(bytes(2048))
        time.sleep(10)
    write(work / "device.json", {"allocated": 20*1024**3 if args.mode == "cuda" else 0,
                                 "reserved": 20*1024**3 if args.mode == "cuda" else 0})
    if args.mode == "cuda":
        time.sleep(10)
    write(work / "fit-finished.json", {"fixture": True, "updates": 5000})
    if args.measurement:
        write(work / "measurement.json", json.loads(args.measurement.read_text()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
