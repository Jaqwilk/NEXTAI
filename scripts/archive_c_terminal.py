"""Lossless administrative preservation after C native geometry failure."""
from pathlib import Path
import json
import shutil

from nextai_autoresearch.utils import load_json, sha256_file, utc_now


def main():
    root = Path(__file__).resolve().parents[1]
    source_binding = load_json(root / "research/reviews/ASM01-C-source-binding-V1.json")
    native = load_json(root / "research/data_manifests/ASM01-C-ACQUISITION-V1.json")
    if root.name != "NEXTAI-VALIDATION-20261002" or native.get("complete") is not False:
        raise ValueError("Only failed canonical clone evidence may be preserved here")
    relative = "research/laboratory/archive/NEXTAI-C-CYCLE344-EVALUATED-V1"
    archive = root / relative
    archive.mkdir(parents=True, exist_ok=False)
    members = dict(source_binding["files"])
    for name in ("config/research.toml", "research/eval_manifest.json", "research/c_events.jsonl",
                 "research/laboratory/preflight_certificate.json", "AGENTS.md",
                 "research/data_manifests/ASM01-C-ACQUISITION-V1.json",
                 "research/reviews/ASM01-C-source-binding-V1.json", "scripts/archive_c_terminal.py"):
        members[name] = sha256_file(root / name)
    for path in sorted((root / "research/reviews").rglob("NEXTAI-C-*")):
        if path.is_file():
            members[path.relative_to(root).as_posix()] = sha256_file(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    members[child.relative_to(root).as_posix()] = sha256_file(child)
    for name, expected in members.items():
        source, target = root / name, archive / name
        if sha256_file(source) != expected:
            raise ValueError("Evaluated evidence source changed:" + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha256_file(target) != expected:
            raise ValueError("Archive copy hash changed:" + name)
    receipt = {"created_at": utc_now(), "archive_path": relative, "members": members,
               "all_member_hashes_verified": True, "member_count": len(members),
               "native_content_not_reopened": True, "publisher_and_NPZ_not_published": True,
               "science_stopped_after_intake_failure": True}
    path = root / "research/laboratory/NEXTAI-C-CYCLE344-ARCHIVE-V1.receipt.json"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"member_count": len(members), "all_member_hashes_verified": True}), flush=True)


if __name__ == "__main__":
    main()
