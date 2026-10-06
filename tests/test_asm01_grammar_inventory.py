"""Redaction, complete coverage and strict scope before remaining native bytes."""
import ast
import builtins
import json
from pathlib import Path

import pytest

from nextai_autoresearch import asm01_grammar_inventory as inventory


def sample(body=None):
    body = body or "PEN_DOWN 1\n314159 271828 1 1\n314160 271829 1 1\n314161 271830 1 1\n314162 271831 1 1\nPEN_UP 0"
    return ("CHARACTER_NAME: SECRET_NAME\nSTROKE_COUNT: 1\nX Y STYLUS_STATE STROKE\n" + body + "\nEND_CHARACTER: SECRET_NAME\n").encode()


@pytest.mark.parametrize("token,kind", [("123", "unsigned_integer"), ("+123", "explicit_plus_integer"),
    ("-123", "negative_integer"), ("1.0", "decimal"), (".5", "decimal"), ("-1.", "decimal"),
    ("1e4", "exponent"), ("-.5E-3", "exponent"), ("SECRET_TOKEN", "text_redacted"),
    ("NaN", "text_redacted"), ("inf", "text_redacted")])
def test_lexical_shapes(token, kind):
    assert inventory.lexical_kind(token) == kind


def test_all_rows_and_no_coordinate_conversion_or_emission(monkeypatch):
    converted = []
    def guarded(value):
        assert value not in {"314159", "271828", "314160", "271829", "314161", "271830", "314162", "271831"}
        converted.append(value)
        return builtins.int(value)
    monkeypatch.setattr(inventory, "int", guarded, raising=False)
    record = inventory.inventory_bytes(sample())
    assert record["nonempty_line_count"] == sum(record["row_counts"].values()) == 10
    assert sum(record["row_form_counts"].values()) == 10
    assert record["structural_anomaly_counts"] == {}
    assert record["point_state_counts"] == {"1": 4}
    assert converted and all(x in {"0", "1"} for x in converted)
    output = json.dumps(record)
    assert all(x not in output for x in ("SECRET_NAME", "314159", "271828"))


def test_unknown_forms_are_counted_and_redacted():
    payload = sample().replace(b"PEN_DOWN 1", b"UNKNOWN_SECRET 987654 123456\nPEN_DOWN 1")
    record = inventory.inventory_bytes(payload)
    assert record["row_counts"]["unknown"] == 1
    assert record["unknown_rows_redacted"] == [{"nonempty_line_index": 3, "arity": 3,
                                             "kinds": ["text_redacted", "unsigned_integer", "unsigned_integer"]}]
    output = json.dumps(record)
    assert all(x not in output for x in ("UNKNOWN_SECRET", "987654", "123456", "SECRET_NAME"))


@pytest.mark.parametrize("payload", [None, "text", b"a" * 262145, b"\xff"],
                         ids=["none", "text", "over-byte-cap", "non-ascii"])
def test_input_type_bytes_and_encoding_guard(payload):
    with pytest.raises(ValueError):
        inventory.inventory_bytes(payload)


@pytest.mark.parametrize("body,anomaly", [
    ("314159 271828 1 1\nPEN_DOWN 1\nPEN_UP 0", "point_outside_stroke"),
    ("PEN_DOWN 1\nPEN_DOWN 2\nPEN_UP 0", "repeated_pen_down"),
    ("PEN_UP 0", "pen_up_without_stroke"),
    ("PEN_DOWN 1\n314159 271828 0 1\nPEN_UP 0", "point_state_not_one"),
    ("PEN_DOWN 1\n314159 271828 1 2\nPEN_UP 0", "point_serial_mismatch"),
    ("PEN_DOWN 1\n-1 271828 1 1\nPEN_UP 0", "point_lexical_form_not_v1"),
    ("PEN_DOWN 1\n314159 271828 1 1", "incomplete_stroke_lifecycle"),
    ("PEN_DOWN 1\nPEN_UP 0 SECRET_TOKEN 765432", "pen_up_serial_form"),
])
def test_lifecycle_and_unrecognized_syntax_preserved(body, anomaly):
    record = inventory.inventory_bytes(sample(body))
    assert record["structural_anomaly_counts"][anomaly] >= 1
    assert "SECRET_TOKEN" not in json.dumps(record)


def test_release_zero_requires_unique_headed_layout():
    payload = sample().replace(b"X Y STYLUS_STATE STROKE\n", b"")
    record = inventory.inventory_bytes(payload)
    assert record["structural_anomaly_counts"]["headed_layout"] == 1
    assert record["structural_anomaly_counts"]["pen_up_serial_form"] == 1


def test_oversized_or_signed_categorical_field_never_converted():
    record = inventory.inventory_bytes(sample("PEN_DOWN 1234567\n1.5 2e4 -1 1234567\nPEN_UP 0"))
    assert record["marker_rows"][0]["categorical_values"] is None
    assert record["point_state_counts"] == {"negative_integer": 1}
    assert record["point_serial_counts"] == {"unsigned_integer": 1}


@pytest.mark.parametrize("marker", ["PEN_UP 999777", "PEN_UP 999777 888666", "PEN_DOWN 999777"])
def test_unknown_marker_operands_cannot_leak_coordinates(marker):
    record = inventory.inventory_bytes(sample("PEN_DOWN 1\n" + marker))
    assert record["marker_rows"][-1]["categorical_values"] is None
    assert all(value not in json.dumps(record) for value in ("999777", "888666"))


def canonical_listing():
    return "\n".join(f"Online Handwritten Assamese Characters Dataset/W{w}/{c}.{w}.txt"
                     for w in inventory.WRITERS for c in range(1, 184)) + "\n"


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "future", "traversal"])
def test_scope_rejects_before_file_content(tmp_path, mutation):
    names = canonical_listing().splitlines()
    if mutation == "missing":
        names.pop()
    elif mutation == "duplicate":
        names[-1] = names[0]
    elif mutation == "future":
        names[-1] = names[-1].replace("W20/183.20", "W21/183.21")
    else:
        names[-1] = "../outside.txt"
    with pytest.raises(ValueError, match="canonical members"):
        inventory.screen_members(tmp_path, "\n".join(names))


def test_complete_membership_and_unexpected_file_guard(tmp_path):
    listing = canonical_listing()
    for name in listing.splitlines():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic fixture; no native payload")
    members = inventory.screen_members(tmp_path, listing)
    assert len(members) == 1830 and members[0][:2] == (1, 1) and members[-1][:2] == (20, 183)
    (tmp_path / "foreign.txt").write_bytes(b"")
    with pytest.raises(ValueError, match="membership differs"):
        inventory.screen_members(tmp_path, listing)


def test_scanner_imports_only_structural_dependencies():
    tree = ast.parse(Path(inventory.__file__).read_text(encoding="utf-8"))
    names = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    names |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert names <= {"collections", "hashlib", "json", "pathlib", "re", "subprocess", "time", "utils"}
