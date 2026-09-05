"""Bounded PC-01 data acquisition only; never prints corpus text or trains a model."""
from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "research/data/pc01_tinyshakespeare_v1/archive/input.txt"
REVISION = "6f9487a6fe5b420b7ca9afb0d7c078e37c1d1b4e"
URL = f"https://raw.githubusercontent.com/karpathy/char-rnn/{REVISION}/data/tinyshakespeare/input.txt"
CAP = 2 * 1024**2
RESERVE = 10 * 1024**3


def main() -> None:
    for gate in (ROOT / "STOP", ROOT / "PAUSE", ROOT / "research/run.lock"):
        if gate.exists():
            raise SystemExit(f"Blocked by {gate}")
    if DEST.exists():
        raise SystemExit("Acquisition target already exists; verify, never overwrite.")
    free_before = shutil.disk_usage(ROOT).free
    if free_before - CAP < RESERVE:
        raise SystemExit(f"Disk blocker: free={free_before}, cap={CAP}, reserve={RESERVE}")
    # The request is capped in memory before creating the destination. No extraction.
    with urllib.request.urlopen(URL, timeout=45) as response:
        payload = response.read(CAP + 1)
    if len(payload) > CAP:
        raise SystemExit("Download exceeded the 2 MiB acquisition cap; nothing written.")
    if len(payload) != 1115394:
        raise SystemExit(f"Unexpected byte count {len(payload)}; do not silently change corpus.")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open("xb") as output:
        output.write(payload)
    free_after = shutil.disk_usage(ROOT).free
    if free_after < RESERVE:
        raise SystemExit(f"Post-acquisition disk blocker: {free_after}; retain data and report.")
    # Fixed byte offsets, chosen before acquisition; hashing is not model evaluation.
    intervals = {"train": (0, 948084), "dev": (948084, 1003854), "final": (1003854, 1115394)}
    print(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "url": URL, "revision": REVISION,
        "path": DEST.relative_to(ROOT).as_posix(),
        "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
        "disk_free_before_bytes": free_before, "disk_free_after_bytes": free_after,
        "bounded_acquisition_footprint_bytes": CAP, "required_free_reserve_bytes": RESERVE,
        "content_displayed": False, "training_or_quality_evaluation": False,
        "splits": {name: {"start_inclusive": a, "end_exclusive": b, "bytes": b-a,
                          "sha256": hashlib.sha256(payload[a:b]).hexdigest()}
                   for name, (a, b) in intervals.items()},
    }, indent=2))


if __name__ == "__main__":
    main()
