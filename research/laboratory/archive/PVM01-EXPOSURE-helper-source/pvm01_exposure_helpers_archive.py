"""Copy and hash only this cycle's temporary helper code; keep all evidence."""
import json
from pathlib import Path
import shutil

from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
paths = sorted((b / "research/tmp").glob("pvm01_exposure_*.py"))
assert paths
estimated = sum(p.stat().st_size for p in paths)
free = shutil.disk_usage(b).free
assert free - estimated > 10 * 1024**3
root = b / "research/laboratory/archive/PVM01-EXPOSURE-helper-source"
root.mkdir(exist_ok=True)
files = {}
for source in paths:
    destination = root / source.name
    assert not destination.exists()
    assert source.resolve().is_relative_to((b / "research/tmp").resolve())
    destination.write_bytes(source.read_bytes())
    assert sha256_file(destination) == sha256_file(source)
    files[source.relative_to(b).as_posix()] = {"archive_path": destination.relative_to(b).as_posix(),
        "raw_sha256": sha256_file(source), "bytes": source.stat().st_size}
atomic_write_json(root / "receipt-V1.json", {"created_at": utc_now(), "estimated_copy_bytes": estimated,
    "free_before_bytes": free, "free_after_bytes": shutil.disk_usage(b).free, "files": files,
    "purpose": "Reproduce pre/postseed maintenance, checks, accounting and stored diagnostics; paid science/runtime/results unchanged",
    "no_scientific_evidence_deleted": True})
print("Archived", len(files), "temporary helpers, raw bytes", estimated)
