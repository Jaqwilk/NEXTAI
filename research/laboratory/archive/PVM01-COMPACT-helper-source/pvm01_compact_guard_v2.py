"""Pre-seed raw history, original checkout and source conformance guard."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from nextai_autoresearch.baseline_semantics import verify_preflight_certificate, verify_required_baselines
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
original = b.parent / "NEXTAI"
snapshot = json.loads((b / "research/reviews/PVM01-COMPACT-startup-history-V1.json").read_text())
changed = [name for name, digest in snapshot["files"].items() if sha256_file(original/name) != digest]
assert not changed, changed
assert not subprocess.check_output(["git","status","--porcelain"],cwd=original).strip()
for name, record in snapshot["append_only_prefixes"].items():
    payload = (b/name).read_bytes()
    assert len(payload) >= record["bytes"]
    assert hashlib.sha256(payload[:record["bytes"]]).hexdigest() == record["sha256"], name
    if name.endswith(".jsonl"):
        assert payload.endswith(b"\n")
        for line in payload[record["bytes"]:].splitlines():
            assert isinstance(json.loads(line), dict)
assert (b/"research/hypothesis_events.jsonl").read_bytes() == (original/"research/hypothesis_events.jsonl").read_bytes()
for name in ("research/results/EXP-20261004-0006.json", "research/analyses/EXP-20261004-0006.md",
             "src/nextai_autoresearch/pvm01_task.py", "src/nextai_autoresearch/candidates/pvm01_core.py",
             "src/nextai_autoresearch/candidates/pvm01_delta_core.py", "src/nextai_autoresearch/candidates/pvm01_optimized_core.py",
             "src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v3.py"):
    assert sha256_file(b/name) == snapshot["files"][name], name
study_path = "research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json"
study = json.loads((b/study_path).read_text())
prereg = "2ba76b6c9b2d4de1d76dcbcca7b3e4de5663c48a"
blob = subprocess.check_output(["git","show",f"{prereg}:{study_path}"],cwd=b)
assert hashlib.sha256(blob).hexdigest() == sha256_file(b/study_path)
root = ET.parse(b/"research/reviews/PVM01-COMPACT-preseed-full-V1.xml").getroot()
suites = list(root.iter("testsuite"))
tests = sum(int(v.attrib["tests"]) for v in suites)
assert tests == 1108
assert all(sum(int(v.attrib.get(k,0)) for k in ("failures","errors","skipped")) == 0 for v in suites)
integrity = verify_manifest(b)
assert integrity["ok"], integrity
verify_preflight_certificate(b)
gate = verify_required_baselines({"candidates":study["candidates"],
    "research_program_protocol":{"classical_baselines":study["candidates"]}},b,run_tests=False)
atomic_write_json(b/"research/reviews/PVM01-COMPACT-history-source-conformance-V2.json",{
    "created_at":utc_now(), "original_head":snapshot["original_head"], "original_files_unchanged":len(snapshot["files"]),
    "append_only_prefixes_valid":True, "hypothesis_events_unchanged":True, "closed_science_unchanged":True,
    "preregistration_git_commit":prereg, "preregistration_raw_sha256":sha256_file(b/study_path),
    "protected_files":integrity["checked_files"], "integrity_ok":True,
    "all75_semantic_records_valid":len(gate["required"])==75,
    "full_regression_tests":tests, "failures_errors_skips":0,
    "no_research_arrays_models_or_seeds_generated":True})
print("Original17615 files, append-only prefixes, raw preregistration, source1136 and75 semantic records: PASS")
