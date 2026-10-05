import numpy as np
import pytest

from nextai_autoresearch.asm01_task import parse_native_sample as parse_v1, transform
from nextai_autoresearch.asm01_task_v3 import parse_native_sample as parse_v3
from nextai_autoresearch.asm01_task_v4 import parse_native_sample


def fixture(strokes=2, header=True, native=True):
    rows = ["CHARACTER_NAME: fixture", f"STROKE_COUNT: {strokes}"]
    if header:
        rows.append("X Y STYLUS_STATE STROKE")
    for stroke in range(1, strokes + 1):
        rows.append(f"PEN_DOWN {stroke}")
        rows += [f"{(stroke-1)*100+i*10} {(stroke-1)*100+i*i} 1 {stroke}" for i in range(12)]
        rows.append("PEN_UP 0" if native else f"PEN_UP 0 {stroke}")
    rows.append("END_CHARACTER: fixture")
    return ("\n".join(rows) + "\n").encode("ascii")


@pytest.mark.parametrize("strokes", [1, 2])
@pytest.mark.parametrize("marker", [b"PEN_UP 0", b"PEN_UP\t0", b"PEN_UP   0"])
def test_native_release_keeps_exact_points_and_all_descriptors(strokes, marker):
    expected = parse_v1(fixture(strokes, header=False, native=False))
    actual = parse_native_sample(fixture(strokes).replace(b"PEN_UP 0", marker))
    np.testing.assert_array_equal(actual, expected)
    assert actual.dtype == np.float32 and actual.shape == (12 * strokes, 2)
    for view in ("write", "nominal", "adverse"):
        np.testing.assert_array_equal(transform(actual, view), transform(expected, view))


def test_v3_failure_remains_reproducible():
    with pytest.raises(ValueError, match="Pen-up supplied state/stroke"):
        parse_v3(fixture())


def test_no_header_zero_retains_legacy_rejection():
    with pytest.raises(ValueError) as previous:
        parse_v3(fixture(header=False))
    with pytest.raises(ValueError) as current:
        parse_native_sample(fixture(header=False))
    assert str(current.value) == str(previous.value)


@pytest.mark.parametrize("header", [False, True])
@pytest.mark.parametrize("form", ["state-and-serial", "serial-only", "bare"])
def test_old_valid_marker_forms_and_no_header_are_unchanged(header, form):
    payload = fixture(header=header, native=False)
    if form != "state-and-serial":
        for stroke in (1, 2):
            replacement = f"PEN_UP {stroke}" if form == "serial-only" else "PEN_UP"
            payload = payload.replace(f"PEN_UP 0 {stroke}".encode(), replacement.encode())
    np.testing.assert_array_equal(parse_native_sample(payload), parse_v3(payload))


@pytest.mark.parametrize("header", [
    b"Y X STYLUS_STATE STROKE", b"X Y STYLUS_STATE", b"X Y STYLUS_STATE STROKE EXTRA",
    b"X Y PRESSURE STROKE", b"x y stylus_state stroke", b"X Y STROKE STYLUS_STATE",
])
def test_malformed_header_cannot_enable_zero_release(header):
    with pytest.raises(ValueError):
        parse_native_sample(fixture().replace(b"X Y STYLUS_STATE STROKE", header))


@pytest.mark.parametrize("position", [0, 1, 3, 5, -1])
def test_misplaced_header_is_still_rejected(position):
    rows = fixture().decode().splitlines()
    rows.insert(position, rows.pop(2))
    with pytest.raises(ValueError, match="Native column header count/location"):
        parse_native_sample(("\n".join(rows) + "\n").encode())


def test_duplicate_header_is_still_rejected():
    with pytest.raises(ValueError, match="Native column header count/location"):
        parse_native_sample(fixture().replace(b"PEN_DOWN 1", b"X Y STYLUS_STATE STROKE\nPEN_DOWN 1"))


@pytest.mark.parametrize("point", [
    b"4393 0 1 1", b"0 4869 1 1", b"-1 0 1 1", b"0.5 0 1 1", b"0 0 0 1", b"0 0 1 2",
])
def test_numeric_coordinate_state_and_serial_rules_do_not_change(point):
    with pytest.raises(ValueError):
        parse_native_sample(fixture().replace(b"0 0 1 1", point, 1))


@pytest.mark.parametrize("marker", [
    b"PEN_UP -1", b"PEN_UP 00", b"PEN_UP 0.0", b"PEN_UP 2", b"PEN_UP 0 0",
    b"PEN_UP 0 2", b"PEN_UP 1 1", b"PEN_UP 0 1 extra",
])
def test_wrong_marker_fields_stay_rejected(marker):
    with pytest.raises(ValueError):
        parse_native_sample(fixture().replace(b"PEN_UP 0\n", marker + b"\n", 1))


@pytest.mark.parametrize("before,after", [
    (b"STROKE_COUNT: 2", b"STROKE_COUNT: 3"),
    (b"PEN_UP 0\nPEN_DOWN 2", b"PEN_DOWN 2"),
    (b"PEN_UP 0\nPEN_DOWN 2", b"PEN_UP 0\nPEN_UP 0\nPEN_DOWN 2"),
    (b"PEN_DOWN 1", b"PEN_UP 0\nPEN_DOWN 1"),
])
def test_release_annotation_does_not_relax_pen_lifecycle(before, after):
    with pytest.raises(ValueError):
        parse_native_sample(fixture().replace(before, after, 1))


@pytest.mark.parametrize("payload", [None, bytearray(b"x"), fixture() + b" " * 262144],
                         ids=["none", "bytearray", "oversize-before-normalization"])
def test_original_byte_and_type_caps_precede_normalization(payload):
    with pytest.raises(ValueError, match="Native sample byte cap/type"):
        parse_native_sample(payload)


def test_ascii_requirement_stays_strict():
    with pytest.raises(UnicodeDecodeError):
        parse_native_sample(fixture().replace(b"fixture", b"\xc3\xa9"))


def test_degenerate_points_are_not_rescued():
    rows = ["CHARACTER_NAME: fixture", "STROKE_COUNT: 1", "X Y STYLUS_STATE STROKE", "PEN_DOWN"]
    rows += ["0 0 1 1"] * 12 + ["PEN_UP 0", "END_CHARACTER: fixture"]
    with pytest.raises(ValueError):
        parse_native_sample(("\n".join(rows) + "\n").encode())
