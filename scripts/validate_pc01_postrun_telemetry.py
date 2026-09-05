"""Validate prospective telemetry V2 without model execution or final-data access."""
from __future__ import annotations

import argparse
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from nextai_autoresearch.pc01_execution import authenticated_series_decision
from nextai_autoresearch.utils import atomic_write_json, load_json, project_root, sha256_file, utc_now


SOURCE = "research/laboratory/versions/PC-01-TELEMETRY-V2/pc01_telemetry.py"
PARENT = "src/nextai_autoresearch/pc01_telemetry.py"
PLAN = "research/plans/PC-01-POSTRUN-TELEMETRY-MAINTENANCE-V1.json"
AUTHORITY = "research/laboratory/PC-01-POSTRUN-TELEMETRY-MAINTENANCE-20260905-V1.json"
ATTEMPTS = "research/laboratory/pc01_attempts.jsonl"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def function_ast(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)
    return ast.dump(node, include_attributes=False)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def reader(source: Path, work: Path) -> int:
    telemetry = load_module(source, "pc01_telemetry_v2_reader")
    path = work / "device.json"
    reads, previous = 0, -1
    unavailable_since = None
    (work / "reader-ready").touch()
    deadline = time.monotonic() + 35
    while not (work / "reader-stop").exists():
        if time.monotonic() > deadline:
            raise TimeoutError("reader wall deadline")
        value = telemetry.read_device_sample(path)
        if value is None:
            unavailable_since = unavailable_since or time.monotonic()
            if time.monotonic() - unavailable_since >= 1:
                raise TimeoutError("persistent telemetry read unavailability")
            time.sleep(0.0005)
            continue
        unavailable_since = None
        if value["reserved"] != value["allocated"] * 2:
            raise AssertionError("incoherent telemetry pair")
        if value["allocated"] < previous:
            raise AssertionError("non-monotonic telemetry sample")
        previous = value["allocated"]
        reads += 1
        time.sleep(0.0005)
    print(json.dumps({"reads": reads, "last": previous}, sort_keys=True))
    return 0


def wait_for(path: Path, seconds: float = 5) -> None:
    deadline = time.monotonic() + seconds
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for {path.name}")
        time.sleep(0.005)


def validate(root: Path) -> dict:
    plan = load_json(root / PLAN)
    authority = load_json(root / AUTHORITY)
    source = root / SOURCE
    parent = root / PARENT
    if sha256_file(parent) != plan["parent_source_sha256"]:
        raise AssertionError("frozen V1 source changed")
    if sha256_file(root / authority["failed_report"]) != authority["failed_report_sha256"]:
        raise AssertionError("preserved failure report changed")
    if function_ast(parent, "write_device_sample") != function_ast(source, "write_device_sample"):
        raise AssertionError("V2 changed writer semantics")

    telemetry = load_module(source, "pc01_telemetry_v2_validation")
    controls: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="nextai-pc01-telemetry-v2-") as temporary:
        work = Path(temporary)
        sample = work / "sample.json"
        atomic_write_json(sample, {"allocated": 3, "reserved": 6})
        controls["valid_sample_exact"] = telemetry.read_device_sample(sample) == {"allocated": 3, "reserved": 6}

        missing = work / "missing.json"
        controls["transient_absence_returns_none"] = telemetry.read_device_sample(missing) is None
        atomic_write_json(missing, {"allocated": 4, "reserved": 8})
        controls["transient_absence_then_valid_recovers"] = telemetry.read_device_sample(missing) == {"allocated": 4, "reserved": 8}

        started = time.monotonic()
        while time.monotonic() - started < 1:
            if telemetry.read_device_sample(work / "persistently-absent.json") is not None:
                raise AssertionError("absent telemetry unexpectedly became valid")
            time.sleep(0.001)
        elapsed = time.monotonic() - started
        controls["persistent_absence_reaches_parent_deadline"] = 1 <= elapsed < 1.2

        malformed = work / "malformed.json"
        malformed.write_text("{not-json", encoding="utf-8")
        try:
            telemetry.read_device_sample(malformed)
        except json.JSONDecodeError:
            controls["malformed_json_fails_closed"] = True
        else:
            controls["malformed_json_fails_closed"] = False

        atomic_write_json(malformed, {"allocated": 8, "reserved": 7})
        try:
            telemetry.read_device_sample(malformed)
        except ValueError as exc:
            controls["malformed_schema_fails_closed"] = str(exc) == "Malformed device telemetry sample"
        else:
            controls["malformed_schema_fails_closed"] = False

        original_load = telemetry.load_json
        transient = PermissionError("synthetic transient")
        transient.winerror = 32
        telemetry.load_json = lambda path: (_ for _ in ()).throw(transient)
        controls["registered_windows_sharing_error_is_unavailable"] = telemetry.read_device_sample(sample) is None
        unrelated = PermissionError("synthetic unrelated")
        unrelated.winerror = 112
        telemetry.load_json = lambda path: (_ for _ in ()).throw(unrelated)
        try:
            telemetry.read_device_sample(sample)
        except PermissionError:
            controls["unrelated_permission_error_fails_closed"] = True
        else:
            controls["unrelated_permission_error_fails_closed"] = False
        finally:
            telemetry.load_json = original_load

        stress = []
        script = Path(__file__).resolve()
        for repetition in range(3):
            case = work / f"stress-{repetition}"
            case.mkdir()
            path = case / "device.json"
            atomic_write_json(path, {"allocated": 0, "reserved": 0})
            process = subprocess.Popen(
                [sys.executable, str(script), "--reader-work", str(case), "--source", str(source)],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            wait_for(case / "reader-ready")
            case_started, retries = time.monotonic(), 0
            recovery_log = io.StringIO()
            try:
                with contextlib.redirect_stdout(recovery_log):
                    for index in range(1, 2001):
                        if time.monotonic() - case_started >= 30:
                            raise TimeoutError("stress writer wall deadline")
                        retries += telemetry.write_device_sample(
                            path, {"allocated": index, "reserved": index * 2}, root
                        )
            finally:
                (case / "reader-stop").touch()
                stdout, stderr = process.communicate(timeout=5)
            if process.returncode != 0:
                raise AssertionError(f"stress reader {repetition} failed: {stderr}{stdout}")
            stats = json.loads(stdout)
            if stats["reads"] <= 0 or load_json(path) != {"allocated": 2000, "reserved": 4000}:
                raise AssertionError("stress case lacks coherent completed reads")
            if list(case.glob(".device.json.*.tmp")):
                raise AssertionError("stress case left temporary files")
            stress.append({
                "repetition": repetition,
                "writes": 2000,
                "reads": stats["reads"],
                "last_reader_value": stats["last"],
                "writer_retries": retries,
                "seconds": time.monotonic() - case_started,
                "recovery_log_lines": len(recovery_log.getvalue().splitlines()),
            })

    finished = {
        row["experiment_id"]: row["result_sha256"]
        for row in read_jsonl(root / ATTEMPTS)
        if row.get("event") == "finished" and row["experiment_id"] in {
            "EXP-20260905-0003", "EXP-20260905-0004", "EXP-20260905-0005"
        }
    }
    if set(finished) != {"EXP-20260905-0003", "EXP-20260905-0004", "EXP-20260905-0005"}:
        raise AssertionError("final-result completion set changed")
    for identifier, digest in finished.items():
        if sha256_file(root / "research/results" / f"{identifier}.json") != digest:
            raise AssertionError(f"completed result changed: {identifier}")
    decision = authenticated_series_decision(root)
    if decision["decision"] != "positive_control_pass":
        raise AssertionError("authenticated series decision changed")
    if not all(controls.values()):
        raise AssertionError(f"dedicated control failed: {controls}")
    return {
        "schema_version": 1,
        "kind": "pc01_postrun_telemetry_v2_validation",
        "created_at": utc_now(),
        "status": "complete",
        "training_performed": False,
        "scoring_performed": False,
        "final_data_accessed": False,
        "plan_path": PLAN,
        "plan_sha256": sha256_file(root / PLAN),
        "authority_path": AUTHORITY,
        "authority_sha256": sha256_file(root / AUTHORITY),
        "parent_source_path": PARENT,
        "parent_source_sha256": sha256_file(parent),
        "prospective_source_path": SOURCE,
        "prospective_source_sha256": sha256_file(source),
        "writer_ast_identical": True,
        "controls": controls,
        "stress": stress,
        "preserved_final_result_sha256": finished,
        "series_decision": decision,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    parser.add_argument("--reader-work", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.reader_work is not None:
        if args.source is None:
            parser.error("--source is required with --reader-work")
        return reader(args.source.resolve(), args.reader_work.resolve())
    if args.report is None:
        parser.error("--report is required")
    root = project_root()
    value = validate(root)
    report = args.report if args.report.is_absolute() else root / args.report
    atomic_write_json(report, value)
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
