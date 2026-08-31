"""Dependency-free structural/numeric audit for the acquired MATLAB v5 files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zlib
from collections import Counter
from pathlib import Path

import numpy as np


MI_MATRIX = 14
MI_COMPRESSED = 15
MX_STRUCT = 2
MX_OBJECT = 3
NUMERIC_DTYPES = {
    1: np.dtype("i1"), 2: np.dtype("u1"), 3: np.dtype("<i2"),
    4: np.dtype("<u2"), 5: np.dtype("<i4"), 6: np.dtype("<u4"),
    7: np.dtype("<f4"), 9: np.dtype("<f8"), 12: np.dtype("<i8"),
    13: np.dtype("<u8"),
}
NAME_RE = re.compile(
    r"^F(?P<fault>[0-3])_SV(?P<severity>[0-3])_SP(?P<speed>[12])_t(?P<trajectory>[1-5])"
    r"(?:_D(?P<drone>[1-3]))?(?:_R(?P<repetition>[1-3]))?\.mat$"
)


def elements(data: bytes | memoryview, *, compressed_unpadded: bool = False):
    view = memoryview(data)
    pos = 0
    while pos + 8 <= len(view):
        first = struct.unpack_from("<I", view, pos)[0]
        if first >> 16:
            kind, size = first & 0xFFFF, first >> 16
            yield kind, view[pos + 4 : pos + 4 + size]
            pos += 8
        else:
            kind, size = first, struct.unpack_from("<I", view, pos + 4)[0]
            start = pos + 8
            yield kind, view[start : start + size]
            pos = start + (size if compressed_unpadded and kind == MI_COMPRESSED else ((size + 7) // 8) * 8)


def scalar_int(payload: memoryview) -> int:
    return int.from_bytes(payload[: min(4, len(payload))], "little", signed=False)


def matrix_leaves(payload: memoryview, prefix: str = "") -> list[dict]:
    parts = list(elements(payload))
    if len(parts) < 3:
        return []
    flags = scalar_int(parts[0][1])
    mx_class = flags & 0xFF
    dims = tuple(np.frombuffer(parts[1][1], dtype="<i4").astype(int).tolist())
    name = bytes(parts[2][1]).decode("utf-8", "replace").rstrip("\0")
    path = ".".join(part for part in (prefix, name) if part)
    cursor = 3
    fields: list[str] = []
    if mx_class in (MX_STRUCT, MX_OBJECT):
        if mx_class == MX_OBJECT:
            cursor += 1
        width = scalar_int(parts[cursor][1])
        raw_names = bytes(parts[cursor + 1][1])
        fields = [
            raw_names[i : i + width].split(b"\0", 1)[0].decode("utf-8", "replace")
            for i in range(0, len(raw_names), width)
        ]
        cursor += 2
    nested = [part for part in parts[cursor:] if part[0] == MI_MATRIX]
    if nested:
        leaves: list[dict] = []
        for index, (_, child) in enumerate(nested):
            field = fields[index % len(fields)] if fields else str(index)
            leaves.extend(matrix_leaves(child, ".".join(part for part in (path, field) if part)))
        return leaves
    numeric = next(((kind, raw) for kind, raw in parts[cursor:] if kind in NUMERIC_DTYPES), None)
    if numeric is None:
        return [{"path": path, "class": mx_class, "dims": dims, "numeric": False}]
    kind, raw = numeric
    values = np.frombuffer(raw, dtype=NUMERIC_DTYPES[kind])
    nan = int(np.isnan(values).sum()) if values.dtype.kind == "f" else 0
    posinf = int(np.isposinf(values).sum()) if values.dtype.kind == "f" else 0
    neginf = int(np.isneginf(values).sum()) if values.dtype.kind == "f" else 0
    nonfinite_rows: dict[str, int] = {}
    first_nonfinite_sample = None
    last_nonfinite_sample = None
    if nan + posinf + neginf and len(dims) == 2 and dims[0] * dims[1] == values.size:
        mask = (~np.isfinite(values)).reshape(dims, order="F")
        nonfinite_rows = {str(index + 1): int(count) for index, count in enumerate(mask.sum(axis=1)) if count}
        sample_indices = np.flatnonzero(mask.any(axis=0))
        first_nonfinite_sample = int(sample_indices[0] + 1)
        last_nonfinite_sample = int(sample_indices[-1] + 1)
    blocks = []
    if path == "QDrone_data" and len(dims) == 2 and dims[0] * dims[1] == values.size:
        row_bytes = dims[0] * values.dtype.itemsize
        for start in range(0, max(0, dims[1] - 1024 + 1), 512):
            blocks.append((start, hashlib.sha256(raw[start * row_bytes : (start + 1024) * row_bytes]).hexdigest()))
    return {
        "path": path,
        "class": mx_class,
        "dims": dims,
        "numeric": True,
        "mi_type": kind,
        "values": int(values.size),
        "numeric_sha256": hashlib.sha256(raw).hexdigest(),
        "nan": nan,
        "posinf": posinf,
        "neginf": neginf,
        "nonfinite": nan + posinf + neginf,
        "nonfinite_rows_1based": nonfinite_rows,
        "first_nonfinite_sample_1based": first_nonfinite_sample,
        "last_nonfinite_sample_1based": last_nonfinite_sample,
        "_qdrone_blocks_1024_stride_512": blocks,
    },


def inspect_mat(path: Path) -> dict:
    raw = path.read_bytes()
    if not raw.startswith(b"MATLAB 5.0 MAT-file") or raw[126:128] != b"IM":
        raise ValueError(f"unsupported MAT header: {path.name}")
    leaves: list[dict] = []
    incomplete_zlib_streams = 0
    for kind, payload in elements(memoryview(raw)[128:], compressed_unpadded=True):
        if kind == MI_COMPRESSED:
            try:
                inflated = zlib.decompress(payload)
            except zlib.error as error:
                decoder = zlib.decompressobj()
                inflated = decoder.decompress(payload)
                if len(inflated) < 8 or struct.unpack_from("<II", inflated, 0) != (MI_MATRIX, len(inflated) - 8):
                    raise ValueError(f"bad compressed element in {path.name}: {len(payload)} bytes") from error
                incomplete_zlib_streams += 1
            for inner_kind, inner in elements(inflated):
                if inner_kind == MI_MATRIX:
                    leaves.extend(matrix_leaves(inner))
        elif kind == MI_MATRIX:
            leaves.extend(matrix_leaves(payload))
    return {
        "name": path.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "incomplete_zlib_streams": incomplete_zlib_streams,
        "leaves": leaves,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--files-jsonl", type=Path)
    args = parser.parse_args()
    paths = sorted(args.root.rglob("*.mat"), key=lambda item: item.name)
    records = [inspect_mat(path) for path in paths]
    parsed_names = [NAME_RE.fullmatch(record["name"]) for record in records]
    schemas = Counter(
        tuple((leaf["path"], leaf["class"], leaf["numeric"], leaf.get("mi_type"), len(leaf["dims"])) for leaf in record["leaves"])
        for record in records
    )
    dims = Counter(tuple((leaf["path"], leaf["dims"]) for leaf in record["leaves"]) for record in records)
    digest_counts = Counter(record["sha256"] for record in records)
    block_locations: dict[str, list[tuple[str, int]]] = {}
    for record in records:
        for leaf in record["leaves"]:
            for start, digest in leaf.pop("_qdrone_blocks_1024_stride_512", []):
                block_locations.setdefault(digest, []).append((record["name"], start))
    repeated_blocks = {digest: locations for digest, locations in block_locations.items() if len(locations) > 1}
    cross_file_blocks = {
        digest: locations for digest, locations in repeated_blocks.items()
        if len({name for name, _ in locations}) > 1
    }
    summary = {
        "mat_files": len(records),
        "filename_pattern_failures": sum(match is None for match in parsed_names),
        "unique_sha256": len(digest_counts),
        "duplicate_sha256_groups": sum(count > 1 for count in digest_counts.values()),
        "schema_signatures": len(schemas),
        "exact_dimension_signatures": len(dims),
        "total_bytes": sum(record["bytes"] for record in records),
        "total_numeric_values": sum(leaf.get("values", 0) for record in records for leaf in record["leaves"]),
        "total_nonfinite": sum(leaf.get("nonfinite", 0) for record in records for leaf in record["leaves"]),
        "total_nan": sum(leaf.get("nan", 0) for record in records for leaf in record["leaves"]),
        "total_posinf": sum(leaf.get("posinf", 0) for record in records for leaf in record["leaves"]),
        "total_neginf": sum(leaf.get("neginf", 0) for record in records for leaf in record["leaves"]),
        "files_with_incomplete_zlib_streams": sum(record["incomplete_zlib_streams"] > 0 for record in records),
        "incomplete_zlib_streams": sum(record["incomplete_zlib_streams"] for record in records),
        "leaf_counts": dict(sorted(Counter(len(record["leaves"]) for record in records).items())),
        "qdrone_windows_1024_stride_512": sum(len(locations) for locations in block_locations.values()),
        "repeated_qdrone_window_groups": len(repeated_blocks),
        "cross_file_repeated_qdrone_window_groups": len(cross_file_blocks),
        "cross_file_repeated_qdrone_window_examples": list(cross_file_blocks.values())[:10],
        "factor_counts": {
            key: dict(sorted(Counter(match.group(key) or "none" for match in parsed_names if match).items()))
            for key in ("fault", "severity", "speed", "trajectory", "drone", "repetition")
        },
        "smallest_file_bytes": min((record["bytes"] for record in records), default=0),
        "largest_file_bytes": max((record["bytes"] for record in records), default=0),
        "smallest_numeric_values": min((sum(leaf.get("values", 0) for leaf in record["leaves"]) for record in records), default=0),
        "largest_numeric_values": max((sum(leaf.get("values", 0) for leaf in record["leaves"]) for record in records), default=0),
        "first_schema": records[0]["leaves"] if records else [],
    }
    if args.files_jsonl:
        with args.files_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
