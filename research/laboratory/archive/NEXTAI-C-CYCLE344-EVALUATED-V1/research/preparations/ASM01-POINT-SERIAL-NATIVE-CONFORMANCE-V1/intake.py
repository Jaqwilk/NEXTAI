"""Standalone fixed-screen preparation; redacted accounting, no active loader."""

import hashlib
import importlib.util
from pathlib import Path
import re

import numpy as np

from nextai_autoresearch.asm01_task import SCREEN_WRITERS, arrays_hash, transform
from nextai_autoresearch.asm01_task_v4 import parse_native_sample


ROOT = Path(__file__).resolve().parents[3]
NORMALIZER_PATH = ROOT / "research/preparations/ASM01-POINT-SERIAL-PREPARATION-V1/normalizer.py"
NORMALIZER_SHA = "fbc87c0ba993b73eaa751bc9ecc21cf0fb1ec544887b679cb9c42e8e5f844a8c"
if hashlib.sha256(NORMALIZER_PATH.read_bytes()).hexdigest() != NORMALIZER_SHA:
    raise ValueError("normalizer_binding")
_spec = importlib.util.spec_from_file_location("asm01_frozen_serial_normalizer", NORMALIZER_PATH)
_normalizer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_normalizer)
normalize_release_bytes = _normalizer.normalize_release_bytes

_IDENTITIES = tuple((writer, sample) for writer in SCREEN_WRITERS for sample in range(1, 184))
_KEYS = {f"{writer}:{sample}" for writer, sample in _IDENTITIES}
_OLD_KEYS = {f"1:{sample}" for sample in range(1, 76)}
_SHA = re.compile(r"[0-9a-f]{64}")


def collect(members, expected_sha, old_sha, receipt, reader=None):
    """Collect all1830 once, retaining the old74 compatibility gate first.

    The caller must obtain members from the frozen screen_members metadata gate.
    An injected reader is supported for synthetic conformance only. No content
    files, arrays or coordinates are written by this engine.
    """
    if receipt.get("collection_started"):
        raise ValueError("collection_consumed")
    receipt.update(collection_started=True, complete=False, attempted_files=0,
                   converted_files=0, validated_files=0, old_compared=0,
                   D_samples_opened=0, current_UID=None, error_category=None,
                   native_files_attempted=0, native_files_converted=0,
                   old74_compared=0, current_sample=None,
                   attempted_sample_text_sha256={}, sample_array_sha256={},
                   old_array_sha256={}, old_descriptor_sha256={})
    phase = "metadata"
    try:
        members = list(members)
        if len(members) != 1830:
            raise ValueError("metadata")
        identities, paths = [], []
        for member in members:
            if not isinstance(member, (tuple, list)) or len(member) != 3:
                raise ValueError("metadata")
            writer, sample, path = member
            if type(writer) is not int or type(sample) is not int or not isinstance(path, Path):
                raise ValueError("metadata")
            identities.append((writer, sample))
            paths.append(path)
        if tuple(identities) != _IDENTITIES or len(set(paths)) != 1830:
            raise ValueError("metadata")
        if not isinstance(expected_sha, dict) or not isinstance(old_sha, dict):
            raise ValueError("metadata")
        if set(expected_sha) != _KEYS or set(old_sha) != _OLD_KEYS:
            raise ValueError("metadata")
        if any(not isinstance(value, str) or _SHA.fullmatch(value) is None
               for value in (*expected_sha.values(), *old_sha.values())):
            raise ValueError("metadata")
        if any(old_sha[key] != expected_sha[key] for key in _OLD_KEYS):
            raise ValueError("metadata")
        if reader is not None and not callable(reader):
            raise ValueError("metadata")

        by_writer = {writer: [] for writer in SCREEN_WRITERS}
        seen = set()
        for writer, sample, path in members:
            key = f"{writer}:{sample}"
            is_old = writer == 1 and sample <= 74
            if not is_old and receipt["old_compared"] != 74:
                phase = "old_array_difference"
                raise ValueError(phase)
            receipt["current_UID"] = key
            receipt["current_sample"] = key
            receipt["attempted_files"] += 1
            receipt["native_files_attempted"] += 1
            receipt["D_samples_opened"] += int(writer >= 16)
            phase = "read"
            payload = path.read_bytes() if reader is None else reader(path)
            if not isinstance(payload, bytes):
                raise ValueError(phase)
            digest = hashlib.sha256(payload).hexdigest()
            receipt["attempted_sample_text_sha256"][key] = digest
            phase = "raw_sha"
            if digest != expected_sha[key] or (is_old and digest != old_sha[key]):
                raise ValueError(phase)

            phase = "normalize"
            normalized = normalize_release_bytes(payload)
            phase = "native_geometry"
            value = parse_native_sample(normalized)
            if (not isinstance(value, np.ndarray) or value.dtype != np.float32
                    or value.ndim != 2 or value.shape[1] != 2):
                raise ValueError(phase)
            receipt["converted_files"] += 1
            receipt["native_files_converted"] += 1
            value_digest = arrays_hash(value)
            receipt["sample_array_sha256"][key] = value_digest
            if is_old:
                phase = "old_reference"
                previous = parse_native_sample(payload)
                phase = "old_array_difference"
                if (previous.dtype != value.dtype or previous.shape != value.shape
                        or previous.tobytes() != value.tobytes()):
                    raise ValueError(phase)
                receipt["old_array_sha256"][key] = arrays_hash(previous)
                descriptor_hashes = {}
                phase = "old_view_difference"
                for view in ("write", "nominal", "adverse"):
                    before, after = transform(previous, view), transform(value, view)
                    if (before.dtype != after.dtype or before.shape != after.shape
                            or before.tobytes() != after.tobytes()):
                        raise ValueError(phase)
                    descriptor_hashes[view] = arrays_hash(before)
                receipt["old_descriptor_sha256"][key] = descriptor_hashes
                receipt["old_compared"] += 1
                receipt["old74_compared"] += 1
            phase = "duplicate"
            if value_digest in seen:
                raise ValueError(phase)
            seen.add(value_digest)
            by_writer[writer].append(value)
            receipt["validated_files"] += 1

        phase = "serialization"
        if (receipt["attempted_files"], receipt["converted_files"],
                receipt["validated_files"], receipt["old_compared"],
                receipt["D_samples_opened"]) != (1830, 1830, 1830, 74, 915):
            raise ValueError(phase)
        arrays, writer_hashes = {}, {}
        for writer in SCREEN_WRITERS:
            values = by_writer[writer]
            offsets = np.r_[0, np.cumsum([len(value) for value in values], dtype=np.int64)]
            points = np.concatenate(values)
            rows = np.column_stack((np.arange(1, 184), np.full(183, writer))).astype(np.int64)
            arrays.update({f"points_{writer}": points, f"offsets_{writer}": offsets,
                           f"rows_{writer}": rows})
            writer_hashes[str(writer)] = arrays_hash(points, offsets, rows)
        receipt.update(complete=True, converted_writers=list(SCREEN_WRITERS),
                       converted_writer_hashes=writer_hashes)
        return arrays, writer_hashes
    except BaseException as error:
        receipt.update(complete=False, error_category=phase, error_type=type(error).__name__)
        raise ValueError(phase) from None
