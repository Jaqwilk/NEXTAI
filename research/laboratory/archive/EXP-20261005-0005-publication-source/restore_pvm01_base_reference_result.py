"""Restore the exact independent-confirmation record with the frozen lossless restorer."""
from pathlib import Path
import json
import shutil
import sys
import restore_pvm01_transport_result as frozen

if __name__ == "__main__":
    frozen.ID = "EXP-20261005-0005"
    frozen.RELATIVE = f"research/results/{frozen.ID}.json"
    root = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
    frozen.main(root)
    result = json.loads((root/frozen.RELATIVE).read_text(encoding="utf-8"))
    jobs = []
    for outcome in result["candidates"]:
        execution = outcome.get("execution") or {}
        if "resource_peaks_path" not in execution:
            continue
        relative = Path(execution["resource_peaks_path"])
        expected = Path("research/tmp") / frozen.ID
        if relative.parent != expected or relative.suffixes[-2:] != [".resources", ".json"]:
            raise ValueError("Trusted resource journal path mismatch")
        source = (root/f"research/laboratory/archive/{frozen.ID}-runtime"/relative).resolve()
        target = (root/relative).resolve()
        if not source.is_relative_to(root) or not target.is_relative_to(root) or frozen.digest(source) != execution["resource_peaks_sha256"]:
            raise ValueError("Archived trusted resource journal binding changed")
        if target.exists():
            if frozen.digest(target) != execution["resource_peaks_sha256"]:
                raise ValueError("Existing resource journal differs; preserved without overwrite")
        else:
            jobs.append((source,target))
    footprint = sum(source.stat().st_size for source,target in jobs)
    if footprint > 64*1024**2 or shutil.disk_usage(root).free-footprint < 10*1024**3:
        raise OSError("Resource hydration exceeds bounded footprint or free-space reserve")
    for source,target in jobs:
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        if frozen.digest(target) != frozen.digest(source):
            raise ValueError("Hydrated resource journal hash mismatch")
    print("Exact saved resource journals available for frozen reanalysis:",len(jobs))
