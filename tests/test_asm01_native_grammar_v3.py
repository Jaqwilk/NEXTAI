import numpy as np
import pytest

from nextai_autoresearch.asm01_task import parse_native_sample as parse_v1, transform
from nextai_autoresearch.asm01_task_v3 import parse_native_sample


def sample():
    rows = ["CHARACTER_NAME: public-fixture", "STROKE_COUNT: 2", "PEN_DOWN 1"]
    rows += [f"{i * 10} {i * i} 1 1" for i in range(12)]
    rows += ["PEN_UP 0 1", "PEN_DOWN 2"]
    rows += [f"{100 + i * 10} {100 + i * i} 1 2" for i in range(8)]
    rows += ["PEN_UP 0 2", "END_CHARACTER: public-fixture"]
    return ("\n".join(rows) + "\n").encode("ascii")


def header_sample(header="X Y STYLUS_STATE STROKE", position=2):
    rows = sample().decode("ascii").splitlines()
    rows.insert(position, header)
    return ("\n".join(rows) + "\n").encode("ascii")


@pytest.mark.parametrize("separator", [" ", "\t", " \t "])
def test_header_changes_no_points_or_descriptors(separator):
    payload = header_sample(separator.join(["X", "Y", "STYLUS_STATE", "STROKE"]))
    expected = parse_v1(sample())
    actual = parse_native_sample(payload)
    np.testing.assert_array_equal(actual, expected)
    assert actual.dtype == np.float32 and actual.shape == (20, 2)
    for view in ("write", "nominal", "adverse"):
        np.testing.assert_array_equal(transform(actual, view), transform(expected, view))


def test_legacy_no_header_preserves_success_and_failure():
    np.testing.assert_array_equal(parse_native_sample(sample()), parse_v1(sample()))
    bad = sample().replace(b"STROKE_COUNT: 2", b"STROKE_COUNT: 3")
    with pytest.raises(ValueError) as original:
        parse_v1(bad)
    with pytest.raises(ValueError) as adapted:
        parse_native_sample(bad)
    assert str(original.value) == str(adapted.value)


def test_original_header_failure_stays_reproducible():
    with pytest.raises(ValueError, match="Native point grammar"):
        parse_v1(header_sample())


@pytest.mark.parametrize("header", [
    "Y X STYLUS_STATE STROKE", "X Y STYLUS_STATE", "X Y STYLUS_STATE STROKE EXTRA",
    "X Y PRESSURE STROKE", "x y stylus_state stroke", "X Y STROKE STYLUS_STATE",
])
def test_malformed_headers_are_not_inferred_or_reordered(header):
    with pytest.raises(ValueError):
        parse_native_sample(header_sample(header))


@pytest.mark.parametrize("position", [0, 1, 3, 5, -1])
def test_misplaced_header_is_rejected(position):
    with pytest.raises(ValueError, match="Native column header count/location"):
        parse_native_sample(header_sample(position=position))


def test_duplicate_header_is_rejected():
    payload = header_sample().replace(b"PEN_DOWN 1", b"X Y STYLUS_STATE STROKE\nPEN_DOWN 1")
    with pytest.raises(ValueError, match="Native column header count/location"):
        parse_native_sample(payload)


@pytest.mark.parametrize("point", ["5000 0 1 1", "0 5000 1 1", "0 0 0 1", "0 0 1 2", "-1 0 1 1", "0.5 0 1 1"])
def test_numeric_rules_remain_strict(point):
    payload = header_sample().replace(b"0 0 1 1", point.encode("ascii"), 1)
    with pytest.raises(ValueError):
        parse_native_sample(payload)


@pytest.mark.parametrize("change", [
    (b"PEN_UP 0 1", b"PEN_UP 0 2"),
    (b"PEN_DOWN 2", b"PEN_DOWN 1"),
    (b"PEN_UP 0 2", b""),
])
def test_pen_lifecycle_remains_strict(change):
    with pytest.raises(ValueError):
        parse_native_sample(header_sample().replace(*change))


def test_degenerate_geometry_is_rejected():
    rows = ["CHARACTER_NAME: x", "STROKE_COUNT: 1", "X Y STYLUS_STATE STROKE", "PEN_DOWN 1"]
    rows += ["0 0 1 1"] * 8 + ["PEN_UP 0 1", "END_CHARACTER: x"]
    with pytest.raises(ValueError):
        parse_native_sample(("\n".join(rows) + "\n").encode("ascii"))


@pytest.mark.parametrize("payload", [None, bytearray(b"x"), header_sample() + b" " * 262144])
def test_original_byte_cap_and_type_precede_header_removal(payload):
    with pytest.raises(ValueError, match="Native sample byte cap/type"):
        parse_native_sample(payload)


def test_non_ascii_remains_rejected():
    with pytest.raises(UnicodeDecodeError):
        parse_native_sample(header_sample().replace(b"public-fixture", b"\xc3\xa9"))
