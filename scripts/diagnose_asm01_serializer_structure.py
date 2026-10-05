"""Inventory exact exposed T1 syntax without converting or emitting X/Y."""
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

import nextai_autoresearch
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI-VALIDATION-20261002"
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(root / "src")
plan_path = root / "research/plans/ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1.json"
assert sha256_file(plan_path) == "8db10c6c2bd714994b86f4b83e88593ef7e90a3ab15014c258cb2e8e88a2f8ae"
plan = json.loads(plan_path.read_text())
scope = plan["native_validation"]
sample = root / scope["relative_path"]
assert sample.resolve().is_relative_to(root.resolve())
assert sample.stat().st_size == scope["expected_bytes"] and sha256_file(sample) == scope["expected_sha256"]
receipt_path = root / "research/reviews/ASM01-SERIALIZER-STRUCTURE-DIAGNOSIS-V1.json"
assert not receipt_path.exists()
payload = sample.read_bytes()
assert len(payload) <= plan["resources"]["native_sample_bytes_cap"]
raw_lines = payload.decode("ascii").splitlines()
lines = [line.strip() for line in raw_lines if line.strip()]


def kind(token):
    if not token.strip():
        return "empty"
    if re.fullmatch(r"[0-9]+", token):
        return "unsigned_integer"
    if re.fullmatch(r"[+-][0-9]+", token):
        return "signed_integer"
    if re.fullmatch(r"[+-]?[0-9]+\.[0-9]+", token):
        return "decimal"
    return "text_redacted"


row_kinds = Counter()
point_kinds = Counter()
point_states = Counter()
point_serials = Counter()
markers = []
header_positions = []
unknown_forms = Counter()
stroke = 0
down = False
alternating = True
serial_consistent = True
declared = None
for index, line in enumerate(lines):
    fields = line.split()
    if fields[0].startswith("CHARACTER_NAME:"):
        row_kinds["character_header"] += 1
    elif fields[0].startswith("END_CHARACTER:"):
        row_kinds["character_end"] += 1
    elif re.fullmatch(r"STROKE_COUNT:\s*[1-9][0-9]*", line):
        row_kinds["stroke_count"] += 1
        declared = int(line.split(":", 1)[1])
    elif fields == ["X", "Y", "STYLUS_STATE", "STROKE"]:
        row_kinds["column_header"] += 1
        header_positions.append(index)
    elif fields[0] in {"PEN_DOWN", "PEN_UP"}:
        marker, extra = fields[0], fields[1:]
        row_kinds[marker] += 1
        if marker == "PEN_DOWN":
            alternating &= not down
            stroke += 1
            down = True
        else:
            alternating &= down
            down = False
        # With at most two marker fields the public four-column row contains
        # only trailing state/serial; larger forms stay entirely redacted.
        categorical = extra if len(extra) <= 2 and all(kind(x) == "unsigned_integer" for x in extra) else None
        if categorical:
            serial_consistent &= int(categorical[-1]) == stroke
        markers.append({"marker": marker, "nonempty_line_index": index,
                        "extra_token_count": len(extra), "extra_kinds": [kind(x) for x in extra],
                        "tab_field_kinds": [kind(x.strip()) for x in line.split("\t")],
                        "trailing_state_serial_tokens": categorical})
    elif len(fields) == 4 and all(kind(x) == "unsigned_integer" for x in fields[-2:]):
        row_kinds["point_row"] += 1
        point_kinds["/".join(kind(x) for x in fields)] += 1
        point_states[fields[2]] += 1
        point_serials[fields[3]] += 1
        serial_consistent &= down and int(fields[3]) == stroke
    else:
        row_kinds["unknown"] += 1
        unknown_forms["/".join(kind(x) for x in fields)] += 1
assert sum(row_kinds.values()) == len(lines)
receipt = {
    "schema_version": 1, "id": "ASM01-SERIALIZER-STRUCTURE-DIAGNOSIS-V1", "created_at": utc_now(),
    "cycle": 323, "complete_row_inventory": True, "study_sha256": sha256_file(plan_path),
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
    "diagnosis_script_sha256": sha256_file(Path(__file__)),
    "sample_path": scope["relative_path"], "sample_sha256": sha256_file(sample), "sample_bytes": len(payload),
    "raw_line_count": len(raw_lines), "nonempty_line_count": len(lines), "row_counts": dict(row_kinds),
    "column_header_positions": header_positions, "declared_strokes": declared, "observed_down_count": stroke,
    "pen_alternation_complete": bool(alternating and not down), "categorical_serial_consistent": bool(serial_consistent),
    "marker_rows": markers, "point_field_lexical_kind_counts": dict(point_kinds),
    "point_state_token_counts": dict(point_states), "point_serial_token_counts": dict(point_serials),
    "unknown_row_forms_redacted": dict(unknown_forms), "character_names_emitted_or_used_as_keys": False,
    "coordinate_values_converted_or_emitted": False, "native_parser_or_models_called": False,
    "point_array_or_descriptors_created": False, "known_T1_samples_opened": 1,
    "new_native_samples_opened": 0, "D_samples_opened": 0, "new_extraction": False,
    "fit": 0, "scoring": False,
}
atomic_write_json(receipt_path, receipt)
print(json.dumps(receipt), flush=True)
