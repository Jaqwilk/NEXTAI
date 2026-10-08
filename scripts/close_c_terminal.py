"""Final administrative C closure after report/archive publication, no science."""
from pathlib import Path
import json
import shutil

from nextai_autoresearch import research_program_c as c
from nextai_autoresearch.ledger import read_jsonl
from nextai_autoresearch.utils import load_json, sha256_file, utc_now


def write_exclusive(path, document):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main():
    root = Path(__file__).resolve().parents[1]
    primary = root.parent / "NEXTAI"
    if root.name != "NEXTAI-VALIDATION-20261002" or not (primary / ".git").exists():
        raise ValueError("Only canonical clone with primary workspace may close C")
    native_path = "research/data_manifests/ASM01-C-ACQUISITION-V1.json"
    native = load_json(root / native_path)
    before = c.status(root)
    if (native.get("complete") is not False or native.get("error_category") != "native_geometry"
            or before["registration_attempts_used"] != 0 or before["program_closed"]
            or before["scoring_authorized"] or before["full_worker_seconds"] != 0
            or before["supervised_fit_seconds"] != 0):
        raise ValueError("C terminal no-science failure binding changed")
    receipt_path = "research/laboratory/NEXTAI-C-CYCLE344-COMPLETION-V1.receipt.json"
    accounting_path = "research/laboratory/NEXTAI-C-CYCLE344-FINAL-ACCOUNTING-V1.json"
    if (root / accounting_path).exists() or (primary / accounting_path).exists():
        raise ValueError("Final C accounting already exists")
    receipt = {"created_at": utc_now(), "program_id": c.PROGRAM_ID,
        "contract_sha256": c.CONTRACT_SHA256, "whole_goal_complete": False,
        "decision": "INCONCLUSIVE technical", "reason": "native_geometry at18:67",
        "native_receipt_path": native_path, "native_receipt_sha256": sha256_file(root / native_path),
        "scientific_registration_attempts": 0, "EXP": 0, "scientific_fit_seconds": 0,
        "scientific_full_workers_seconds": 0, "paid_retry_authorized": False,
        "archive_receipt": "research/laboratory/NEXTAI-C-CYCLE344-ARCHIVE-V1.receipt.json",
        "final_accounting_path": accounting_path, "C_outer_window_includes_final_administration": True}
    write_exclusive(root / receipt_path, receipt)
    c.close(root, receipt_path)
    shutil.copyfile(root / receipt_path, primary / receipt_path)
    report = "research/analyses/NEXTAI-C-CYCLE344-STABILIZATION-AND-ASM-SCREEN-V1.md"
    shutil.copyfile(primary / report, root / report)
    # Charge administrative preservation/publication through this final control
    # endpoint. Reading/writing the endpoint itself is clock-resolution overhead.
    c.checkpoint(root, "final report/archive publication and administrative preservation complete")
    event = read_jsonl(root / c.EVENTS)[-1]
    accounting = {"program_id": c.PROGRAM_ID, "contract_sha256": c.CONTRACT_SHA256,
        "work_started_at": "2026-10-07T23:42:00Z", "charged_through": event["created_at"],
        "outer_work_seconds": event["outer_elapsed_seconds"],
        "inherited_uncertain_liability_seconds": event["liability_seconds"],
        "inherited_measured_minimum_seconds": 110.724645,
        "inherited_upper_bound_verified": False, "total_seconds_charged": event["total_seconds_charged"],
        "total_seconds_cap": 43200, "remaining_C_seconds_not_released_to_B": 43200 - event["total_seconds_charged"],
        "registration_attempts_used": 0, "scientific_full_worker_seconds": 0, "scientific_supervised_fit_seconds": 0,
        "component_costs_nested_not_added": True, "B_tickets_used": 2,
        "B_seconds_used": 30999.55024020007, "B_protected_tickets": 6, "B_protected_seconds": 41000,
        "whole_goal_complete": False, "C_closed": True, "scoring_authorized": False,
        "timing_boundary": "Inclusive outer work through final control endpoint; final endpoint serialization/copy/return is logging overhead at subsecond resolution, not a new research phase.",
        "final_control_event_sha256": c.sha256_json(event), "event_sequence": event["sequence"]}
    write_exclusive(root / accounting_path, accounting)
    shutil.copyfile(root / accounting_path, primary / accounting_path)
    shutil.copyfile(root / c.EVENTS, primary / c.EVENTS)
    print(json.dumps(accounting), flush=True)


if __name__ == "__main__":
    main()
