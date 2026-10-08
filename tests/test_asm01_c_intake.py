"""Independent public/synthetic C parser and complete-intake conformance.

No fixture reads the publisher, extracted native files or historical arrays.
The historical receipt shape below is generated from independent synthetic
coordinates, including the fixed 1171-success/1172-attempt prefix.
"""
from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from nextai_autoresearch import asm01_task as old_task
from nextai_autoresearch import asm01_task_v6 as task
from nextai_autoresearch.asm01_task_v4 import parse_native_sample as old_parse


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/acquire_asm01_c_v1.py"
_spec = importlib.util.spec_from_file_location("asm01_c_synthetic_intake", SCRIPT)
intake = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(intake)
WRITERS = (1, 2, 3, 4, 5, 16, 17, 18, 19, 20)
POINTS = [(10 * i, 100 + i * i) for i in range(8)]


def release(points=None, count=1, serials=None, markers=True):
    points = POINTS if points is None else points
    serials = [1] * len(points) if serials is None else serials
    rows = ["CHARACTER_NAME: public-synthetic", f"STROKE_COUNT: {count}",
            "X Y STYLUS_STATE STROKE"]
    if markers:
        rows.append("PEN_DOWN")
    rows.extend(f"{x} {y} 1 {serial}" for (x, y), serial in zip(points, serials, strict=True))
    if markers:
        rows.append("PEN_UP 0")
    rows.append("END_CHARACTER: public-synthetic")
    return ("\n".join(rows) + "\n").encode("ascii")


def exact_array(actual, expected):
    expected = np.asarray(expected, dtype=np.float32)
    assert actual.dtype == np.float32 and actual.flags.c_contiguous
    assert actual.shape == expected.shape and actual.tobytes() == expected.tobytes()


@pytest.mark.parametrize("axis,value", [(0, -4392), (0, 4392), (1, -4868), (1, 4868)],
                         ids=["xmin", "xmax", "ymin", "ymax"])
def test_signed_inclusive_bounds_preserve_coordinate_values(axis, value):
    points = [list(point) for point in POINTS]
    points[0][axis] = value
    exact_array(task.parse_native_sample(release(points)), points)


@pytest.mark.parametrize("tokens", [("-0", "000100"), ("-0000", "0100"),
                                    ("0000", "00100"), ("00010", "-0009")],
                         ids=["minus-zero", "long-minus-zero", "zero", "signed-leading"])
def test_signed_zero_and_leading_zeros_are_numerical_equivalence(tokens):
    payload = release().replace(b"0 100 1 1", f"{tokens[0]} {tokens[1]} 01 0001".encode(), 1)
    expected = list(POINTS)
    expected[0] = (int(tokens[0]), int(tokens[1]))
    exact_array(task.parse_native_sample(payload), expected)


def test_long_zero_prefix_is_bounded_before_integer_conversion(monkeypatch):
    converted = []
    def bounded_int(value, *args):
        if isinstance(value, str):
            assert len(value.lstrip("-")) <= 5, "unbounded decimal conversion"
            converted.append(value)
        return builtins.int(value, *args)
    monkeypatch.setattr(task, "int", bounded_int, raising=False)
    payload = release().replace(b"0 100 1 1", b"-" + b"0" * 5000 + b"10 000100 0001 0001", 1)
    expected = list(POINTS)
    expected[0] = (-10, 100)
    exact_array(task.parse_native_sample(payload), expected)
    assert converted


@pytest.mark.parametrize("point", [
    b"-4393 100 1 1", b"4393 100 1 1", b"0 -4869 1 1", b"0 4869 1 1",
    b"+0 100 1 1", b"0.0 100 1 1", b"0 1e2 1 1", b"NaN 100 1 1",
    b"0 inf 1 1", b"0 100 -1 1", b"0 100 +1 1", b"0 100 0 1",
    b"0 100 2 1", b"0 100 1 -1", b"0 100 1 +1", b"0 100 1 0",
    b"0 100 1 2", b"0 100 1", b"0 100 1 1 extra",
], ids=["xmin-over", "xmax-over", "ymin-over", "ymax-over", "plus", "decimal",
        "exponent", "nan", "inf", "state-minus", "state-plus", "state-zero",
        "state-two", "serial-minus", "serial-plus", "serial-zero", "serial-over",
        "arity-three", "arity-five"])
def test_coordinate_and_unsigned_metadata_rejections(point):
    with pytest.raises(ValueError):
        task.parse_native_sample(release().replace(b"0 100 1 1", point, 1))


@pytest.mark.parametrize("count", ["0", "-1", "+1", "01", "16385", "1" + "0" * 5000],
                         ids=["zero", "minus", "plus", "noncanonical", "over", "huge"])
def test_stroke_count_must_be_canonical_and_bounded(count):
    with pytest.raises(ValueError):
        task.parse_native_sample(release().replace(b"STROKE_COUNT: 1", f"STROKE_COUNT: {count}".encode()))


def test_empty_ids_orphan_annotations_and_monotone_serials_preserve_order():
    second = [POINTS[-1]] + [(200 + 10 * i, 300 + i * i) for i in range(1, 8)]
    points = POINTS[:2] + [POINTS[1]] + POINTS[2:] + second
    serials = [2] * 9 + [4] * 8
    payload = release(points, count=5, serials=serials, markers=False)
    payload = payload.replace(b"X Y STYLUS_STATE STROKE\n",
                              b"X Y STYLUS_STATE STROKE\nPEN_UP 0\nPEN_DOWN\nPEN_DOWN\n")
    payload = payload.replace(b"END_CHARACTER:", b"PEN_UP 0\nPEN_UP 0\nEND_CHARACTER:")
    expected = POINTS + second
    metadata = {}
    value = task.parse_native_sample(payload, metadata=metadata)
    exact_array(value, expected)
    assert value.shape == (16, 2) and value[7].tobytes() == value[8].tobytes()
    assert metadata == {"declared_strokes": 5, "point_serial_counts": {"2": 9, "4": 8},
                        "empty_stroke_ids": [1, 3, 5], "raw_point_rows": 17, "retained_points": 16}
    without_annotations = release(points, count=5, serials=serials, markers=False)
    exact_array(task.parse_native_sample(without_annotations), expected)
    with pytest.raises(ValueError):
        task.parse_native_sample(release(POINTS, count=2, serials=[2, 2, 1, 1, 1, 1, 1, 1]))


def test_maximum_declared_empty_ids_do_not_infer_points():
    metadata = {}
    exact_array(task.parse_native_sample(release(count=16384, serials=[2] * 8), metadata=metadata), POINTS)
    assert metadata["declared_strokes"] == 16384 and metadata["point_serial_counts"] == {"2": 8}
    assert len(metadata["empty_stroke_ids"]) == 16383
    assert metadata["empty_stroke_ids"][:2] == [1, 3] and metadata["empty_stroke_ids"][-1] == 16384


def test_public_whitespace_and_opaque_names_cannot_change_geometry():
    payload = release().replace(b" ", b"\t").replace(b"\n", b"\r\n\r\n")
    payload = payload.replace(b"public-synthetic", b"other-opaque-envelope")
    exact_array(task.parse_native_sample(payload), POINTS)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "misplaced", "wrong",
                                       "unknown", "down-operand", "up-operand", "middle-count",
                                       "middle-end", "missing-envelope"],
                         ids=["missing", "duplicate", "misplaced", "wrong", "unknown",
                              "down-operand", "up-operand", "middle-count", "middle-end", "envelope"])
def test_release_grammar_has_no_legacy_fallback(mutation):
    payload = release()
    if mutation == "missing":
        payload = payload.replace(b"X Y STYLUS_STATE STROKE\n", b"")
    elif mutation == "duplicate":
        payload = payload.replace(b"PEN_DOWN\n", b"X Y STYLUS_STATE STROKE\nPEN_DOWN\n")
    elif mutation == "misplaced":
        payload = payload.replace(b"X Y STYLUS_STATE STROKE\nPEN_DOWN\n", b"PEN_DOWN\nX Y STYLUS_STATE STROKE\n")
    elif mutation == "wrong":
        payload = payload.replace(b"X Y STYLUS_STATE STROKE", b"Y X STYLUS_STATE STROKE")
    elif mutation == "unknown":
        payload = payload.replace(b"PEN_DOWN\n", b"UNKNOWN_ROW\nPEN_DOWN\n")
    elif mutation == "down-operand":
        payload = payload.replace(b"PEN_DOWN\n", b"PEN_DOWN 1\n")
    elif mutation == "up-operand":
        payload = payload.replace(b"PEN_UP 0\n", b"PEN_UP 00\n")
    elif mutation == "middle-count":
        payload = payload.replace(b"PEN_DOWN\n", b"STROKE_COUNT: 1\nPEN_DOWN\n")
    elif mutation == "middle-end":
        payload = payload.replace(b"PEN_DOWN\n", b"END_CHARACTER: x\nPEN_DOWN\n")
    else:
        payload = payload.replace(b"CHARACTER_NAME:", b"UNKNOWN_NAME:", 1)
    with pytest.raises(ValueError):
        task.parse_native_sample(payload)


@pytest.mark.parametrize("payload", [None, bytearray(release()), b"x" * 262145,
                                      release().replace(b"synthetic", b"\xc3\xa9")],
                         ids=["none", "bytearray", "bytes-over", "nonascii"])
def test_type_ascii_and_byte_envelope(payload):
    with pytest.raises(ValueError):
        task.parse_native_sample(payload)


def test_point_cap_exact_boundary_and_independent_reachable_branch(monkeypatch):
    assert task.POINTS_CAP == 32768
    # The real byte envelope normally dominates a 32769-row text. Temporarily
    # shrink only the fixture's cap to exercise the independent retained guard.
    monkeypatch.setattr(task, "POINTS_CAP", 4)
    exact_array(task.parse_native_sample(release(POINTS[:4])), POINTS[:4])
    with pytest.raises(ValueError, match="native_point_cap"):
        task.parse_native_sample(release(POINTS[:5]))


def test_each_required_view_and_minimum_points_must_be_valid():
    with pytest.raises(ValueError):
        task.parse_native_sample(release(POINTS[:3]))
    with pytest.raises(ValueError):
        task.parse_native_sample(release([(0, 0)] * 8))
    # Whole path varies, but the even write view is constant.
    points = [(0, 0), (1, 1), (0, 0), (2, 4), (0, 0), (3, 9), (0, 0), (4, 16)]
    with pytest.raises(ValueError):
        task.parse_native_sample(release(points))
    # Nominal query is constant, although the write view remains nondegenerate.
    points = [(0, 0), (500, 500), (1, 2), (500, 500), (2, 3), (500, 500), (3, 5), (500, 500)]
    with pytest.raises(ValueError):
        task.parse_native_sample(release(points))
    # Nominal query varies only at its fourth point; adverse removes that point.
    points[-1] = (800, 800)
    with pytest.raises(ValueError):
        task.parse_native_sample(release(points))


def test_transform_object_and_accepted_arrays_views_are_unchanged():
    assert task.transform is old_task.transform
    for name in ("pairs", "episode", "prepared_calibration", "training_sets", "arrays_hash", "episode_hash"):
        assert getattr(task, name) is getattr(old_task, name)
    payload = release()
    before, after = old_parse(payload), task.parse_native_sample(payload)
    exact_array(after, before)
    for view in ("write", "nominal", "adverse"):
        left, right = old_task.transform(before, view), task.transform(after, view)
        assert left.dtype == right.dtype == np.float32 and left.shape == right.shape == (64,)
        assert left.tobytes() == right.tobytes()


@pytest.fixture(scope="module")
def synthetic_corpus():
    members, payloads, expected, expected_arrays = [], {}, {}, {}
    for writer_index, writer in enumerate(WRITERS):
        for sample in range(1, 184):
            ordinal = writer_index * 183 + sample - 1
            base = ordinal if ordinal < 1171 else -(ordinal - 1170)
            points = [(base + 10 * i, 100 + i * i) for i in range(6 + ordinal % 5)]
            payload = release(points)
            path = Path("synthetic-only") / f"{writer}-{sample}.TXT"
            uid = f"{writer}:{sample}"
            members.append((writer, sample, path))
            payloads[path] = payload
            expected[uid] = hashlib.sha256(payload).hexdigest()
            expected_arrays[uid] = np.asarray(points, dtype=np.float32)
    first = [f"{w}:{s}" for w, s, _ in members]
    old = {key: expected[key] for key in first[:75]}
    prior = {
        "complete": False, "native_files_attempted": 1172, "native_files_converted": 1171,
        "old74_compared": 74, "D_samples_opened": 257, "current_sample": "17:74",
        "error_category": "normalize",
        "attempted_sample_text_sha256": {key: expected[key] for key in first[:1172]},
        "sample_array_sha256": {key: old_task.arrays_hash(expected_arrays[key]) for key in first[:1171]},
        "old_array_sha256": {key: old_task.arrays_hash(expected_arrays[key]) for key in first[:74]},
        "old_descriptor_sha256": {
            key: {view: old_task.arrays_hash(old_task.transform(expected_arrays[key], view))
                  for view in ("write", "nominal", "adverse")} for key in first[:74]},
    }
    return members, payloads, expected, old, prior, expected_arrays


def call_collect(corpus, *, mutate=None):
    members, payloads, expected, old, prior, expected_arrays = copy.deepcopy(corpus)
    if mutate:
        mutate(members, payloads, expected, old, prior, expected_arrays)
    receipt, reads = {}, []
    def reader(path):
        reads.append(path)
        return payloads[path]
    return members, receipt, reads, lambda: intake.collect(members, expected, old, prior, receipt, reader=reader)


def stopped(call, receipt, reads, members, attempted):
    with pytest.raises(ValueError):
        call()
    assert receipt["complete"] is False and receipt["error_category"]
    assert receipt["native_files_attempted"] == attempted
    assert reads == [entry[2] for entry in members[:attempted]]
    return receipt


def test_complete_1830_intake_compares_all_1171_and_74_before_serving(synthetic_corpus):
    members, receipt, reads, call = call_collect(synthetic_corpus)
    arrays, hashes = call()
    assert receipt["complete"] is True
    assert receipt["native_files_attempted"] == receipt["native_files_converted"] == 1830
    assert receipt["old74_compared"] == 74 and receipt["previous1171_compared"] == 1171
    assert receipt["D_samples_opened"] == 915
    assert reads == [entry[2] for entry in members] and len(set(reads)) == 1830
    assert receipt["attempted_sample_text_sha256"] == synthetic_corpus[2]
    assert receipt["sample_array_sha256"] == {
        key: old_task.arrays_hash(value) for key, value in synthetic_corpus[5].items()}
    assert set(arrays) == {f"{prefix}_{writer}" for writer in WRITERS for prefix in ("points", "offsets", "rows")}
    assert set(hashes) == {str(writer) for writer in WRITERS}
    for writer in WRITERS:
        paths = [synthetic_corpus[5][f"{writer}:{sample}"] for sample in range(1, 184)]
        expected = {"points": np.concatenate(paths),
                    "offsets": np.asarray([0] + list(np.cumsum([len(v) for v in paths])), dtype=np.int64),
                    "rows": np.asarray([(sample, writer) for sample in range(1, 184)], dtype=np.int64)}
        for prefix, value in expected.items():
            actual = arrays[f"{prefix}_{writer}"]
            assert actual.dtype == value.dtype and actual.shape == value.shape
            assert actual.tobytes() == value.tobytes()
        assert hashes[str(writer)] == old_task.arrays_hash(*(expected[name] for name in ("points", "offsets", "rows")))


def test_old_74_array_difference_stops_before_75_and_any_D(synthetic_corpus, monkeypatch):
    original = intake.parse_native_sample
    def changed(payload, **kwargs):
        value = original(payload, **kwargs).copy()
        value[0, 0] += np.float32(1)
        return value
    monkeypatch.setattr(intake, "parse_native_sample", changed)
    members, receipt, reads, call = call_collect(synthetic_corpus)
    stopped(call, receipt, reads, members, 1)
    assert receipt["old74_compared"] == receipt["D_samples_opened"] == 0


@pytest.mark.parametrize("view", ["write", "nominal", "adverse"])
def test_each_saved_old_view_is_mandatory_before_75(synthetic_corpus, view):
    def mutate(members, payloads, expected, old, prior, arrays):
        prior["old_descriptor_sha256"]["1:1"][view] = "0" * 64
    members, receipt, reads, call = call_collect(synthetic_corpus, mutate=mutate)
    stopped(call, receipt, reads, members, 1)
    assert receipt["old74_compared"] == receipt["D_samples_opened"] == 0


def test_previous_accepted_array_75_is_checked_not_only_old74(synthetic_corpus):
    def mutate(members, payloads, expected, old, prior, arrays):
        prior["sample_array_sha256"]["1:75"] = "0" * 64
    members, receipt, reads, call = call_collect(synthetic_corpus, mutate=mutate)
    stopped(call, receipt, reads, members, 75)
    assert receipt["old74_compared"] == 74 and receipt["previous1171_compared"] == 74
    assert receipt["D_samples_opened"] == 0


def test_corrupt_raw_reader_payload_stops_before_conversion(synthetic_corpus):
    def mutate(members, payloads, expected, old, prior, arrays):
        path = members[0][2]
        payloads[path] = payloads[path].replace(b"0 100 1 1", b"1 100 1 1", 1)
    members, receipt, reads, call = call_collect(synthetic_corpus, mutate=mutate)
    stopped(call, receipt, reads, members, 1)
    assert receipt["native_files_converted"] == receipt["old74_compared"] == 0


def test_unknown_row_75_stops_after_exact_old74_without_D(synthetic_corpus):
    def mutate(members, payloads, expected, old, prior, arrays):
        path = members[74][2]
        payloads[path] = payloads[path].replace(b"PEN_DOWN\n", b"UNKNOWN_ROW\nPEN_DOWN\n", 1)
        digest = hashlib.sha256(payloads[path]).hexdigest()
        expected["1:75"] = old["1:75"] = prior["attempted_sample_text_sha256"]["1:75"] = digest
    members, receipt, reads, call = call_collect(synthetic_corpus, mutate=mutate)
    stopped(call, receipt, reads, members, 75)
    assert receipt["old74_compared"] == receipt["native_files_converted"] == 74
    assert receipt["D_samples_opened"] == 0


def test_duplicate_final_array_invalidates_complete_cohort_without_filtering(synthetic_corpus):
    def mutate(members, payloads, expected, old, prior, arrays):
        path = members[-1][2]
        payloads[path] = payloads[members[0][2]].replace(b"public-synthetic", b"different-opaque-name")
        expected["20:183"] = hashlib.sha256(payloads[path]).hexdigest()
    members, receipt, reads, call = call_collect(synthetic_corpus, mutate=mutate)
    stopped(call, receipt, reads, members, 1830)
    assert receipt["validated_files"] == 1829 and receipt["native_files_converted"] == 1830
    assert receipt["previous1171_compared"] == 1171 and receipt["old74_compared"] == 74


@pytest.mark.parametrize("alter", ["future", "sample", "order", "path", "expected", "old75",
                                   "prior-prefix", "prior-array", "prior-old", "prior-view", "prior-count"],
                         ids=["future", "sample", "order", "path", "expected", "old75",
                              "prior-prefix", "prior-array", "prior-old", "prior-view", "prior-count"])
def test_foreign_or_inconsistent_metadata_rejects_before_reader(synthetic_corpus, alter):
    def mutate(members, payloads, expected, old, prior, arrays):
        if alter == "future":
            members[0] = (6, 1, members[0][2])
        elif alter == "sample":
            members[0] = (1, 184, members[0][2])
        elif alter == "order":
            members[0], members[1] = members[1], members[0]
        elif alter == "path":
            members[1] = (1, 2, members[0][2])
        elif alter == "expected":
            del expected["20:183"]
        elif alter == "old75":
            old["1:75"] = "0" * 64
        elif alter == "prior-prefix":
            prior["attempted_sample_text_sha256"]["17:75"] = prior["attempted_sample_text_sha256"].pop("17:74")
        elif alter == "prior-array":
            del prior["sample_array_sha256"]["17:73"]
        elif alter == "prior-old":
            prior["old_array_sha256"]["1:1"] = "0" * 64
        elif alter == "prior-view":
            del prior["old_descriptor_sha256"]["1:1"]["adverse"]
        else:
            prior["native_files_converted"] = 1170
    members, receipt, reads, call = call_collect(synthetic_corpus, mutate=mutate)
    stopped(call, receipt, reads, members, 0)
    assert receipt["native_files_converted"] == receipt["D_samples_opened"] == 0


def test_receipt_cannot_be_reused_as_an_intake_retry(synthetic_corpus):
    members, receipt, reads, call = call_collect(synthetic_corpus)
    call()
    before = len(reads)
    with pytest.raises(ValueError):
        call()
    assert len(reads) == before == 1830
