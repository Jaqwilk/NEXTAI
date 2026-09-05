from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from .utils import project_root


SCHEMA_FILES = {
    "pc01_plan": "pc01_plan.schema.json",
    "pc01_result": "pc01_result.schema.json",
    "pc01_replica": "pc01_replica.schema.json",
    "laboratory_restart": "laboratory_restart.schema.json",
    "hypothesis": "hypothesis.schema.json",
    "experiment_plan": "experiment_plan.schema.json",
    "experiment_result": "experiment_result.schema.json",
    "research_state": "research_state.schema.json",
    "source": "source.schema.json",
}


def schema_path(name: str, root: Path | None = None) -> Path:
    try:
        filename = SCHEMA_FILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown schema: {name}") from exc
    return (root or project_root()) / "schemas" / filename


def load_schema(name: str, root: Path | None = None) -> dict[str, Any]:
    path = schema_path(name, root)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check_all_schemas(root: Path | None = None) -> list[str]:
    problems: list[str] = []
    for name in SCHEMA_FILES:
        try:
            Draft202012Validator.check_schema(load_schema(name, root))
        except (OSError, json.JSONDecodeError, SchemaError) as exc:
            problems.append(f"{name}: {exc}")
    return problems


def validate_document(name: str, value: Any, root: Path | None = None) -> None:
    if isinstance(value, dict):
        if name == "experiment_plan" and value.get("kind") == "pc01_diagnostic_plan":
            name = "pc01_plan"
        elif name == "experiment_result" and value.get("kind") == "pc01_diagnostic_result":
            name = "pc01_result"
    validator = Draft202012Validator(load_schema(name, root))
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if not errors:
        if name == "experiment_result":
            validate_metric_domains(value)
        return
    rendered: list[str] = []
    for error in errors[:20]:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        rendered.append(f"{location}: {error.message}")
    raise ValidationError("; ".join(rendered))


def validate_metric_domains(value: dict[str, Any]) -> None:
    """Enforce shared metric domains in summaries and final trial payloads."""
    problems: list[str] = []
    for candidate in value.get("candidates", ()):
        objects = [("summary", candidate.get("summary", {}))]
        objects.extend((f"trials.{index}", row) for index, row in enumerate(candidate.get("trials", ())))
        for location, metrics in objects:
            for metric, raw in metrics.items():
                if raw is None or isinstance(raw, bool) or not isinstance(raw, (int, float)):
                    continue
                number = float(raw)
                if not math.isfinite(number):
                    problems.append(f"{location}.{metric}: metric must be finite")
                    continue
                unit_interval = (
                    "accuracy" in metric
                    or metric.endswith("_rate")
                    or metric.endswith("_precision")
                    or metric.endswith("_coverage")
                    or metric.endswith("_retention")
                )
                nonnegative = (
                    "nrmse" in metric
                    or metric.endswith("normalized_rmse")
                    or "_ops" in metric
                    or "_bytes" in metric
                    or "latency_" in metric
                    or metric.endswith("_seconds")
                )
                if unit_interval and not 0.0 <= number <= 1.0:
                    problems.append(f"{location}.{metric}: rate/accuracy must be in [0, 1]")
                elif nonnegative and number < 0.0:
                    problems.append(f"{location}.{metric}: NRMSE/cost must be >= 0")
    if problems:
        raise ValidationError("; ".join(problems[:20]))
