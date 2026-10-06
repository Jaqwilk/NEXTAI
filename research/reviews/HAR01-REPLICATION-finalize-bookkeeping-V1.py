"""Preserve one failed conformance; never resume scientific execution."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

from nextai_autoresearch.research_program import auxiliary_charge, status
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

ROOT = Path.cwd()
CLONE = ROOT.parent / "NEXTAI-VALIDATION-20261002"
STUDY = "research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json"
SHA = "d5567973e85b444d95ac13a70db9fe24b87c0ab3b672932e8322862c336ad12a"
PREP = "research/laboratory/HAR01-REPLICATION-PREPARATION-COMPLETION-V1.receipt.json"
STOP = "research/laboratory/HAR01-REPLICATION-STOP-V1.receipt.json"
COMPLETION = "research/laboratory/HAR01-REPLICATION-FAILURE-COMPLETION-V1.receipt.json"
REPORT = "research/analyses/HAR01-CYCLE337-INDEPENDENT-REPLICATION-V1.md"
ARCHIVE = "research/results/HAR01-REPLICATION-PREPARATION-FAILURE-V1.zip"
BINDING = "research/reviews/HAR01-REPLICATION-SOURCE-BINDING-V1.json"
XML = "research/reviews/HAR01-REPLICATION-conformance-V1.xml"


def main():
    assert not (ROOT / COMPLETION).exists()
    assert sha256_file(ROOT / STUDY) == SHA
    prep = json.loads((ROOT / PREP).read_text(encoding="utf-8"))
    assert not prep["ready"] and prep["fit"] == prep["EXP"] == 0
    assert len(prep["jobs"]) == 1 and prep["jobs"][0]["returncode"] != 0
    cases = ET.parse(ROOT / XML).findall(".//testcase")
    failed = [c for c in cases if c.find("failure") is not None or c.find("error") is not None]
    assert len(cases) == 50 and len(failed) == 1
    assert (ROOT / XML).read_bytes() == (CLONE / XML).read_bytes()
    binding = json.loads((ROOT / BINDING).read_text(encoding="utf-8"))
    for relative, digest in binding["files"].items():
        assert sha256_file(ROOT / relative) == sha256_file(CLONE / relative) == digest, relative
    absent = [
        "research/data/har01_replication_v1/replication.npz",
        "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V1.json",
        "research/checks/HAR01-replication-readiness-V1.json",
        "research/reviews/HAR01-REPLICATION-controller-V1.started.json",
    ]
    assert all(not (base / p).exists() for base in (ROOT, CLONE) for p in absent)
    with zipfile.ZipFile(ROOT / ARCHIVE) as archive:
        assert archive.testzip() is None
        hashes = {p: hashlib.sha256(archive.read(p)).hexdigest() for p in archive.namelist()}
    files = sorted(hashes)
    events = [json.loads(line) for line in (ROOT / "research/events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    for identity in ("HAR01-REPLICATION-preparation-V1", "HAR01-REPLICATION-controller-V1"):
        charges = [e for e in events if e.get("event") == "research_program_aux_fit_charged" and e.get("charge_id") == identity]
        assert len(charges) == 1 and charges[0]["seconds"] == 1200
    # Original closure already archived and charged; never repeat either operation.
    wallet = status(ROOT)
    assert wallet["study_terminal"] and not wallet["scoring_authorized"]
    assert wallet["stage_b_registration_attempts_used"] == 1
    assert abs(wallet["stage_b_compute_seconds_charged"] - 27369.55024020007) < 1e-6
    assert wallet["fit_seconds_remaining"] >= 41000 + 3600
    now = datetime.now(timezone.utc)
    admin_start = datetime.fromisoformat("2026-10-06T15:16:00+00:00")
    admin_deadline = datetime.fromisoformat("2026-10-06T15:36:00+00:00")
    assert now < admin_deadline
    receipt = {
        "created_at": utc_now(), "id": "HAR01-REPLICATION-FAILURE-COMPLETION-V1",
        "study_path": STUDY, "study_sha256": SHA, "source_commit": "f8911b9",
        "decision": "INCONCLUSIVE through clone conformance failure; scientific scope stopped",
        "tests_completed": 50, "tests_passed": 49, "tests_failed": 1,
        "failure_node": failed[0].attrib, "job": prep["jobs"][0],
        "clone_package_origin": str(CLONE / "src/nextai_autoresearch/__init__.py"),
        "fit": 0, "EXP": 0, "registration": 0, "native_intake": 0, "retry": False,
        "absent_scientific_artifacts_verified": absent,
        "frozen_source_hashes_equal_root_and_clone": binding["files"],
        "archive_path": ARCHIVE, "archive_sha256": sha256_file(ROOT / ARCHIVE),
        "lossless_archived_files_sha256": hashes,
        "preparation_seconds_charged_conservative": 1200,
        "failure_archive_report_seconds_charged_conservative": 1200,
        "total_stage_seconds_charged_conservative": 2400, "whole_stage_cap": 6000,
        "preparation_execution_stop_at": prep["created_at"],
        "preparation_deadline_at": "2026-10-06T15:16:00Z",
        "formal_stop_receipt_at": "2026-10-06T15:16:05Z",
        "formal_stop_receipt_deadline_overshoot_seconds": 5,
        "failure_admin_clock_start": "2026-10-06T15:16:00Z",
        "failure_admin_deadline": "2026-10-06T15:36:00Z",
        "failure_admin_seconds_observed_through_receipt": (now - admin_start).total_seconds(),
        "publication_and_remaining_admin_included_in_charged_envelope": True,
        "unused_failed_stage_seconds": 3600, "unused_seconds_released_for_reuse": False,
        "other_protected_registrations": 6, "other_protected_seconds": 41000,
        "wallet_after_conservative_charge": wallet,
        "administration_failure_preserved": "research/reviews/HAR01-REPLICATION-closure-admin-failure-V1.json",
        "administration_recovery_only_no_repeated_auxiliary_charge": True,
        "full_goal_status": "ACTIVE/INCOMPLETE",
        "unperformed_scope": ["remaining clone conformance", "fresh HAR native intake",
            "integrity/preflight/readiness", "one experiment:45 roles/810 trials/five paired units",
            "ranking/UNKNOWN/source/update/economic estimates and confidence intervals",
            "broader second native family, independent replications, fresh target finals and local prototype"],
    }
    atomic_write_json(ROOT / COMPLETION, receipt)
    report = f"""# HAR01: first independent replication — failed preparation

Decision: **INCONCLUSIVE; scientific execution stopped.** This is a technical conformance failure. There are no new HAR measurements, effect sizes or confidence intervals. The earlier HAR screen's DISCARD decision remains unchanged; this failed preparation neither confirms nor overturns it.

## Frozen authority and implementation

Human authority permitted preparation up to1200s inside the existing6000s first HAR independent-replication stage, including pre-EXP work. The other6 registrations/41000s stay protected. Plan `{STUDY}` was committed before implementation/data at b2b1cb8; SHA256 `{SHA}`. Full tested source was frozen at f8911b9, with29 exact file bindings verified equal in root and independent clone.

The prospective cohort was T6–10/D21–25, five paired source/target units, three scales K16/32/64, updates0/1/4 and nominal/adverse views. The nine arms,4096 alignment pairs,2048/1024 dense steps, source states, models, mathematical transformations, metrics, calibration and decision thresholds were preserved against the parent. Source fitting was prohibited. The implementation added a versioned cohort/intake binding, isolated wrapper around the original HAR suite, scoped cost ownership and failure accounting, readiness/controller bindings, an unchanged-analysis adapter, and synthetic contract tests. These changes are **not fully validated**.

## Sole clone validation and failure

Exactly one bounded pytest invocation ran with `-q -x` and clone/src package provenance. JUnit records50 cases: **49PASS/1FAIL** —26 budget passes,23 intake passes and one intake failure. The analysis, integration, original HAR, authority and process-supervision groups were not reached. The preliminary driver receipt's `conformance_cases=0` means its success-only XML-parsing branch did not execute; the preserved XML and subsequent STOP receipt supply the actual50-case count.

The failing node was `tests/test_har01_replication_intake.py::test_selected_zip_rows_only_are_converted_and_labels_stay_closed`. Dynamic `spec_from_file_location('har01_replication_intake', path)` leaves `__package__` empty. Consequently `scripts/acquire_har01_replication.py:12` executes `from acquire_har01 import data_archive`; dynamic loading does not add `scripts` to the import path. This raised **ModuleNotFoundError** before the selected-row synthetic intake ran. This failure does not demonstrate a defect in native archive contents or in the model's learning/transfer logic. A normal direct-script invocation has a different import-path context, but that route was not executed after failure.

The process receipt also records wrapper return124, root return1, reason `lingering_descendants`, exit active-process count1 and descendant PID6844. The sole job lasted13.032867s and sampled peak tree RSS487190528bytes. A later read-only PID query at approximately15:15Z found no such process. This later absence does not erase the failed exit receipt or identify the lingering process's cause. No conformance rescue, import fix, test retry or native continuation was attempted.

## Costs and deadlines

| Item | Charged seconds | Meaning |
|---|---:|---|
| Preregistration/implementation/clone preparation |1200|Full conservative frozen preparation cap, includes failed test and administration.|
| Failure preservation/archive/report/publication |1200|Full conservative second auxiliary envelope; **no experiment-controller job**.|
| Scientific workers / supervised fit |0|No native intake, readiness, EXP or fit.|
| Total stage charge |2400/6000|Unused3600 remains associated with the failed stage, without release or retry authority.|

The frozen policy explicitly allocates auxiliary2400 as prep1200 plus controller/archive/report1200. The latter was reserved and charged under the exact bound ID solely for required failure preservation and reporting. These are conservative time charges, not measured fit time, money or energy. No old cost, failure or wallet was reset. Final B usage is **1/12 registrations and27369.55024020007/72000s**; remaining44630.44975979993s covers the untouched other6/41000s plus3600 unused current-stage seconds and30.44975979993s original unprotected remainder. Seven protected future registrations remain in the ledger because this stage registered no EXP.

The preparation driver stopped at15:12:51Z, before its15:16:00Z deadline. The formal administrative STOP receipt was written at15:16:05Z: **5s late**. This lateness is disclosed; no claim of perfect preparation-clock conformance is made. Administration from15:16:00Z, including those5s, is included in the separate archive/report charge and must end by15:36:00Z; the full stage deadline remains16:36:00Z. The completion receipt records observed administration through its creation and the prepaid remaining envelope.

The first archive/report helper stopped at an administrative assertion because it compared the aggregate historical wallet with a B-only number. The durable B charge had already been written correctly. Its unchanged source and error are preserved; the bookkeeping continuation reads the B-specific field and does not repeat the archive, charge, tests or scientific execution.

## Preserved evidence and uncertainty

All failed source bytes, preregistrations, stdout/stderr, JUnit XML, job and stop receipts, original AGENTS history and the append-only event prefix are in `{ARCHIVE}`. Every archived file was checked byte-for-byte by SHA256 after decompression; archive SHA256 `{receipt['archive_sha256']}`. Frozen source hashes were compared in both repositories without re-executing tests. Fresh NPZ, acquisition manifest, readiness receipt and controller-start marker are absent in both repositories. Current HARv2 configuration stays maintenance; the study is terminal and scoring=false.

Synthetic passes support only the particular budget/intake bindings exercised. They cannot establish conformance of the unrun groups or native feasibility. Ranking, source identity, retained/updated answers and UNKNOWN are all **unmeasured** here. Economic qualification is also unmeasured; fit0 is not a scientific efficiency result.

## Unperformed scope and next prospective boundary

The remaining tests, fresh intake, integrity/preflight/readiness,45-role/810-trial experiment and all scientific estimates were not performed. The broader transfer/prototype goal remains ACTIVE/INCOMPLETE. If continuation is separately authorized, first freeze a narrow import-loading conformance correction and an exit-accounting diagnosis against the preserved failed version, before any execution or new content; keep models/gates/source states unchanged and debit every cost from an explicit existing allocation. This report does not authorize a retry, use of the unconsumed replication registration slot, use of the other protected budgets, or opening other future HAR/ASM data.

Machine accounting and immutable bindings: `{COMPLETION}`. Earlier `PREPARATION-COMPLETION` and `STOP` receipts remain unchanged.
"""
    (ROOT / REPORT).write_text(report, encoding="utf-8")
    prefix = """# Completed cycle337 — HAR independent-replication preparation failed (2026-10-06)

Human-owned HAR01-INDEPENDENT-REPLICATION-V1 froze before implementation/data.
Exactly one independent-clone conformance:49PASS/1FAIL; dynamic intake import
ModuleNotFoundError before synthetic selected-row conversion. Job root1/wrapper124,
lingering descendant recorded; no failure rescue or retry. Remaining tests unrun.
No fresh native intake, readiness, EXP, registration or scientific fit.
Decision INCONCLUSIVE through technical failure; old HAR DISCARD unchanged.
Preparation1200 plus failure archive/report1200 conservatively charged inside6000.
Driver stop15:12:51Z; formal STOP15:16:05Z was5s after prep deadline, disclosed.
B active:1/12 registrations,27369.55024020007/72000s; no history reset.
Other6 protected tickets/41000s untouched; unused current-stage3600s not released.
All source/failed evidence retained losslessly; HARv2 maintenance,scoring=false,
study terminal. Report research/analyses/HAR01-CYCLE337-INDEPENDENT-REPLICATION-V1.md.
Further execution/repair needs separate frozen authority; no retry/source refit,
new architecture, WT8-9, external model/API or schedule change. Other future
HAR/ASM data remain closed. Broader transfer/fresh-target-final/prototype goal open.
Earlier stage-specific sections below are preserved history.

"""
    agents = ROOT / "AGENTS.md"
    agents.write_bytes(prefix.encode("utf-8") + agents.read_bytes())
    print(json.dumps({"receipt": COMPLETION, "report": REPORT,
        "archive_sha256": receipt["archive_sha256"], "archived_files": len(files),
        "stage_charge": 2400, "wallet_used": wallet["stage_b_compute_seconds_charged"],
        "protected_other_seconds": 41000, "scoring": wallet["scoring_authorized"]}))


if __name__ == "__main__":
    main()
