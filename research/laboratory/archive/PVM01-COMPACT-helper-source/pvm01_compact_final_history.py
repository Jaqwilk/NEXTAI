"""Raw history and staged archive verification before original fast-forward."""
import hashlib
import json
from pathlib import Path
import subprocess

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.research_program import status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
original = b.parent / "NEXTAI"
snapshot = json.loads((b / "research/reviews/PVM01-COMPACT-startup-history-V1.json").read_text())
assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=original).strip()
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=original, text=True).strip() == snapshot["original_head"]
assert not [name for name, digest in snapshot["files"].items() if sha256_file(original / name) != digest]
allowed = {".gitattributes", "AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md",
           "docs/SCIENTIFIC_PROTOCOL.md", "config/research.toml", "config/baseline_semantics.json", "research/eval_manifest.json",
           "research/laboratory/preflight_certificate.json", "research/REPORT.md", "research/REPORT.provenance.json",
           "schemas/experiment_plan.schema.json", "src/nextai_autoresearch/integrity.py",
           "src/nextai_autoresearch/research_program.py", "src/nextai_autoresearch/runner.py",
           "tests/test_pvm01_delta_memory.py", "research/state.json", *snapshot["append_only_prefixes"]}
changed = set(subprocess.check_output(["git", "diff", "--name-only", snapshot["original_head"], "--"], text=True).splitlines())
deleted = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=D", snapshot["original_head"], "--"]).strip()
assert not deleted
assert not (changed & snapshot["files"].keys()) - allowed
eol = []
for name, digest in snapshot["files"].items():
    if name in allowed:
        continue
    assert (b / name).is_file(), name
    if sha256_file(b / name) != digest:
        assert (b / name).read_bytes().replace(b"\r\n", b"\n") == (original / name).read_bytes().replace(b"\r\n", b"\n"), name
        eol.append(name)
for name, prefix in snapshot["append_only_prefixes"].items():
    raw = (b / name).read_bytes()
    assert hashlib.sha256(raw[:prefix["bytes"]]).hexdigest() == prefix["sha256"], name
    if name.endswith(".jsonl"):
        for line in raw[prefix["bytes"]:].splitlines():
            assert isinstance(json.loads(line), dict)
    if name == "research/hypothesis_events.jsonl":
        assert len(raw) == prefix["bytes"]
for name in ("AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md", "docs/SCIENTIFIC_PROTOCOL.md"):
    assert (b / name).read_text(encoding="utf8").endswith((original / name).read_text(encoding="utf8")), name
assert (b / ".gitattributes").read_text().startswith((original / ".gitattributes").read_text())
archive_path = b / "research/reviews/PVM01-COMPACT-scientific-archive-V1.json"
archive = json.loads(archive_path.read_text())
expected = {name: record["sha256"] for name, record in archive["copies"].items()}
for path in (b / "research/laboratory/archive/PVM01-COMPACT-helper-source").rglob("*"):
    if path.is_file():
        expected[path.relative_to(b).as_posix()] = sha256_file(path)
for path in (b / "research/reviews").glob("PVM01-COMPACT-*.txt"):
    expected[path.relative_to(b).as_posix()] = sha256_file(path)
expected["research/results/EXP-20261004-0007.json"] = archive["result_sha256"]
expected["research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json"] = "fff220213f1b1cea96ef53754f96d40bbcb6f2997f8a7371ecbed6a58e731aad"
expected["research/reviews/PVM01-COMPACT-startup-history-V1.json"] = sha256_file(b / "research/reviews/PVM01-COMPACT-startup-history-V1.json")
names = sorted(expected)
requests = "".join(f":{name}\n" for name in names).encode()
run = subprocess.run(["git", "cat-file", "--batch"], input=requests, capture_output=True, check=True)
payload = run.stdout
cursor = 0
for name in names:
    end = payload.index(b"\n", cursor)
    header = payload[cursor:end].split()
    assert len(header) == 3 and header[1] == b"blob", (name, header)
    size = int(header[2])
    blob = payload[end+1:end+1+size]
    assert hashlib.sha256(blob).hexdigest() == expected[name] == sha256_file(b / name), name
    assert payload[end+1+size:end+2+size] == b"\n"
    cursor = end+2+size
assert cursor == len(payload)
# Apply whitespace checking only to live source/text; raw archives/native diagnostics use SHA256 instead.
files = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).splitlines()
live = [name for name in files if not name.startswith("research/laboratory/archive/")
        and not name.endswith((".stdout.txt", ".stderr.txt", ".xml"))
        and name not in ("research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json", "research/reviews/PVM01-COMPACT-startup-history-V1.json")]
for first in range(0, len(live), 100):
    subprocess.run(["git", "diff", "--cached", "--check", "--", *live[first:first+100]], check=True)
assert verify_manifest(b)["ok"]
value = status(b)
assert not value["paid_run_pending"] and not value["program_closed"] and value["study_terminal"]
atomic_write_json(b / "research/reviews/PVM01-COMPACT-final-history-source-index-V1.json", {
    "created_at": utc_now(), "original_head": snapshot["original_head"], "original_raw_files_unchanged": len(snapshot["files"]),
    "old_scientific_bytes_and_append_only_prefixes_preserved": True, "no_deleted_files": True,
    "preexisting_line_ending_differences": eol, "historical_authority_sections_preserved": True,
    "indexed_raw_archive_native_result_preregistration_files": len(names), "all_indexed_raw_sha256_valid": True,
    "live_staged_whitespace_valid": True, "archive_receipt_sha256": sha256_file(archive_path),
    "failed_helpers_and_diagnostics_preserved": True, "candidate_bundle_unchanged": True})
print("Original", len(snapshot["files"]), "raw scientific history; indexed", len(names), "raw archive/native/result files; live whitespace: PASS")
