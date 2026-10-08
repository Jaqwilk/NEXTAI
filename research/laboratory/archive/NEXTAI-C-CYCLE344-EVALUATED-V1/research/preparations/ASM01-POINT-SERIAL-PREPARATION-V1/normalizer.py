"""Pure, preparatory release-to-legacy serialization; no native authority."""

import re


BYTES_CAP = 262144
_COLUMNS = ["X", "Y", "STYLUS_STATE", "STROKE"]
_UNSIGNED = re.compile(r"[0-9]+")
_COUNT = re.compile(r"STROKE_COUNT:\s*([1-9][0-9]*)")


def normalize_release_bytes(payload: bytes) -> bytes:
    """Preserve opaque point rows while making their serials authoritative."""
    if not isinstance(payload, bytes):
        raise ValueError("bytes required")
    if len(payload) > BYTES_CAP:
        raise ValueError("input too large")
    try:
        decoded = payload.decode("ascii")
    except UnicodeDecodeError:
        raise ValueError("ASCII required") from None
    lines = [line.strip() for line in decoded.splitlines() if line.strip()]
    if (
        len(lines) < 4
        or not lines[0].startswith("CHARACTER_NAME:")
        or not lines[-1].startswith("END_CHARACTER:")
    ):
        raise ValueError("invalid envelope")
    count_match = _COUNT.fullmatch(lines[1])
    if count_match is None:
        raise ValueError("invalid stroke count")
    count_token = count_match.group(1)
    maximum_count = str(BYTES_CAP // 16)
    if len(count_token) > len(maximum_count) or (
        len(count_token) == len(maximum_count) and count_token > maximum_count
    ):
        raise ValueError("normalized output too large")
    count = int(count_token)
    header_positions = [
        index for index, line in enumerate(lines) if line.split() == _COLUMNS
    ]
    if header_positions != [2]:
        raise ValueError("invalid column header")

    # No output is materialized until its complete, exact size is known.
    normalized_size = sum(len(lines[index]) + 1 for index in (0, 1, 2, len(lines) - 1))
    normalized_size += 16 * count
    points = []
    previous_serial = 0
    for line in lines[3:-1]:
        fields = line.split()
        if fields == ["PEN_DOWN"] or fields == ["PEN_UP", "0"]:
            continue
        if len(fields) != 4:
            raise ValueError("invalid body row")
        for index in (0, 1):
            token = fields[index]
            if token == "-0":
                fields[index] = "0"
            elif _UNSIGNED.fullmatch(token) is None:
                raise ValueError("invalid coordinate token")
        if (
            _UNSIGNED.fullmatch(fields[2]) is None
            or _UNSIGNED.fullmatch(fields[3]) is None
        ):
            raise ValueError("invalid point metadata")
        # Remove redundant zeros only for bounded metadata conversion; output
        # still retains the original state and serial token strings.
        state_token = fields[2].lstrip("0") or "0"
        if state_token != "1" or int(state_token) != 1:
            raise ValueError("invalid point state")
        serial_token = fields[3].lstrip("0") or "0"
        if len(serial_token) > len(count_token) or (
            len(serial_token) == len(count_token) and serial_token > count_token
        ):
            raise ValueError("point serial out of range")
        serial = int(serial_token)
        if serial < 1 or serial < previous_serial:
            raise ValueError("invalid point serial")
        previous_serial = serial
        normalized_size += sum(len(token) for token in fields) + 4
        points.append((serial, fields))
    if len(points) < 4:
        raise ValueError("too few point rows")
    if normalized_size > BYTES_CAP:
        raise ValueError("normalized output too large")

    output_lines = lines[:3]
    point_index = 0
    for serial in range(1, count + 1):
        output_lines.append("PEN_DOWN")
        while point_index < len(points) and points[point_index][0] == serial:
            output_lines.append(" ".join(points[point_index][1]))
            point_index += 1
        output_lines.append("PEN_UP")
    output_lines.append(lines[-1])
    return ("\n".join(output_lines) + "\n").encode("ascii")
