"""Post-failure observation of existing filenames only; do not repair or read points."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
study = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.json"
assert sha256_file(root / study) == "6351509210dc6ad6f4247665db14ea50aba70e79a6f9dc46b2b0c654e6254726"
plan = json.loads((root / study).read_text())
scope = plan["scope"]
failed = json.loads((root / plan["native_receipt_path"]).read_text())
assert not failed["complete"] and failed["attempted_files"] == 0
listing = root / scope["listing_relative_path"]
assert sha256_file(listing) == scope["listing_sha256"]
names = listing.read_text(encoding="ascii").splitlines()
expected = {scope["canonical_path_template"].format(writer=w, sample=i)
            for w in scope["fixed_writers"] for i in range(1, 184)}


def extension_observation(name):
    return name[:-4] + ".txt" if name.endswith(".TXT") else name


normalized = [extension_observation(n) for n in names]
directory = root / scope["extracted_root_relative_path"]
assert directory.resolve().is_relative_to(root.resolve())
actual, linked = [], 0
for path in directory.rglob("*"):
    if path.is_symlink() or path.is_junction():
        linked += 1
    if path.is_file():
        actual.append(path.relative_to(directory).as_posix())
normalized_actual = [extension_observation(n) for n in actual]
assert len(names) == len(actual) == len(expected) == 1830
assert len(set(normalized)) == len(set(normalized_actual)) == 1830
assert set(normalized) == set(normalized_actual) == expected
assert set(names) == set(actual) and linked == 0
uppercase = Counter()
for name in names:
    if name.endswith(".TXT"):
        uppercase[name.split("/")[-2]] += 1
assert sum(uppercase.values()) == 153
output = root / "research/reviews/ASM01-INVENTORY-V2-EXTENSION-CASE-DIAGNOSIS-V1.json"
assert not output.exists()
receipt = {"created_at": utc_now(), "cycle": 326, "study_sha256": sha256_file(root / study),
    "failed_native_receipt_sha256": sha256_file(root / plan["native_receipt_path"]),
    "listing_sha256": sha256_file(listing), "script_sha256": sha256_file(Path(__file__)),
    "listed_names": len(names), "disk_files": len(actual), "canonical_UIDs": len(expected),
    "uppercase_extension_files": 153, "uppercase_extension_by_writer": dict(uppercase),
    "listing_and_disk_raw_names_identical": True, "only_final_extension_case_differs": True,
    "extension_only_bijection_preserves_all_UIDs": True, "normalized_name_collisions": 0,
    "linked_entries": linked, "raw_name_set_sha256": hashlib.sha256(
        json.dumps(sorted(names), separators=(",", ":")).encode("ascii")).hexdigest(),
    "new_native_texts_read": 0, "coordinate_conversions": 0, "parser_or_model_called": False,
    "native_inventory_restarted": False, "repair_implemented": False,
    "existing_listing_or_extracted_files_modified": False, "research_fit": 0, "new_EXPs": 0,
    "decision": "KEEP metadata diagnosis; inventory remains INCONCLUSIVE and stopped",
    "next_rule": "In a NEW preregistered scope accept only final .txt/.TXT aliases; normalize BOTH listing and extracted names, reject collisions/foreign names/links, retain all 1830 actual paths and unchanged byte limits/UIDs. Validate the complete real filename metadata before any native content. Do not alter point grammar, geometry, scientific gates or completed records."}
atomic_write_json(output, receipt)
print(json.dumps({k: v for k, v in receipt.items() if k != "next_rule"}), flush=True)
