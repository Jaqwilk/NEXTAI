"""Eight frozen synthetic intake cases; no native bytes or research fits."""
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import nextai_autoresearch
from nextai_autoresearch.asm01_task import arrays_hash, transform
from nextai_autoresearch.utils import load_json, sha256_file


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = Path(__file__).with_name("intake.py")
PLAN_PATH = ROOT / "research/plans/ASM01-POINT-SERIAL-NATIVE-CONFORMANCE-V1.json"
PLAN_SHA = "6db8382e5080fbc4b3b244289bb04bbb6f0f3b7f730b5f12bfef9d3d8da3b8c4"
BINDING_PATH = ROOT / "research/reviews/ASM01-POINT-SERIAL-NATIVE-SOURCE-BINDINGS-V1.json"
spec = importlib.util.spec_from_file_location("frozen_native_conformance_intake", MODULE_PATH)
intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intake)
WRITERS = (1, 2, 3, 4, 5, 16, 17, 18, 19, 20)
CASES = ("complete", "old-difference", "raw-sha", "duplicate", "stop-first",
         "future-scope", "bindings", "clone-origin")


def synthetic_input():
    """Independently construct every raw payload and its expected point array."""
    members, payloads, expected_sha, expected_arrays = [], {}, {}, {}
    for writer_index, writer in enumerate(WRITERS):
        for sample in range(1, 184):
            ordinal = writer_index * 183 + sample - 1
            points = [(ordinal + 10 * point, 100 + point * point)
                      for point in range(6 + ordinal % 5)]
            lines = ["CHARACTER_NAME: synthetic", "STROKE_COUNT: 1",
                     "X Y STYLUS_STATE STROKE", "PEN_DOWN"]
            lines.extend(f"{x} {y} 1 1" for x, y in points)
            lines.extend(("PEN_UP 0", "END_CHARACTER: synthetic"))
            payload = ("\n".join(lines) + "\n").encode("ascii")
            path = ROOT / "research/preparations/synthetic-only" / f"{writer}-{sample}.TXT"
            uid = f"{writer}:{sample}"
            members.append((writer, sample, path))
            payloads[path] = payload
            expected_sha[uid] = hashlib.sha256(payload).hexdigest()
            expected_arrays[uid] = np.asarray(points, dtype=np.float32)
    old_sha = {f"1:{sample}": expected_sha[f"1:{sample}"] for sample in range(1, 76)}
    return members, payloads, expected_sha, old_sha, expected_arrays


def run_synthetic(members, payloads, expected_sha, old_sha):
    receipt, reads = {}, []
    def reader(path):
        reads.append(path)
        return payloads[path]
    arrays, writer_hashes = intake.collect(members, expected_sha, old_sha, receipt, reader=reader)
    return {"arrays": arrays, "writer_hashes": writer_hashes}, receipt, reads


def expect_failure(members, payloads, expected_sha, old_sha, category, attempted):
    receipt, reads = {}, []
    def reader(path):
        reads.append(path)
        return payloads[path]
    with pytest.raises(ValueError):
        intake.collect(members, expected_sha, old_sha, receipt, reader=reader)
    assert receipt["complete"] is False
    assert receipt["error_category"] == category
    assert receipt["attempted_files"] == attempted
    assert len(reads) == attempted
    assert reads == [entry[2] for entry in members[:attempted]]
    assert receipt["D_samples_opened"] == 0
    assert not any(entry[0] >= 16 and entry[2] in reads for entry in members)
    return receipt, reads


@pytest.mark.parametrize("case", CASES, ids=CASES)
def test_intake(case, monkeypatch):
    if case == "clone-origin":
        assert ROOT.name == "NEXTAI-VALIDATION-20261002"
        assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(ROOT / "src")
        assert MODULE_PATH.resolve().is_relative_to(ROOT)
        assert sha256_file(PLAN_PATH) == PLAN_SHA
        plan = load_json(PLAN_PATH)
        assert plan["fixtures"]["new8_ids"] == list(CASES)
        assert plan["fixtures"]["total"] == 46
        assert plan["scientific_execution_authority"] is False
        assert plan["research_fit_seconds_cap"] == plan["EXP_cap"] == plan["registration_cap"] == 0
        for name, digest in plan["parent_file_bindings"].items():
            assert sha256_file(ROOT / name) == digest, name
        for name, binding in plan["ledger_prefixes"].items():
            prefix = (ROOT / "research" / name).read_bytes()[:binding["bytes"]]
            assert hashlib.sha256(prefix).hexdigest() == binding["sha256"], name
        binding = load_json(BINDING_PATH)
        assert binding["plan_sha256"] == PLAN_SHA
        # The root freezes the complete sources before the sole execution.
        for name in plan["implementation_paths"]:
            assert binding["files"][name] == sha256_file(ROOT / name), name
        normalizer = plan["intake_binding"]
        assert sha256_file(ROOT / normalizer["normalizer_path"]) == normalizer["normalizer_sha256"]
        return

    members, payloads, expected_sha, old_sha, expected_arrays = synthetic_input()
    if case == "complete":
        result, receipt, reads = run_synthetic(members, payloads, expected_sha, old_sha)
        assert receipt["complete"] is True
        assert receipt["attempted_files"] == receipt["converted_files"] == 1830
        assert receipt["old_compared"] == 74
        assert receipt["D_samples_opened"] == 915
        assert reads == [entry[2] for entry in members]
        assert len(set(reads)) == 1830
        assert receipt["attempted_sample_text_sha256"] == expected_sha
        assert set(result["arrays"]) == {f"{key}_{writer}" for writer in WRITERS
                                         for key in ("points", "offsets", "rows")}
        assert set(result["writer_hashes"]) == {str(writer) for writer in WRITERS}
        for writer in WRITERS:
            paths = [expected_arrays[f"{writer}:{sample}"] for sample in range(1, 184)]
            points = np.concatenate(paths)
            offsets = np.asarray([0] + list(np.cumsum([len(path) for path in paths])), dtype=np.int64)
            rows = np.asarray([(sample, writer) for sample in range(1, 184)], dtype=np.int64)
            for key, expected in (("points", points), ("offsets", offsets), ("rows", rows)):
                actual = result["arrays"][f"{key}_{writer}"]
                assert actual.dtype == expected.dtype and actual.shape == expected.shape
                assert actual.tobytes() == expected.tobytes()
            assert result["writer_hashes"][str(writer)] == arrays_hash(points, offsets, rows)
            for sample, expected in enumerate(paths, 1):
                actual = result["arrays"][f"points_{writer}"][offsets[sample - 1]:offsets[sample]]
                for view in ("write", "nominal", "adverse"):
                    left, right = transform(actual, view), transform(expected, view)
                    assert left.dtype == right.dtype and left.shape == right.shape == (64,)
                    assert left.tobytes() == right.tobytes()
        return

    if case == "old-difference":
        original = intake.normalize_release_bytes
        def changed(payload):
            return original(payload).replace(b"0 100 1 1\n", b"1 100 1 1\n", 1)
        with monkeypatch.context() as patch:
            patch.setattr(intake, "normalize_release_bytes", changed)
            receipt, _ = expect_failure(members, payloads, expected_sha, old_sha, "old_array_difference", 1)
            assert receipt["old_compared"] == 0 and receipt["current_UID"] == "1:1"
            assert receipt["converted_files"] == 1
        # Independently challenge each mandatory old/new descriptor comparison.
        for target_view in ("write", "nominal", "adverse"):
            target_calls = [0]
            def changed_view(value, view):
                output = transform(value, view)
                if view == target_view:
                    target_calls[0] += 1
                    if target_calls[0] == 2:
                        output = output.copy()
                        output[0] += np.float32(0.001)
                return output
            with monkeypatch.context() as patch:
                patch.setattr(intake, "transform", changed_view)
                receipt, _ = expect_failure(members, payloads, expected_sha, old_sha, "old_view_difference", 1)
                assert receipt["old_compared"] == 0 and receipt["converted_files"] == 1
                assert receipt["current_UID"] == "1:1"
        return

    if case == "raw-sha":
        # Keep preregistered maps consistent; corrupt only the injected payload.
        path = members[0][2]
        payloads[path] = payloads[path].replace(b"0 100 1 1", b"1 100 1 1", 1)
        receipt, _ = expect_failure(members, payloads, expected_sha, old_sha, "raw_sha", 1)
        assert receipt["converted_files"] == receipt["old_compared"] == 0
        assert receipt["attempted_sample_text_sha256"]["1:1"] == hashlib.sha256(payloads[path]).hexdigest()
        assert receipt["current_UID"] == "1:1"
        return

    if case == "duplicate":
        target = members[74][2]
        # A different envelope keeps raw bytes distinct but duplicates canonical points.
        payloads[target] = payloads[members[0][2]].replace(b"synthetic", b"synthetic-duplicate")
        expected_sha["1:75"] = hashlib.sha256(payloads[target]).hexdigest()
        old_sha["1:75"] = expected_sha["1:75"]
        receipt, _ = expect_failure(members, payloads, expected_sha, old_sha, "duplicate", 75)
        assert receipt["old_compared"] == 74 and receipt["converted_files"] == 75
        assert receipt["current_UID"] == "1:75"
        return

    if case == "stop-first":
        target = members[74][2]
        payloads[target] = payloads[target].replace(b"PEN_DOWN\n", b"UNKNOWN_ROW\nPEN_DOWN\n", 1)
        expected_sha["1:75"] = hashlib.sha256(payloads[target]).hexdigest()
        old_sha["1:75"] = expected_sha["1:75"]
        receipt, _ = expect_failure(members, payloads, expected_sha, old_sha, "normalize", 75)
        assert receipt["old_compared"] == 74 and receipt["converted_files"] == 74
        assert receipt["current_UID"] == "1:75"
        assert len(receipt["attempted_sample_text_sha256"]) == 75
        return

    if case == "future-scope":
        variants = []
        future = list(members)
        future[0] = (6, 1, members[0][2])
        variants.append(future)
        wrong_uid = list(members)
        wrong_uid[0] = (1, 184, members[0][2])
        variants.append(wrong_uid)
        wrong_order = list(members)
        wrong_order[0], wrong_order[1] = wrong_order[1], wrong_order[0]
        variants.append(wrong_order)
        repeated_path = list(members)
        repeated_path[1] = (1, 2, repeated_path[0][2])
        variants.append(repeated_path)
        for variant in variants:
            expect_failure(variant, payloads, expected_sha, old_sha, "metadata", 0)
        return

    assert case == "bindings"
    missing_expected = dict(expected_sha)
    del missing_expected["20:183"]
    foreign_expected = dict(expected_sha, **{"6:1": "0" * 64})
    invalid_expected = dict(expected_sha, **{"20:183": "G" * 64})
    wrong_old75 = dict(old_sha, **{"1:75": "0" * 64})
    missing_old = dict(old_sha)
    del missing_old["1:75"]
    foreign_old = dict(old_sha, **{"1:76": expected_sha["1:76"]})
    for expected, old in ((missing_expected, old_sha), (foreign_expected, old_sha),
                          (invalid_expected, old_sha), (expected_sha, wrong_old75),
                          (expected_sha, missing_old), (expected_sha, foreign_old)):
        expect_failure(members, payloads, expected, old, "metadata", 0)
