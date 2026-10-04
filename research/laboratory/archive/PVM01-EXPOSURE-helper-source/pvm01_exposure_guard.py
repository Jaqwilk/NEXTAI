"""Raw history, preregistration and independent clone conformance; no new arrays."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from nextai_autoresearch.baseline_semantics import verify_preflight_certificate, verify_required_baselines
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

b = Path.cwd()
original = b.parent/"NEXTAI"
snapshot = json.loads((b/"research/reviews/PVM01-EXPOSURE-startup-history-V1.json").read_text())
changed = [name for name,digest in snapshot["files"].items() if sha256_file(original/name) != digest]
assert not changed,changed
assert not subprocess.check_output(["git","status","--porcelain"],cwd=original).strip()
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=original).decode().strip() == snapshot["original_head"]
for name,record in snapshot["append_only_prefixes"].items():
    payload = (b/name).read_bytes()
    assert len(payload) >= record["bytes"]
    assert hashlib.sha256(payload[:record["bytes"]]).hexdigest() == record["sha256"],name
    if name.endswith(".jsonl"):
        assert payload.endswith(b"\n")
        for line in payload[record["bytes"]:].splitlines():
            if line.strip():
                assert isinstance(json.loads(line),dict)
assert (b/"research/hypothesis_events.jsonl").read_bytes() == (original/"research/hypothesis_events.jsonl").read_bytes()
closed = [name for name in snapshot["files"] if name.startswith(("research/plans/","research/results/","research/analyses/","research/laboratory/archive/","src/nextai_autoresearch/candidates/"))]
closed += ["src/nextai_autoresearch/pvm01_task.py"]
closed += [f"src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v{i}.py" for i in range(1,5)]
for name in closed:
    assert sha256_file(b/name) == snapshot["files"][name],name
for name in ("AGENTS.md","program.md","research/LAB_PLAN.md","docs/SCIENTIFIC_PROTOCOL.md","docs/CURRENT_STATUS.md"):
    assert (b/name).read_bytes().endswith((original/name).read_bytes()),name
study_path = "research/plans/PVM01-CAPACITY-EXPOSURE-V1.json"
study = json.loads((b/study_path).read_text())
prereg = "8fb10251a0c03356856469e1c37742c3956f15dc"
blob = subprocess.check_output(["git","show",f"{prereg}:{study_path}"],cwd=b)
assert hashlib.sha256(blob).hexdigest() == sha256_file(b/study_path)
suites = list(ET.parse(b/"research/reviews/PVM01-EXPOSURE-preseed-full-V2.xml").getroot().iter("testsuite"))
tests = sum(int(v.attrib["tests"]) for v in suites)
assert tests >= 1114
assert all(sum(int(v.attrib.get(k,0)) for k in ("failures","errors","skipped")) == 0 for v in suites)
integrity = verify_manifest(b)
assert integrity["ok"],integrity
verify_preflight_certificate(b)
gate = verify_required_baselines({"candidates":study["candidates"],
    "research_program_protocol":{"classical_baselines":study["candidates"]}},b,run_tests=False)
atomic_write_json(b/"research/reviews/PVM01-EXPOSURE-history-source-conformance-V1.json",{
    "created_at":utc_now(),"original_head":snapshot["original_head"],"original_files_unchanged":len(snapshot["files"]),
    "append_only_prefixes_valid":True,"hypothesis_events_unchanged":True,"closed_scientific_files_unchanged":len(closed),
    "preregistration_git_commit":prereg,"preregistration_raw_sha256":sha256_file(b/study_path),
    "protected_files":integrity["checked_files"],"integrity_ok":True,"all80_semantic_records_valid":len(gate["required"]) == 80,
    "full_regression_tests":tests,"failures_errors_skips":0,"no_new_research_units_or_fit":True})
print(json.dumps({"history_and_source":True,"original_files":len(snapshot["files"]),"closed_files":len(closed),"tests":tests,"roles":len(gate["required"])}))
