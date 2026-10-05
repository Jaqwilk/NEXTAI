"""One frozen known-T1 conformance with independent direct point extraction."""
import json
from pathlib import Path
import subprocess

import nextai_autoresearch
import numpy as np
from nextai_autoresearch.asm01_task import transform
from nextai_autoresearch.asm01_task_v3 import parse_native_sample as parse_v3
from nextai_autoresearch.asm01_task_v4 import parse_native_sample
from nextai_autoresearch.utils import atomic_write_json, sha256_file, sha256_json, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
repair_path = root / "research/plans/ASM01-SERIALIZER-METADATA-REPAIR-V1.json"
assert sha256_file(repair_path) == "9b4d91cd42c681bf89c5dc42420a7d4f723a0de5f798674ce06825df92d04a86"
repair = json.loads(repair_path.read_text())
for relative, digest in repair["immutable_source_sha256"].items():
    assert sha256_file(root / relative) == digest
scope = repair["native_validation"]
sample = root / scope["relative_path"]
assert sample.resolve().is_relative_to(root.resolve())
assert sample.stat().st_size == scope["expected_bytes"] and sha256_file(sample) == scope["expected_sha256"]
receipt_path = root / "research/reviews/ASM01-EXPOSED-T1-SERIALIZER-CONFORMANCE-V1.json"
assert not receipt_path.exists()
receipt = {"created_at": utc_now(), "cycle": 323, "repair_sha256": sha256_file(repair_path),
           "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
           "sample_sha256": sha256_file(sample), "samples_opened": 1, "new_samples_opened": 0,
           "D_samples_opened": 0, "new_extraction": False, "fit": 0, "scoring": False}
try:
    payload = sample.read_bytes()
    try:
        parse_v3(payload)
    except ValueError as error:
        assert str(error) == "Pen-up supplied state/stroke"
        receipt["old_v3_failure_reproduced"] = str(error)
    else:
        raise AssertionError("Old V3 failure no longer reproduced")
    actual = parse_native_sample(payload)
    # This reference reads the original numeric rows directly, independently
    # of header/release normalization; names and marker extras never become points.
    expected = []
    previous = None
    raw_points = 0
    for line in payload.decode("ascii").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] in {"PEN_DOWN", "PEN_UP"}:
            previous = None
        elif len(fields) == 4 and all(token.isdigit() for token in fields):
            x, y, state, serial = map(int, fields)
            assert state == 1 and serial > 0
            raw_points += 1
            if (x, y) != previous:
                expected.append((x, y))
                previous = (x, y)
    expected = np.asarray(expected, dtype=np.float32)
    if not np.array_equal(actual, expected):
        raise ValueError("Native point reference mismatch")
    descriptors = {}
    for view in ("write", "nominal", "adverse"):
        value = transform(actual, view)
        if not np.array_equal(value, transform(expected, view)):
            raise ValueError("Native descriptor reference mismatch")
        assert value.shape == (64,) and value.dtype == np.float32 and np.isfinite(value).all()
        descriptors[view] = sha256_json({"dtype": str(value.dtype), "shape": list(value.shape),
                                        "bytes_hex": value.tobytes().hex()})
    receipt.update(complete=True, native_array_returned=True, point_shape=list(actual.shape),
                   raw_numeric_point_rows=raw_points, point_dtype=str(actual.dtype),
                   independent_point_reference_equal=True, all3_descriptors_equal=True,
                   descriptor_sha256=descriptors, coordinate_values_or_names_emitted=False)
except BaseException as error:
    receipt.update(complete=False, error=f"{type(error).__name__}: {error}",
                   partial_numeric_conversion_count="not instrumented; authorized T1 only")
    atomic_write_json(receipt_path, receipt)
    raise
atomic_write_json(receipt_path, receipt)
print(json.dumps(receipt), flush=True)
