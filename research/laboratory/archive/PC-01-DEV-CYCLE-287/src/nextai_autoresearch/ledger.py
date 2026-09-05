from __future__ import annotations

import csv
import json
import os
import re
import socket
import time
from contextlib import AbstractContextManager
from datetime import datetime
from pathlib import Path
from typing import Any

from .utils import atomic_write_json, load_json, project_root, sha256_json, utc_now


EXPERIMENT_HEADER = [
    "experiment_id",
    "hypothesis_id",
    "candidate",
    "budget",
    "status",
    "accuracy",
    "mean_query_ops",
    "p95_latency_us",
    "state_bytes",
    "knowledge_compute_slope",
    "depth_compute_slope",
    "integrity_ok",
    "plan_sha256",
    "result_path",
    "created_at",
]


def research_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "research"


def ensure_layout(root: Path | None = None) -> None:
    base = research_dir(root)
    for child in (
        "analyses",
        "logs",
        "plans",
        "results",
        "reviews",
        "tmp",
    ):
        (base / child).mkdir(parents=True, exist_ok=True)
    _ensure_text_file(base / "experiments.tsv", "\t".join(EXPERIMENT_HEADER) + "\n")
    _ensure_text_file(base / "hypothesis_events.jsonl", "")
    _ensure_text_file(base / "plan_registry.jsonl", "")
    _ensure_text_file(base / "plan_status_events.jsonl", "")
    _ensure_text_file(base / "sources.jsonl", "")
    _ensure_text_file(base / "events.jsonl", "")


def _ensure_text_file(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    values: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"Expected object at {path}:{line_number}")
            values.append(value)
    return values


def latest_hypotheses(root: Path | None = None) -> dict[str, dict[str, Any]]:
    path = research_dir(root) / "hypothesis_events.jsonl"
    latest: dict[str, dict[str, Any]] = {}
    for event in read_jsonl(path):
        hypothesis_id = event["hypothesis_id"]
        previous = latest.get(hypothesis_id)
        if previous is None or int(event["revision"]) > int(previous["revision"]):
            latest[hypothesis_id] = event
    return latest


def load_state(root: Path | None = None) -> dict[str, Any]:
    return load_json(research_dir(root) / "state.json")


def save_state(state: dict[str, Any], root: Path | None = None) -> None:
    atomic_write_json(research_dir(root) / "state.json", state)


def append_experiment_row(row: dict[str, Any], root: Path | None = None) -> None:
    path = research_dir(root) / "experiments.tsv"
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=EXPERIMENT_HEADER,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writerow({field: row.get(field, "") for field in EXPERIMENT_HEADER})
        handle.flush()
        os.fsync(handle.fileno())


def register_plan(plan: dict[str, Any], path: Path, root: Path | None = None) -> str:
    digest = sha256_json(plan)
    append_jsonl(
        research_dir(root) / "plan_registry.jsonl",
        {
            "experiment_id": plan["experiment_id"],
            "path": path.relative_to(root or project_root()).as_posix(),
            "plan_sha256": digest,
            "registered_at": utc_now(),
        },
    )
    return digest


def append_plan_status(
    experiment_id: str,
    status: str,
    reason: str,
    root: Path | None = None,
) -> None:
    if status != "invalidated":
        raise ValueError(f"Unsupported append-only plan status: {status!r}")
    if not reason.strip():
        raise ValueError("Plan invalidation requires a non-empty reason")
    if experiment_id in latest_plan_statuses(root):
        raise ValueError(f"Plan already has a terminal status event: {experiment_id}")
    append_jsonl(
        research_dir(root) / "plan_status_events.jsonl",
        {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "status": status,
            "reason": reason.strip(),
            "created_at": utc_now(),
        },
    )


def latest_plan_statuses(root: Path | None = None) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in read_jsonl(research_dir(root) / "plan_status_events.jsonl"):
        latest[str(event["experiment_id"])] = event
    return latest


def registered_plan_hash(experiment_id: str, root: Path | None = None) -> str | None:
    matches = [
        event
        for event in read_jsonl(research_dir(root) / "plan_registry.jsonl")
        if event.get("experiment_id") == experiment_id
    ]
    if not matches:
        return None
    return str(matches[-1]["plan_sha256"])


def next_experiment_id(root: Path | None = None) -> str:
    base = research_dir(root)
    date_part = datetime.now().strftime("%Y%m%d")
    pattern = re.compile(rf"^EXP-{date_part}-(\d{{4}})$")
    seen: set[int] = set()
    for directory in (base / "plans", base / "results"):
        if not directory.exists():
            continue
        for path in directory.glob(f"EXP-{date_part}-*.json"):
            match = pattern.match(path.stem)
            if match:
                seen.add(int(match.group(1)))
    number = 1
    while number in seen:
        number += 1
    return f"EXP-{date_part}-{number:04d}"


class RunLock(AbstractContextManager["RunLock"]):
    def __init__(self, root: Path | None = None, stale_seconds: int = 7200) -> None:
        self.root = root or project_root()
        self.path = research_dir(self.root) / "run.lock"
        self.stale_seconds = stale_seconds
        self.acquired = False

    def __enter__(self) -> "RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "created_at": utc_now(),
            "epoch": time.time(),
        }
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            existing = load_json(self.path)
            age = time.time() - float(existing.get("epoch", time.time()))
            if age <= self.stale_seconds:
                raise RuntimeError(f"Research run lock is active: {existing}") from exc
            stale_path = self.path.with_name(f"run.lock.stale-{int(time.time())}")
            os.replace(self.path, stale_path)
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.acquired = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.acquired and self.path.exists():
            self.path.unlink()
        self.acquired = False
