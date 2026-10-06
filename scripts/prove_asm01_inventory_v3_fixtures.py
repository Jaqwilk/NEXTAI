"""Bind the one complete synthetic validation to exact source before native metadata."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from nextai_autoresearch import asm01_grammar_inventory as scanner
from nextai_autoresearch import asm01_inventory_v3 as binding
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
plan = json.loads((root / binding.STUDY).read_text())
assert sha256_file(root / binding.STUDY) == binding.STUDY_SHA
check_path = "research/reviews/NEXTAI-B-327-inventory-fixtures-V1.json"
check = json.loads((root / check_path).read_text())
assert check["result"]["returncode"] == 0 and not check["error"]
assert check["result"]["exit_job_active_process_count"] == 0
xml_path = "research/reviews/NEXTAI-B-327-inventory-fixtures-V1.xml"
suite = ET.parse(root / xml_path).getroot().find("testsuite")
assert suite.get("tests") == "70" and len(suite.findall("testcase")) == 70
assert all(suite.get(k) == "0" for k in ("failures", "errors", "skipped"))
names = [case.get("name") for case in suite.findall("testcase")]
for identifier in plan["prospective_fixture_matrix"]["adapter_cases"]:
    assert sum(name.endswith("[" + identifier + "]") for name in names) == 1, identifier
assert binding.inventory_bytes is scanner.inventory_bytes
paths = ["src/nextai_autoresearch/asm01_grammar_inventory.py",
    "src/nextai_autoresearch/asm01_inventory_members_v3.py",
    "src/nextai_autoresearch/asm01_inventory_v3.py", "tests/test_asm01_grammar_inventory.py",
    "tests/test_asm01_inventory_v3.py", "scripts/run_asm01_inventory_v3_check.py",
    "scripts/prove_asm01_inventory_v3_metadata.py", "scripts/run_asm01_inventory_v3_fixtures.py"]
hashes = {p: sha256_file(root / p) for p in paths}
assert hashes[paths[0]] == "cd5759386fa5f412ea125c849c5958b7d284dec91e811f93f173a6ccb544eb86"
assert hashes[paths[3]] == "6619d0a07e3b80e9dbd97352cec884dc508d1bf2fc144d7d8b0c14a40a8b5fd9"
checks = {}
for label, directory in (("original", root), ("clone", clone)):
    checks[label] = verify_manifest(directory)
    assert checks[label]["ok"]
    for relative, digest in hashes.items():
        assert sha256_file(directory / relative) == digest
    assert not any((directory / p).exists() for p in (plan["native_receipt_path"],
        plan["real_metadata_proof_path"], "STOP", "PAUSE", "research/run.lock"))
output = root / plan["conformance_path"]
assert not output.exists()
atomic_write_json(output, dict(created_at=utc_now(), cycle=327, study_sha256=binding.STUDY_SHA,
    xml_sha256=sha256_file(root / xml_path), check_receipt_sha256=sha256_file(root / check_path),
    passed_cases=70, all_fixture_tests_passed=True, new_native_content_not_yet_read=True,
    implementation_sha256=hashes, both_manifest_verification=checks,
    scanner_byte_identity=True, native_payloads_read=0, numeric_conversions=0,
    research_fit=0, new_EXPs=0, scoring=False))
print(json.dumps(dict(synthetic_cases=70, both_manifests_ok=True, scanner_unchanged=True, native_payloads_read=0)))
