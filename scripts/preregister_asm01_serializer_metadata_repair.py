"""Freeze one exact metadata-only change after diagnosis, before parser code."""
import json
from pathlib import Path

from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
assert root.name == "NEXTAI"
parent_path = "research/plans/ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1.json"
diagnosis_path = "research/reviews/ASM01-SERIALIZER-STRUCTURE-DIAGNOSIS-V1.json"
repair_path = "research/plans/ASM01-SERIALIZER-METADATA-REPAIR-V1.json"
assert not (root / repair_path).exists() and not (root / "src/nextai_autoresearch/asm01_task_v4.py").exists()
assert sha256_file(root / parent_path) == "8db10c6c2bd714994b86f4b83e88593ef7e90a3ab15014c258cb2e8e88a2f8ae"
diagnosis = json.loads((root / diagnosis_path).read_text())
assert diagnosis["complete_row_inventory"] and diagnosis["nonempty_line_count"] == 300
assert diagnosis["column_header_positions"] == [2] and not diagnosis["unknown_row_forms_redacted"]
assert diagnosis["point_state_token_counts"] == {"1": 290}
assert diagnosis["declared_strokes"] == diagnosis["observed_down_count"] == 3
assert diagnosis["pen_alternation_complete"] and not diagnosis["coordinate_values_converted_or_emitted"]
assert all(m["extra_token_count"] == 0 if m["marker"] == "PEN_DOWN"
           else m["trailing_state_serial_tokens"] == ["0"] for m in diagnosis["marker_rows"])
parent = json.loads((root / parent_path).read_text())
plan = {
    "schema_version": 1, "id": "ASM01-SERIALIZER-METADATA-REPAIR-V1", "created_at": utc_now(),
    "cycle": 323, "study_kind": "preparation_only", "parent_study_path": parent_path,
    "parent_study_sha256": sha256_file(root / parent_path),
    "diagnosis_path": diagnosis_path, "diagnosis_sha256": sha256_file(root / diagnosis_path),
    "diagnosis_interpretation": "All exposed T1 strokes end in PEN_UP followed only by0. V1 treats one trailing integer as a positive current stroke serial, causing the reproduced failure. The diagnosis categorical_serial_consistent=false combines that conservative old marker interpretation with point checks; it is not separate proof that point serials are wrong. No point/geometry law is changed.",
    "question": "Does removing only the singleton0 annotation of explicit PEN_UP in a correctly headed publisher sample resolve T1 while preserving every V3 numeric, serial, lifecycle, descriptor and legacy rule?",
    "recipe": {
        "new_module": "src/nextai_autoresearch/asm01_task_v4.py",
        "pre_normalization": "Original bytes type, ASCII decoding and262144-byte cap before any normalization.",
        "header_gate": "Normalize only when the exact X/Y/STYLUS_STATE/STROKE header occurs once at stripped nonempty index2. Otherwise delegate original bytes to exact V3, preserving legacy no-header success/failure and malformed/duplicate/misplaced-header rejection.",
        "sole_new_rule": "Only a stripped line with exact whitespace-separated tokens [PEN_UP,0] is replaced by PEN_UP. Interpret that explicit marker's singleton0 as publisher release-state annotation, not a stroke serial. Do not remove any other token or row.",
        "delegation": "Pass normalized bytes to exact V3. V3/V1 still enforce alternating pen lifecycle, declared stroke count, every point integer/bound/state1/current serial, deduplication,32768-point cap and all three view feasibility checks.",
        "all_other_forms": "Preserve V3 meaning and outcome. In particular legacy PEN_UP/current-positive-serial and PEN_UP/0/current-positive-serial remain unchanged; negative, decimal, wrong or extra state/serial fields still reject under V3. No-header PEN_UP0 remains rejected, because no publisher header identifies the new format.",
        "geometry_models_metrics_change": False,
    },
    "fixtures": [
        "Single/multi-stroke native singleton0 closes, with whitespace variants; exact points and all3 descriptor arrays equal original explicit-serial legacy fixtures.",
        "No-header old valid/error equivalence, old V3 header/singleton0 failure remains reproducible, headed old valid forms unchanged.",
        "Duplicate/misplaced/malformed header, missing/repeated/early UP, wrong declared count, wrong point serial/state and XY bounds/type must fail.",
        "Wrong/negative/decimal/extra marker flags, byte/type/ASCII caps and degenerate geometry remain strict; short pytest parameter IDs only.",
        "All31 earlier V3 fixture cases pass without modification; new module does not replace any historical source.",
    ],
    "native_validation": parent["native_validation"],
    "native_test": "Exactly one bounded numeric conversion of SHA-bound already-exposed T1 after fixture PASS, independent clone only. Verify point array against direct point-row extraction with within-stroke deduplication and per-stroke reset; compare all3 descriptors exactly. Emit only counts,shape,dtype and hashes, never coordinates or names. No model or fit.",
    "resources": "Same parent120min/2200s, including every startup/failure/test/admin; no extra allowance. Zero research fit/EXP/registration/new sample/download/extraction/NPZ/D/future access.",
    "immutable_source_sha256": {p: sha256_file(root / p) for p in (
        "src/nextai_autoresearch/asm01_task.py", "src/nextai_autoresearch/asm01_task_v2.py",
        "src/nextai_autoresearch/asm01_task_v3.py", "tests/test_asm01_native_grammar_v3.py")},
    "unchanged_gates": parent["unchanged_gates"],
    "decision_rule": "KEEP narrowly for exact technical conformance only if all declared tests,T1 comparison and clone integrity/lifecycle pass. Native failure stops unstarted scope without another parser rescue in this cycle. No transfer/economic/quality or scoring readiness claim; new scientific cohort/intake still required.",
}
atomic_write_json(root / repair_path, plan)
append_jsonl(root / "research/events.jsonl", {
    "event": "maintenance_repair_preregistered", "created_at": utc_now(), "cycle": 323,
    "program_id": parent["program_id"], "plan_path": repair_path, "plan_sha256": sha256_file(root / repair_path),
    "diagnosis_path": diagnosis_path, "diagnosis_sha256": sha256_file(root / diagnosis_path),
    "before_repair_implementation_and_native_numeric_conversion": True,
})
print(json.dumps({"repair_plan": repair_path, "repair_sha256": sha256_file(root / repair_path),
                  "new_parser_implemented": False, "native_numeric_conversion": False}), flush=True)
