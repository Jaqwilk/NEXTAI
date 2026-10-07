"""One separately preregistered synthetic clone conformance and durable closure."""
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict
import ast
import hashlib
import json
import os
import shutil
import traceback
import zipfile
import xml.etree.ElementTree as ET

from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.research_program import auxiliary_charge, status

ROOT = Path.cwd()
CLONE = ROOT.parent / "NEXTAI-VALIDATION-20261002"
PLAN = "research/plans/HAR01-LABEL-GUARD-CONFORMANCE-V1.json"
SHA = "243ee6fe7d8634440b92bb88fb8dd712d89761513f32663ee54c1bd226af651b"
PREFIX = "research/reviews/HAR01-LABEL-GUARD-conformance-V1"
DEADLINE = datetime.fromisoformat("2026-10-07T00:33:00+00:00")
TESTS = ["tests/test_har01_import_loading_conformance_v2.py",
         "tests/test_har01_label_guard_ownership.py", "tests/test_har01_replication_process_exit.py"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def main():
    marker = ROOT / "research/reviews/HAR01-LABEL-GUARD-conformance-V1.started.json"
    assert not marker.exists()
    plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
    assert digest(ROOT / PLAN) == digest(CLONE / PLAN) == SHA
    binding = json.loads((ROOT / "research/reviews/HAR01-LABEL-GUARD-source-V1.json").read_text(encoding="utf-8"))
    for p, h in binding["files"].items():
        assert digest(ROOT / p) == digest(CLONE / p) == h, p
    for p, h in plan["parent_bindings"].items():
        assert digest(ROOT / p) == h, p
    old_archive = ROOT / "research/results/HAR01-REPLICATION-PREPARATION-FAILURE-V1.zip"
    with zipfile.ZipFile(old_archive) as bundle:
        old = ast.parse(bundle.read("scripts/acquire_har01_replication.py").decode())
    with zipfile.ZipFile(ROOT / "research/results/HAR01-IMPORT-EXIT-CONFORMANCE-V1.zip") as previous:
        previous_owner = ast.parse(previous.read("src/nextai_autoresearch/research_program.py").decode())
    current_owner = ast.parse((ROOT / "src/nextai_autoresearch/research_program.py").read_text(encoding="utf-8"))
    for name in ("_har_replication_auxiliary", "_har_import_exit_auxiliary"):
        before = next(n for n in previous_owner.body if isinstance(n, ast.FunctionDef) and n.name == name)
        after = next(n for n in current_owner.body if isinstance(n, ast.FunctionDef) and n.name == name)
        assert ast.dump(before) == ast.dump(after), name
    clarification = ROOT / "research/plans/HAR01-LABEL-GUARD-FIXTURE-LABEL-CLARIFICATION-V1.json"
    assert digest(clarification) == "df412083695977f34f41cdc1252f576a2e8352fe5a976a4fb0c9a98b3bd06057"
    new = ast.parse((ROOT / "scripts/acquire_har01_replication.py").read_text(encoding="utf-8"))
    old_functions = [ast.dump(n) for n in old.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    new_functions = [ast.dump(n) for n in new.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    assert old_functions == new_functions
    save(marker, {"study_sha256": SHA, "created_at": datetime.now(timezone.utc).isoformat(), "attempt": 1})
    env = os.environ.copy()
    env.update(PYTHONPATH=str(CLONE / "src"), NEXTAI_PROJECT_ROOT=str(CLONE),
               PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    xml = CLONE / (PREFIX + ".xml")
    temp = CLONE / "research/tmp/HAR01-LABEL-GUARD-CONFORMANCE-V1"
    command_args = ["-q", "-x", *TESTS, f"--junitxml={xml}", f"--basetemp={temp}"]
    code = ("from pathlib import Path;import nextai_autoresearch,pytest;"
            f"assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(Path({str(CLONE / 'src')!r}).resolve());"
            f"raise SystemExit(pytest.main({command_args!r}))")
    result = None
    error = None
    count = passed = failed = skipped = 0
    try:
        remaining = (DEADLINE - datetime.now(timezone.utc)).total_seconds() - 90
        assert remaining > 0, "Closing reserve exhausted before tests"
        result = run_bounded([str(CLONE / ".venv/Scripts/python.exe"), "-c", code],
                             cwd=CLONE, env=env, stdout_path=ROOT / (PREFIX + ".stdout.txt"),
                             stderr_path=ROOT / (PREFIX + ".stderr.txt"), timeout_seconds=min(180, remaining))
        if xml.exists():
            shutil.copyfile(xml, ROOT / (PREFIX + ".xml"))
            cases = ET.parse(xml).findall(".//testcase")
            count = len(cases)
            failed = sum(c.find("failure") is not None or c.find("error") is not None for c in cases)
            skipped = sum(c.find("skipped") is not None for c in cases)
            passed = count - failed - skipped
        assert result.returncode == result.root_returncode == 0 and result.reason == "exited"
        assert not result.exit_live_descendant_pids
        assert count == passed == 14 and failed == skipped == 0
    except BaseException:
        error = traceback.format_exc()
    finally:
        auxiliary_charge(ROOT, "HAR01-LABEL-GUARD-preparation-V1", 600)
    wallet = status(ROOT)
    assert abs(wallet["stage_b_compute_seconds_charged"] - 28569.55024020007) < 1e-6
    assert wallet["protected_future_compute_seconds"] == 43400 and not wallet["scoring_authorized"]
    assert wallet["stage_b_registration_attempts_used"] == 1
    files = sorted(set(binding["files"]) | {PLAN, plan["preparation_authority_path"],
        "research/laboratory/NEXTAI-FUTURE-STAGES-AUTHORITY-20261007-V1.json",
        "research/reviews/HAR01-LABEL-GUARD-source-V1.json", str(marker.relative_to(ROOT)).replace("\\", "/"),
        "research/events.jsonl"} | {PREFIX + suffix for suffix in (".stdout.txt", ".stderr.txt", ".xml") if (ROOT / (PREFIX + suffix)).exists()})
    archive = ROOT / "research/results/HAR01-LABEL-GUARD-CONFORMANCE-V1.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for p in files:
            bundle.write(ROOT / p, p)
        if temp.exists():
            for p in temp.rglob("*"):
                if p.is_file():
                    bundle.write(p, "synthetic-runtime/" + str(p.relative_to(temp)).replace("\\", "/"))
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        archived_hashes = {p: hashlib.sha256(bundle.read(p)).hexdigest() for p in bundle.namelist()}
    decision = "KEEP technical import/label-guard/exit conformance" if error is None else "INCONCLUSIVE technical conformance failure; stop unstarted scope"
    receipt_path = "research/laboratory/HAR01-LABEL-GUARD-COMPLETION-V1.receipt.json"
    receipt = {"created_at": datetime.now(timezone.utc).isoformat(), "study_sha256": SHA,
               "decision": decision, "error": error, "tests": count, "passed": passed, "failed": failed,
               "skipped": skipped, "job": asdict(result) if result else None, "retry": False,
               "native_intake": 0, "fit": 0, "EXP": 0, "registration": 0,
               "charged_seconds_conservative": 600, "prior_consumed_stage_seconds": 3000,
               "cumulative_first_replication_stage_seconds": 3600, "unused_unreleased_stage_seconds": 2400,
               "archive_sha256": digest(archive), "archive_files_sha256": archived_hashes,
               "parent_scientific_hashes_unchanged": True, "prior_ownership_helpers_AST_unchanged": True, "intake_function_AST_unchanged": True,
               "wallet": wallet, "deadline": plan["study_deadline_at"],
               "remaining_publication_included_in_charged_envelope": True, "full_goal": "ACTIVE/INCOMPLETE"}
    save(ROOT / receipt_path, receipt)
    event = {"event": "research_program_preparation_completed", "created_at": receipt["created_at"],
             "program_id": wallet["id"], "study_path": PLAN, "study_sha256": SHA,
             "receipt_path": receipt_path, "receipt_sha256": digest(ROOT / receipt_path), "decision": decision}
    with (ROOT / "research/events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
    report = f"""# HAR import and process-exit conformance â€” cycle339

Decision: **{decision}**. One canonical independent-clone invocation: {passed}/{count} PASS, {failed} failed, {skipped} skipped. Study SHA256 `{SHA}`; frozen before changes at6a1bc91. Prior49PASS/1FAIL source, XML, failure and costs remain unchanged.

The previously repaired standalone/dynamic import stays unchanged. The new version corrects only two synthetic label guards to compare complete ZIP basenames; all five payloads and remaining assertions are preserved. The failed V1 remains byte-identical. The intake functions' ASTs and all frozen model/geometry/analysis/process-supervisor bytes are unchanged. Five new import cases, six exact cost-ownership cases and three process-exit cases were preregistered. Synthetic cases exercise normal exit, explicit root failure and root failure with a live child; diagnostic outcomes actually executed are preserved in the runtime archive; missing/unrun cases are not evidence. The supervisor source was not repaired or weakened. A pre-cleanup live-child snapshot and actual cleanup completion are different observations.

Full600s is conservatively charged from the first replication's unused3000s, including this report and publication. Prior3000s stays consumed: cumulative3600/6000s; unused2400s is not released by technical success. B used28569.55024020007/72000s,1/12 registrations; protected43400s includes untouched other6 registrations/41000s plus current2400s. No budget/history reset or additional B grant.

Native intake, research fit, EXP and registration are all0. This technical study produces no ranking, source, update, UNKNOWN, confidence-interval or economic result. The earlier HAR DISCARD remains unchanged. Maintenance/scoring=false; broader two-family replication/fresh-target-final/prototype goal remains incomplete.

Machine receipt: `{receipt_path}`. Lossless source/diagnostic archive: `{archive.relative_to(ROOT)}`; SHA256 `{receipt['archive_sha256']}`. Every archived member was read and hashed after decompression. Error: `{error}`.

The human separately approved subsequent stages. Each still needs a new prospective frozen contract under unchanged scientific rules and existing budgets; this technical contract authorizes no native/EXP execution.
"""
    (ROOT / "research/analyses/HAR01-CYCLE339-IMPORT-EXIT-CONFORMANCE-V1.md").write_bytes(report.encode())
    assert datetime.now(timezone.utc) < DEADLINE
    print(json.dumps({"decision": decision, "tests": [passed, failed, skipped], "B_used": wallet["stage_b_compute_seconds_charged"], "protected": 43400, "created_at": receipt["created_at"]}), flush=True)
    return 0 if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
