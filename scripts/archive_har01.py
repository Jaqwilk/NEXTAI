"""Preserve the sole HAR screen's exact evaluated source, outcome and journals."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


def main():
    root = Path(__file__).resolve().parents[1]
    identity = "EXP-20261005-0007"
    receipt = root / f"research/laboratory/{identity}-archive-V1.json"
    assert not receipt.exists(), "Archive receipt is append-only"
    manifest_path = root / "research/eval_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["benchmark_version"] == "har01_native_memory_v1"
    for relative, expected in manifest["files"].items():
        assert sha256_file(root / relative) == expected, relative
    assert shutil.disk_usage(root).free - 1024**3 >= 10 * 1024**3

    source_path = root / f"research/results/{identity}.evaluated-source.zip"
    assert not source_path.exists()
    source_files = sorted(set(manifest["files"]) | {
        "research/eval_manifest.json", "research/laboratory/preflight_certificate.json",
        f"research/plans/{identity}.json"})
    with zipfile.ZipFile(source_path, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as bundle:
        for relative in source_files:
            bundle.write(root / relative, relative)
    with zipfile.ZipFile(source_path) as bundle:
        assert bundle.testzip() is None
        for relative in source_files:
            assert hashlib.sha256(bundle.read(relative)).hexdigest() == sha256_file(root / relative)

    runtime = root / f"research/tmp/{identity}"
    archive = root / f"research/laboratory/archive/{identity}-runtime/research/tmp/{identity}"
    assert not archive.exists()
    runtime_files = sorted(p for p in runtime.rglob("*") if p.is_file())
    assert runtime_files and all(p.suffix in (".json", ".jsonl") for p in runtime_files)
    runtime_hashes = {}
    for path in runtime_files:
        relative = path.relative_to(runtime)
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        expected = sha256_file(path)
        assert sha256_file(target) == expected
        runtime_hashes[relative.as_posix()] = {"sha256": expected, "bytes": path.stat().st_size}

    native_path = root / f"research/results/{identity}.json"
    native_hash = sha256_file(native_path)
    bundle_path = native_path.with_suffix(".json.gz")
    assert not bundle_path.exists()
    with bundle_path.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0,
                           compresslevel=6) as output, native_path.open("rb") as source:
            shutil.copyfileobj(source, output, length=1024**2)
    digest, size = hashlib.sha256(), 0
    with gzip.open(bundle_path, "rb") as restored:
        for block in iter(lambda: restored.read(1024**2), b""):
            size += len(block)
            digest.update(block)
    assert size == native_path.stat().st_size and digest.hexdigest() == native_hash
    publication = root / f"research/laboratory/{identity}-publication-V2.json"
    assert not publication.exists()
    atomic_write_json(publication, {
        "schema_version": 2, "created_at": utc_now(), "experiment_id": identity,
        "native_path": native_path.relative_to(root).as_posix(),
        "native_sha256": native_hash, "native_bytes": size,
        "bundle_path": bundle_path.relative_to(root).as_posix(),
        "bundle_sha256": sha256_file(bundle_path), "bundle_bytes": bundle_path.stat().st_size,
        "codec": "lossless gzip/mtime0", "native_result_unmodified": True,
        "all_trials_predictions_failures_and_costs_included": True,
        "restoration_command": f"uv run --no-sync python scripts/restore_har01_result.py {identity}",
        "restoration_script_sha256": sha256_file(root / "scripts/restore_har01_result.py"),
        "frozen_shared_restorer_sha256": sha256_file(root / "scripts/restore_pvm01_transport_result.py")})
    atomic_write_json(receipt, {
        "schema_version": 1, "created_at": utc_now(), "experiment_id": identity,
        "before_postrun_protected_source_changes": True,
        "evaluated_manifest_sha256": sha256_file(manifest_path),
        "evaluated_preflight_sha256": sha256_file(root / "research/laboratory/preflight_certificate.json"),
        "source_bundle_path": source_path.relative_to(root).as_posix(),
        "source_bundle_sha256": sha256_file(source_path), "source_files": len(source_files),
        "native_publication_path": publication.relative_to(root).as_posix(),
        "native_publication_sha256": sha256_file(publication),
        "runtime_archive_path": archive.relative_to(root).as_posix(),
        "runtime_files": runtime_hashes,
        "publisher_numeric_payload_included": False,
        "free_bytes_after": shutil.disk_usage(root).free,
        "archive_script_sha256": sha256_file(Path(__file__))})
    print(json.dumps({"native_sha256": native_hash, "source_files": len(source_files),
                      "runtime_files": len(runtime_hashes), "bundle_bytes": bundle_path.stat().st_size}), flush=True)


if __name__ == "__main__":
    main()
