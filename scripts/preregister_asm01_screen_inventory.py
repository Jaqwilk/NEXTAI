"""Freeze complete screen grammar inventory before implementation or new bytes."""
from pathlib import Path
import json
import shutil

from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.research_program import auxiliary_charge, auxiliary_reserve, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root = Path(__file__).resolve().parents[1]
clone = root.parent / "NEXTAI-VALIDATION-20261002"
plan_path = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.json"
assert root.name == "NEXTAI" and not (root / plan_path).exists()
assert not any((root / p).exists() for p in ("STOP", "PAUSE", "research/run.lock"))
assert not (root / "src/nextai_autoresearch/asm01_grammar_inventory.py").exists()
for suffix in ("startup-doctor", "startup-lab"):
    check = json.loads((root / f"research/reviews/NEXTAI-B-325-{suffix}.json").read_text())
    assert check["result"]["returncode"] == 0 and not check["error"]
lab = json.loads((root / "research/reviews/NEXTAI-B-325-startup-lab.stdout.txt").read_text())
assert not lab["errors"] and not lab["warnings"]
wallet = status(root)
assert wallet["study_terminal"] and not wallet["program_terminal"]
assert not wallet["paid_run_pending"] and wallet["pending_fit_reservation_seconds"] == 0
assert wallet["stage_b_registration_attempts_used"] == 1
assert wallet["protected_future_compute_seconds"] == 47000
assert verify_manifest(root)["ok"]
identifier = "NEXTAI-B-325-administration-prepaid"
auxiliary_reserve(root, identifier, 300)
auxiliary_charge(root, identifier, 300)
atomic_write_json(root / f"research/reviews/{identifier}.json", {
    "id": identifier, "created_at": utc_now(), "seconds_charged": 300,
    "cap_seconds": 300, "conservative_prepaid": True,
    "scope": "Required reads including unsuccessful administrative path/glob/blank-JSON reads, syntax and contract construction, metadata archives, settled mirrors/report and Git. No native inventory, parser/model call or fixture fit; substantive checks charged separately.",
})
parent_paths = ["AGENTS.md", "program.md", "research/LAB_PLAN.md", "docs/CURRENT_STATUS.md",
                "config/research.toml", "research/eval_manifest.json",
                "research/laboratory/preflight_certificate.json", "research/state.json"]
archive = root / "research/laboratory/archive/ASM01-cycle325-parent-V1"
assert not archive.exists()
for relative in parent_paths:
    destination = archive / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / relative, destination)
listing = "research/data/asm01_native_v1/selected-screen-members-v3.txt"
assert (clone / listing).is_file()
previous_intake_path = "research/data_manifests/ASM01-ACQUISITION-V3.json"
previous = json.loads((root / previous_intake_path).read_text())
assert not previous["complete"] and previous["native_files_attempted"] == 75
assert previous["native_files_converted"] == 74 and previous["D_samples_opened"] == 0
references = [previous_intake_path, "research/laboratory/ASM01-CYCLE324-COMPLETION-V1.receipt.json",
              "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json",
              "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json",
              "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json",
              "research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json",
              "src/nextai_autoresearch/asm01_task.py",
              "src/nextai_autoresearch/asm01_task_v3.py",
              "src/nextai_autoresearch/asm01_task_v4.py",
              "src/nextai_autoresearch/asm01_task_v5.py"]
plan = {
    "schema_version": 1, "id": "ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1", "cycle": 325,
    "created_at": utc_now(), "stage": "task_design", "study_kind": "preparation_only",
    "cohort": "asm01_native_memory_v3", "program_id": wallet["id"],
    "program_contract_path": wallet["contract_path"],
    "program_contract_sha256": sha256_file(root / wallet["contract_path"]),
    "study_started_at": "2026-10-05T23:37:00Z", "study_deadline_at": "2026-10-06T01:37:00Z",
    "work_start_policy": "Conservative start before this turn's startup checks and preregistration; includes required reads and all administration.",
    "registration_attempts_for_this_study_cap": 0,
    "question": "What complete lexical row and categorical lifecycle forms occur in every fixed screen member, and which structural incompatibilities need an independently preregistered metadata-equivalent repair?",
    "previous_goal_turn_classification": "progress: cycle324 completed131 clone conformance cases, preserved the native failure75 and all costs, sealed1446 protected files and identical clean checkouts; not a learning result or an impasse",
    "resources": {"work_minutes_cap": 120, "auxiliary_test_seconds_cap": 1800,
                  "fit_seconds_study_cap": 0, "fit_seconds_per_role_cap": 0,
                  "administration_prepaid_seconds": 300, "native_files_cap": 1830,
                  "native_sample_bytes_cap": 262144, "native_total_bytes_cap": 479723520,
                  "new_download_bytes_cap": 0, "new_extraction_bytes_cap": 0},
    "budget_at_freeze": wallet,
    "protected_future_compute_seconds": 47000, "protected_future_registration_attempts": 7,
    "parent_reference_sha256": {p: sha256_file(root / p) for p in references},
    "parent_archive_path": archive.relative_to(root).as_posix(),
    "parent_manifest_sha256": sha256_file(root / "research/eval_manifest.json"),
    "scope": {
        "independent_clone": str(clone), "listing_relative_path": listing,
        "listing_sha256": sha256_file(clone / listing),
        "extracted_root_relative_path": "research/data/asm01_native_v1/screen-text-v3",
        "fixed_writers": [1, 2, 3, 4, 5, 16, 17, 18, 19, 20], "samples_per_writer": 183,
        "canonical_path_template": "Online Handwritten Assamese Characters Dataset/W{writer}/{sample}.{writer}.txt",
        "known_text_sha256": previous["attempted_sample_text_sha256"],
        "known_texts": 75, "new_texts_expected": 1755, "D_texts_expected": 915,
        "prior_numeric_complete_conversions": 74, "partial_failed_sample_point_count": None,
        "new_numeric_conversions": 0,
    },
    "inventory_recipe": {
        "coverage": "Exactly every1830 listed regular file once; validate the complete canonical membership before content. Check known75 raw hashes, record every new full-file SHA and byte count; inventory every raw/nonempty line with no selective omission.",
        "rows": "Classify declaration/end/column-header/PEN_DOWN/PEN_UP/point-shaped/unknown rows; record token arity and per-field lexical kinds, header/marker/unknown positions, pen alternation and trailing categorical state/stroke where unambiguous. All unknown grammar forms are observations, not reasons to stop before the rest of the fixed cohort.",
        "lexical_kinds": ["unsigned_integer", "explicit_plus_integer", "negative_integer", "decimal", "exponent", "text_redacted"],
        "categorical_policy": "Only unsigned decimal strings of at most6 digits in declared stroke count or trailing unambiguous state/stroke fields may be converted to integers. Longer, signed or ambiguous categorical fields retain kind only; count anomalies without guessing meanings. X/Y fields are never converted.",
        "redaction": "Never emit names, raw lines, unknown raw tokens, X/Y strings or coordinate values. Diagnostics consist only of fixed sample identifiers, SHA, line indices, grammar categories, lexical kinds, arities, counts and unambiguous categorical state/stroke values.",
        "model_access": "Pure standard-library structural scanner; no original parser, NumPy, point array, descriptor, model, source state replay, calibration, fit or scoring.",
        "lifecycle": "Track declared versus observed stroke counts, alternation, whether point-shaped rows lie inside a stroke, and categorical serial equality; singleton PEN_UP0 is a release-state marker only with the frozen unique headed layout. Preserve all anomalies and per-file evidence.",
    },
    "validation": "Synthetic known-good and malformed syntax, numeric-type redaction, non-ASCII/byte/type bounds, complete per-row accounting, ambiguous markers, mismatched serials, exact1830 membership and unsafe paths; then exactly one complete native inventory in the independent clone, hash-bound to preregistration and conformed scanner/tests before new native bytes.",
    "failure_policy": "Preserve any IO/encoding/hash/scope/resource or fixture failure and its whole supervised process cost; stop unstarted native scope. Unknown row/lifecycle forms are fully inventoried without parsing or rescue. No native inventory retry or sample replacement.",
    "decision_rule": "KEEP only complete structural evidence if1830/1830 files and every nonempty row are accounted for with zero redaction/scope violations and clone integrity/lifecycle pass. Scientific comparison remains INCONCLUSIVE. Freeze concrete normalization and synthetic accept/reject fixtures in a NEW immutable prospective contract before any parser change; no parser repair or numeric native conversion in this cycle. If geometry/population rules would need changing, retain this cohort as infeasible and prospectively assess a distinct licensed family without weakening gates.",
    "scientific_gates_unchanged": True,
    "forbidden": ["EXP/registration", "research fit/scoring", "native X/Y conversion/emission",
                  "native parser/descriptor/model calls", "parser repair in this cycle",
                  "native NPZ", "new download/extraction", "future writers6..15/21..30",
                  "Data_Table/character-name emission", "source refit", "sample replacement/filtering",
                  "metric/grid/threshold/geometry changes", "completed artifact edits", "paid retry",
                  "WT8-9", "external model/API", "schedule changes"],
    "next_discriminating_experiment": "Use the full inventory to freeze one concrete metadata-equivalent repair and a NEW unchanged-model five-pair ASM scientific cohort before implementation/numeric arrays. Validate synthetic conformance and complete native feasibility in clone, freeze/preflight/readiness, then at most one audited EXP atK16/32/64 with source controls,strong classics,updates0/1/4 and nominal/adverse. Disclose all1830 prior lexical exposures and74 prior complete conversions. Otherwise choose a distinct justified licensed native family prospectively; preserve all failures and future7tickets/47000s. The complete transfer/replication/fresh-final/prototype goal remains active.",
}
atomic_write_json(root / plan_path, plan)
atomic_write_json(root / "research/reviews/ASM01-CYCLE325-PARENT-BYTES-V1.json", {
    "created_at": utc_now(), "archive_path": archive.relative_to(root).as_posix(),
    "files": {p: sha256_file(root / p) for p in parent_paths},
    "all_current_protected_files": len(json.loads((root / "research/eval_manifest.json").read_text())["files"]),
})
append_jsonl(root / "research/events.jsonl", {
    "event": "research_program_study_frozen", "created_at": utc_now(), "cycle": 325,
    "program_id": wallet["id"], "study_path": plan_path, "study_sha256": sha256_file(root / plan_path),
    "inventory_implementation_or_new_native_texts_seen": False,
})
config = root / "config/research.toml"
old = b'study_path = "research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json"'
assert config.read_bytes().count(old) == 1
config.write_bytes(config.read_bytes().replace(old, f'study_path = "{plan_path}"'.encode()))
header = ("# Current cycle325 — complete ASM01 screen grammar inventory (2026-10-05)\n\n"
          "ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1 is preparation only.\n"
          "Deadline2026-10-06T01:37:00Z;auxiliary1800s includes startup,failure/admin costs.\n"
          "Exactly1830 fixed screen text files;75 prior raw exposures/74 conversions disclosed.\n"
          "Inventory every lexical row and categorical lifecycle; redact names/X/Y/unknown tokens.\n"
          "No numeric coordinates,parser/model/descriptor,repair,fit,EXP,new extraction/download.\n"
          "Future writers6..15/21..30 and Data_Table remain inaccessible.\n"
          "Freeze a concrete separate repair before future code; preserve all V1/V2/V3 failures.\n"
          "Scientific comparison remains INCONCLUSIVE; maintenance/scoring=false.\n"
          "B/full goal active; protected7tickets/47000s and every scientific gate unchanged.\n"
          "No paid retry,WT8-9,external models/API or schedule change.\n\n"
          "Earlier stage-specific sections below remain preserved history.\n\n").encode()
for relative in parent_paths[:4]:
    (root / relative).write_bytes(header + (root / relative).read_bytes())
state = json.loads((root / "research/state.json").read_text())
assert state["cycle_number"] == 324 and state["completed_experiments"] == 122 and state["active_experiment_id"] is None
state.update(cycle_number=325, updated_at=utc_now())
atomic_write_json(root / "research/state.json", state)
print(json.dumps({"plan_path": plan_path, "plan_sha256": sha256_file(root / plan_path),
                  "inventory_implemented": False, "new_native_texts_seen": 0,
                  "maintenance": True, "scoring": False}), flush=True)
