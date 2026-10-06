"""Complete real filename/bounds proof; no native payload, coordinate or parser."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import nextai_autoresearch
from nextai_autoresearch.asm01_inventory_v3 import STUDY, STUDY_SHA
from nextai_autoresearch.asm01_inventory_members_v3 import screen_members
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
assert sha256_file(root / STUDY) == STUDY_SHA
plan = json.loads((root / STUDY).read_text())
proof_path = root / plan["conformance_path"]
proof = json.loads(proof_path.read_text())
assert proof["all_fixture_tests_passed"] and proof["new_native_content_not_yet_read"]
assert proof["study_sha256"] == STUDY_SHA
for relative, digest in proof["implementation_sha256"].items():
    assert sha256_file(root / relative) == digest
assert verify_manifest(root)["ok"]
scope = plan["scope"]
listing = root / scope["listing_relative_path"]
assert sha256_file(listing) == scope["listing_sha256"]
directory = root / scope["extracted_root_relative_path"]
assert directory.resolve().is_relative_to(root.resolve())
text = listing.read_text(encoding="ascii")
members = screen_members(directory, text)
names = text.splitlines()
sizes = [p.stat().st_size for _, _, p in members]
uppercase = Counter(w for w, _, p in members if p.name.endswith(".TXT"))
requirements = plan["real_metadata_requirements"]
assert len(members) == len(names) == requirements["files"] == 1830
assert uppercase == {5: 153}
assert max(sizes) == requirements["known_max_bytes"] and sum(sizes) == requirements["known_total_bytes"]
name_sha = hashlib.sha256(json.dumps(sorted(names), separators=(",", ":")).encode("ascii")).hexdigest()
assert name_sha == requirements["raw_name_set_sha256"]
output = root / plan["real_metadata_proof_path"]
assert not output.exists() and not (root / plan["native_receipt_path"]).exists()
atomic_write_json(output, dict(created_at=utc_now(), cycle=327, study_sha256=STUDY_SHA,
    conformance_sha256=sha256_file(proof_path), implementation_sha256=proof["implementation_sha256"],
    listing_sha256=sha256_file(listing), raw_name_set_sha256=name_sha,
    files=1830, canonical_UIDs=1830, raw_listing_equals_disk=True, fixed_order_preserved=True,
    actual_paths_preserved=True, alias_collisions=0, linked_entries=0,
    uppercase_extensions=153, uppercase_extensions_by_writer=dict(uppercase),
    total_bytes=sum(sizes), max_bytes=max(sizes), all_metadata_bounds_pass=True,
    complete_metadata_validated_before_payload=True, native_payloads_read=0,
    numeric_conversions=0, research_fit=0, new_EXPs=0, scoring=False))
print(json.dumps(dict(metadata_complete=True, canonical_UIDs=1830, uppercase_extensions=153,
    total_bytes=sum(sizes), max_bytes=max(sizes), native_payloads_read=0)))
