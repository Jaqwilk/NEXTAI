"""Restore the exact independent-confirmation record with the frozen lossless restorer."""
from pathlib import Path
import json
import shutil
import sys
import restore_pvm01_transport_result as frozen

if __name__ == "__main__":
    frozen.ID = "EXP-20261005-0006"
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
    import zipfile
    import re
    publication = json.loads((root/f"research/laboratory/{frozen.ID}-fitted-state-publication-V1.json").read_text(encoding="utf-8"))
    bundle_path = root/f"research/results/{frozen.ID}.fitted-state.zip"
    if (publication["experiment_id"] != frozen.ID or publication["bundle_path"] != bundle_path.relative_to(root).as_posix()
            or frozen.digest(bundle_path) != publication["bundle_sha256"] or publication["bundle_bytes"] > 10485760):
        raise ValueError("Fitted-source bundle provenance mismatch")
    jobs = []
    with zipfile.ZipFile(bundle_path) as bundle:
        if set(bundle.namelist()) != set(publication["files"]) or len(bundle.infolist()) != 50:
            raise ValueError("Fitted-source bundle has unexpected or duplicate files")
        if sum(info.file_size for info in bundle.infolist()) > 54067200:
            raise ValueError("Fitted-source expanded payload exceeds bound")
        for name, record in publication["files"].items():
            if not re.fullmatch(r"pvm01_tc_(?:transport_pca|transport_pca_untrained|transport_pca_shuffled|ridge_pca_scan|dense_cached_cpu)_s[0-4]/(?:metadata\.json|parameters\.npz)",name):
                raise ValueError("Unexpected fitted-source path")
            target=(root/f"research/tmp/{frozen.ID}/fitted-source"/name).resolve()
            if not target.is_relative_to(root):raise ValueError("Fitted-source path escapes checkout")
            if bundle.getinfo(name).file_size != record["bytes"]:raise ValueError("Fitted-source file size mismatch")
            data=bundle.read(name)
            if frozen.hashlib.sha256(data).hexdigest() != record["sha256"]:raise ValueError("Fitted-source file hash mismatch")
            if target.exists():
                if frozen.digest(target) != record["sha256"]:raise ValueError("Existing fitted source differs; preserved without overwrite")
            else:jobs.append((target,data))
    archive_root=root/f"research/laboratory/archive/{frozen.ID}-runtime/research/tmp/{frozen.ID}"
    for name in sorted({Path(name).parts[0] for name in publication["files"]}):
        source=archive_root/(name+".fits.jsonl");target=root/f"research/tmp/{frozen.ID}"/(name+".fits.jsonl")
        if source.stat().st_size>262144:raise ValueError("Fitted-source journal exceeds bound")
        if target.exists():
            if frozen.digest(target)!=frozen.digest(source):raise ValueError("Existing fitted journal differs; preserved without overwrite")
        else:jobs.append((target,source.read_bytes()))
    footprint=sum(len(data) for target,data in jobs)
    if footprint>64*1024**2 or shutil.disk_usage(root).free-footprint<10*1024**3:
        raise OSError("Fitted-source hydration exceeds bounded disk reserve")
    for target,data in jobs:
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb") as handle:handle.write(data)
    print("Exact fitted-source states/journals available without fit:",len(jobs))
    print("Exact saved resource journals available for frozen reanalysis:",len(jobs))
