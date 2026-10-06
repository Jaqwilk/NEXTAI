"""Fixed V2 inventory binding; reuse the unchanged structural scanner."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import time

from .asm01_grammar_inventory import inventory_bytes, screen_members

STUDY = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.json"
STUDY_SHA = "6351509210dc6ad6f4247665db14ea50aba70e79a6f9dc46b2b0c654e6254726"


def main():
    from .utils import atomic_write_json, sha256_file, utc_now
    root = Path(__file__).resolve().parents[2]
    assert root.name == "NEXTAI-VALIDATION-20261002"
    assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
    assert sha256_file(root / STUDY) == STUDY_SHA
    plan = json.loads((root / STUDY).read_text())
    assert plan["study_kind"] == "preparation_only" and plan["cycle"] == 326
    for relative, digest in plan["parent_reference_sha256"].items():
        assert sha256_file(root / relative) == digest
    proof = json.loads((root / "research/reviews/ASM01-INVENTORY-V2-PRECONTENT-CONFORMANCE-V1.json").read_text())
    assert proof["all_fixture_tests_passed"] and proof["new_native_content_not_yet_read"]
    assert proof["study_sha256"] == STUDY_SHA
    for relative, digest in proof["implementation_sha256"].items():
        assert sha256_file(root / relative) == digest
    scope = plan["scope"]
    prior = json.loads((root / "research/data_manifests/ASM01-ACQUISITION-V3.json").read_text())
    assert sha256_file(root / "research/data/asm01_native_v1/publisher.rar") == prior["publisher_sha256"]
    listing = root / scope["listing_relative_path"]
    directory = root / scope["extracted_root_relative_path"]
    assert sha256_file(listing) == scope["listing_sha256"]
    assert directory.resolve().is_relative_to(root.resolve()) and not directory.is_symlink() and not directory.is_junction()
    output = root / "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.receipt.json"
    assert not output.exists(), "Native inventory already consumed; no retry"
    receipt = {"created_at": utc_now(), "cycle": 326, "study_sha256": STUDY_SHA,
               "scanner_sha256": sha256_file(root / "src/nextai_autoresearch/asm01_grammar_inventory.py"),
               "entrypoint_sha256": sha256_file(Path(__file__)),
               "conformance_sha256": sha256_file(root / "research/reviews/ASM01-INVENTORY-V2-PRECONTENT-CONFORMANCE-V1.json"),
               "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
               "complete": False, "attempted_files": 0, "inventoried_files": 0,
               "known_texts_reopened": 0, "new_texts_opened": 0, "D_texts_opened": 0,
               "sample_sha256": {}, "files": {}, "coordinate_values_converted_or_emitted": False,
               "character_names_or_unknown_tokens_emitted": False, "parsers_descriptors_models_called": False,
               "new_download_extraction_or_NPZ": False, "numeric_native_conversions": 0,
               "research_fit_seconds": 0, "new_EXPs": 0, "scoring": False}
    started = time.monotonic()
    try:
        for writer, sample, path in screen_members(directory, listing.read_text(encoding="ascii")):
            key = f"{writer}:{sample}"
            payload = path.read_bytes()
            receipt["attempted_files"] += 1
            receipt["current_sample"] = key
            receipt["D_texts_opened"] += writer >= 16
            digest = hashlib.sha256(payload).hexdigest()
            receipt["sample_sha256"][key] = digest
            if key in scope["known_text_sha256"]:
                receipt["known_texts_reopened"] += 1
                if digest != scope["known_text_sha256"][key]:
                    raise ValueError("Previously exposed raw bytes changed")
            else:
                receipt["new_texts_opened"] += 1
            record = inventory_bytes(payload)
            receipt["files"][key] = {"bytes": len(payload), **record}
            receipt["inventoried_files"] += 1
        assert (receipt["attempted_files"], receipt["inventoried_files"], receipt["known_texts_reopened"],
                receipt["new_texts_opened"], receipt["D_texts_opened"]) == (1830, 1830, 75, 1755, 915)
        rows, forms, anomalies = Counter(), Counter(), Counter()
        for record in receipt["files"].values():
            rows.update(record["row_counts"])
            forms.update(record["row_form_counts"])
            anomalies.update(record["structural_anomaly_counts"])
        receipt.update(complete=True, row_counts=dict(rows), row_form_counts=dict(forms),
                       structural_anomaly_counts=dict(anomalies),
                       files_with_structural_anomalies=sum(bool(x["structural_anomaly_counts"]) for x in receipt["files"].values()),
                       files_with_unknown_rows=sum(bool(x["unknown_rows_redacted"]) for x in receipt["files"].values()))
    except BaseException as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        receipt["whole_inventory_wall_seconds"] = time.monotonic() - started
        atomic_write_json(output, receipt)
        print(json.dumps({k: v for k, v in receipt.items() if k not in {"files", "sample_sha256"}}), flush=True)


if __name__ == "__main__":
    main()
