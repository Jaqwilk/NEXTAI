"""Frozen publisher release annotation adapter; keep V3 point/geometry laws."""
from .asm01_task_v3 import _COLUMNS, parse_native_sample as _parse_v3


def parse_native_sample(payload):
    if not isinstance(payload, bytes) or len(payload) > 262144:
        raise ValueError("Native sample byte cap/type")
    lines = [line.strip() for line in payload.decode("ascii").splitlines() if line.strip()]
    if [i for i, line in enumerate(lines) if line.split() == _COLUMNS] != [2]:
        return _parse_v3(payload)
    if not any(line.split() == ["PEN_UP", "0"] for line in lines):
        return _parse_v3(payload)
    # An explicitly headed publisher row uses singleton0 for release state.
    # V1 still validates the active stroke and every point's positive serial.
    normalized = ["PEN_UP" if line.split() == ["PEN_UP", "0"] else line for line in lines]
    return _parse_v3(("\n".join(normalized) + "\n").encode("ascii"))
