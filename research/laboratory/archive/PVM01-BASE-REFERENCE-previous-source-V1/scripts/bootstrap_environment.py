"""Bootstrap only the locked local tools, with a conservative disk estimate."""
from __future__ import annotations

import os
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib


GIB = 1024 ** 3
RESERVE = 10 * GIB


def footprint_estimate(lock: dict, supplement: dict | None = None) -> int:
    largest_archives = 0
    for package in lock.get("package", []):
        if "editable" in package.get("source", {}):
            continue
        assets = [*package.get("wheels", [])]
        if package.get("sdist"):
            assets.append(package["sdist"])
        sizes = []
        for asset in assets:
            size = asset.get("size")
            if size is None:
                record = (supplement or {}).get(asset.get("hash"), {})
                if record.get("url") == asset.get("url"):
                    size = record.get("size")
            sizes.append(size)
        if not sizes or any(not isinstance(size, int) or size <= 0 for size in sizes):
            raise ValueError(f"Cannot bound footprint for {package.get('name')}")
        largest_archives += max(sizes)
    if largest_archives == 0:
        raise ValueError("Empty lock cannot bound an installation")
    # Count all locked packages, then reserve extraction, cache + environment
    # copies and interpreter overhead. This is an estimate, not a filesystem quota.
    return largest_archives * 6 + 2 * GIB


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    sizes = json.loads((root / "config/bootstrap_sizes.json").read_text(encoding="utf-8"))
    required = footprint_estimate(lock, sizes["sizes"])
    free = shutil.disk_usage(root).free
    print(f"Disk preflight: free={free} estimated_install_cache_bytes={required} reserve={RESERVE}", flush=True)
    if free - required < RESERVE:
        raise RuntimeError(f"Disk blocker: need {required + RESERVE} free bytes on {root.anchor}; found {free}")
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is missing. Provision the uv tool first (validated locally: 0.11.15); no automatic remote shell installer was run.")
    environment = os.environ.copy()
    environment["UV_CACHE_DIR"] = str(root / "research" / "tmp" / "bootstrap" / "cache")
    environment["UV_PYTHON_INSTALL_DIR"] = str(root / "research" / "tmp" / "bootstrap" / "python")
    environment["UV_PROJECT_ENVIRONMENT"] = str(root / ".venv")
    environment["UV_LINK_MODE"] = "copy"
    try:
        subprocess.run([uv, "sync", "--frozen", "--extra", "dev"], cwd=root, env=environment, check=True)
    finally:
        after = shutil.disk_usage(root).free
        print(f"Disk after bootstrap: free={after} reserve={RESERVE}", flush=True)
        if after < RESERVE:
            raise RuntimeError(f"Disk reserve violated after bootstrap: {after} free bytes; no further work authorized")
    subprocess.run([uv, "run", "--no-sync", "nextai", "doctor"], cwd=root, env=environment, check=True)
    print("Locked environment verified. Laboratory preparation only; no experiment started.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Bootstrap blocked: {exc}", file=sys.stderr)
        sys.exit(1)
