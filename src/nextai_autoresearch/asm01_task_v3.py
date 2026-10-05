"""Prospective header-only adapter; preserve V1 numeric/stroke/geometry rules."""
from .asm01_task import parse_native_sample as _parse_v1


_COLUMNS = ["X", "Y", "STYLUS_STATE", "STROKE"]


def parse_native_sample(payload):
    if not isinstance(payload, bytes) or len(payload) > 262144:
        raise ValueError("Native sample byte cap/type")
    lines = [line.strip() for line in payload.decode("ascii").splitlines() if line.strip()]
    headers = [i for i, line in enumerate(lines) if line.split() == _COLUMNS]
    if not headers:
        return _parse_v1(payload)
    if headers != [2]:
        raise ValueError("Native column header count/location")
    # V1 already normalizes nonempty lines. Remove only the one public header;
    # its original strict parser still owns every point and lifecycle check.
    normalized = ("\n".join(lines[:2] + lines[3:]) + "\n").encode("ascii")
    return _parse_v1(normalized)
