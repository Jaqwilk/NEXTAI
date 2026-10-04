"""Fail closed on the explicitly excluded WT recordings, including test I/O."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_INSTALLED = False


def require_data_access(path: str | bytes | os.PathLike) -> None:
    value = os.fsdecode(path).replace("\\", "/").lower()
    if "/research/data/wt_changepoints_v1/" in "/" + value:
        if value.rsplit("/", 1)[-1] in {"load_in_seed_8.csv", "load_in_seed_9.csv"}:
            raise PermissionError("WT files 8-9 are excluded by the current laboratory authority")


def install_data_access_guard() -> None:
    """Python open guard; native loaders are also checked before resolving paths.

    This is an accidental-access guard, not an operating-system sandbox.
    It deliberately has no environment-variable or pytest opt-out.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    def guard(event: str, args: tuple) -> None:
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            require_data_access(args[0])

    sys.addaudithook(guard)
    _INSTALLED = True
