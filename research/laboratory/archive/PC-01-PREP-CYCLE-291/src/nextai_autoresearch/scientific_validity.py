from __future__ import annotations

from pathlib import Path

from .ledger import read_jsonl, research_dir


def problems(root: Path | None = None) -> list[str]:
    base = research_dir(root)
    found: list[str] = []
    for event in read_jsonl(base / "events.jsonl"):
        if event.get("event") != "experiment_scientific_validity_correction":
            continue
        experiment_id = str(event.get("experiment_id", ""))
        if not experiment_id:
            found.append("scientific-validity correction lacks experiment_id")
            continue
        if event.get("scientific_validity") != "invalid":
            found.append(f"unsupported scientific-validity correction: {experiment_id}")
        if not str(event.get("reason", "")).strip():
            found.append(f"scientific-validity correction lacks reason: {experiment_id}")
        if not (base / "results" / f"{experiment_id}.json").is_file():
            found.append(f"scientific-validity correction references missing result: {experiment_id}")
        if not (base / "analyses" / f"{experiment_id}.md").is_file():
            found.append(f"scientific-validity correction references missing analysis: {experiment_id}")
    return found


def invalid_experiment_ids(root: Path | None = None) -> set[str]:
    return {
        str(event["experiment_id"])
        for event in read_jsonl(research_dir(root) / "events.jsonl")
        if event.get("event") == "experiment_scientific_validity_correction"
        and event.get("scientific_validity") == "invalid"
        and event.get("experiment_id")
    }
