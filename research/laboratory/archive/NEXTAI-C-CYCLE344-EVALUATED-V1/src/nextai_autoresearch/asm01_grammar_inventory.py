"""Structural evidence only: never convert or emit native pen coordinates."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

WRITERS = (1, 2, 3, 4, 5, 16, 17, 18, 19, 20)
COLUMNS = ["X", "Y", "STYLUS_STATE", "STROKE"]
STUDY = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.json"
STUDY_SHA = "2f01c210d0e1ea1d067106188a39660246e59e71d56a2528dfaa52b35bb9c683"


def lexical_kind(token):
    for pattern, label in (
        (r"[0-9]+", "unsigned_integer"),
        (r"\+[0-9]+", "explicit_plus_integer"),
        (r"-[0-9]+", "negative_integer"),
        (r"[+-]?(?:[0-9]+\.[0-9]*|\.[0-9]+)", "decimal"),
        (r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)[eE][+-]?[0-9]+", "exponent"),
    ):
        if re.fullmatch(pattern, token):
            return label
    return "text_redacted"


def categorical(token):
    # Called ONLY on declaration/state/serial fields, never X/Y.
    return int(token) if re.fullmatch(r"[0-9]{1,6}", token) else None


def inventory_bytes(payload):
    if not isinstance(payload, bytes) or len(payload) > 262144:
        raise ValueError("Inventory byte cap/type")
    try:
        raw = payload.decode("ascii").splitlines()
    except UnicodeDecodeError:
        raise ValueError("Inventory requires ASCII; raw tokens redacted") from None
    rows = [line.strip().split() for line in raw if line.strip()]
    columns = [i for i, fields in enumerate(rows) if fields == COLUMNS]
    headed = columns == [2]
    counts, forms, states, serials, anomalies = (Counter() for _ in range(5))
    markers, unknown, declarations, ends = [], [], [], []
    declared = None
    stroke, down = 0, False
    for i, fields in enumerate(rows):
        kinds = [lexical_kind(x) for x in fields]
        if fields[0].startswith("CHARACTER_NAME:"):
            category = "character_header"
            declarations.append(i)
        elif fields[0].startswith("END_CHARACTER:"):
            category = "character_end"
            ends.append(i)
        elif fields[0] == "STROKE_COUNT:":
            category = "stroke_count"
            value = categorical(fields[1]) if len(fields) == 2 else None
            if i != 1 or declared is not None or value is None or value < 1:
                anomalies["stroke_declaration"] += 1
            else:
                declared = value
        elif fields == COLUMNS:
            category = "column_header"
        elif fields[0] in {"PEN_DOWN", "PEN_UP"}:
            category = fields[0]
            extra = fields[1:]
            # Unknown marker operands could be coordinates: do not cast/emit them.
            # Recognized values below come from the stroke counter/constants.
            values = [] if not extra else None
            if category == "PEN_DOWN":
                if down:
                    anomalies["repeated_pen_down"] += 1
                stroke += 1
                down = True
                if extra == [str(stroke)]:
                    values = [stroke]
                if extra and values is None:
                    anomalies["pen_down_serial_form"] += 1
            else:
                if not down:
                    anomalies["pen_up_without_stroke"] += 1
                release = headed and extra == ["0"]
                if release:
                    values = [0]
                elif extra == [str(stroke)] and stroke > 0:
                    values = [stroke]
                elif extra == ["0", str(stroke)] and stroke > 0:
                    values = [0, stroke]
                if extra and values is None:
                    anomalies["pen_up_serial_form"] += 1
                down = False
            markers.append({"marker": category, "nonempty_line_index": i,
                            "extra_arity": len(extra), "extra_kinds": kinds[1:],
                            "categorical_values": values})
        elif len(fields) == 4 and all(x != "text_redacted" for x in kinds[:2]):
            category = "point_shaped"
            state, serial = (categorical(x) for x in fields[2:]) if headed else (None, None)
            if not headed:
                anomalies["point_categorical_roles_ambiguous"] += 1
            states[str(state) if state is not None else kinds[2]] += 1
            serials[str(serial) if serial is not None else kinds[3]] += 1
            if not down:
                anomalies["point_outside_stroke"] += 1
            if state != 1:
                anomalies["point_state_not_one"] += 1
            if serial != stroke:
                anomalies["point_serial_mismatch"] += 1
            if kinds != ["unsigned_integer"] * 4:
                anomalies["point_lexical_form_not_v1"] += 1
        else:
            category = "unknown"
            unknown.append({"nonempty_line_index": i, "arity": len(fields), "kinds": kinds})
        counts[category] += 1
        forms[f"{category}|{len(fields)}|{'/'.join(kinds)}"] += 1
    if declarations != [0] or ends != [len(rows) - 1] or len(rows) < 5:
        anomalies["character_boundary"] += 1
    if not headed:
        anomalies["headed_layout"] += 1
    if declared is None or stroke != declared or down:
        anomalies["incomplete_stroke_lifecycle"] += 1
    if counts["point_shaped"] < 4:
        anomalies["fewer_than_four_point_rows"] += 1
    assert sum(counts.values()) == len(rows) == sum(forms.values())
    return {"raw_line_count": len(raw), "nonempty_line_count": len(rows),
            "blank_line_count": len(raw) - len(rows), "row_counts": dict(counts),
            "row_form_counts": dict(forms), "column_header_positions": columns,
            "declared_strokes": declared, "observed_down_count": stroke,
            "marker_rows": markers, "point_state_counts": dict(states),
            "point_serial_counts": dict(serials), "unknown_rows_redacted": unknown,
            "structural_anomaly_counts": dict(anomalies)}


def screen_members(directory, listing):
    expected = {f"Online Handwritten Assamese Characters Dataset/W{w}/{c}.{w}.txt"
                for w in WRITERS for c in range(1, 184)}
    names = listing.splitlines()
    if len(names) != 1830 or set(names) != expected:
        raise ValueError("Exactly the frozen1830 canonical members required")
    actual = set()
    for entry in directory.rglob("*"):
        if entry.is_symlink() or entry.is_junction():
            raise ValueError("Linked inventory member/directory forbidden")
        if entry.is_file():
            actual.add(entry.relative_to(directory).as_posix())
    if actual != expected:
        raise ValueError("Extracted inventory membership differs")
    total = 0
    members = []
    for w in WRITERS:
        for c in range(1, 184):
            path = directory / f"Online Handwritten Assamese Characters Dataset/W{w}/{c}.{w}.txt"
            if not path.resolve().is_relative_to(directory.resolve()) or path.is_symlink():
                raise ValueError("Inventory member outside frozen scope")
            size = path.stat().st_size
            if size > 262144:
                raise ValueError("Inventory per-file byte cap")
            total += size
            members.append((w, c, path))
    if total > 479723520:
        raise ValueError("Inventory aggregate byte cap")
    return members


def main():
    from .utils import atomic_write_json, sha256_file, utc_now
    root = Path(__file__).resolve().parents[2]
    assert root.name == "NEXTAI-VALIDATION-20261002"
    assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
    assert sha256_file(root / STUDY) == STUDY_SHA
    plan = json.loads((root / STUDY).read_text())
    assert plan["study_kind"] == "preparation_only" and plan["cycle"] == 325
    for relative, digest in plan["parent_reference_sha256"].items():
        assert sha256_file(root / relative) == digest
    proof = json.loads((root / "research/reviews/ASM01-INVENTORY-PRECONTENT-CONFORMANCE-V1.json").read_text())
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
    output = root / "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.receipt.json"
    assert not output.exists(), "Native inventory already consumed; no retry"
    receipt = {"created_at": utc_now(), "cycle": 325, "study_sha256": STUDY_SHA,
               "scanner_sha256": sha256_file(Path(__file__)),
               "conformance_sha256": sha256_file(root / "research/reviews/ASM01-INVENTORY-PRECONTENT-CONFORMANCE-V1.json"),
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
