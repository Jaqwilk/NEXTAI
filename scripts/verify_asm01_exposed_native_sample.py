"""One preregistered already-exposed T1 grammar check; no fit or new samples."""
import json
from pathlib import Path
import subprocess

import nextai_autoresearch
import numpy as np

from nextai_autoresearch.asm01_task import parse_native_sample as parse_v1, transform
from nextai_autoresearch.asm01_task_v3 import parse_native_sample
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
plan_path = root / "research/plans/ASM01-NATIVE-GRAMMAR-CONFORMANCE-V1.json"
assert sha256_file(plan_path) == "2e33af01acf0fee203275a84f434279de6c5f098a6ee2178bc87fd994b7ea217"
plan = json.loads(plan_path.read_text())
rule = plan["native_validation"]
path = (root / rule["relative_path"]).resolve()
assert path.is_relative_to((root / "research/data/asm01_native_v1").resolve()) and not path.is_symlink()
receipt_path = root / "research/reviews/ASM01-EXPOSED-T1-GRAMMAR-CONFORMANCE-V1.json"
assert not receipt_path.exists()
receipt = {"created_at": utc_now(), "study_sha256": sha256_file(plan_path),
           "single_already_exposed_training_sample": rule["relative_path"],
           "samples_opened": 1, "new_samples_opened": 0, "D_samples_opened": 0,
           "new_extraction": False, "fit": 0, "scoring": False, "native_array_returned": False,
           "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()}
try:
    assert path.stat().st_size == rule["expected_bytes"] and sha256_file(path) == rule["expected_sha256"]
    payload = path.read_bytes()
    try:
        parse_v1(payload)
    except ValueError as error:
        receipt["preserved_original_parser_error"] = str(error)
        assert str(error) == "Native point grammar"
    else:
        raise AssertionError("Original parser failure changed")
    points = parse_native_sample(payload)
    assert points.dtype == np.float32 and points.ndim == 2 and points.shape[1] == 2
    receipt.update(native_array_returned=True, point_count=len(points), native_points_sha256=__import__("hashlib").sha256(points.tobytes()).hexdigest())
    descriptors = {}
    for view in ("write", "nominal", "adverse"):
        value = transform(points, view)
        assert value.shape == (64,) and value.dtype == np.float32 and np.isfinite(value).all()
        assert np.isclose(np.linalg.norm(value), 1., atol=1e-5)
        descriptors[view] = __import__("hashlib").sha256(value.tobytes()).hexdigest()
    receipt.update(complete=True, descriptor_sha256=descriptors,
                   payload_bytes=len(payload), payload_sha256=sha256_file(path),
                   original_parser_sha256=sha256_file(root / "src/nextai_autoresearch/asm01_task.py"),
                   adapter_sha256=sha256_file(root / "src/nextai_autoresearch/asm01_task_v3.py"))
except Exception as error:
    receipt.update(complete=False, error=f"{type(error).__name__}: {error}",
                   partial_numeric_conversion_count="not instrumented; authorized T1 only")
    atomic_write_json(receipt_path, receipt)
    print(json.dumps(receipt), flush=True)
    raise SystemExit(1)
atomic_write_json(receipt_path, receipt)
print(json.dumps(receipt), flush=True)
